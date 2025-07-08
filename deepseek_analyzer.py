"""
DeepSeek Language Model Integration for Code Analysis
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_community.cache import SQLiteCache
from langchain_core.globals import set_llm_cache
from dotenv import load_dotenv


class DeepSeekAnalyzer:
    """
    DeepSeek language model integration for intelligent code analysis.
    """
    
    def __init__(self):
        """Initialize DeepSeek analyzer with configuration from environment."""
        load_dotenv()
        
        # Configuration
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.base_url = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        self.model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
        self.max_tokens = int(os.getenv('DEEPSEEK_MAX_TOKENS', '8192'))
        self.temperature = float(os.getenv('DEEPSEEK_TEMPERATURE', '0'))
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Validate configuration
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is required")
        
        # Setup LangChain caching
        cache_enabled = os.getenv('ENABLE_CACHE', 'true').lower() == 'true'
        if cache_enabled:
            cache_path = os.getenv('CACHE_DATABASE_PATH', '.langchain.db')
            set_llm_cache(SQLiteCache(database_path=cache_path))
            self.logger.info(f"LangChain cache enabled: {cache_path}")
        else:
            self.logger.info("LangChain cache disabled")
        
        # Initialize LLM client
        self.llm = ChatOpenAI(
            temperature=self.temperature,
            model=self.model,
            base_url=self.base_url,
            api_key=self.api_key,
            max_tokens=self.max_tokens
        )
        
        self.logger.info(f"DeepSeek analyzer initialized with model: {self.model}")
    
    def analyze_code_function(self, code: str) -> Dict[str, Any]:
        """
        Analyze code functionality using DeepSeek model.
        
        Args:
            code: Python code to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            prompt = f"""
            分析以下Python代码的功能和特征：
            
            ```python
            {code}
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
            
            response = self.llm.invoke(prompt)
            result = self._parse_analysis_response(response.content)
            
            self.logger.debug(f"Code analysis completed for {len(code)} characters")
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing code: {str(e)}")
            return self._get_default_analysis()
    
    def classify_code_similarity(self, code1: str, code2: str) -> float:
        """
        Calculate semantic similarity between two code snippets.
        
        Args:
            code1: First code snippet
            code2: Second code snippet
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        try:
            prompt = f"""
            比较以下两段代码的功能相似度，返回0-1之间的数值：
            
            代码1：
            ```python
            {code1}
            ```
            
            代码2：
            ```python
            {code2}
            ```
            
            请只返回一个数值，表示相似度（0表示完全不同，1表示完全相同）。
            考虑因素：功能目的、算法逻辑、数据结构使用、API调用等。
            """
            
            response = self.llm.invoke(prompt)
            similarity = self._parse_similarity_response(response.content)
            
            self.logger.debug(f"Similarity analysis completed: {similarity}")
            return similarity
            
        except Exception as e:
            self.logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0
    
    def generate_code_summary(self, code: str) -> str:
        """
        Generate a concise summary of code functionality.
        
        Args:
            code: Python code to summarize
            
        Returns:
            Human-readable summary string
        """
        try:
            prompt = f"""
            为以下Python代码生成一个简洁的功能摘要（不超过100字）：
            
            ```python
            {code}
            ```
            
            请用中文描述代码的主要功能和用途。
            """
            
            response = self.llm.invoke(prompt)
            summary = response.content.strip()
            
            self.logger.debug(f"Code summary generated: {len(summary)} characters")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating summary: {str(e)}")
            return "代码摘要生成失败"
    
    def suggest_refactoring(self, code: str) -> Dict[str, Any]:
        """
        Suggest code refactoring improvements.
        
        Args:
            code: Python code to analyze for refactoring
            
        Returns:
            Dictionary containing refactoring suggestions
        """
        try:
            prompt = f"""
            分析以下Python代码并提出重构建议：
            
            ```python
            {code}
            ```
            
            请以JSON格式返回重构建议：
            {{
                "issues": ["问题1", "问题2"],
                "suggestions": ["建议1", "建议2"],
                "improvements": ["改进1", "改进2"],
                "priority": "high|medium|low"
            }}
            """
            
            response = self.llm.invoke(prompt)
            result = self._parse_refactoring_response(response.content)
            
            self.logger.debug("Refactoring suggestions generated")
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating refactoring suggestions: {str(e)}")
            return self._get_default_refactoring()
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse analysis response from DeepSeek."""
        try:
            # Try to extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Fallback parsing
                return self._parse_text_response(response_text)
                
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse JSON response, using fallback")
            return self._parse_text_response(response_text)
    
    def _parse_text_response(self, text: str) -> Dict[str, Any]:
        """Fallback text parsing for analysis response."""
        return {
            "functionality": text[:200] + "..." if len(text) > 200 else text,
            "complexity": 5,
            "quality": 7,
            "suggestions": ["代码分析完成"],
            "tags": ["general"],
            "dependencies": []
        }
    
    def _parse_similarity_response(self, response_text: str) -> float:
        """Parse similarity score from response."""
        try:
            # Extract number from response
            import re
            numbers = re.findall(r'0?\.\d+|\d+\.?\d*', response_text)
            if numbers:
                score = float(numbers[0])
                return max(0.0, min(1.0, score))  # Clamp between 0 and 1
            return 0.0
        except (ValueError, IndexError):
            return 0.0
    
    def _parse_refactoring_response(self, response_text: str) -> Dict[str, Any]:
        """Parse refactoring suggestions from response."""
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return self._get_default_refactoring()
                
        except json.JSONDecodeError:
            return self._get_default_refactoring()
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """Get default analysis result when API fails."""
        return {
            "functionality": "代码分析暂不可用",
            "complexity": 5,
            "quality": 5,
            "suggestions": ["请检查DeepSeek API配置"],
            "tags": ["unknown"],
            "dependencies": []
        }
    
    def _get_default_refactoring(self) -> Dict[str, Any]:
        """Get default refactoring suggestions when API fails."""
        return {
            "issues": ["无法分析代码问题"],
            "suggestions": ["请检查DeepSeek API配置"],
            "improvements": ["API连接失败"],
            "priority": "medium"
        }
    
    def is_available(self) -> bool:
        """Check if DeepSeek API is available (configuration check only)."""
        return bool(self.api_key and self.llm)
    
    def clear_cache(self) -> bool:
        """
        Clear the LangChain cache database.
        
        Returns:
            True if cache was cleared successfully, False otherwise
        """
        try:
            cache_path = os.getenv('CACHE_DATABASE_PATH', '.langchain.db')
            if os.path.exists(cache_path):
                os.remove(cache_path)
                self.logger.info(f"Cache cleared: {cache_path}")
                return True
            else:
                self.logger.info("Cache database not found")
                return True
        except Exception as e:
            self.logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about the cache database.
        
        Returns:
            Dictionary containing cache information
        """
        cache_path = os.getenv('CACHE_DATABASE_PATH', '.langchain.db')
        cache_info = {
            'cache_enabled': os.getenv('ENABLE_CACHE', 'true').lower() == 'true',
            'cache_path': cache_path,
            'cache_exists': os.path.exists(cache_path),
            'cache_size': 0
        }
        
        if cache_info['cache_exists']:
            try:
                cache_info['cache_size'] = os.path.getsize(cache_path)
            except Exception:
                pass
        
        return cache_info