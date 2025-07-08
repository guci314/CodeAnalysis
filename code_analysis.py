"""
Main CodeAnalysis Class for Python Project Analysis
"""

import os
import ast
import json
import logging
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import networkx as nx
from deepseek_analyzer import DeepSeekAnalyzer
from community_detector import CommunityDetector
from datetime import datetime


class CodeElement:
    """Represents a code element (class, function, module)."""
    
    def __init__(self, element_type: str, name: str, file_path: str, 
                 line_number: int, complexity: int = 1, docstring: str = ""):
        self.type = element_type  # 'class', 'function', 'module'
        self.name = name
        self.file_path = file_path
        self.line_number = line_number
        self.complexity = complexity
        self.docstring = docstring
        self.dependencies: List[str] = []
        self.semantic_info: Dict[str, Any] = {}
        self.methods: List[str] = []  # For classes
        self.parameters: List[str] = []  # For functions
        self.decorators: List[str] = []
        self.inheritance: List[str] = []  # For classes
        self.calls: List[str] = []  # Functions/methods called
        self.imports: List[str] = []  # For modules
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'type': self.type,
            'name': self.name,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'complexity': self.complexity,
            'docstring': self.docstring,
            'dependencies': self.dependencies,
            'semantic_info': self.semantic_info,
            'methods': self.methods,
            'parameters': self.parameters,
            'decorators': self.decorators,
            'inheritance': self.inheritance,
            'calls': self.calls,
            'imports': self.imports
        }
    
    def __repr__(self):
        return f"CodeElement({self.type}, {self.name}, {self.file_path}:{self.line_number})"


class Relationship:
    """Represents a relationship between code elements."""
    
    def __init__(self, source: str, target: str, rel_type: str, 
                 weight: float = 1.0, context: str = ""):
        self.source = source
        self.target = target
        self.type = rel_type  # 'inherit', 'call', 'import', 'compose'
        self.weight = weight
        self.context = context
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'source': self.source,
            'target': self.target,
            'type': self.type,
            'weight': self.weight,
            'context': self.context
        }


