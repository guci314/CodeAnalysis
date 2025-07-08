#!/usr/bin/env python3
"""
Command-line interface for CodeAnalysis system
"""

import argparse
import logging
import sys
import os
from pathlib import Path
import time
from typing import Dict, Any

from code_analysis import CodeAnalysis
from deepseek_analyzer import DeepSeekAnalyzer


def setup_logging(level: str = 'INFO'):
    """Setup logging configuration."""
    log_format = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def validate_project_path(path: str) -> Path:
    """Validate and return project path."""
    project_path = Path(path).resolve()
    
    if not project_path.exists():
        raise argparse.ArgumentTypeError(f"Project path does not exist: {path}")
    
    if not project_path.is_dir():
        raise argparse.ArgumentTypeError(f"Project path is not a directory: {path}")
    
    return project_path


def print_summary(summary: Dict[str, Any]):
    """Print analysis summary in a formatted way."""
    print("\n" + "="*60)
    print("📊 CODE ANALYSIS SUMMARY")
    print("="*60)
    
    print(f"📁 Project Path: {summary.get('project_path', 'Unknown')}")
    print(f"📄 Total Files: {summary.get('total_files', 0)}")
    print(f"🏗️  Total Classes: {summary.get('total_classes', 0)}")
    print(f"⚙️  Total Functions: {summary.get('total_functions', 0)}")
    
    graph_complexity = summary.get('graph_complexity', {})
    print(f"🔗 Graph Nodes: {graph_complexity.get('nodes', 0)}")
    print(f"🔗 Graph Edges: {graph_complexity.get('edges', 0)}")


def print_community_results(results: Dict[str, Any]):
    """Print community detection results."""
    print("\n" + "="*60)
    print("🏘️  COMMUNITY DETECTION RESULTS")
    print("="*60)
    
    print(f"🔍 Algorithm: {results.get('algorithm', 'Unknown')}")
    print(f"🏘️  Communities Found: {results.get('num_communities', 0)}")
    print(f"📈 Modularity Score: {results.get('modularity', 0):.3f}")
    
    # Print community details
    statistics = results.get('statistics', {})
    community_details = statistics.get('community_details', {})
    
    if community_details:
        print(f"\n📋 Community Details:")
        print(f"{'Community':<12} {'Size':<6} {'Cohesion':<10} {'Coupling':<10}")
        print("-" * 40)
        
        for comm_id, details in community_details.items():
            size = details.get('size', 0)
            cohesion = details.get('cohesion', 0)
            coupling = details.get('coupling', 0)
            print(f"{comm_id:<12} {size:<6} {cohesion:<10.3f} {coupling:<10.3f}")
    
    # Print recommendations
    recommendations = results.get('recommendations', [])
    if recommendations:
        print(f"\n💡 Optimization Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")


def print_comparison_results(results: Dict[str, Any]):
    """Print algorithm comparison results."""
    print("\n" + "="*60)
    print("🔬 ALGORITHM COMPARISON RESULTS")
    print("="*60)
    
    comparison_results = results.get('results', {})
    best_algorithm = results.get('best_algorithm', 'Unknown')
    best_modularity = results.get('best_modularity', 0)
    
    print(f"🏆 Best Algorithm: {best_algorithm} (Modularity: {best_modularity:.3f})")
    print(f"\n📊 Algorithm Performance:")
    print(f"{'Algorithm':<20} {'Communities':<12} {'Modularity':<12} {'Status':<10}")
    print("-" * 56)
    
    for algorithm, result in comparison_results.items():
        if 'error' in result:
            status = "Failed"
            communities = "N/A"
            modularity = "N/A"
        else:
            status = "Success"
            communities = str(result.get('num_communities', 0))
            modularity = f"{result.get('modularity', 0):.3f}"
        
        print(f"{algorithm:<20} {communities:<12} {modularity:<12} {status:<10}")


