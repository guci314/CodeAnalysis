"""
DeepSeek-powered Community Naming Module with Concurrent API calls
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import time

try:
    from langchain_community.llms import DeepSeek
    from langchain.cache import SQLiteCache
    from langchain.globals import set_llm_cache
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


class DeepSeekCommunityNamer:
    """
    Generate meaningful names for code communities using DeepSeek API with concurrent processing.
    """
    
    def __init__(self, max_concurrent_requests: int = 8, request_delay: float = 0.1):
        """
        Initialize DeepSeek community namer.
        
        Args:
            max_concurrent_requests: Maximum concurrent API requests
            request_delay: Delay between requests (seconds)
        """
        self.max_concurrent_requests = max_concurrent_requests
        self.request_delay = request_delay
        self.logger = logging.getLogger(__name__)
        
        # Initialize DeepSeek API
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.base_url = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        self.model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
        
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is required")
        
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain community package is required. Install with: pip install langchain-community")
        
        # Setup LangChain cache
        cache_path = os.getenv('CACHE_DATABASE_PATH', '.langchain.db')
        set_llm_cache(SQLiteCache(database_path=cache_path))
        
        # Initialize DeepSeek LLM
        self.llm = DeepSeek(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            max_tokens=1024,
            temperature=0.1
        )
        
        self.logger.info(f"DeepSeek Community Namer initialized with {max_concurrent_requests} concurrent requests")
    
    def generate_names_for_communities(self, community_data: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        """
        Generate meaningful names for multiple communities concurrently.
        
        Args:
            community_data: Dictionary with community IDs as keys and community info as values
            
        Returns:
            Dictionary mapping community IDs to generated names
        """
        if not community_data:
            return {}
        
        # Filter meaningful communities (>= min size)
        min_size = int(os.getenv('MIN_COMMUNITY_SIZE_FOR_AI', '5'))
        meaningful_communities = {
            comm_id: data for comm_id, data in community_data.items()
            if data.get('size', 0) >= min_size
        }
        
        if not meaningful_communities:
            self.logger.info("No meaningful communities found for naming")
            return {}
        
        self.logger.info(f"🏷️  Generating names for {len(meaningful_communities)} meaningful communities using DeepSeek...")
        
        # Use asyncio for concurrent processing
        return asyncio.run(self._generate_names_async(meaningful_communities))
    
    async def _generate_names_async(self, community_data: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        """
        Asynchronously generate names for communities with controlled concurrency.
        """
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        async def generate_single_name(comm_id: str, data: Dict[str, Any]) -> tuple:
            """Generate name for a single community with semaphore control."""
            async with semaphore:
                try:
                    # Add delay to respect API rate limits
                    await asyncio.sleep(self.request_delay)
                    
                    # Generate name using DeepSeek
                    name = await self._call_deepseek_for_name(comm_id, data)
                    self.logger.debug(f"Generated name for community {comm_id}: {name}")
                    return comm_id, name
                    
                except Exception as e:
                    self.logger.warning(f"Failed to generate name for community {comm_id}: {e}")
                    # Fallback to generic name
                    fallback_name = self._generate_fallback_name(comm_id, data)
                    return comm_id, fallback_name
        
        # Create tasks for all communities
        tasks = [
            generate_single_name(comm_id, data) 
            for comm_id, data in community_data.items()
        ]
        
        # Execute all tasks concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        execution_time = time.time() - start_time
        
        # Convert results to dictionary
        community_names = dict(results)
        
        self.logger.info(f"✅ Generated {len(community_names)} community names in {execution_time:.2f} seconds")
        return community_names
    
    async def _call_deepseek_for_name(self, comm_id: str, community_data: Dict[str, Any]) -> str:
        """
        Call DeepSeek API to generate a meaningful name for a community.
        """
        # Prepare community information for the prompt
        size = community_data.get('size', 0)
        elements = community_data.get('elements', [])
        nodes = community_data.get('nodes', [])
        
        # Extract file paths and function names
        file_paths = []
        function_names = []
        class_names = []
        
        for element in elements:
            if element.get('file_path'):
                file_paths.append(Path(element['file_path']).stem)
            if element.get('type') == 'function':
                function_names.append(element.get('name', ''))
            elif element.get('type') == 'class':
                class_names.append(element.get('name', ''))
        
        # Extract additional info from nodes
        for node in nodes:
            if ':' in node:
                file_part, func_part = node.split(':', 1)
                file_paths.append(Path(file_part).stem)
                function_names.append(func_part)
        
        # Create context summary
        context_info = {
            'size': size,
            'files': list(set(file_paths))[:5],  # Top 5 unique files
            'functions': list(set(function_names))[:5],  # Top 5 unique functions
            'classes': list(set(class_names))[:3]  # Top 3 unique classes
        }
        
        # Build prompt for name generation
        prompt = self._build_naming_prompt(comm_id, context_info)
        
        # Call DeepSeek API in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = loop.run_in_executor(executor, self.llm.invoke, prompt)
            response = await future
        
        # Extract and clean the generated name
        generated_name = self._extract_name_from_response(response)
        return generated_name
    
    def _build_naming_prompt(self, comm_id: str, context_info: Dict[str, Any]) -> str:
        """
        Build a prompt for DeepSeek to generate a meaningful community name.
        """
        prompt = f"""你是一个代码架构分析专家。请为以下代码社区生成一个简洁、有意义的中文名称。

