"""
社区描述生成器 - 使用异步并发DeepSeek分析
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from async_deepseek_analyzer import AsyncDeepSeekAnalyzer


class CommunityDescriptionGenerator:
    """
    使用异步并发DeepSeek分析生成社区功能描述的专用类
    """
    
    def __init__(self, max_concurrent_requests: int = 20, request_delay: float = 0.1):
        """
        初始化社区描述生成器
        
        Args:
            max_concurrent_requests: 最大并发请求数
            request_delay: 请求间延迟(秒)
        """
        self.logger = logging.getLogger(__name__)
        self.max_concurrent_requests = max_concurrent_requests
        self.request_delay = request_delay
        
        # 初始化异步DeepSeek分析器
        try:
            self.deepseek_analyzer = AsyncDeepSeekAnalyzer(
                max_concurrent_requests=max_concurrent_requests,
                request_delay=request_delay
            )
            self.deepseek_available = self.deepseek_analyzer.is_available()
        except Exception as e:
            self.logger.warning(f"DeepSeek analyzer initialization failed: {e}")
            self.deepseek_analyzer = None
            self.deepseek_available = False
    
    async def generate_all_descriptions_async(self, communities_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        异步并发生成所有社区的功能描述
        
        Args:
            communities_data: 社区数据字典
            
        Returns:
            包含所有社区描述的字典
        """
        if not self.deepseek_available:
            self.logger.warning("DeepSeek not available, generating basic descriptions")
            return self._generate_basic_descriptions(communities_data)
        
        start_time = time.time()
        total_communities = len(communities_data)
        
        self.logger.info(f"🚀 Starting async generation of {total_communities} community descriptions...")
        self.logger.info(f"📊 Concurrency settings: {self.max_concurrent_requests} max requests, {self.request_delay}s delay")
        
        try:
            # 使用异步批量分析
            descriptions = await self.deepseek_analyzer.analyze_communities_batch_async(communities_data)
            
            elapsed_time = time.time() - start_time
            avg_time = elapsed_time / total_communities if total_communities > 0 else 0
            
            self.logger.info(f"✅ Async community descriptions completed!")
            self.logger.info(f"⏱️  Total time: {elapsed_time:.2f}s")
            self.logger.info(f"📈 Average time per community: {avg_time:.2f}s")
            self.logger.info(f"🚀 Speedup vs sequential: ~{self.max_concurrent_requests}x")
            
            return descriptions
            
        except Exception as e:
            self.logger.error(f"❌ Async description generation failed: {e}")
            return self._generate_basic_descriptions(communities_data)
    
    def generate_descriptions_sync(self, communities_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        同步运行异步描述生成 (供非异步环境调用)
        
        Args:
            communities_data: 社区数据字典
            
        Returns:
            包含所有社区描述的字典
        """
        try:
            # 在新的事件循环中运行异步方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.generate_all_descriptions_async(communities_data))
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Error in sync wrapper: {e}")
            return self._generate_basic_descriptions(communities_data)
    
    def _generate_basic_descriptions(self, communities_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成基础社区描述 (不使用AI)
        
        Args:
            communities_data: 社区数据字典
            
        Returns:
            基础描述字典
        """
        descriptions = {}
        
        for community_id, community_data in communities_data.items():
            size = community_data.get('size', 0)
            cohesion = community_data.get('cohesion', 0)
            coupling = community_data.get('coupling', 0)
            nodes = community_data.get('nodes', [])
            
            # 分析文件类型分布
            file_types = self._analyze_file_types(nodes)
            
            # 生成基础描述
            descriptions[community_id] = {
                "functionality": f"社区{community_id}包含{size}个代码元素，主要涉及{', '.join(file_types)}",
                "architecture_pattern": self._infer_pattern_from_nodes(nodes),
                "design_quality": self._calculate_design_quality(cohesion, coupling),
                "refactor_suggestions": self._generate_basic_suggestions(cohesion, coupling),
                "functional_tags": file_types,
                "external_dependencies": []
            }
        
        return descriptions
    
    def _analyze_file_types(self, nodes: List[str]) -> List[str]:
        """分析节点中的文件类型分布"""
        file_patterns = {
            'test': ['test_', '_test', 'tests/'],
            'config': ['config', 'settings', 'env'],
            'api': ['api', 'endpoint', 'service'],
            'model': ['model', 'entity', 'schema'],
            'util': ['util', 'helper', 'common'],
            'ui': ['ui', 'view', 'component'],
            'core': ['core', 'base', 'main']
        }
        
        detected_types = set()
        
        for node in nodes:
            node_lower = node.lower()
            for type_name, patterns in file_patterns.items():
                if any(pattern in node_lower for pattern in patterns):
                    detected_types.add(type_name)
        
        return list(detected_types) if detected_types else ['general']
    
    def _infer_pattern_from_nodes(self, nodes: List[str]) -> str:
        """从节点推断架构模式"""
        if any('test' in node.lower() for node in nodes):
            return "testing"
        elif any('api' in node.lower() for node in nodes):
            return "api_layer"
        elif any('model' in node.lower() for node in nodes):
            return "data_model"
        elif any('service' in node.lower() for node in nodes):
            return "service_layer"
        else:
            return "functional_module"
    
    def _calculate_design_quality(self, cohesion: float, coupling: float) -> int:
        """计算设计质量评分 (1-10)"""
        # 高内聚低耦合得分高
        quality_score = (cohesion * 10) - (coupling * 20)
        return max(1, min(10, int(quality_score + 5)))
    
    def _generate_basic_suggestions(self, cohesion: float, coupling: float) -> List[str]:
        """生成基础重构建议"""
        suggestions = []
        
        if cohesion < 0.3:
            suggestions.append("建议提高模块内聚性，将相关功能组织在一起")
        
        if coupling > 0.3:
            suggestions.append("建议降低模块耦合度，减少对外部模块的依赖")
        
        if not suggestions:
            suggestions.append("当前模块设计合理，保持良好的内聚性和低耦合性")
        
        return suggestions
    
    def save_descriptions_to_file(self, descriptions: Dict[str, Any], output_path: str):
        """
        保存社区描述到文件
        
        Args:
            descriptions: 社区描述字典
            output_path: 输出文件路径
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存JSON格式
        json_path = output_file.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(descriptions, f, indent=2, ensure_ascii=False)
        
        # 保存Markdown格式
        md_path = output_file.with_suffix('.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("# 社区功能描述报告\\n\\n")
            f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"总社区数: {len(descriptions)}\\n\\n")
            
            for i, (community_id, desc) in enumerate(descriptions.items(), 1):
                f.write(f"## {i}. 社区 {community_id}\\n\\n")
                f.write(f"**功能描述**: {desc.get('functionality', 'N/A')}\\n\\n")
                f.write(f"**架构模式**: {desc.get('architecture_pattern', 'N/A')}\\n\\n")
                f.write(f"**设计质量**: {desc.get('design_quality', 'N/A')}/10\\n\\n")
                
                suggestions = desc.get('refactor_suggestions', [])
                if suggestions:
                    f.write("**重构建议**:\\n")
                    for suggestion in suggestions:
                        f.write(f"- {suggestion}\\n")
                    f.write("\\n")
                
                tags = desc.get('functional_tags', [])
                if tags:
                    f.write(f"**功能标签**: {', '.join(tags)}\\n\\n")
                
                f.write("---\\n\\n")
        
        self.logger.info(f"📄 Community descriptions saved to:")
        self.logger.info(f"  - JSON: {json_path}")
        self.logger.info(f"  - Markdown: {md_path}")


# 使用示例和测试
async def test_async_community_description():
    """测试异步社区描述生成"""
    
    # 模拟社区数据 (使用真实的AgentFramework数据结构)
    test_communities = {
        "0": {
            "size": 26,
            "cohesion": 0.08,
            "coupling": 0.018867924528301886,
            "nodes": [
                "/home/guci/aiProjects/AgentFrameWork/enhancedAgent_v2.py:validate_variables",
                "/home/guci/aiProjects/AgentFrameWork/enhancedAgent_v2.py:_categorize_state_relevance",
                "/home/guci/aiProjects/AgentFrameWork/static_workflow/MultiStepAgent_v3.py:get_workflow_info"
            ]
        },
        "1": {
            "size": 24,
            "cohesion": 0.09782608695652174,
            "coupling": 0.01818181818181818,
            "nodes": [
                "/home/guci/aiProjects/AgentFrameWork/demo_agent_compression.py:chat_with_compression",
                "/home/guci/aiProjects/AgentFrameWork/message_compress.py:compress_messages",
                "/home/guci/aiProjects/AgentFrameWork/performance_monitor.py:decorator"
            ]
        }
    }
    
    # 创建生成器并测试
    generator = CommunityDescriptionGenerator(max_concurrent_requests=3, request_delay=0.1)
    
    print("🧪 Testing async community description generation...")
    descriptions = await generator.generate_all_descriptions_async(test_communities)
    
    print("\\n📋 Generated descriptions:")
    for comm_id, desc in descriptions.items():
        print(f"\\n{comm_id}: {desc['functionality']}")
    
    # 保存结果
    generator.save_descriptions_to_file(descriptions, "test_community_descriptions")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_async_community_description())