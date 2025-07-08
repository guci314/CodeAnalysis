#!/usr/bin/env python3
"""
Demo script for SerenaClient - Shows how to use Serena to analyze Python codebases.

This script demonstrates:
1. Connecting to Serena MCP server
2. Activating a project for analysis
3. Performing various code analysis tasks
4. Handling results and errors

Usage:
    python demo_serena.py [project_path]
    
If no project_path is provided, it will analyze the current directory.
"""

import asyncio
import sys
from pathlib import Path
from serena_client import SerenaClient, SerenaClientContext, AnalysisResult
import os
os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'

async def print_result(result: AnalysisResult, operation: str):
    """Helper function to print analysis results"""
    print(f"\n{'='*60}")
    print(f"Operation: {operation}")
    print(f"{'='*60}")
    
    if result.success:
        print(f"✅ Success: {result.message}")
        if result.data:
            print(f"📊 Data: {result.data}")
    else:
        print(f"❌ Failed: {result.message}")
        if result.error:
            print(f"🔍 Error: {result.error}")


async def analyze_with_serena(project_path: str):
    """
    Main analysis function using SerenaClient
    
    Args:
        project_path: Path to the Python project to analyze
    """
    print(f"🚀 Starting Serena analysis for: {project_path}")
    
    # Using context manager for automatic cleanup
    async with SerenaClientContext(SerenaClient()) as client:
        
        # Check if connected
        if not client.is_connected():
            print("❌ Failed to connect to Serena MCP server")
            print("Make sure Serena is running: uvx --from git+https://github.com/oraios/serena serena-mcp-server")
            return
        
        print(f"✅ Connected to Serena")
        print(f"🔧 Available tools: {await client.list_available_tools()}")
        
        # Activate the project
        result = await client.activate_project(project_path)
        await print_result(result, "Project Activation")
        
        if not result.success:
            print("Cannot proceed without project activation")
            return
        
        # Perform various analyses
        analyses = [
            ("File Structure Analysis", client.get_file_structure()),
            ("Find All Classes", client.find_classes()),
            ("Find All Functions", client.find_functions()),
            ("Import Analysis", client.analyze_imports()),
            ("Code Metrics", client.get_code_metrics()),
            ("Search for 'Client' classes", client.search_code("class.*Client")),
            ("Search for 'main' functions", client.find_functions("main")),
        ]
        
        # Run all analyses
        for description, analysis_coro in analyses:
            try:
                result = await analysis_coro
                await print_result(result, description)
                
                # Add a small delay between analyses
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error in {description}: {e}")
        
        print(f"\n🎉 Analysis complete for project: {client.get_current_project()}")


async def demo_basic_usage():
    """Demo basic SerenaClient usage without context manager"""
    print("\n" + "="*80)
    print("DEMO: Basic SerenaClient Usage (Manual Connection Management)")
    print("="*80)
    
    client = SerenaClient()
    
    try:
        # Start connection
        print("🔌 Connecting to Serena...")
        if not await client.start():
            print("❌ Failed to connect to Serena")
            return
        
        print("✅ Connected successfully")
        
        # Show available tools
        tools = await client.list_available_tools()
        print(f"🔧 Available tools: {tools}")
        
        # Try to activate current directory
        current_dir = str(Path.cwd())
        result = await client.activate_project(current_dir)
        await print_result(result, "Activate Current Directory")
        
        if result.success:
            # Quick analysis
            classes = await client.find_classes()
            await print_result(classes, "Find Classes in Current Directory")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
    finally:
        await client.stop()
        print("🔌 Disconnected from Serena")


async def main():
    """Main entry point"""
    print("🤖 Serena Code Analysis Demo")
    print("="*40)
    
    # Get project path from command line or use current directory
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = str(Path.cwd())
    
    # Validate project path
    path = Path(project_path)
    if not path.exists():
        print(f"❌ Project path does not exist: {project_path}")
        sys.exit(1)
    
    if not path.is_dir():
        print(f"❌ Project path is not a directory: {project_path}")
        sys.exit(1)
    
    try:
        # Main analysis
        await analyze_with_serena(str(path.absolute()))
        
        # Additional demo
        await demo_basic_usage()
        
    except KeyboardInterrupt:
        print("\n⏹️  Analysis interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Check if in async-capable environment
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "asyncio.run() cannot be called from a running event loop" in str(e):
            # We're already in an event loop (e.g., Jupyter notebook)
            import nest_asyncio
            nest_asyncio.apply()
            asyncio.create_task(main())
        else:
            raise