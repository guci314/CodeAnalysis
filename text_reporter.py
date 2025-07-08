"""
Text-only Report Generator for Code Analysis
"""

import os
import json
import logging
import shutil
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime


class TextReporter:
    """
    Generates text-only reports for code analysis results.
    """
    
    def __init__(self, output_dir: str = "analysis_output"):
        """
        Initialize reporter with output directory.
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.logger = logging.getLogger(__name__)
        self._clean_and_create_output_dir()
    
    def generate_comprehensive_report(self, analysis_results: Dict[str, Any], 
                                      community_results: Dict[str, Any] = None,
                                      community_descriptions: Dict[str, Any] = None) -> str:
        """
        Generate a comprehensive text report.
        
        Args:
            analysis_results: Results from code analysis
            community_results: Results from community detection
            community_descriptions: AI-generated community descriptions
            
        Returns:
            Path to the generated report file
        """
        report_path = self.output_dir / "analysis_report.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(self._generate_markdown_report(analysis_results, community_results, community_descriptions))
        
        self.logger.info(f"Comprehensive report generated: {report_path}")
        return str(report_path)
    
    def export_results_json(self, analysis_results: Dict[str, Any], 
                           community_results: Dict[str, Any] = None) -> str:
        """
        Export analysis results to JSON format.
        
        Args:
            analysis_results: Results from code analysis
            community_results: Results from community detection
            
        Returns:
            Path to the exported JSON file
        """
        json_path = self.output_dir / "analysis_results.json"
        
        export_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "analysis_results": analysis_results,
            "community_results": community_results
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"JSON export completed: {json_path}")
        return str(json_path)
    
    def _generate_markdown_report(self, analysis_results: Dict[str, Any],
                                  community_results: Dict[str, Any] = None,
                                  community_descriptions: Dict[str, Any] = None) -> str:
        """
        Generate a simplified markdown report focused on community descriptions.
        
        Args:
            analysis_results: Results from code analysis
            community_results: Results from community detection
            community_descriptions: AI-generated community descriptions with meaningful names
            
        Returns:
            Markdown formatted report content
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report_lines = [
            f"# Code Analysis Report",
            f"",
            f"**Generated:** {timestamp}",
            f""
        ]
        
        # Only include AI-generated community descriptions
        if community_descriptions:
            report_lines.extend([
                f"## Community Descriptions",
                f"",
                f"*AI-Generated Natural Language Descriptions*",
                f""
            ])
            
            # Sort communities by ID for consistent ordering
            sorted_communities = sorted(community_descriptions.items(), 
                                      key=lambda x: int(x[0]) if x[0].isdigit() else x[0])
            
            for comm_id, description in sorted_communities:
                if description and description.get('functionality'):
                    # Use meaningful name if available, otherwise use Community ID
                    meaningful_name = description.get('meaningful_name', f"Community {comm_id}")
                    original_id = description.get('original_id', comm_id)
                    
                    # Display format: "Meaningful Name (Community ID)"
                    if meaningful_name != f"Community {comm_id}":
                        title = f"{meaningful_name} (Community {original_id})"
                    else:
                        title = f"Community {original_id}"
                    
                    report_lines.extend([
                        f"### {title}",
                        f"",
                        f"**功能描述:**",
                        f"{description.get('functionality', 'No functionality description available')}",
                        f"",
                        f"**架构模式:**",
                        f"{description.get('architecture_pattern', 'Unknown')}",
                        f"",
                        f"**设计质量评分:** {description.get('design_quality', 'N/A')}/10",
                        f"",
                        f"**重构建议:**",
                    ])
                    
                    # Add refactor suggestions as bullet points
                    suggestions = description.get('refactor_suggestions', [])
                    if suggestions:
                        for suggestion in suggestions:
                            report_lines.append(f"- {suggestion}")
                    else:
                        report_lines.append("- 暂无建议")
                    
                    report_lines.extend([
                        f"",
                        f"**功能标签:** {', '.join(description.get('functional_tags', ['unknown']))}",
                        f"",
                        f"**外部依赖:** {', '.join(description.get('external_dependencies', ['无']))}",
                        f""
                    ])
                    
                    # Add related files/modules section
                    related_files = self._extract_related_files(description)
                    if related_files:
                        report_lines.extend([
                            f"**相关文件（模块）:**",
                            f""
                        ])
                        for file_path in related_files:
                            # Display relative path for better readability
                            display_path = self._format_file_path(file_path)
                            report_lines.append(f"- `{display_path}`")
                        report_lines.append("")
                    
                    report_lines.extend([
                        f"---",
                        f""
                    ])
        else:
            # If no community descriptions available
            report_lines.extend([
                f"## Community Descriptions",
                f"",
                f"*No AI-generated community descriptions available.*",
                f"",
                f"To generate community descriptions, please:",
                f"1. Ensure DeepSeek API is configured",
                f"2. Run analysis with `--enable-deepseek` flag",
                f"3. Include community detection with `--detect-communities`",
                f""
            ])
        
        # Add footer
        report_lines.extend([
            f"---",
            f"",
            f"*Report generated by CodeAnalysis v2.0*"
        ])
        
        return "\n".join(report_lines)
    
    def _clean_and_create_output_dir(self):
        """
        Clean and recreate the output directory.
        """
        try:
            # Remove directory if it exists
            if self.output_dir.exists():
                shutil.rmtree(self.output_dir)
                self.logger.info(f"Cleaned existing output directory: {self.output_dir}")
            
            # Create fresh directory
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created output directory: {self.output_dir}")
            
        except Exception as e:
            self.logger.warning(f"Could not clean output directory: {e}")
            # Fallback: just ensure directory exists
            self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _extract_related_files(self, description: Dict[str, Any]) -> List[str]:
        """
        Extract related files from community description.
        
        Args:
            description: Community description containing nodes and elements
            
        Returns:
            List of unique file paths
        """
        files = set()
        
        # Extract from nodes (format: file_path:function_name)
        nodes = description.get('nodes', [])
        for node in nodes:
            if ':' in node:
                file_path = node.split(':')[0]
                files.add(file_path)
        
        # Extract from elements (code elements with file_path)
        elements = description.get('elements', [])
        for element in elements:
            file_path = element.get('file_path', '')
            if file_path:
                files.add(file_path)
        
        # Return sorted list for consistent ordering
        return sorted(list(files))
    
    def _format_file_path(self, file_path: str) -> str:
        """
        Format file path for display in report.
        
        Args:
            file_path: Full file path
            
        Returns:
            Formatted path for display
        """
        try:
            # Convert to Path object for easier manipulation
            path = Path(file_path)
            
            # Try to make it relative to common project roots
            common_roots = [
                'AgentFrameWork', 'CodeAnalysis', 'aiProjects', 
                'src', 'lib', 'app', 'project'
            ]
            
            # Find if path contains any common root
            parts = path.parts
            for i, part in enumerate(parts):
                if part in common_roots:
                    # Return path from the common root
                    relative_parts = parts[i:]
                    return str(Path(*relative_parts))
            
            # If no common root found, just return the filename and parent directory
            if len(parts) >= 2:
                return str(Path(parts[-2]) / parts[-1])
            else:
                return path.name
                
        except Exception:
            # Fallback: just return the filename
            return Path(file_path).name