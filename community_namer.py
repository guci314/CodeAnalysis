"""
Community Naming Module - Generate meaningful names for code communities
"""

import os
import re
import logging
from typing import Dict, List, Any, Optional, Set
from collections import Counter
from pathlib import Path


class CommunityNamer:
    """
    Generate meaningful names for code communities based on their members and characteristics.
    """
    
    def __init__(self, language: str = "zh", style: str = "descriptive"):
        """
        Initialize community namer.
        
        Args:
            language: Language for names ('zh', 'en', 'auto')
            style: Naming style ('descriptive', 'technical', 'simple')
        """
        self.language = language
        self.style = style
        self.logger = logging.getLogger(__name__)
        
        # 功能模式映射
        self.function_patterns = {
            'zh': {
                'agent': '智能体',
                'compression': '压缩',
                'performance': '性能监控',
                'monitor': '监控',
                'memory': '内存管理',
                'message': '消息处理',
                'workflow': '工作流',
                'static': '静态',
                'dynamic': '动态',
                'enhanced': '增强',
                'multi': '多',
                'demo': '演示',
                'test': '测试',
                'config': '配置',
                'api': 'API接口',
                'service': '服务',
                'handler': '处理器',
                'manager': '管理器',
                'processor': '处理器',
                'analyzer': '分析器',
                'detector': '检测器',
                'generator': '生成器',
                'validator': '验证器',
                'optimizer': '优化器',
                'controller': '控制器',
                'executor': '执行器',
                'scheduler': '调度器',
                'router': '路由器',
                'filter': '过滤器',
                'parser': '解析器',
                'formatter': '格式化器',
                'transformer': '转换器',
                'adapter': '适配器',
                'factory': '工厂',
                'builder': '构建器',
                'helper': '辅助',
                'util': '工具',
                'common': '通用',
                'base': '基础',
                'core': '核心',
                'main': '主要',
                'client': '客户端',
                'server': '服务端',
                'model': '模型',
                'view': '视图',
                'component': '组件',
                'module': '模块',
                'system': '系统',
                'framework': '框架',
                'library': '库',
                'package': '包',
                'interface': '接口',
                'abstract': '抽象',
                'concrete': '具体',
                'implementation': '实现'
            },
            'en': {
                'agent': 'Agent',
                'compression': 'Compression',
                'performance': 'Performance',
                'monitor': 'Monitor',
                'memory': 'Memory',
                'message': 'Message',
                'workflow': 'Workflow',
                'static': 'Static',
                'dynamic': 'Dynamic',
                'enhanced': 'Enhanced',
                'multi': 'Multi',
                'demo': 'Demo',
                'test': 'Test',
                'config': 'Config',
                'api': 'API',
                'service': 'Service',
                'handler': 'Handler',
                'manager': 'Manager',
                'processor': 'Processor',
                'analyzer': 'Analyzer',
                'detector': 'Detector',
                'generator': 'Generator',
                'validator': 'Validator',
                'optimizer': 'Optimizer',
                'controller': 'Controller',
                'executor': 'Executor',
                'scheduler': 'Scheduler',
                'router': 'Router',
                'filter': 'Filter',
                'parser': 'Parser',
                'formatter': 'Formatter',
                'transformer': 'Transformer',
                'adapter': 'Adapter',
                'factory': 'Factory',
                'builder': 'Builder',
                'helper': 'Helper',
                'util': 'Utility',
                'common': 'Common',
                'base': 'Base',
                'core': 'Core',
                'main': 'Main',
                'client': 'Client',
                'server': 'Server',
                'model': 'Model',
                'view': 'View',
                'component': 'Component',
                'module': 'Module',
                'system': 'System',
                'framework': 'Framework',
                'library': 'Library',
                'package': 'Package',
                'interface': 'Interface',
                'abstract': 'Abstract',
                'concrete': 'Concrete',
                'implementation': 'Implementation'
            }
        }
        
        # 架构模式映射
        self.architecture_patterns = {
            'zh': {
                'testing': '测试模块',
                'api_layer': 'API层',
                'data_model': '数据模型层',
                'service_layer': '服务层',
                'functional_module': '功能模块',
                'controller': '控制器层',
                'view': '视图层',
                'middleware': '中间件',
                'adapter': '适配器模式',
                'factory': '工厂模式',
                'observer': '观察者模式',
                'strategy': '策略模式',
                'decorator': '装饰器模式',
                'facade': '外观模式',
                'proxy': '代理模式',
                'singleton': '单例模式'
            },
            'en': {
                'testing': 'Testing Module',
                'api_layer': 'API Layer',
                'data_model': 'Data Model Layer',
                'service_layer': 'Service Layer',
                'functional_module': 'Functional Module',
                'controller': 'Controller Layer',
                'view': 'View Layer',
                'middleware': 'Middleware',
                'adapter': 'Adapter Pattern',
                'factory': 'Factory Pattern',
                'observer': 'Observer Pattern',
                'strategy': 'Strategy Pattern',
                'decorator': 'Decorator Pattern',
                'facade': 'Facade Pattern',
                'proxy': 'Proxy Pattern',
                'singleton': 'Singleton Pattern'
            }
        }
    
    def generate_community_name(self, community_data: Dict[str, Any], 
                               ai_description: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a meaningful name for a community.
        
        Args:
            community_data: Community data including nodes, elements, etc.
            ai_description: Optional AI-generated description
            
        Returns:
            Meaningful community name
        """
        try:
            # 提取关键信息
            nodes = community_data.get('nodes', [])
            elements = community_data.get('elements', [])
            size = community_data.get('size', 0)
            
            # 方法1: 基于AI描述生成名称（优先级最高）
            if ai_description:
                ai_name = self._generate_name_from_ai_description(ai_description)
                if ai_name:
                    return ai_name
            
            # 方法2: 基于文件路径分析
            path_name = self._generate_name_from_paths(nodes)
            if path_name:
                return path_name
            
            # 方法3: 基于代码元素分析
            element_name = self._generate_name_from_elements(elements)
            if element_name:
                return element_name
            
            # 方法4: 基于节点名称分析
            node_name = self._generate_name_from_nodes(nodes)
            if node_name:
                return node_name
            
            # 备用方案：基于大小的通用名称
            return self._generate_generic_name(size)
            
        except Exception as e:
            self.logger.warning(f"Error generating community name: {e}")
            return self._generate_generic_name(community_data.get('size', 0))
    
    def _generate_name_from_ai_description(self, ai_description: Dict[str, Any]) -> Optional[str]:
        """基于AI描述生成名称，优先考虑功能内容而不是架构模式"""
        try:
            # 获取关键信息
            tags = ai_description.get('functional_tags', [])
            functionality = ai_description.get('functionality', '')
            architecture_pattern = ai_description.get('architecture_pattern', '')
            
            # 方法1: 基于功能描述提取关键词（优先级最高）
            if functionality:
                keywords = self._extract_keywords_from_functionality(functionality)
                if keywords:
                    return self._build_name_from_keywords(keywords)
            
            # 方法2: 基于功能标签生成名称
            if tags and tags != ['unknown']:
                # 使用前2个最相关的标签
                relevant_tags = [tag for tag in tags[:2] if tag in self.function_patterns.get(self.language, {})]
                if relevant_tags:
                    tag_names = []
                    for tag in relevant_tags:
                        tag_name = self.function_patterns[self.language][tag]
                        tag_names.append(tag_name)
                    
                    if self.language == 'zh':
                        return f"{''.join(tag_names)}模块"
                    else:
                        return f"{' '.join(tag_names)} Module"
                
                # 如果没有匹配的模式，使用原始标签
                primary_tag = tags[0]
                if self.language == 'zh':
                    return f"{primary_tag.title()}模块"
                else:
                    return f"{primary_tag.title()} Module"
            
            # 方法3: 基于架构模式（降低优先级，且只在无其他信息时使用）
            if architecture_pattern and architecture_pattern != 'unknown':
                # 只有在确实没有其他功能信息时才使用架构模式
                if not functionality and not tags:
                    pattern_name = self.architecture_patterns.get(self.language, {}).get(
                        architecture_pattern, architecture_pattern
                    )
                    if pattern_name:
                        return pattern_name
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error in AI description naming: {e}")
            return None
    
    def _generate_name_from_paths(self, nodes: List[str]) -> Optional[str]:
        """基于文件路径生成名称"""
        try:
            if not nodes:
                return None
            
            # 提取文件名（不含扩展名）
            file_names = []
            for node in nodes:
                if ':' in node:
                    file_path = node.split(':')[0]
                    file_name = Path(file_path).stem
                    file_names.append(file_name)
            
            if not file_names:
                return None
            
            # 寻找共同前缀或模式
            common_patterns = self._find_common_patterns(file_names)
            if common_patterns:
                return self._build_name_from_patterns(common_patterns)
            
            # 使用最频繁的文件名作为基础
            file_counter = Counter(file_names)
            most_common_file = file_counter.most_common(1)[0][0] if file_counter else ''
            
            if most_common_file:
                return self._transform_filename_to_name(most_common_file)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error in path-based naming: {e}")
            return None
    
    def _generate_name_from_elements(self, elements: List[Dict[str, Any]]) -> Optional[str]:
        """基于代码元素生成名称"""
        try:
            if not elements:
                return None
            
            # 分析元素类型分布
            type_counter = Counter(elem.get('type', 'unknown') for elem in elements)
            name_words = []
            
            # 提取所有元素名称中的关键词
            for element in elements:
                name = element.get('name', '')
                if name:
                    # 分解驼峰命名和下划线命名
                    words = self._split_identifier(name)
                    name_words.extend(words)
            
            # 找出最频繁的关键词
            word_counter = Counter(name_words)
            top_words = [word for word, count in word_counter.most_common(3) if count > 1]
            
            if top_words:
                return self._build_name_from_keywords(top_words)
            
            # 基于元素类型
            most_common_type = type_counter.most_common(1)[0][0] if type_counter else 'unknown'
            if most_common_type != 'unknown':
                if self.language == 'zh':
                    type_map = {'class': '类群组', 'function': '函数群组', 'module': '模块群组'}
                    return type_map.get(most_common_type, f"{most_common_type}群组")
                else:
                    return f"{most_common_type.title()} Group"
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error in element-based naming: {e}")
            return None
    
    def _generate_name_from_nodes(self, nodes: List[str]) -> Optional[str]:
        """基于节点名称生成名称"""
        try:
            if not nodes:
                return None
            
            # 提取函数/类名
            identifiers = []
            for node in nodes:
                if ':' in node:
                    identifier = node.split(':')[-1]  # 取最后一部分作为标识符
                    identifiers.append(identifier)
            
            if not identifiers:
                return None
            
            # 寻找共同模式
            common_words = []
            for identifier in identifiers:
                words = self._split_identifier(identifier)
                common_words.extend(words)
            
            word_counter = Counter(common_words)
            top_words = [word for word, count in word_counter.most_common(2) if count > 1]
            
            if top_words:
                return self._build_name_from_keywords(top_words)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error in node-based naming: {e}")
            return None
    
    def _generate_generic_name(self, size: int) -> str:
        """生成通用名称"""
        if self.language == 'zh':
            if size >= 20:
                return "大型功能模块"
            elif size >= 10:
                return "中型功能模块"
            else:
                return "小型功能模块"
        else:
            if size >= 20:
                return "Large Functional Module"
            elif size >= 10:
                return "Medium Functional Module"
            else:
                return "Small Functional Module"
    
    def _split_identifier(self, identifier: str) -> List[str]:
        """分解标识符为单词"""
        # 处理驼峰命名
        words = re.findall(r'[A-Z][a-z]*|[a-z]+|[0-9]+', identifier)
        
        # 处理下划线命名
        if '_' in identifier:
            underscore_words = identifier.split('_')
            words.extend(underscore_words)
        
        # 清理和标准化
        cleaned_words = []
        for word in words:
            word = word.lower().strip()
            if len(word) > 2 and word.isalpha():  # 只保留有意义的字母单词
                cleaned_words.append(word)
        
        return cleaned_words
    
    def _find_common_patterns(self, file_names: List[str]) -> List[str]:
        """寻找文件名中的共同模式"""
        if not file_names:
            return []
        
        # 寻找共同前缀
        common_prefix = os.path.commonprefix(file_names)
        patterns = []
        
        if len(common_prefix) > 3:
            patterns.append(common_prefix.rstrip('_-'))
        
        # 寻找共同关键词
        all_words = []
        for filename in file_names:
            words = self._split_identifier(filename)
            all_words.extend(words)
        
        word_counter = Counter(all_words)
        common_words = [word for word, count in word_counter.most_common(3) 
                       if count > len(file_names) * 0.3]  # 出现在30%以上文件中
        
        patterns.extend(common_words)
        return patterns
    
    def _build_name_from_patterns(self, patterns: List[str]) -> str:
        """从模式构建名称"""
        if not patterns:
            return ""
        
        # 映射到友好名称
        friendly_names = []
        for pattern in patterns:
            if pattern.lower() in self.function_patterns.get(self.language, {}):
                friendly_name = self.function_patterns[self.language][pattern.lower()]
                friendly_names.append(friendly_name)
            else:
                friendly_names.append(pattern.title())
        
        if self.language == 'zh':
            return f"{''.join(friendly_names[:2])}模块"
        else:
            return f"{' '.join(friendly_names[:2])} Module"
    
    def _build_name_from_keywords(self, keywords: List[str]) -> str:
        """从关键词构建名称"""
        if not keywords:
            return ""
        
        # 映射关键词
        mapped_keywords = []
        for keyword in keywords[:2]:  # 最多使用前2个关键词
            if keyword.lower() in self.function_patterns.get(self.language, {}):
                mapped = self.function_patterns[self.language][keyword.lower()]
                mapped_keywords.append(mapped)
            else:
                mapped_keywords.append(keyword.title())
        
        if self.language == 'zh':
            return f"{''.join(mapped_keywords)}模块"
        else:
            return f"{' '.join(mapped_keywords)} Module"
    
    def _extract_keywords_from_functionality(self, functionality: str) -> List[str]:
        """从功能描述中提取关键词，智能识别功能特征"""
        try:
            keywords = []
            functionality_lower = functionality.lower()
            
            # 定义功能关键词映射（中文到英文）
            functionality_keywords = {
                # 核心功能动作
                '验证': 'validation',
                '校验': 'validation', 
                '检查': 'validation',
                '压缩': 'compression',
                '解压': 'compression',
                '监控': 'monitoring',
                '监测': 'monitoring',
                '分析': 'analysis',
                '解析': 'parsing',
                '处理': 'processing',
                '管理': 'management',
                '控制': 'control',
                '执行': 'execution',
                '调度': 'scheduling',
                '路由': 'routing',
                '转换': 'transformation',
                '优化': 'optimization',
                '缓存': 'caching',
                '存储': 'storage',
                '持久化': 'persistence',
                '同步': 'synchronization',
                '异步': 'async',
                '并发': 'concurrency',
                '测试': 'testing',
                '调试': 'debugging',
                '日志': 'logging',
                '记录': 'logging',
                '配置': 'configuration',
                '设置': 'configuration',
                '初始化': 'initialization',
                '启动': 'startup',
                '连接': 'connection',
                '通信': 'communication',
                '传输': 'transmission',
                '发送': 'sending',
                '接收': 'receiving',
                '响应': 'response',
                '请求': 'request',
                '查询': 'query',
                '搜索': 'search',
                '过滤': 'filtering',
                '排序': 'sorting',
                '计算': 'calculation',
                '统计': 'statistics',
                '报告': 'reporting',
                '展示': 'display',
                '渲染': 'rendering',
                '界面': 'interface',
                '用户': 'user',
                '系统': 'system',
                '服务': 'service',
                '模块': 'module',
                '组件': 'component',
                '工具': 'utility',
                '帮助': 'helper',
                '辅助': 'auxiliary',
                
                # 领域特定
                '智能体': 'agent',
                '代理': 'agent',
                '工作流': 'workflow',
                '任务': 'task',
                '状态': 'state',
                '决策': 'decision',
                '策略': 'strategy',
                '规则': 'rule',
                '算法': 'algorithm',
                '模型': 'model',
                '数据': 'data',
                '消息': 'message',
                '事件': 'event',
                '队列': 'queue',
                '栈': 'stack',
                '树': 'tree',
                '图': 'graph',
                '网络': 'network',
                '协议': 'protocol',
                '编码': 'encoding',
                '解码': 'decoding',
                '加密': 'encryption',
                '安全': 'security',
                '认证': 'authentication',
                '授权': 'authorization',
                '权限': 'permission',
                '用户界面': 'ui',
                '命令行': 'cli',
                '命令': 'command',
                '指令': 'instruction',
                '脚本': 'script',
                '文件': 'file',
                '目录': 'directory',
                '路径': 'path',
                '资源': 'resource',
                '内存': 'memory',
                '性能': 'performance',
                '效率': 'efficiency',
                '速度': 'speed',
                '时间': 'time',
                '定时': 'timer',
                '延迟': 'delay',
                '错误': 'error',
                '异常': 'exception',
                '故障': 'failure',
                '恢复': 'recovery',
                '备份': 'backup',
                '还原': 'restore',
                '版本': 'version',
                '更新': 'update',
                '升级': 'upgrade',
                '迁移': 'migration'
            }
            
            # 1. 从中文功能描述中提取关键词
            for chinese_word, english_keyword in functionality_keywords.items():
                if chinese_word in functionality_lower:
                    keywords.append(english_keyword)
            
            # 2. 检查已知英文模式
            for pattern in self.function_patterns.get(self.language, {}):
                if pattern in functionality_lower:
                    keywords.append(pattern)
            
            # 3. 特殊短语检测
            special_phrases = {
                '输入验证': 'input_validation',
                '数据验证': 'data_validation', 
                '状态管理': 'state_management',
                '任务管理': 'task_management',
                '工作流管理': 'workflow_management',
                '消息处理': 'message_processing',
                '数据处理': 'data_processing',
                '错误处理': 'error_handling',
                '异常处理': 'exception_handling',
                '性能监控': 'performance_monitoring',
                '系统监控': 'system_monitoring',
                '网络传输': 'network_transmission',
                '文件操作': 'file_operations',
                '数据库操作': 'database_operations',
                '缓存管理': 'cache_management',
                '配置管理': 'configuration_management',
                '日志记录': 'logging',
                '用户界面': 'user_interface',
                '命令行界面': 'cli_interface',
                'API接口': 'api_interface',
                '数据分析': 'data_analysis',
                '算法实现': 'algorithm_implementation',
                '模型训练': 'model_training',
                '结果展示': 'result_display',
                '报告生成': 'report_generation'
            }
            
            for phrase, keyword in special_phrases.items():
                if phrase in functionality_lower:
                    keywords.append(keyword)
            
            # 4. 去重并返回前2个最相关的关键词
            unique_keywords = list(dict.fromkeys(keywords))  # 保持顺序的去重
            return unique_keywords[:2]
            
        except Exception as e:
            self.logger.debug(f"Error extracting keywords from functionality: {e}")
            return []
    
    def _transform_filename_to_name(self, filename: str) -> str:
        """将文件名转换为友好名称"""
        # 分解文件名
        words = self._split_identifier(filename)
        
        # 映射到友好名称
        friendly_words = []
        for word in words[:2]:  # 最多使用前2个词
            if word.lower() in self.function_patterns.get(self.language, {}):
                friendly_word = self.function_patterns[self.language][word.lower()]
                friendly_words.append(friendly_word)
            else:
                friendly_words.append(word.title())
        
        if self.language == 'zh':
            return f"{''.join(friendly_words)}模块"
        else:
            return f"{' '.join(friendly_words)} Module"


# 使用示例
def test_community_namer():
    """测试社区命名器"""
    namer = CommunityNamer(language='zh', style='descriptive')
    
    # 测试数据
    test_community = {
        'size': 15,
        'nodes': [
            '/path/to/agent_processor.py:process_request',
            '/path/to/agent_handler.py:handle_message',
            '/path/to/agent_validator.py:validate_input'
        ],
        'elements': [
            {'type': 'function', 'name': 'process_request', 'file_path': '/path/to/agent_processor.py'},
            {'type': 'function', 'name': 'handle_message', 'file_path': '/path/to/agent_handler.py'},
            {'type': 'class', 'name': 'AgentValidator', 'file_path': '/path/to/agent_validator.py'}
        ]
    }
    
    test_ai_description = {
        'functionality': '这个社区主要负责智能体的请求处理和消息处理功能',
        'architecture_pattern': 'service_layer',
        'functional_tags': ['agent', 'processor'],
        'design_quality': 8
    }
    
    name = namer.generate_community_name(test_community, test_ai_description)
    print(f"Generated name: {name}")


if __name__ == "__main__":
    test_community_namer()