def analyze_command(args):
    """Handle the analyze command."""
    print(f"🔍 Starting analysis of project: {args.project_path}")
    
    start_time = time.time()
    
    try:
        # Initialize analyzer
        analyzer = CodeAnalysis(str(args.project_path), enable_deepseek=args.enable_deepseek)
        
        # Check DeepSeek availability
        if args.enable_deepseek:
            if analyzer.deepseek_analyzer and analyzer.deepseek_analyzer.is_available():
                print("✅ DeepSeek API is available")
            else:
                print("⚠️  DeepSeek API is not available, continuing without AI analysis")
        else:
            print("⚠️  DeepSeek analysis disabled")
        
        # Analyze project
        print("📊 Analyzing project structure...")
        results = analyzer.analyze_project()
        
        analysis_time = time.time() - start_time
        print(f"✅ Analysis completed in {analysis_time:.2f} seconds")
        
        # Print summary
        summary = analyzer.get_summary()
        print_summary(summary)
        
        # Detect communities if requested
        if args.detect_communities:
            print(f"\n🏘️  Detecting communities using {args.algorithm} algorithm...")
            
            community_start = time.time()
            community_results = analyzer.detect_communities(
                algorithm=args.algorithm,
                resolution=args.resolution
            )
            community_time = time.time() - community_start
            
            print(f"✅ Community detection completed in {community_time:.2f} seconds")
            print_community_results(community_results)
        
        # Generate report if requested
        if args.generate_report:
            print(f"\n📄 Generating comprehensive report...")
            
            report_files = analyzer.generate_report(
                output_dir=args.output_dir,
                include_communities=args.detect_communities,
                enable_ai_descriptions=args.enable_deepseek  # 使用AI描述功能
            )
            
            print(f"✅ Report generated successfully!")
            print(f"📁 Output directory: {args.output_dir}")
            print(f"📋 Generated files:")
            for file_type, file_path in report_files.items():
                print(f"  - {file_type}: {file_path}")
        
        # Export graph if requested
        if args.export_graph:
            graph_path = os.path.join(args.output_dir, f"graph.{args.graph_format}")
            analyzer.export_graph(graph_path, args.graph_format)
            print(f"📊 Graph exported to: {graph_path}")
        
        total_time = time.time() - start_time
        print(f"\n⏱️  Total execution time: {total_time:.2f} seconds")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def compare_command(args):
    """Handle the compare command."""
    print(f"🔬 Comparing community detection algorithms for: {args.project_path}")
    
    try:
        # Initialize analyzer (disable DeepSeek for comparison to speed up)
        analyzer = CodeAnalysis(str(args.project_path), enable_deepseek=False)
        
        # Analyze project first
        print("📊 Analyzing project structure...")
        analyzer.analyze_project()
        
        # Compare algorithms
        print("🔬 Comparing community detection algorithms...")
        
        algorithms = args.algorithms or ['leiden', 'louvain', 'girvan_newman', 'label_propagation']
        comparison_results = analyzer.compare_community_algorithms(algorithms)
        
        print_comparison_results(comparison_results)
        
        # Save comparison results if requested
        if args.save_comparison:
            import json
            output_path = os.path.join(args.output_dir, "algorithm_comparison.json")
            os.makedirs(args.output_dir, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(comparison_results, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Comparison results saved to: {output_path}")
    
    except Exception as e:
        print(f"❌ Error during comparison: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def test_command(args):
    """Handle the test command."""
    print("🧪 Running CodeAnalysis system tests...")
    
    try:
        # Test DeepSeek connection
        if args.test_deepseek:
            print("🔍 Testing DeepSeek API connection...")
            try:
                analyzer = DeepSeekAnalyzer()
                if analyzer.is_available():
                    print("✅ DeepSeek API connection successful")
                    
                    # Test basic functionality
                    test_code = "def hello_world():\n    return 'Hello, World!'"
                    result = analyzer.analyze_code_function(test_code)
                    print(f"✅ DeepSeek analysis test successful: {result.get('functionality', 'No description')}")
                    
                    # Show cache info
                    cache_info = analyzer.get_cache_info()
                    print(f"💾 Cache status: {'Enabled' if cache_info['cache_enabled'] else 'Disabled'}")
                    if cache_info['cache_exists']:
                        print(f"💾 Cache size: {cache_info['cache_size']} bytes")
                else:
                    print("❌ DeepSeek API connection failed")
            except Exception as e:
                print(f"❌ DeepSeek test failed: {str(e)}")
        
        # Test sample project analysis
        if args.test_sample:
            sample_path = Path(__file__).parent / "sample_project"
            if sample_path.exists():
                print(f"🧪 Testing with sample project: {sample_path}")
                
                analyzer = CodeAnalysis(str(sample_path))
                results = analyzer.analyze_project()
                
                print(f"✅ Sample project analysis successful:")
                print(f"  - Files: {results.get('total_files', 0)}")
                print(f"  - Classes: {results.get('total_classes', 0)}")
                print(f"  - Functions: {results.get('total_functions', 0)}")
                
                # Test community detection
                communities = analyzer.detect_communities('label_propagation')
                print(f"✅ Community detection test successful: {communities.get('num_communities', 0)} communities found")
            else:
                print("⚠️  Sample project not found, skipping sample test")
        
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def cache_command(args):
    """Handle the cache command."""
    try:
        analyzer = DeepSeekAnalyzer()
        
        if args.cache_action == 'info':
            print("💾 Cache Information:")
            cache_info = analyzer.get_cache_info()
            print(f"  - Status: {'Enabled' if cache_info['cache_enabled'] else 'Disabled'}")
            print(f"  - Path: {cache_info['cache_path']}")
            print(f"  - Exists: {'Yes' if cache_info['cache_exists'] else 'No'}")
            if cache_info['cache_exists']:
                size_mb = cache_info['cache_size'] / (1024 * 1024)
                print(f"  - Size: {cache_info['cache_size']} bytes ({size_mb:.2f} MB)")
        
        elif args.cache_action == 'clear':
            print("🗑️  Clearing cache...")
            if analyzer.clear_cache():
                print("✅ Cache cleared successfully")
            else:
                print("❌ Failed to clear cache")
        
    except Exception as e:
        print(f"❌ Cache operation failed: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="CodeAnalysis - Analyze Python project structure and detect code communities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic analysis
  python main.py analyze /path/to/project
  
  # Full analysis with community detection and report
  python main.py analyze /path/to/project --detect-communities --generate-report
  
  # Compare algorithms
  python main.py compare /path/to/project
  
  # Test system
  python main.py test --test-deepseek --test-sample
  
  # Cache management
  python main.py cache info
  python main.py cache clear
  
For more information, visit: https://github.com/your-repo/CodeAnalysis
        """
    )
    
    # Global options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Set logging level')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a Python project')
    analyze_parser.add_argument('project_path', type=validate_project_path,
                               help='Path to the Python project to analyze')
    analyze_parser.add_argument('--detect-communities', action='store_true',
                               help='Detect code communities')
    analyze_parser.add_argument('--algorithm', choices=['leiden', 'louvain', 'girvan_newman', 'label_propagation'],
                               default='leiden', help='Community detection algorithm')
    analyze_parser.add_argument('--resolution', type=float, default=1.0,
                               help='Resolution parameter for community detection')
    analyze_parser.add_argument('--generate-report', action='store_true',
                               help='Generate comprehensive HTML report')
    analyze_parser.add_argument('--output-dir', default='analysis_output',
                               help='Output directory for reports and visualizations')
    analyze_parser.add_argument('--export-graph', action='store_true',
                               help='Export knowledge graph')
    analyze_parser.add_argument('--graph-format', choices=['graphml', 'gexf', 'json', 'edgelist'],
                               default='graphml', help='Graph export format')
    analyze_parser.add_argument('--enable-deepseek', action='store_true',
                               help='Enable DeepSeek AI analysis (requires API key)')
    
    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare community detection algorithms')
    compare_parser.add_argument('project_path', type=validate_project_path,
                               help='Path to the Python project to analyze')
    compare_parser.add_argument('--algorithms', nargs='+',
                               choices=['leiden', 'louvain', 'girvan_newman', 'label_propagation'],
                               help='Algorithms to compare (default: all)')
    compare_parser.add_argument('--save-comparison', action='store_true',
                               help='Save comparison results to JSON file')
    compare_parser.add_argument('--output-dir', default='analysis_output',
                               help='Output directory for comparison results')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test system functionality')
    test_parser.add_argument('--test-deepseek', action='store_true',
                            help='Test DeepSeek API connection')
    test_parser.add_argument('--test-sample', action='store_true',
                            help='Test with sample project')
    
    # Cache command
    cache_parser = subparsers.add_parser('cache', help='Manage LangChain cache')
    cache_parser.add_argument('cache_action', choices=['info', 'clear'],
                             help='Cache action to perform')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Handle commands
    if args.command == 'analyze':
        analyze_command(args)
    elif args.command == 'compare':
        compare_command(args)
    elif args.command == 'test':
        test_command(args)
    elif args.command == 'cache':
        cache_command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()