"""
异步并发 DeepSeek Language Model Integration for Code Analysis
"""

import os
import json
import logging
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import time


class AsyncDeepSeekAnalyzer:
    """
    异步并发 DeepSeek language model integration for intelligent code analysis.
    """
    
    def __init__(self, max_concurrent_requests: int = 20, request_delay: float = 0.1):
        """
        Initialize Async DeepSeek analyzer with configuration from environment.
        
        Args:
            max_concurrent_requests: 最大并发请求数
            request_delay: 请求间延迟(秒)，避免API限流
        """
        load_dotenv()
        
        # Configuration
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.base_url = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        self.model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
        self.max_tokens = int(os.getenv('DEEPSEEK_MAX_TOKENS', '8192'))
        self.temperature = float(os.getenv('DEEPSEEK_TEMPERATURE', '0'))
        
        # 并发控制
        self.max_concurrent_requests = max_concurrent_requests
        self.request_delay = request_delay
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Validate configuration
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is required")
        
        self.logger.info(f"Async DeepSeek analyzer initialized with model: {self.model}")
        self.logger.info(f"Max concurrent requests: {max_concurrent_requests}")
    
    async def analyze_code_function_async(self, code: str, element_id: str = None) -> Dict[str, Any]:
        """
        异步分析代码功能.
        
        Args:
            code: Python code to analyze
            element_id: 代码元素ID，用于日志追踪
            
        Returns:
            Dictionary containing analysis results
        """
        async with self.semaphore:  # 限制并发数
            try:
                # 添加请求延迟避免API限流
                await asyncio.sleep(self.request_delay)
                
                prompt = f"""
                分析以下Python代码的功能和特征：
                
                ```python
                {code[:2000]}  # 限制代码长度避免超出token限制
                ```
                
                请从以下方面分析，并以JSON格式返回结果：
                1. 主要功能描述 (functionality)
                2. 复杂度评估，1-10分 (complexity)
                3. 代码质量评估，1-10分 (quality)
                4. 重构建议列表 (suggestions)
                5. 功能分类标签列表 (tags)
                6. 依赖关系分析 (dependencies)
                
                返回格式：
                {{
                    "functionality": "功能描述",
                    "complexity": 数字,
                    "quality": 数字,
                    "suggestions": ["建议1", "建议2"],
                    "tags": ["标签1", "标签2"],
                    "dependencies": ["依赖1", "依赖2"]
                }}
                """
                
                result = await self._make_api_request_async(prompt)
                
                self.logger.debug(f"Code analysis completed for {element_id or 'unknown'}")
                return result
                
            except Exception as e:
                self.logger.error(f"Error analyzing code {element_id or 'unknown'}: {str(e)}")
                return self._get_default_analysis()
    
    async def analyze_community_function_async(self, community_data: Dict[str, Any], community_id: str) -> Dict[str, Any]:
        """
        异步分析社区功能.
        
        Args:
            community_data: 社区数据，包含成员列表和统计信息
            community_id: 社区ID
            
        Returns:
            Dictionary containing community analysis results
        """
        async with self.semaphore:
            try:
                await asyncio.sleep(self.request_delay)
                
                # 构建社区摘要
                community_summary = self._build_community_summary(community_data)
                
                prompt = f"""
                分析以下代码社区的功能和特征：
                
                社区信息：
                - 社区ID: {community_id}
                - 成员数量: {community_data.get('size', 0)}
                - 内聚性: {community_data.get('cohesion', 0):.3f}
                - 耦合性: {community_data.get('coupling', 0):.3f}
                
                社区成员：
                {community_summary}
                
                请从以下方面分析，并以JSON格式返回结果：
                1. 社区主要功能描述 (functionality)
                2. 架构模式识别 (architecture_pattern)
                3. 设计质量评估，1-10分 (design_quality)
                4. 重构建议列表 (refactor_suggestions)
                5. 功能分类标签 (functional_tags)
                6. 与其他模块的关系分析 (external_dependencies)
                
                返回格式：
                {{
                    "functionality": "社区功能描述",
                    "architecture_pattern": "架构模式",
                    "design_quality": 数字,
                    "refactor_suggestions": ["建议1", "建议2"],
                    "functional_tags": ["标签1", "标签2"],
                    "external_dependencies": ["依赖1", "依赖2"]
                }}
                """
                
                result = await self._make_api_request_async(prompt)
                
                self.logger.debug(f"Community analysis completed for {community_id}")
                return result
                
            except Exception as e:
                self.logger.error(f"Error analyzing community {community_id}: {str(e)}")
                return self._get_default_community_analysis()
    
    async def analyze_communities_batch_async(self, communities: Dict[str, Any]) -> Dict[str, Any]:
        """
        批量异步分析所有社区.
        
        Args:
            communities: 社区字典，key为社区ID，value为社区数据
            
        Returns:
            Dictionary containing all community analysis results
        """
        start_time = time.time()
        self.logger.info(f"Starting batch analysis of {len(communities)} communities...")
        
        # 创建异步任务列表
        tasks = []
        for community_id, community_data in communities.items():
            task = self.analyze_community_function_async(community_data, community_id)
            tasks.append((community_id, task))
        
        # 并发执行所有任务
        results = {}
        completed_tasks = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        # 处理结果
        for (community_id, _), result in zip(tasks, completed_tasks):
            if isinstance(result, Exception):
                self.logger.error(f"Community {community_id} analysis failed: {result}")
                results[community_id] = self._get_default_community_analysis()
            else:
                results[community_id] = result
        
        elapsed_time = time.time() - start_time
        self.logger.info(f"Batch analysis completed in {elapsed_time:.2f} seconds")
        self.logger.info(f"Average time per community: {elapsed_time/len(communities):.2f} seconds")
        
        return results
    
    async def _make_api_request_async(self, prompt: str) -> Dict[str, Any]:
        """
        异步发送API请求到DeepSeek.
        
        Args:
            prompt: 提示文本
            
        Returns:
            解析后的API响应
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.model,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
            async with session.post(
                f'{self.base_url}/chat/completions',
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data['choices'][0]['message']['content']
                    return self._parse_analysis_response(content)
                else:
                    error_text = await response.text()
                    raise Exception(f"API request failed: {response.status} - {error_text}")
    
    def _build_community_summary(self, community_data: Dict[str, Any]) -> str:
        """构建社区成员摘要."""
        nodes = community_data.get('nodes', [])
        
        # 限制显示的节点数量
        max_nodes = 20
        if len(nodes) > max_nodes:
            summary_nodes = nodes[:max_nodes]
            summary = "\\n".join([f"- {node}" for node in summary_nodes])
            summary += f"\\n... 还有 {len(nodes) - max_nodes} 个成员"
        else:
            summary = "\\n".join([f"- {node}" for node in nodes])
        
        return summary
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """解析API响应内容."""
        try:
            # 尝试直接解析JSON
            if response.strip().startswith('{'):
                return json.loads(response.strip())
            
            # 如果响应包含代码块，提取JSON部分
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                json_str = response[start:end].strip()
                return json.loads(json_str)
            
            # 如果响应包含普通代码块，提取内容
            if '```' in response:
                start = response.find('```') + 3
                end = response.find('```', start)
                json_str = response[start:end].strip()
                return json.loads(json_str)
            
            # 如果都不是，返回默认结果
            return self._get_default_analysis()
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse response as JSON: {e}")
            return self._get_default_analysis()
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """获取默认分析结果."""
        return {
            "functionality": "分析失败，无法确定功能",
            "complexity": 5,
            "quality": 5,
            "suggestions": ["建议重新分析"],
            "tags": ["unknown"],
            "dependencies": []
        }
    
    def _get_default_community_analysis(self) -> Dict[str, Any]:
        """获取默认社区分析结果."""
        return {
            "functionality": "社区分析失败，无法确定功能",
            "architecture_pattern": "unknown",
            "design_quality": 5,
            "refactor_suggestions": ["建议重新分析"],
            "functional_tags": ["unknown"],
            "external_dependencies": []
        }
    
    def is_available(self) -> bool:
        """检查DeepSeek API是否可用."""
        return bool(self.api_key)


# 使用示例
async def main():
    """演示异步并发使用."""
    analyzer = AsyncDeepSeekAnalyzer(max_concurrent_requests=5, request_delay=0.2)
    
    # 模拟社区数据
    communities = {
        "community_1": {
            "size": 10,
            "cohesion": 0.8,
            "coupling": 0.2,
            "nodes": ["file1.py:function1", "file1.py:function2"]
        },
        "community_2": {
            "size": 15,
            "cohesion": 0.7,
            "coupling": 0.3,
            "nodes": ["file2.py:class1", "file2.py:class2"]
        }
    }
    
    # 批量分析
    results = await analyzer.analyze_communities_batch_async(communities)
    
    for community_id, result in results.items():
        print(f"\\n{community_id}: {result['functionality']}")


if __name__ == "__main__":
    asyncio.run(main())