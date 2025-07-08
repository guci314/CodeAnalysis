#!/usr/bin/env python3
"""
Script to explore and document Serena MCP tools and their parameters
"""

import asyncio
import json
from serena_client import SerenaClient, SerenaClientContext

async def explore_serena_tools():
    """Explore all available Serena tools and their capabilities"""
    
    async with SerenaClientContext(SerenaClient()) as client:
        if not client.is_connected():
            print("❌ Failed to connect to Serena")
            return
        
        print("🔧 Available Serena MCP Tools:")
        print("=" * 50)
        
        tools = await client.list_available_tools()
        
        for i, tool in enumerate(tools, 1):
            print(f"{i:2d}. {tool}")
        
        print(f"\n📊 Total tools: {len(tools)}")
        
        # Test basic tools to understand their parameters
        print("\n🧪 Testing basic tool calls...")
        print("=" * 50)
        
        # Test activate_project (we know this one works)
        try:
            result = await client.activate_project("/home/guci/aiProjects/CodeAnalysis")
            print(f"✅ activate_project: {result.success}")
        except Exception as e:
            print(f"❌ activate_project: {e}")
        
        # Test list_dir
        try:
            result = await client.get_file_structure()
            print(f"✅ list_dir: {result.success}")
        except Exception as e:
            print(f"❌ list_dir: {e}")
        
        # Test get_symbols_overview  
        try:
            result = await client.get_code_metrics()
            print(f"✅ get_symbols_overview: {result.success}")
        except Exception as e:
            print(f"❌ get_symbols_overview: {e}")
        
        # Test search_for_pattern
        try:
            result = await client.search_code("class")
            print(f"✅ search_for_pattern: {result.success}")
        except Exception as e:
            print(f"❌ search_for_pattern: {e}")

if __name__ == "__main__":
    asyncio.run(explore_serena_tools())