社区信息：
- 社区ID: {comm_id}
- 成员数量: {context_info['size']}
- 相关文件: {', '.join(context_info['files'])}
- 主要函数: {', '.join(context_info['functions'])}
- 主要类: {', '.join(context_info['classes'])}

命名要求：
1. 名称应该反映这个代码社区的主要功能或用途
2. 使用2-6个中文字符，简洁明了
3. 避免使用"社区"、"模块"、"组件"等通用词汇
4. 重点体现功能特征而非技术实现
5. 名称应该让开发者一眼就能理解这部分代码的作用

请只返回生成的名称，不要包含其他解释文字。

示例：
- 如果社区主要处理用户认证 → "用户认证"
- 如果社区主要处理消息队列 → "消息队列"
- 如果社区主要处理文件上传 → "文件上传"

生成的社区名称："""

        return prompt
    
    def _extract_name_from_response(self, response: str) -> str:
        """
        Extract and clean the generated name from DeepSeek response.
        """
        if not response:
            return "未知功能"
        
        # Clean the response
        name = response.strip()
        
        # Remove common prefixes/suffixes
        prefixes_to_remove = ['社区名称：', '名称：', '生成的社区名称：', '社区：']
        for prefix in prefixes_to_remove:
            if name.startswith(prefix):
                name = name[len(prefix):].strip()
        
        # Remove quotes
        name = name.strip('"\'""''')
        
        # Limit length
        if len(name) > 10:
            name = name[:10]
        
        # Fallback if empty
        if not name:
            name = "未知功能"
        
        return name
    
    def _generate_fallback_name(self, comm_id: str, community_data: Dict[str, Any]) -> str:
        """
        Generate a fallback name when DeepSeek API fails.
        """
        size = community_data.get('size', 0)
        elements = community_data.get('elements', [])
        
        # Try to extract meaningful info for fallback
        file_names = []
        for element in elements:
            if element.get('file_path'):
                file_names.append(Path(element['file_path']).stem)
        
        if file_names:
            # Use most common file name
            from collections import Counter
            most_common = Counter(file_names).most_common(1)
            if most_common:
                base_name = most_common[0][0]
                # Simple keyword mapping
                keyword_map = {
                    'agent': '智能体',
                    'message': '消息处理',
                    'memory': '内存管理',
                    'performance': '性能监控',
                    'config': '配置管理',
                    'util': '工具函数',
                    'helper': '辅助功能',
                    'handler': '处理器',
                    'manager': '管理器',
                    'processor': '处理器',
                    'analyzer': '分析器',
                    'generator': '生成器'
                }
                
                for keyword, chinese in keyword_map.items():
                    if keyword in base_name.lower():
                        return chinese
                
                return f"{base_name.title()}功能"
        
        # Final fallback based on size
        if size >= 10:
            return "大型功能"
        elif size >= 5:
            return "中型功能"
        else:
            return "小型功能"
    
    def is_available(self) -> bool:
        """
        Check if DeepSeek API is available.
        """
        return bool(self.api_key and LANGCHAIN_AVAILABLE)


# Usage example and testing
def test_deepseek_community_namer():
    """
    Test the DeepSeek community namer.
    """
    try:
        namer = DeepSeekCommunityNamer(max_concurrent_requests=3, request_delay=0.2)
        
        # Test data
        test_communities = {
            "0": {
                "size": 8,
                "elements": [
                    {"type": "function", "name": "validate_input", "file_path": "/path/to/validator.py"},
                    {"type": "function", "name": "process_request", "file_path": "/path/to/processor.py"},
                    {"type": "class", "name": "AgentValidator", "file_path": "/path/to/agent.py"}
                ],
                "nodes": [
                    "/path/to/validator.py:validate_input",
                    "/path/to/processor.py:process_request"
                ]
            },
            "1": {
                "size": 12,
                "elements": [
                    {"type": "function", "name": "compress_data", "file_path": "/path/to/compression.py"},
                    {"type": "function", "name": "decompress_data", "file_path": "/path/to/compression.py"},
                    {"type": "class", "name": "CompressionManager", "file_path": "/path/to/manager.py"}
                ],
                "nodes": [
                    "/path/to/compression.py:compress_data",
                    "/path/to/compression.py:decompress_data"
                ]
            }
        }
        
        # Generate names
        names = namer.generate_names_for_communities(test_communities)
        
        print("Generated community names:")
        for comm_id, name in names.items():
            print(f"Community {comm_id}: {name}")
            
    except Exception as e:
        print(f"Test failed: {e}")


if __name__ == "__main__":
    test_deepseek_community_namer()