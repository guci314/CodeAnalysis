"""
Comprehensive test suite for CodeAnalysis system
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import networkx as nx

# Import modules to test
from code_analysis import CodeAnalysis, CodeElement, Relationship
from deepseek_analyzer import DeepSeekAnalyzer
from community_detector import CommunityDetector
from visualization import CodeAnalysisReporter


class TestCodeElement(unittest.TestCase):
    """Test CodeElement class."""
    
    def test_code_element_creation(self):
        """Test creating a CodeElement."""
        element = CodeElement(
            element_type='class',
            name='TestClass',
            file_path='/test/file.py',
            line_number=10,
            complexity=5,
            docstring='Test class'
        )
        
        self.assertEqual(element.type, 'class')
        self.assertEqual(element.name, 'TestClass')
        self.assertEqual(element.file_path, '/test/file.py')
        self.assertEqual(element.line_number, 10)
        self.assertEqual(element.complexity, 5)
        self.assertEqual(element.docstring, 'Test class')
    
    def test_code_element_to_dict(self):
        """Test converting CodeElement to dictionary."""
        element = CodeElement('function', 'test_func', '/test.py', 1)
        element.parameters = ['param1', 'param2']
        element.calls = ['other_func']
        
        result = element.to_dict()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['type'], 'function')
        self.assertEqual(result['name'], 'test_func')
        self.assertEqual(result['parameters'], ['param1', 'param2'])
        self.assertEqual(result['calls'], ['other_func'])


class TestRelationship(unittest.TestCase):
    """Test Relationship class."""
    
    def test_relationship_creation(self):
        """Test creating a Relationship."""
        rel = Relationship('ClassA', 'ClassB', 'inherit', 1.0, 'inheritance context')
        
        self.assertEqual(rel.source, 'ClassA')
        self.assertEqual(rel.target, 'ClassB')
        self.assertEqual(rel.type, 'inherit')
        self.assertEqual(rel.weight, 1.0)
        self.assertEqual(rel.context, 'inheritance context')
    
    def test_relationship_to_dict(self):
        """Test converting Relationship to dictionary."""
        rel = Relationship('A', 'B', 'call', 0.5)
        result = rel.to_dict()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['source'], 'A')
        self.assertEqual(result['target'], 'B')
        self.assertEqual(result['type'], 'call')
        self.assertEqual(result['weight'], 0.5)


class TestCodeAnalysis(unittest.TestCase):
    """Test CodeAnalysis main class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory with sample Python files
        self.temp_dir = tempfile.mkdtemp()
        self.sample_files = self._create_sample_files()
        
        # Mock DeepSeekAnalyzer to avoid API calls
        self.deepseek_patcher = patch('code_analysis.DeepSeekAnalyzer')
        self.mock_deepseek_class = self.deepseek_patcher.start()
        self.mock_deepseek = Mock()
        self.mock_deepseek.is_available.return_value = False
        self.mock_deepseek_class.return_value = self.mock_deepseek
        
        self.analyzer = CodeAnalysis(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        self.deepseek_patcher.stop()
        shutil.rmtree(self.temp_dir)
    
    def _create_sample_files(self):
        """Create sample Python files for testing."""
        files = {}
        
        # Simple class file
        class_file = Path(self.temp_dir) / 'test_class.py'
        class_content = '''
class TestClass:
    """A test class."""
    
    def __init__(self):
        self.value = 0
    
    def get_value(self):
        """Get the value."""
        return self.value
    
    def set_value(self, value):
        """Set the value."""
        self.value = value
'''
        class_file.write_text(class_content)
        files['class'] = str(class_file)
        
        # Function file
        func_file = Path(self.temp_dir) / 'test_functions.py'
        func_content = '''
def add_numbers(a, b):
    """Add two numbers."""
    return a + b

def multiply_numbers(a, b):
    """Multiply two numbers."""
    result = add_numbers(a, 0)
    for _ in range(b - 1):
        result = add_numbers(result, a)
    return result
'''
        func_file.write_text(func_content)
        files['functions'] = str(func_file)
        
        # Import file
        import_file = Path(self.temp_dir) / 'test_imports.py'
        import_content = '''
import os
import sys
from pathlib import Path
from typing import List, Dict

def process_files():
    """Process files."""
    pass
'''
        import_file.write_text(import_content)
        files['imports'] = str(import_file)
        
        return files
    
    def test_initialization(self):
        """Test CodeAnalysis initialization."""
        self.assertEqual(str(self.analyzer.project_path), self.temp_dir)
        self.assertIsInstance(self.analyzer.graph, nx.Graph)
        self.assertEqual(len(self.analyzer.code_elements), 0)
    
    def test_invalid_project_path(self):
        """Test initialization with invalid project path."""
        with self.assertRaises(FileNotFoundError):
            CodeAnalysis('/nonexistent/path')
    
    def test_scan_python_files(self):
        """Test scanning Python files."""
        files = self.analyzer.scan_python_files()
        
        self.assertGreater(len(files), 0)
        self.assertTrue(all(f.endswith('.py') for f in files))
        # Should find our test files
        file_names = [os.path.basename(f) for f in files]
        self.assertIn('test_class.py', file_names)
        self.assertIn('test_functions.py', file_names)
        self.assertIn('test_imports.py', file_names)
    
    def test_parse_file_class(self):
        """Test parsing a file with classes."""
        result = self.analyzer.parse_file(self.sample_files['class'])
        
        self.assertIn('classes', result)
        self.assertIn('functions', result)
        self.assertIn('imports', result)
        
        classes = result['classes']
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0]['name'], 'TestClass')
        self.assertEqual(classes[0]['type'], 'class')
        
        # Check if methods were extracted
        methods = classes[0]['methods']
        self.assertIn('__init__', methods)
        self.assertIn('get_value', methods)
        self.assertIn('set_value', methods)
    
    def test_parse_file_functions(self):
        """Test parsing a file with functions."""
        result = self.analyzer.parse_file(self.sample_files['functions'])
        
        functions = result['functions']
        self.assertEqual(len(functions), 2)
        
        func_names = [f['name'] for f in functions]
        self.assertIn('add_numbers', func_names)
        self.assertIn('multiply_numbers', func_names)
        
        # Check function calls
        multiply_func = next(f for f in functions if f['name'] == 'multiply_numbers')
        self.assertIn('add_numbers', multiply_func['calls'])
    
    def test_parse_file_imports(self):
        """Test parsing a file with imports."""
        result = self.analyzer.parse_file(self.sample_files['imports'])
        
        imports = result['imports']
        self.assertIn('os', imports)
        self.assertIn('sys', imports)
        self.assertIn('pathlib.Path', imports)
        self.assertIn('typing.List', imports)
        self.assertIn('typing.Dict', imports)
    
    def test_parse_invalid_file(self):
        """Test parsing a non-existent file."""
        result = self.analyzer.parse_file('/nonexistent/file.py')
        
        self.assertEqual(result['classes'], [])
        self.assertEqual(result['functions'], [])
        self.assertEqual(result['imports'], [])
    
    def test_analyze_project(self):
        """Test complete project analysis."""
        results = self.analyzer.analyze_project()
        
        self.assertIsInstance(results, dict)
        self.assertIn('total_files', results)
        self.assertIn('total_classes', results)
        self.assertIn('total_functions', results)
        self.assertIn('graph_nodes', results)
        self.assertIn('graph_edges', results)
        
        # Check that elements were found
        self.assertGreater(results['total_files'], 0)
        self.assertGreater(results['total_classes'], 0)
        self.assertGreater(results['total_functions'], 0)
        
        # Check that graph was built
        self.assertGreater(len(self.analyzer.graph.nodes), 0)
    
    def test_get_summary(self):
        """Test getting analysis summary."""
        # First analyze the project
        self.analyzer.analyze_project()
        
        summary = self.analyzer.get_summary()
        
        self.assertIn('project_path', summary)
        self.assertIn('total_files', summary)
        self.assertIn('total_classes', summary)
        self.assertIn('total_functions', summary)
        self.assertIn('graph_complexity', summary)
    
    def test_get_summary_without_analysis(self):
        """Test getting summary without running analysis first."""
        summary = self.analyzer.get_summary()
        
        self.assertIn('error', summary)