class CodeAnalysis:
    """
    Main class for analyzing Python project structure and building knowledge graphs.
    """
    
    def __init__(self, project_path: str, enable_deepseek: bool = True):
        """
        Initialize CodeAnalysis with project path.
        
        Args:
            project_path: Path to the Python project to analyze
            enable_deepseek: Whether to enable DeepSeek AI analysis
        """
        self.project_path = Path(project_path)
        if not self.project_path.exists():
            raise FileNotFoundError(f"Project path does not exist: {project_path}")
        
        # Initialize components
        self.enable_deepseek = enable_deepseek
        if enable_deepseek:
            try:
                self.deepseek_analyzer = DeepSeekAnalyzer()
            except Exception as e:
                self.logger.warning(f"DeepSeek initialization failed: {e}")
                self.deepseek_analyzer = None
                self.enable_deepseek = False
        else:
            self.deepseek_analyzer = None
        
        self.graph = nx.Graph()
        self.code_elements: Dict[str, CodeElement] = {}
        self.relationships: List[Relationship] = []
        self.analysis_results: Dict[str, Any] = {}
        
        # Configuration
        self.max_file_size = int(os.getenv('MAX_FILE_SIZE', '1000000'))  # 1MB
        self.excluded_dirs = {'__pycache__', '.git', '.venv', 'venv', 'node_modules', '.pytest_cache'}
        self.included_extensions = {'.py'}
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"CodeAnalysis initialized for project: {self.project_path}")
    
    def analyze_project(self) -> Dict[str, Any]:
        """
        Perform complete project analysis.
        
        Returns:
            Dictionary containing analysis results
        """
        self.logger.info("Starting project analysis...")
        
        try:
            # Step 1: Scan Python files
            python_files = self.scan_python_files()
            self.logger.info(f"Found {len(python_files)} Python files")
            
            # Step 2: Parse files and extract code elements
            self._parse_all_files(python_files)
            self.logger.info(f"Extracted {len(self.code_elements)} code elements")
            
            # Step 3: Build knowledge graph
            self.build_knowledge_graph()
            self.logger.info(f"Built knowledge graph with {len(self.graph.nodes)} nodes and {len(self.graph.edges)} edges")
            
            # Step 4: DeepSeek analysis optimization - moved to community description phase
            # ❌ 注释掉逐个代码元素的DeepSeek分析 (性能优化)
            # 原因: 3217次API调用导致16小时执行时间，改为仅在社区描述时使用
            # if (self.enable_deepseek and self.deepseek_analyzer and 
            #     self.deepseek_analyzer.is_available()):
            #     self._analyze_with_deepseek()
            #     self.logger.info("DeepSeek analysis completed")
            # else:
            #     if not self.enable_deepseek:
            #         self.logger.info("DeepSeek analysis disabled")
            #     else:
            #         self.logger.warning("DeepSeek analysis skipped - API not available")
            
            # ✅ 新的策略: DeepSeek仅用于社区级别的功能描述分析
            self.logger.info("DeepSeek analysis optimized - will be used only for community descriptions")
            
            # Step 5: Generate analysis results
            self.analysis_results = self._generate_analysis_results()
            self.logger.info("Project analysis completed successfully")
            
            return self.analysis_results
            
        except Exception as e:
            self.logger.error(f"Error during project analysis: {str(e)}")
            raise
    
    def scan_python_files(self) -> List[str]:
        """
        Recursively scan project directory for Python files.
        
        Returns:
            List of Python file paths
        """
        python_files = []
        
        for root, dirs, files in os.walk(self.project_path):
            # Exclude certain directories
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in self.included_extensions):
                    file_path = os.path.join(root, file)
                    
                    # Check file size
                    try:
                        if os.path.getsize(file_path) <= self.max_file_size:
                            python_files.append(file_path)
                        else:
                            self.logger.warning(f"Skipping large file: {file_path}")
                    except OSError as e:
                        self.logger.warning(f"Error checking file size: {file_path} - {e}")
        
        return python_files
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a single Python file and extract code elements.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            Dictionary containing extracted elements
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (UnicodeDecodeError, IOError) as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return {'classes': [], 'functions': [], 'imports': [], 'semantic_info': {}}
        
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            self.logger.error(f"Syntax error in file {file_path}: {e}")
            return {'classes': [], 'functions': [], 'imports': [], 'semantic_info': {}}
        
        # Extract elements
        classes = self.extract_classes(tree, file_path)
        functions = self.extract_functions(tree, file_path)
        imports = self.extract_imports(tree, file_path)
        
        # Store elements
        for cls in classes:
            element_id = f"{file_path}:{cls.name}"
            self.code_elements[element_id] = cls
        
        for func in functions:
            element_id = f"{file_path}:{func.name}"
            self.code_elements[element_id] = func
        
        # ❌ DeepSeek analysis moved to community description phase for performance optimization
        # 原因: 逐个文件分析导致过多API调用，现在仅在社区描述阶段使用DeepSeek
        semantic_info = {}
        # if (self.enable_deepseek and self.deepseek_analyzer and 
        #     self.deepseek_analyzer.is_available() and content.strip()):
        #     try:
        #         semantic_info = self.deepseek_analyzer.analyze_code_function(content)
        #     except Exception as e:
        #         self.logger.warning(f"DeepSeek analysis failed for {file_path}: {e}")
        
        return {
            'file_path': file_path,
            'classes': [cls.to_dict() for cls in classes],
            'functions': [func.to_dict() for func in functions],
            'imports': imports,
            'semantic_info': semantic_info
        }
    
    def extract_classes(self, ast_node: ast.AST, file_path: str) -> List[CodeElement]:
        """
        Extract class information from AST.
        
        Args:
            ast_node: AST node to analyze
            file_path: Path to the source file
            
        Returns:
            List of CodeElement objects representing classes
        """
        classes = []
        
        for node in ast.walk(ast_node):
            if isinstance(node, ast.ClassDef):
                class_element = CodeElement(
                    element_type='class',
                    name=node.name,
                    file_path=file_path,
                    line_number=node.lineno,
                    docstring=ast.get_docstring(node) or ""
                )
                
                # Extract methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        class_element.methods.append(item.name)
                
                # Extract inheritance
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        class_element.inheritance.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        class_element.inheritance.append(ast.unparse(base))
                
                # Extract decorators
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        class_element.decorators.append(decorator.id)
                    else:
                        class_element.decorators.append(ast.unparse(decorator))
                
                classes.append(class_element)
        
        return classes
    
    def extract_functions(self, ast_node: ast.AST, file_path: str) -> List[CodeElement]:
        """
        Extract function information from AST.
        
        Args:
            ast_node: AST node to analyze
            file_path: Path to the source file
            
        Returns:
            List of CodeElement objects representing functions
        """
        functions = []
        
        for node in ast.walk(ast_node):
            if isinstance(node, ast.FunctionDef):
                # Skip methods (functions inside classes)
                parent = getattr(node, 'parent', None)
                if parent and isinstance(parent, ast.ClassDef):
                    continue
                
                func_element = CodeElement(
                    element_type='function',
                    name=node.name,
                    file_path=file_path,
                    line_number=node.lineno,
                    docstring=ast.get_docstring(node) or ""
                )
                
                # Extract parameters
                for arg in node.args.args:
                    func_element.parameters.append(arg.arg)
                
                # Extract decorators
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        func_element.decorators.append(decorator.id)
                    else:
                        func_element.decorators.append(ast.unparse(decorator))
                
                # Extract function calls
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            func_element.calls.append(child.func.id)
                        elif isinstance(child.func, ast.Attribute):
                            func_element.calls.append(ast.unparse(child.func))
                
                functions.append(func_element)
        
        return functions
    
    def extract_imports(self, ast_node: ast.AST, file_path: str) -> List[str]:
        """
        Extract import statements from AST.
        
        Args:
            ast_node: AST node to analyze
            file_path: Path to the source file
            
        Returns:
            List of import statements
        """
        imports = []
        
        for node in ast.walk(ast_node):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        imports.append(f"{node.module}.{alias.name}")
        
        return imports
    
    def build_knowledge_graph(self):
        """Build knowledge graph from extracted code elements."""
        # Add nodes
        for element_id, element in self.code_elements.items():
            self.graph.add_node(element_id, **element.to_dict())
        
        # Add edges based on relationships
        self._add_inheritance_edges()
        self._add_call_edges()
        self._add_import_edges()
    
    def _parse_all_files(self, python_files: List[str]):
        """Parse all Python files in the project."""
        for file_path in python_files:
            try:
                self.parse_file(file_path)
            except Exception as e:
                self.logger.error(f"Error parsing file {file_path}: {e}")
    
    def _analyze_with_deepseek(self):
        """Analyze code elements with DeepSeek."""
        for element_id, element in self.code_elements.items():
            try:
                # Read file content for analysis
                with open(element.file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Analyze with DeepSeek
                analysis = self.deepseek_analyzer.analyze_code_function(content)
                element.semantic_info = analysis
                
            except Exception as e:
                self.logger.warning(f"DeepSeek analysis failed for {element_id}: {e}")
    
    def _add_inheritance_edges(self):
        """Add inheritance relationship edges."""
        for element_id, element in self.code_elements.items():
            if element.type == 'class':
                for base_class in element.inheritance:
                    # Find base class in code elements
                    for other_id, other_element in self.code_elements.items():
                        if other_element.name == base_class and other_element.type == 'class':
                            self.graph.add_edge(element_id, other_id, 
                                              relationship='inherit', weight=1.0)
    
    def _add_call_edges(self):
        """Add function call relationship edges."""
        for element_id, element in self.code_elements.items():
            if element.type == 'function':
                for call in element.calls:
                    # Find called function
                    for other_id, other_element in self.code_elements.items():
                        if other_element.name == call and other_element.type == 'function':
                            self.graph.add_edge(element_id, other_id, 
                                              relationship='call', weight=1.0)
    
    def _add_import_edges(self):
        """Add import relationship edges."""
        # Implementation depends on specific import analysis requirements
        pass
    
    def _generate_analysis_results(self) -> Dict[str, Any]:
        """Generate comprehensive analysis results."""
        return {
            'total_files': len(set(element.file_path for element in self.code_elements.values())),
            'total_classes': len([e for e in self.code_elements.values() if e.type == 'class']),
            'total_functions': len([e for e in self.code_elements.values() if e.type == 'function']),
            'graph_nodes': len(self.graph.nodes),
            'graph_edges': len(self.graph.edges),
            'code_elements': {k: v.to_dict() for k, v in self.code_elements.items()},
            'timestamp': str(Path.cwd())  # Placeholder for timestamp
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the analysis results."""
        if not self.analysis_results:
            return {'error': 'No analysis results available. Run analyze_project() first.'}
        
        return {
            'project_path': str(self.project_path),
            'total_files': self.analysis_results.get('total_files', 0),
            'total_classes': self.analysis_results.get('total_classes', 0),
            'total_functions': self.analysis_results.get('total_functions', 0),
            'graph_complexity': {
                'nodes': self.analysis_results.get('graph_nodes', 0),
                'edges': self.analysis_results.get('graph_edges', 0)
            }
        }
    
    def detect_communities(self, algorithm: str = 'leiden', **kwargs) -> Dict[str, Any]:
        """
        Detect communities in the code graph.
        
        Args:
            algorithm: Algorithm to use ('leiden', 'louvain', 'girvan_newman', 'label_propagation')
            **kwargs: Additional parameters for the algorithm
            
        Returns:
            Dictionary containing community detection results
        """
        if len(self.graph.nodes) == 0:
            raise ValueError("No graph available. Run analyze_project() first.")
        
        detector = CommunityDetector(self.graph)
        results = detector.detect_communities(algorithm, **kwargs)
        
        # Add recommendations
        recommendations = detector.get_community_recommendations(
            results['communities'], 
            results['statistics']
        )
        results['recommendations'] = recommendations
        
        return results
    
    def analyze_community_structure(self, communities: Dict[str, int]) -> Dict[str, Any]:
        """
        Analyze the structure of detected communities.
        
        Args:
            communities: Dictionary mapping nodes to community IDs
            
        Returns:
            Dictionary containing detailed community analysis
        """
        if len(self.graph.nodes) == 0:
            raise ValueError("No graph available. Run analyze_project() first.")
        
        detector = CommunityDetector(self.graph)
        return detector._analyze_community_structure(communities)
    
    def compare_community_algorithms(self, algorithms: List[str] = None) -> Dict[str, Any]:
        """
        Compare multiple community detection algorithms.
        
        Args:
            algorithms: List of algorithm names to compare
            
        Returns:
            Dictionary containing comparison results
        """
        if len(self.graph.nodes) == 0:
            raise ValueError("No graph available. Run analyze_project() first.")
        
        detector = CommunityDetector(self.graph)
        return detector.compare_algorithms(algorithms)
    
    def generate_report(self, output_dir: str = "analysis_output", 
                       include_communities: bool = True,
                       enable_ai_descriptions: bool = False) -> Dict[str, str]:
        """
        Generate comprehensive analysis report with natural language descriptions.
        
        Args:
            output_dir: Directory to save reports
            include_communities: Whether to include community analysis
            enable_ai_descriptions: Whether to generate AI-powered community descriptions
            
        Returns:
            Dictionary containing paths to generated files
        """
        if not self.analysis_results:
            raise ValueError("No analysis results available. Run analyze_project() first.")
        
        from text_reporter import TextReporter
        reporter = TextReporter(output_dir)
        generated_files = {}
        
        # Detect communities if requested
        community_results = None
        community_descriptions = None
        
        if include_communities and len(self.graph.nodes) > 0:
            try:
                community_results = self.detect_communities()
                self.logger.info("Community detection completed for report")
                
                # Generate AI-powered community descriptions if enabled
                if enable_ai_descriptions and community_results:
                    self.logger.info("🤖 Generating AI-powered community descriptions...")
                    community_descriptions = self._generate_ai_community_descriptions(
                        community_results.get('communities', {})
                    )
                    
            except Exception as e:
                self.logger.warning(f"Community detection failed for report: {e}")
        
        # Generate comprehensive text report
        try:
            report_path = reporter.generate_comprehensive_report(
                self.analysis_results, community_results, community_descriptions
            )
            generated_files['text_report'] = report_path
        except Exception as e:
            self.logger.error(f"Failed to generate text report: {e}")
        
        # Export JSON results
        try:
            json_path = reporter.export_results_json(
                self.analysis_results, community_results
            )
            generated_files['json_export'] = json_path
        except Exception as e:
            self.logger.error(f"Failed to export JSON: {e}")
        
        self.logger.info(f"Report generation completed. Files: {list(generated_files.keys())}")
        return generated_files
    
    def export_graph(self, file_path: str, format: str = 'graphml'):
        """
        Export the knowledge graph to a file.
        
        Args:
            file_path: Path to save the graph file
            format: Export format ('graphml', 'gexf', 'json', 'edgelist')
        """
        if len(self.graph.nodes) == 0:
            raise ValueError("No graph available. Run analyze_project() first.")
        
        if format == 'graphml':
            nx.write_graphml(self.graph, file_path)
        elif format == 'gexf':
            nx.write_gexf(self.graph, file_path)
        elif format == 'json':
            data = nx.node_link_data(self.graph)
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        elif format == 'edgelist':
            nx.write_edgelist(self.graph, file_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_ai_community_descriptions(self, communities: Dict[str, int]) -> Dict[str, Any]:
        """
        Generate AI-powered community descriptions using async DeepSeek.
        
        Args:
            communities: Dictionary mapping node names to community IDs
            
        Returns:
            Dictionary containing AI-generated community descriptions
        """
        try:
            # Import the async community description generator
            from community_description_generator import CommunityDescriptionGenerator
            
            # Convert communities mapping to structured community data
            community_data = self._prepare_community_data_for_ai(communities)
            
            # Create generator with configurable settings
            max_concurrent = int(os.getenv('DEEPSEEK_MAX_CONCURRENT_REQUESTS', '20'))
            request_delay = float(os.getenv('DEEPSEEK_REQUEST_DELAY', '0.1'))
            
            desc_generator = CommunityDescriptionGenerator(
                max_concurrent_requests=max_concurrent,  # Configurable concurrency
                request_delay=request_delay               # Configurable delay
            )
            
            # Generate descriptions synchronously (handles async internally)
            descriptions = desc_generator.generate_descriptions_sync(community_data)
            
            # Generate meaningful names for communities
            descriptions_with_names = self._add_meaningful_names_to_descriptions(
                descriptions, community_data
            )
            
            self.logger.info(f"✅ AI descriptions generated for {len(descriptions_with_names)} communities")
            return descriptions_with_names
            
        except ImportError:
            self.logger.warning("CommunityDescriptionGenerator not available, skipping AI descriptions")
            return {}
        except Exception as e:
            self.logger.error(f"Failed to generate AI community descriptions: {e}")
            return {}
    
    def _prepare_community_data_for_ai(self, communities: Dict[str, int]) -> Dict[str, Dict[str, Any]]:
        """
        Convert community membership mapping to structured data for AI analysis.
        Only includes meaningful communities (size >= 2).
        
        Args:
            communities: Dictionary mapping node names to community IDs
            
        Returns:
            Dictionary with community IDs as keys and structured data as values
        """
        # Group nodes by community
        community_groups = {}
        for node, comm_id in communities.items():
            if comm_id not in community_groups:
                community_groups[comm_id] = []
            community_groups[comm_id].append(node)
        
        # Build structured data for meaningful communities only
        community_data = {}
        min_community_size = int(os.getenv('MIN_COMMUNITY_SIZE_FOR_AI', '5'))  # 可配置的最小社区大小
        
        for comm_id, members in community_groups.items():
            size = len(members)
            
            # 只分析有意义的社区（包含多个成员）
            if size < min_community_size:
                continue
                
            # Get code elements for this community
            community_elements = []
            for member in members:
                if member in self.code_elements:
                    element = self.code_elements[member]
                    community_elements.append({
                        'type': element.type,
                        'name': element.name,
                        'file_path': element.file_path,
                        'docstring': element.docstring
                    })
            
            community_data[str(comm_id)] = {
                'id': comm_id,
                'size': size,
                'nodes': members,  # AsyncDeepSeekAnalyzer expects 'nodes' field
                'elements': community_elements,
                'cohesion': 0.0,  # Will be filled by community stats if available
                'coupling': 0.0   # Will be filled by community stats if available
            }
        
        # 记录过滤统计
        total_communities = len(community_groups)
        meaningful_communities = len(community_data)
        filtered_out = total_communities - meaningful_communities
        
        self.logger.info(f"🎯 AI分析社区过滤:")
        self.logger.info(f"   - 总社区数: {total_communities}")
        self.logger.info(f"   - 有意义社区 (>={min_community_size}成员): {meaningful_communities}")
        self.logger.info(f"   - 过滤掉单元素社区: {filtered_out}")
        
        return community_data
    
    def _add_meaningful_names_to_descriptions(self, descriptions: Dict[str, Any], 
                                             community_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        为社区描述添加有意义的名称，使用DeepSeek API并发生成智能名称。
        
        Args:
            descriptions: AI生成的社区描述
            community_data: 社区数据
            
        Returns:
            包含有意义名称的描述字典
        """
        try:
            # 检查是否启用智能命名
            enable_naming = os.getenv('ENABLE_MEANINGFUL_COMMUNITY_NAMES', 'true').lower() == 'true'
            use_deepseek_naming = os.getenv('USE_DEEPSEEK_NAMING', 'true').lower() == 'true'
            
            if not enable_naming:
                # 如果禁用命名，直接返回原始描述
                self.logger.info("Community naming disabled, using original descriptions")
                return descriptions
            
            # 尝试使用DeepSeek API进行命名
            if use_deepseek_naming and self.enable_deepseek:
                try:
                    from deepseek_community_namer import DeepSeekCommunityNamer
                    
                    # 配置并发参数
                    max_concurrent = int(os.getenv('DEEPSEEK_MAX_CONCURRENT_REQUESTS', '8'))
                    request_delay = float(os.getenv('DEEPSEEK_REQUEST_DELAY', '0.1'))
                    
                    # 创建DeepSeek命名器
                    deepseek_namer = DeepSeekCommunityNamer(
                        max_concurrent_requests=max_concurrent,
                        request_delay=request_delay
                    )
                    
                    # 只对有意义的社区生成名称（并发调用DeepSeek）
                    self.logger.info("🚀 Using DeepSeek API to generate intelligent community names...")
                    generated_names = deepseek_namer.generate_names_for_communities(community_data)
                    
                    # 将生成的名称添加到描述中
                    enhanced_descriptions = {}
                    for comm_id, description in descriptions.items():
                        enhanced_description = description.copy()
                        
                        # 使用DeepSeek生成的名称，如果有的话
                        if comm_id in generated_names:
                            meaningful_name = generated_names[comm_id]
                            self.logger.debug(f"DeepSeek generated name for community {comm_id}: {meaningful_name}")
                        else:
                            # 对于小社区或API失败的情况，使用默认名称
                            meaningful_name = f"Community {comm_id}"
                        
                        enhanced_description['meaningful_name'] = meaningful_name
                        enhanced_description['original_id'] = comm_id
                        
                        # 添加社区成员信息用于报告显示
                        if comm_id in community_data:
                            community_info = community_data[comm_id]
                            enhanced_description['nodes'] = community_info.get('nodes', [])
                            enhanced_description['elements'] = community_info.get('elements', [])
                            enhanced_description['size'] = community_info.get('size', 0)
                        
                        enhanced_descriptions[comm_id] = enhanced_description
                    
                    self.logger.info(f"✅ DeepSeek generated names for {len(generated_names)} meaningful communities")
                    return enhanced_descriptions
                    
                except ImportError:
                    self.logger.warning("DeepSeekCommunityNamer not available, falling back to local naming")
                except Exception as e:
                    self.logger.warning(f"DeepSeek naming failed: {e}, falling back to local naming")
            
            # 备用方案：使用本地模式匹配命名器
            try:
                from community_namer import CommunityNamer
                
                # 获取配置
                language = os.getenv('COMMUNITY_NAME_LANGUAGE', 'zh')
                style = os.getenv('COMMUNITY_NAME_STYLE', 'descriptive')
                
                # 创建本地命名器
                local_namer = CommunityNamer(language=language, style=style)
                
                # 为每个社区生成名称
                enhanced_descriptions = {}
                for comm_id, description in descriptions.items():
                    if comm_id in community_data:
                        # 生成有意义的名称
                        meaningful_name = local_namer.generate_community_name(
                            community_data[comm_id], 
                            description
                        )
                        
                        # 添加名称和社区数据到描述中
                        enhanced_description = description.copy()
                        enhanced_description['meaningful_name'] = meaningful_name
                        enhanced_description['original_id'] = comm_id
                        
                        # 添加社区成员信息用于报告显示
                        community_info = community_data[comm_id]
                        enhanced_description['nodes'] = community_info.get('nodes', [])
                        enhanced_description['elements'] = community_info.get('elements', [])
                        enhanced_description['size'] = community_info.get('size', 0)
                        
                        enhanced_descriptions[comm_id] = enhanced_description
                        
                        self.logger.debug(f"Local naming for community {comm_id}: {meaningful_name}")
                    else:
                        # 如果没有对应的社区数据，保持原样
                        enhanced_descriptions[comm_id] = description
                
                self.logger.info(f"🏷️  Generated meaningful names for {len(enhanced_descriptions)} communities (local fallback)")
                return enhanced_descriptions
                
            except ImportError:
                self.logger.warning("Local CommunityNamer not available, using original descriptions")
                return descriptions
            
        except Exception as e:
            self.logger.error(f"Error adding meaningful names: {e}")
            return descriptions