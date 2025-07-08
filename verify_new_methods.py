#!/usr/bin/env python3
"""
Quick verification of new SerenaClient methods
"""

import asyncio
from serena_client import SerenaClient, SerenaClientContext

async def verify_methods():
    """Verify new methods work"""
    
    async with SerenaClientContext(SerenaClient()) as client:
        if not client.is_connected():
            print("❌ Failed to connect")
            return
        
        print("✅ Connected to Serena")
        
        # Test project activation first
        result = await client.activate_project("/home/guci/aiProjects/CodeAnalysis")
        print(f"📁 Project activation: {'✅' if result.success else '❌'}")
        
        # Test new find_symbol method
        result = await client.find_symbol("SerenaClient", symbol_type="class")
        print(f"🔍 Find symbol: {'✅' if result.success else '❌'}")
        if result.success and result.data:
            print(f"   Found: {str(result.data)[:100]}...")
        
        # Test memory operations
        result = await client.write_memory("test", "Hello Serena")
        print(f"💾 Write memory: {'✅' if result.success else '❌'}")
        
        result = await client.read_memory("test")
        print(f"📖 Read memory: {'✅' if result.success else '❌'}")
        if result.success and result.data:
            print(f"   Content: {result.data}")
        
        print("🎉 Verification complete!")

if __name__ == "__main__":
    asyncio.run(verify_methods())