class TestDeepSeekAnalyzer(unittest.TestCase):
    """Test DeepSeekAnalyzer class."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'DEEPSEEK_API_KEY': 'test_key',
            'DEEPSEEK_BASE_URL': 'https://api.test.com',
            'DEEPSEEK_MODEL': 'test-model',
            'DEEPSEEK_MAX_TOKENS': '4096',
            'DEEPSEEK_TEMPERATURE': '0.5'
        })
        self.env_patcher.start()
        
        # Mock ChatOpenAI
        self.llm_patcher = patch('deepseek_analyzer.ChatOpenAI')
        self.mock_llm_class = self.llm_patcher.start()
        self.mock_llm = Mock()
        self.mock_llm_class.return_value = self.mock_llm
    
    def tearDown(self):
        """Clean up test environment."""
        self.env_patcher.stop()
        self.llm_patcher.stop()
    
    def test_initialization_with_env_vars(self):
        """Test initialization with environment variables."""
        analyzer = DeepSeekAnalyzer()
        
        self.assertEqual(analyzer.api_key, 'test_key')
        self.assertEqual(analyzer.base_url, 'https://api.test.com')
        self.assertEqual(analyzer.model, 'test-model')
        self.assertEqual(analyzer.max_tokens, 4096)
        self.assertEqual(analyzer.temperature, 0.5)
    
    def test_initialization_without_api_key(self):
        """Test initialization without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('deepseek_analyzer.load_dotenv'):  # Mock load_dotenv to prevent loading actual .env
                with self.assertRaises(ValueError):
                    DeepSeekAnalyzer()
    
    def test_analyze_code_function(self):
        """Test code function analysis."""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = '''
        {
            "functionality": "测试函数",
            "complexity": 5,
            "quality": 8,
            "suggestions": ["优化建议"],
            "tags": ["test"],
            "dependencies": []
        }
        '''
        self.mock_llm.invoke.return_value = mock_response
        
        analyzer = DeepSeekAnalyzer()
        result = analyzer.analyze_code_function("def test(): pass")
        
        self.assertIsInstance(result, dict)
        self.assertIn('functionality', result)
        self.assertIn('complexity', result)
        self.assertIn('quality', result)
    
    def test_classify_code_similarity(self):
        """Test code similarity classification."""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = "0.75"
        self.mock_llm.invoke.return_value = mock_response
        
        analyzer = DeepSeekAnalyzer()
        similarity = analyzer.classify_code_similarity("code1", "code2")
        
        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)
    
    def test_is_available(self):
        """Test checking if DeepSeek is available."""
        # Mock successful response
        mock_response = Mock()
        mock_response.content = "test response"
        self.mock_llm.invoke.return_value = mock_response
        
        analyzer = DeepSeekAnalyzer()
        self.assertTrue(analyzer.is_available())
        
        # Mock failed response
        self.mock_llm.invoke.side_effect = Exception("API Error")
        self.assertFalse(analyzer.is_available())


