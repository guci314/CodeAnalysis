#!/usr/bin/env python3
"""
Improved Serena demo based on official documentation
https://github.com/oraios/serena?tab=readme-ov-file#project-activation--indexing
"""

import asyncio
import sys
from pathlib import Path
from serena_client import SerenaClient, SerenaClientContext, AnalysisResult
import os

# Set proxy if needed
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
            # Show a preview of data
            data_str = str(result.data)
            if len(data_str) > 200:
                print(f"📊 Data preview: {data_str[:200]}...")
            else:
                print(f"📊 Data: {data_str}")
    else:
        print(f"❌ Failed: {result.message}")
        if result.error:
            print(f"🔍 Error: {result.error}")

async def check_and_suggest_indexing(client: SerenaClient, project_path: str):
    """Check if project needs indexing and provide suggestions"""
    print(f"\n🔍 Checking project indexing status...")
    
    # Check if .serena directory exists
    serena_dir = Path(project_path) / ".serena"
    if serena_dir.exists():
        print(f"✅ Found .serena directory - project appears to be configured")
        
        # Check for cache files indicating indexing
        cache_dir = serena_dir / "cache"
        if cache_dir.exists() and list(cache_dir.glob("*")):
            print(f"✅ Found cache files - project appears to be indexed")
        else:
            print(f"⚠️  No cache found - consider indexing for better performance")
            print(f"💡 Run: uvx --from git+https://github.com/oraios/serena index-project")
    else:
        print(f"ℹ️  No .serena directory found - will be created on first activation")
        print(f"💡 For large projects, consider running indexing after activation:")
        print(f"   uvx --from git+https://github.com/oraios/serena index-project")

async def demonstrate_proper_activation(client: SerenaClient, project_path: str):
    """Demonstrate proper project activation following official guidelines"""
    
    print(f"🚀 Demonstrating proper project activation for: {project_path}")
    
    # Step 1: Check current configuration (since get_active_project isn't available)
    print(f"\n📋 Step 1: Check current configuration")
    result = await client.get_current_config()
    await print_result(result, "Get Current Configuration")
    
    # Step 2: Activate project using absolute path (recommended)
    print(f"\n🎯 Step 2: Activate project using absolute path")
    abs_path = str(Path(project_path).absolute())
    result = await client.activate_project(abs_path)
    await print_result(result, "Project Activation (Absolute Path)")
    
    if not result.success:
        print("❌ Project activation failed - cannot proceed with demo")
        return False
    
    # Step 3: Verify activation by checking config again
    print(f"\n✅ Step 3: Verify project activation")
    result = await client.get_current_config()
    await print_result(result, "Verify Active Project")
    
    # Step 4: Check configuration
    print(f"\n⚙️  Step 4: Check current configuration")
    result = await client.get_current_config()
    await print_result(result, "Current Configuration")
    
    return True

async def demonstrate_key_features(client: SerenaClient):
    """Demonstrate key Serena features after proper activation"""
    
    print(f"\n🎨 Demonstrating Key Serena Features")
    print(f"=" * 50)
    
    # Feature 1: Project structure analysis
    print(f"\n📁 Feature 1: Project Structure Analysis")
    result = await client.get_file_structure()
    await print_result(result, "File Structure Analysis")
    
    # Feature 2: Symbol analysis
    print(f"\n🔍 Feature 2: Code Symbol Analysis")
    result = await client.get_code_metrics()
    await print_result(result, "Symbol Overview")
    
    # Feature 3: Intelligent search
    print(f"\n🔎 Feature 3: Intelligent Symbol Search")
    result = await client.find_symbol("SerenaClient", symbol_type="class")
    await print_result(result, "Find SerenaClient Class")
    
    # Feature 4: Memory system
    print(f"\n🧠 Feature 4: Memory System")
    result = await client.write_memory("demo_session", "Demo session with improved Serena client")
    await print_result(result, "Write to Memory")
    
    result = await client.list_memories()
    await print_result(result, "List Available Memories")
    
    # Feature 5: Thinking capabilities
    print(f"\n🤔 Feature 5: AI Thinking Capabilities")
    result = await client.think_about_collected_information()
    await print_result(result, "Think About Collected Information")

async def main():
    """Main demo function following official best practices"""
    
    print("🤖 Improved Serena Code Analysis Demo")
    print("Based on: https://github.com/oraios/serena")
    print("="*60)
    
    # Get project path
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
    
    print(f"📂 Target project: {path.absolute()}")
    
    try:
        # Using context manager for automatic cleanup
        async with SerenaClientContext(SerenaClient()) as client:
            
            # Check connection
            if not client.is_connected():
                print("❌ Failed to connect to Serena MCP server")
                print("💡 Make sure you have Serena installed:")
                print("   pip install git+https://github.com/oraios/serena")
                return
            
            print(f"✅ Connected to Serena MCP server")
            tools = await client.list_available_tools()
            print(f"🔧 Available tools: {len(tools)}")
            
            # Check indexing status
            await check_and_suggest_indexing(client, project_path)
            
            # Demonstrate proper activation
            activation_success = await demonstrate_proper_activation(client, project_path)
            
            if activation_success:
                # Demonstrate key features
                await demonstrate_key_features(client)
                
                print(f"\n🎉 Demo completed successfully!")
                print(f"💡 Next steps:")
                print(f"   - Try indexing for better performance on large projects")
                print(f"   - Explore memory system for storing analysis results")
                print(f"   - Use thinking tools for intelligent code analysis")
            else:
                print(f"\n❌ Demo failed due to activation issues")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())