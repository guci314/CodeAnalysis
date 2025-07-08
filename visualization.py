"""
Visualization and Reporting Module for Code Analysis
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns
import networkx as nx
import numpy as np
from datetime import datetime

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logging.warning("Plotly not available, interactive plots will be disabled")


class CodeAnalysisReporter:
    """
    Generates reports and visualizations for code analysis results.
    """
    
    def __init__(self, output_dir: str = "analysis_output"):
        """
        Initialize reporter with output directory.
        
        Args:
            output_dir: Directory to save reports and visualizations
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Configuration
        self.dpi = int(os.getenv('PLOT_DPI', '300'))
        self.style = os.getenv('PLOT_STYLE', 'seaborn-v0_8')
        self.figure_width = int(os.getenv('FIGURE_SIZE_WIDTH', '12'))
        self.figure_height = int(os.getenv('FIGURE_SIZE_HEIGHT', '8'))
        
        # Setup matplotlib
        plt.style.use(self.style)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Reporter initialized with output directory: {self.output_dir}")
    
    def generate_comprehensive_report(self, analysis_results: Dict[str, Any], 
                                    community_results: Dict[str, Any] = None) -> str:
        """
        Generate a comprehensive analysis report.
        
        Args:
            analysis_results: Results from CodeAnalysis.analyze_project()
            community_results: Results from community detection
            
        Returns:
            Path to generated report file
        """
        report_path = self.output_dir / f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        # Generate HTML report
        html_content = self._generate_html_report(analysis_results, community_results)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"Comprehensive report generated: {report_path}")
        return str(report_path)
    
    def visualize_communities(self, graph: nx.Graph, communities: Dict[str, int], 
                            title: str = "Code Communities") -> str:
        """
        Visualize community structure of the code graph.
        
        Args:
            graph: NetworkX graph
            communities: Dictionary mapping nodes to community IDs
            title: Title for the visualization
            
        Returns:
            Path to generated visualization file
        """
        fig, ax = plt.subplots(figsize=(self.figure_width, self.figure_height))
        
        # Create color map for communities
        unique_communities = set(communities.values())
        colors = plt.cm.Set3(np.linspace(0, 1, len(unique_communities)))
        color_map = {comm: colors[i] for i, comm in enumerate(unique_communities)}
        
        # Set node colors based on community
        node_colors = [color_map[communities.get(node, 0)] for node in graph.nodes()]
        
        # Calculate layout
        pos = nx.spring_layout(graph, k=1, iterations=50)
        
        # Draw graph
        nx.draw(graph, pos, ax=ax, 
                node_color=node_colors,
                node_size=300,
                with_labels=True,
                font_size=8,
                font_weight='bold',
                edge_color='gray',
                alpha=0.7)
        
        # Add legend
        legend_elements = [patches.Patch(color=color_map[comm], label=f'Community {comm}') 
                          for comm in unique_communities]
        ax.legend(handles=legend_elements, loc='upper right')
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        
        # Save visualization
        vis_path = self.output_dir / f"communities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(vis_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Community visualization saved: {vis_path}")
        return str(vis_path)
    
    def create_community_metrics_plot(self, community_stats: Dict[str, Any]) -> str:
        """
        Create plots showing community metrics.
        
        Args:
            community_stats: Community analysis statistics
            
        Returns:
            Path to generated plot file
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Community size distribution
        sizes = community_stats.get('community_sizes', [])
        if sizes:
            ax1.hist(sizes, bins=min(10, len(sizes)), alpha=0.7, color='skyblue')
            ax1.set_title('Community Size Distribution')
            ax1.set_xlabel('Community Size')
            ax1.set_ylabel('Frequency')
        
        # Cohesion vs Coupling scatter plot
        cohesion_data = community_stats.get('community_cohesion', {})
        coupling_data = community_stats.get('community_coupling', {})
        
        if cohesion_data and coupling_data:
            communities = list(cohesion_data.keys())
            cohesion_values = [cohesion_data[c] for c in communities]
            coupling_values = [coupling_data[c] for c in communities]
            
            ax2.scatter(cohesion_values, coupling_values, alpha=0.7, s=50)
            ax2.set_xlabel('Cohesion')
            ax2.set_ylabel('Coupling')
            ax2.set_title('Community Cohesion vs Coupling')
            
            # Add quadrant lines
            ax2.axhline(y=0.5, color='red', linestyle='--', alpha=0.5)
            ax2.axvline(x=0.5, color='red', linestyle='--', alpha=0.5)
        
        # Community details table
        details = community_stats.get('community_details', {})
        if details:
            table_data = []
            for comm_id, detail in details.items():
                table_data.append([
                    f"Community {comm_id}",
                    detail.get('size', 0),
                    f"{detail.get('cohesion', 0):.2f}",
                    f"{detail.get('coupling', 0):.2f}"
                ])
            
            ax3.axis('tight')
            ax3.axis('off')
            table = ax3.table(cellText=table_data,
                             colLabels=['Community', 'Size', 'Cohesion', 'Coupling'],
                             cellLoc='center',
                             loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1.2, 1.5)
            ax3.set_title('Community Summary')
        
        # Community size pie chart
        if sizes:
            community_labels = [f"Community {i}" for i in range(len(sizes))]
            ax4.pie(sizes, labels=community_labels, autopct='%1.1f%%', startangle=90)
            ax4.set_title('Community Size Distribution')
        
        plt.tight_layout()
        
        # Save plot
        plot_path = self.output_dir / f"community_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(plot_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Community metrics plot saved: {plot_path}")
        return str(plot_path)
    
    def create_interactive_graph(self, graph: nx.Graph, communities: Dict[str, int]) -> str:
        """
        Create an interactive graph visualization using Plotly.
        
        Args:
            graph: NetworkX graph
            communities: Dictionary mapping nodes to community IDs
            
        Returns:
            Path to generated HTML file
        """
        if not PLOTLY_AVAILABLE:
            self.logger.warning("Plotly not available, skipping interactive graph")
            return ""
        
        # Calculate layout
        pos = nx.spring_layout(graph, k=1, iterations=50)
        
        # Prepare node traces
        node_x = []
        node_y = []
        node_text = []
        node_color = []
        
        for node in graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(f"{node}<br>Community: {communities.get(node, 'Unknown')}")
            node_color.append(communities.get(node, 0))
        
        # Prepare edge traces
        edge_x = []
        edge_y = []
        
        for edge in graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        # Create edge trace
        edge_trace = go.Scatter(x=edge_x, y=edge_y,
                               line=dict(width=0.5, color='gray'),
                               hoverinfo='none',
                               mode='lines')
        
        # Create node trace
        node_trace = go.Scatter(x=node_x, y=node_y,
                               mode='markers',
                               hoverinfo='text',
                               text=node_text,
                               marker=dict(size=10,
                                         color=node_color,
                                         colorscale='Viridis',
                                         line=dict(width=2, color='black')))
        
        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title=dict(text='Interactive Code Graph', font=dict(size=16)),
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           annotations=[ dict(
                               text="Code structure graph with community detection",
                               showarrow=False,
                               xref="paper", yref="paper",
                               x=0.005, y=-0.002 ) ],
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
        
        # Save interactive plot
        interactive_path = self.output_dir / f"interactive_graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        fig.write_html(str(interactive_path))
        
        self.logger.info(f"Interactive graph saved: {interactive_path}")
        return str(interactive_path)
    
    def export_results_json(self, analysis_results: Dict[str, Any], 
                           community_results: Dict[str, Any] = None) -> str:
        """
        Export analysis results to JSON format.
        
        Args:
            analysis_results: Analysis results
            community_results: Community detection results
            
        Returns:
            Path to exported JSON file
        """
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'analysis_results': analysis_results,
            'community_results': community_results
        }
        
        json_path = self.output_dir / f"analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Results exported to JSON: {json_path}")
        return str(json_path)
    
    def _generate_html_report(self, analysis_results: Dict[str, Any], 
                             community_results: Dict[str, Any] = None) -> str:
        """
        Generate HTML report content.
        
        Args:
            analysis_results: Analysis results
            community_results: Community detection results
            
        Returns:
            HTML content string
        """
        html_template = """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>代码分析报告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #007acc; }}
                .metrics {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .metric {{ text-align: center; padding: 10px; background-color: #f9f9f9; border-radius: 5px; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #007acc; }}
                .recommendations {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>代码分析报告</h1>
                <p>生成时间: {timestamp}</p>
            </div>
            
            <div class="section">
                <h2>项目概览</h2>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value">{total_files}</div>
                        <div>文件总数</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{total_classes}</div>
                        <div>类总数</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{total_functions}</div>
                        <div>函数总数</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{graph_nodes}</div>
                        <div>图节点数</div>
                    </div>
                </div>
            </div>
            
            {community_section}
            
            <div class="section">
                <h2>代码元素详情</h2>
                <p>详细的代码元素信息已导出到JSON文件中。</p>
            </div>
            
            <div class="section">
                <h2>分析总结</h2>
                <p>此报告包含了项目的完整代码分析结果，包括结构分析、社区检测和代码质量评估。</p>
            </div>
        </body>
        </html>
        """
        
        # Prepare community section
        community_section = ""
        if community_results:
            recommendations = community_results.get('recommendations', [])
            recommendations_html = "<ul>" + "".join(f"<li>{rec}</li>" for rec in recommendations) + "</ul>"
            
            community_section = f"""
            <div class="section">
                <h2>社区检测结果</h2>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value">{community_results.get('num_communities', 0)}</div>
                        <div>检测到的社区数</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{community_results.get('modularity', 0):.3f}</div>
                        <div>模块度</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{community_results.get('algorithm', 'Unknown')}</div>
                        <div>使用算法</div>
                    </div>
                </div>
                
                <div class="recommendations">
                    <h3>优化建议</h3>
                    {recommendations_html}
                </div>
            </div>
            """
        
        # Format the template
        return html_template.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_files=analysis_results.get('total_files', 0),
            total_classes=analysis_results.get('total_classes', 0),
            total_functions=analysis_results.get('total_functions', 0),
            graph_nodes=analysis_results.get('graph_nodes', 0),
            community_section=community_section
        )