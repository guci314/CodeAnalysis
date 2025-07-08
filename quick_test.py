#!/usr/bin/env python3
"""
Quick test of new Serena methods
"""

import asyncio
from serena_client import SerenaClient, SerenaClientContext

async def quick_test():
    """Quick test of new methods"""
    
    async with SerenaClientContext(SerenaClient()) as client:
        if not client.is_connected():
            print("❌ Failed to connect")
            return
        
        print("✅ Connected to Serena")
        
        # Test direct tool calling
        result = await client.call_tool_directly("list_memories")
        print(f"📋 List memories: {'✅' if result.success else '❌'}")
        if result.data:
            print(f"Result: {result.data}")
        if result.error:
            print(f"Error: {result.error}")

if __name__ == "__main__":
    asyncio.run(quick_test())