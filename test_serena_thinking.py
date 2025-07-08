#!/usr/bin/env python3
"""
Test script for Serena's thinking and memory capabilities
"""

import asyncio
from serena_client import SerenaClient, SerenaClientContext

async def test_serena_thinking():
    """Test Serena's thinking and memory methods"""
    
    async with SerenaClientContext(SerenaClient()) as client:
        if not client.is_connected():
            print("❌ Failed to connect to Serena")
            return
        
        print("🧠 Testing Serena's Thinking Capabilities")
        print("=" * 50)
        
        # Activate project first
        result = await client.activate_project("/home/guci/aiProjects/CodeAnalysis")
        print(f"📁 Project activation: {'✅' if result.success else '❌'}")
        
        # Test memory operations
        print("\n💾 Testing Memory Operations...")
        
        # Write to memory
        memory_result = await client.write_memory("test_analysis", "This is a test analysis of the CodeAnalysis project")
        print(f"📝 Write memory: {'✅' if memory_result.success else '❌'}")
        if not memory_result.success:
            print(f"   Error: {memory_result.error}")
        
        # List memories
        list_result = await client.list_memories()
        print(f"📋 List memories: {'✅' if list_result.success else '❌'}")
        if list_result.success and list_result.data:
            print(f"   Available memories: {list_result.data}")
        
        # Read from memory
        read_result = await client.read_memory("test_analysis")
        print(f"📖 Read memory: {'✅' if read_result.success else '❌'}")
        if read_result.success and read_result.data:
            print(f"   Memory content: {read_result.data}")
        
        # Test thinking methods
        print("\n🤔 Testing Thinking Methods...")
        
        # Think about collected information
        think_info = await client.think_about_collected_information()
        print(f"💭 Think about info: {'✅' if think_info.success else '❌'}")
        if think_info.success and think_info.data:
            print(f"   Response: {str(think_info.data)[:200]}...")
        elif not think_info.success:
            print(f"   Error: {think_info.error}")
        
        # Think about task adherence
        think_task = await client.think_about_task_adherence()
        print(f"📋 Think about task: {'✅' if think_task.success else '❌'}")
        if think_task.success and think_task.data:
            print(f"   Response: {str(think_task.data)[:200]}...")
        elif not think_task.success:
            print(f"   Error: {think_task.error}")
        
        # Think if done
        think_done = await client.think_about_whether_you_are_done()
        print(f"✅ Think if done: {'✅' if think_done.success else '❌'}")
        if think_done.success and think_done.data:
            print(f"   Response: {str(think_done.data)[:200]}...")
        elif not think_done.success:
            print(f"   Error: {think_done.error}")
        
        # Test direct tool calling
        print("\n🔧 Testing Direct Tool Access...")
        
        # Call a tool directly that we haven't wrapped
        initial_instructions = await client.call_tool_directly("initial_instructions")
        print(f"📝 Initial instructions: {'✅' if initial_instructions.success else '❌'}")
        if initial_instructions.success and initial_instructions.data:
            print(f"   Response: {str(initial_instructions.data)[:200]}...")
        elif not initial_instructions.success:
            print(f"   Error: {initial_instructions.error}")

if __name__ == "__main__":
    asyncio.run(test_serena_thinking())