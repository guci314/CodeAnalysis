#!/usr/bin/env python3
"""
Simple test script to check Serena server connection options
"""

import asyncio
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_http_connection():
    """Test HTTP connection to Serena server"""
    try:
        async with httpx.AsyncClient() as client:
            # Test dashboard endpoint
            response = await client.get("http://localhost:4283/dashboard")
            logger.info(f"Dashboard response status: {response.status_code}")
            
            # Test if there's an API endpoint
            try:
                api_response = await client.get("http://localhost:4283/api/projects")
                logger.info(f"API response status: {api_response.status_code}")
                logger.info(f"API response: {api_response.text[:200]}...")
            except Exception as e:
                logger.info(f"No API endpoint found: {e}")
                
            # Test if there's an MCP endpoint
            try:
                mcp_response = await client.get("http://localhost:4283/mcp")
                logger.info(f"MCP response status: {mcp_response.status_code}")
            except Exception as e:
                logger.info(f"No MCP endpoint found: {e}")
                
    except Exception as e:
        logger.error(f"HTTP connection failed: {e}")

async def test_stdio_connection():
    """Test if we can still start a new MCP server"""
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        from contextlib import AsyncExitStack
        
        async with AsyncExitStack() as stack:
            # Configure server parameters for Serena
            server_params = StdioServerParameters(
                command="uvx",
                args=["--from", "git+https://github.com/oraios/serena", "serena-mcp-server"],
                env=None
            )
            
            logger.info("Testing stdio connection to new Serena MCP server...")
            
            # Establish stdio transport
            stdio_transport = await stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            
            # Create client session
            session = await stack.enter_async_context(
                ClientSession(read, write)
            )
            
            # Initialize connection
            await session.initialize()
            
            # Get available tools
            tools_response = await session.list_tools()
            available_tools = [tool.name for tool in tools_response.tools]
            
            logger.info(f"Successfully connected via stdio with tools: {available_tools}")
            return True
            
    except Exception as e:
        logger.error(f"Stdio connection failed: {e}")
        return False

async def main():
    print("🔍 Testing Serena server connections...")
    
    print("\n1. Testing HTTP connection to running server...")
    await test_http_connection()
    
    print("\n2. Testing stdio connection to new MCP server...")
    success = await test_stdio_connection()
    
    if success:
        print("✅ MCP connection works - you can use the existing client")
    else:
        print("❌ MCP connection failed - may need different approach")

if __name__ == "__main__":
    asyncio.run(main())