class TestCommunityDetector(unittest.TestCase):
    """Test CommunityDetector class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a simple test graph
        self.graph = nx.Graph()
        self.graph.add_edges_from([
            ('A', 'B'), ('B', 'C'), ('C', 'D'),
            ('E', 'F'), ('F', 'G'), ('G', 'H'),
            ('D', 'E')  # Connection between communities
        ])
        
        self.detector = CommunityDetector(self.graph)
    
    def test_initialization(self):
        """Test detector initialization."""
        self.assertEqual(len(self.detector.graph.nodes), 8)
        self.assertEqual(len(self.detector.graph.edges), 7)
    
    def test_initialization_with_empty_graph(self):
        """Test initialization with empty graph."""
        empty_graph = nx.Graph()
        with self.assertRaises(ValueError):
            CommunityDetector(empty_graph)
    
    def test_initialization_with_invalid_graph(self):
        """Test initialization with invalid graph type."""
        with self.assertRaises(ValueError):
            CommunityDetector("not a graph")
    
    def test_detect_communities_label_propagation(self):
        """Test label propagation algorithm."""
        result = self.detector.detect_communities('label_propagation')
        
        self.assertIsInstance(result, dict)
        self.assertIn('algorithm', result)
        self.assertIn('communities', result)
        self.assertIn('modularity', result)
        self.assertIn('num_communities', result)
        self.assertIn('statistics', result)
        
        self.assertEqual(result['algorithm'], 'label_propagation')
        self.assertGreater(result['num_communities'], 0)
    
    @patch('community_detector.LOUVAIN_AVAILABLE', True)
    @patch('community_detector.community_louvain', create=True)
    def test_detect_communities_louvain(self, mock_louvain):
        """Test Louvain algorithm."""
        # Mock Louvain results
        mock_communities = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 1, 'F': 1, 'G': 1, 'H': 1}
        mock_louvain.best_partition.return_value = mock_communities
        mock_louvain.modularity.return_value = 0.5
        
        result = self.detector.detect_communities('louvain')
        
        self.assertEqual(result['algorithm'], 'louvain')
        self.assertEqual(result['modularity'], 0.5)
        self.assertEqual(result['num_communities'], 2)
    
    def test_detect_communities_girvan_newman(self):
        """Test Girvan-Newman algorithm."""
        result = self.detector.detect_communities('girvan_newman', k=2)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['algorithm'], 'girvan_newman')
        self.assertIn('communities', result)
    
    def test_detect_communities_unknown_algorithm(self):
        """Test unknown algorithm."""
        with self.assertRaises(ValueError):
            self.detector.detect_communities('unknown_algorithm')
    
    def test_analyze_community_structure(self):
        """Test community structure analysis."""
        communities = {'A': 0, 'B': 0, 'C': 1, 'D': 1, 'E': 1, 'F': 1, 'G': 2, 'H': 2}
        stats = self.detector._analyze_community_structure(communities)
        
        self.assertIn('num_communities', stats)
        self.assertIn('community_sizes', stats)
        self.assertIn('avg_community_size', stats)
        self.assertIn('community_details', stats)
        
        self.assertEqual(stats['num_communities'], 3)
        self.assertEqual(len(stats['community_sizes']), 3)
    
    def test_get_community_recommendations(self):
        """Test community recommendations."""
        communities = {'A': 0, 'B': 0, 'C': 0, 'D': 0}  # Single large community
        stats = {
            'largest_community': 25,
            'smallest_community': 1,
            'community_details': {
                0: {'cohesion': 0.2, 'coupling': 0.8}
            }
        }
        
        recommendations = self.detector.get_community_recommendations(communities, stats)
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)


class TestCodeAnalysisReporter(unittest.TestCase):
    """Test CodeAnalysisReporter class."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.reporter = CodeAnalysisReporter(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test reporter initialization."""
        self.assertTrue(Path(self.temp_dir).exists())
        self.assertEqual(str(self.reporter.output_dir), self.temp_dir)
    
    def test_export_results_json(self):
        """Test JSON export functionality."""
        analysis_results = {
            'total_files': 5,
            'total_classes': 10,
            'total_functions': 20
        }
        
        community_results = {
            'num_communities': 3,
            'modularity': 0.5
        }
        
        json_path = self.reporter.export_results_json(analysis_results, community_results)
        
        self.assertTrue(os.path.exists(json_path))
        self.assertTrue(json_path.endswith('.json'))
    
    def test_visualize_communities(self):
        """Test community visualization."""
        # Create test graph
        graph = nx.Graph()
        graph.add_edges_from([('A', 'B'), ('B', 'C'), ('D', 'E')])
        
        communities = {'A': 0, 'B': 0, 'C': 0, 'D': 1, 'E': 1}
        
        vis_path = self.reporter.visualize_communities(graph, communities)
        
        self.assertTrue(os.path.exists(vis_path))
        self.assertTrue(vis_path.endswith('.png'))


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self._create_sample_project()
        
        # Mock DeepSeek to avoid API calls
        self.deepseek_patcher = patch('code_analysis.DeepSeekAnalyzer')
        self.mock_deepseek_class = self.deepseek_patcher.start()
        self.mock_deepseek = Mock()
        self.mock_deepseek.is_available.return_value = False
        self.mock_deepseek_class.return_value = self.mock_deepseek
    
    def tearDown(self):
        """Clean up integration test environment."""
        self.deepseek_patcher.stop()
        shutil.rmtree(self.temp_dir)
    
    def _create_sample_project(self):
        """Create a sample project for integration testing."""
        # Create a more complex project structure
        (Path(self.temp_dir) / 'main.py').write_text('''
from utils import helper_function
from models import DataModel

class Application:
    """Main application class."""
    
    def __init__(self):
        self.model = DataModel()
    
    def run(self):
        """Run the application."""
        result = helper_function()
        self.model.process(result)
        return result

if __name__ == "__main__":
    app = Application()
    app.run()
''')
        
        (Path(self.temp_dir) / 'utils.py').write_text('''
def helper_function():
    """Helper function."""
    return "helper result"

def another_helper():
    """Another helper."""
    return helper_function()
''')
        
        (Path(self.temp_dir) / 'models.py').write_text('''
class BaseModel:
    """Base model class."""
    
    def validate(self):
        """Validate the model."""
        pass

class DataModel(BaseModel):
    """Data model class."""
    
    def __init__(self):
        super().__init__()
        self.data = []
    
    def process(self, data):
        """Process data."""
        self.validate()
        self.data.append(data)
''')
    
    def test_full_analysis_pipeline(self):
        """Test the complete analysis pipeline."""
        analyzer = CodeAnalysis(self.temp_dir)
        
        # Step 1: Analyze project
        results = analyzer.analyze_project()
        
        self.assertIsInstance(results, dict)
        self.assertGreater(results['total_files'], 0)
        self.assertGreater(results['total_classes'], 0)
        self.assertGreater(results['total_functions'], 0)
        
        # Step 2: Detect communities
        communities = analyzer.detect_communities()
        
        self.assertIsInstance(communities, dict)
        self.assertIn('communities', communities)
        self.assertIn('statistics', communities)
        
        # Step 3: Generate report
        report_files = analyzer.generate_report(
            output_dir=os.path.join(self.temp_dir, 'output')
        )
        
        self.assertIsInstance(report_files, dict)
        
        # Verify files were created
        for file_type, file_path in report_files.items():
            self.assertTrue(os.path.exists(file_path), 
                          f"File not created for {file_type}: {file_path}")


if __name__ == '__main__':
    # Setup logging for tests
    logging.basicConfig(level=logging.WARNING)
    
    # Run tests
    unittest.main(verbosity=2)