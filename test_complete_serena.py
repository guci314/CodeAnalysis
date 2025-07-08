#!/usr/bin/env python3
"""
Complete test of all Serena client methods based on official tool list
"""

import asyncio
from serena_client import SerenaClient, SerenaClientContext

async def test_complete_serena():
    """Test all major Serena client capabilities"""
    
    async with SerenaClientContext(SerenaClient()) as client:
        if not client.is_connected():
            print("❌ Failed to connect to Serena")
            return
        
        print("🔧 Testing Complete Serena Client")
        print("=" * 50)
        
        # === Project Management ===
        print("\n📁 Project Management:")
        
        # Get active project info
        result = await client.get_active_project()
        print(f"   📋 Get active project: {'✅' if result.success else '❌'}")
        
        # Activate our project
        result = await client.activate_project("/home/guci/aiProjects/CodeAnalysis")
        print(f"   🚀 Activate project: {'✅' if result.success else '❌'}")
        
        # Check onboarding
        result = await client.check_onboarding_performed()
        print(f"   ✅ Check onboarding: {'✅' if result.success else '❌'}")
        
        # Get current config
        result = await client.get_current_config()
        print(f"   ⚙️  Get config: {'✅' if result.success else '❌'}")
        
        # === File Operations ===
        print("\n📄 File Operations:")
        
        # Read a file
        result = await client.read_file("demo_serena.py")
        print(f"   📖 Read file: {'✅' if result.success else '❌'}")
        
        # List directory
        result = await client.get_file_structure()
        print(f"   📁 List directory: {'✅' if result.success else '❌'}")
        
        # === Symbol Operations ===
        print("\n🔍 Symbol Operations:")
        
        # Get symbols overview
        result = await client.get_code_metrics()
        print(f"   📊 Symbols overview: {'✅' if result.success else '❌'}")
        
        # Find symbol
        result = await client.find_symbol("SerenaClient")
        print(f"   🔎 Find symbol: {'✅' if result.success else '❌'}")
        
        # Search for pattern
        result = await client.search_code("async def")
        print(f"   🔍 Search pattern: {'✅' if result.success else '❌'}")
        
        # === Memory Operations ===
        print("\n🧠 Memory Operations:")
        
        # Write memory
        result = await client.write_memory("test_key", "Test memory content")
        print(f"   💾 Write memory: {'✅' if result.success else '❌'}")
        
        # Read memory
        result = await client.read_memory("test_key")
        print(f"   📖 Read memory: {'✅' if result.success else '❌'}")
        
        # List memories
        result = await client.list_memories()
        print(f"   📋 List memories: {'✅' if result.success else '❌'}")
        
        # === Thinking Operations ===
        print("\n🤔 Thinking Operations:")
        
        # Think about collected information
        result = await client.think_about_collected_information()
        print(f"   💭 Think about info: {'✅' if result.success else '❌'}")
        
        # Think about task adherence
        result = await client.think_about_task_adherence()
        print(f"   📋 Think about task: {'✅' if result.success else '❌'}")
        
        # Think if done
        result = await client.think_about_whether_you_are_done()
        print(f"   ✅ Think if done: {'✅' if result.success else '❌'}")
        
        # === System Operations ===
        print("\n⚙️  System Operations:")
        
        # Initial instructions
        result = await client.initial_instructions()
        print(f"   📝 Initial instructions: {'✅' if result.success else '❌'}")
        
        # Prepare for new conversation
        result = await client.prepare_for_new_conversation()
        print(f"   🔄 Prepare new conversation: {'✅' if result.success else '❌'}")
        
        print(f"\n🎉 Testing completed!")
        print(f"🔧 Total available tools: {len(await client.list_available_tools())}")

if __name__ == "__main__":
    asyncio.run(test_complete_serena())