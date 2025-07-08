#!/usr/bin/env python3
"""
Project Summary Generator using Serena MCP
利用Serena的AI能力生成项目智能总结
"""

import asyncio
import sys
from pathlib import Path
from serena_client import SerenaClient, SerenaClientContext, AnalysisResult
import json
import os

# Set proxy if needed
os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'

class ProjectSummarizer:
    """使用Serena进行项目分析和总结的类"""
    
    def __init__(self, client: SerenaClient):
        self.client = client
        self.project_info = {}
        self.analysis_results = {}
    
    async def collect_project_info(self, project_path: str) -> bool:
        """收集项目基本信息"""
        print("📊 收集项目基本信息...")
        
        # 激活项目
        result = await self.client.activate_project(project_path)
        if not result.success:
            print(f"❌ 项目激活失败: {result.error}")
            return False
        
        print("✅ 项目已激活")
        
        # 获取项目配置
        config_result = await self.client.get_current_config()
        if config_result.success:
            self.project_info['config'] = config_result.data
            print("✅ 获取项目配置")
        
        # 获取文件结构
        structure_result = await self.client.get_file_structure()
        if structure_result.success:
            self.project_info['structure'] = structure_result.data
            print("✅ 分析文件结构")
        
        # 获取代码符号概览
        symbols_result = await self.client.get_code_metrics()
        if symbols_result.success:
            self.project_info['symbols'] = symbols_result.data
            print("✅ 分析代码符号")
        
        return True
    
    async def analyze_project_patterns(self):
        """分析项目模式和架构"""
        print("\n🔍 分析项目模式和架构...")
        
        # Skip import analysis to avoid timeout - focus on key patterns only
        print("⏭️  跳过导入分析以避免超时")
        
        # 搜索主要模式 - 限制搜索范围提高性能
        patterns_to_search = [
            ("classes", "class "),
            ("functions", "def "),
            ("async_functions", "async def"),
            ("main_functions", "if __name__"),
            ("tests", "test_")
        ]
        
        pattern_results = {}
        for pattern_name, pattern in patterns_to_search:
            try:
                print(f"🔍 搜索 {pattern_name}...")
                result = await asyncio.wait_for(
                    self.client.search_code(pattern), 
                    timeout=30.0  # 30秒超时
                )
                if result.success:
                    pattern_results[pattern_name] = result.data
                    print(f"✅ 搜索 {pattern_name} 完成")
                else:
                    print(f"⚠️  搜索 {pattern_name} 失败: {result.message}")
            except asyncio.TimeoutError:
                print(f"⏰ 搜索 {pattern_name} 超时，跳过")
                continue
            except Exception as e:
                print(f"❌ 搜索 {pattern_name} 出错: {e}")
                continue
        
        self.analysis_results['patterns'] = pattern_results
    
    async def perform_intelligent_analysis(self):
        """使用Serena的AI功能进行智能分析"""
        print("\n🤖 进行AI智能分析...")
        
        # 将收集的信息存储到记忆中 - 仅存储可序列化的数据
        try:
            # 提取可序列化的基本信息
            serializable_summary = {
                "project_path": self.client.get_current_project(),
                "analysis_timestamp": asyncio.get_event_loop().time(),
                "files_analyzed": len(self.project_info.get('structure', {}).get('files', [])) if 'structure' in self.project_info else 0,
                "patterns_found": list(self.analysis_results.get('patterns', {}).keys()),
                "has_symbols": 'symbols' in self.analysis_results
            }
            
            memory_result = await asyncio.wait_for(
                self.client.write_memory(
                    "project_analysis", 
                    json.dumps(serializable_summary, indent=2)
                ),
                timeout=15.0
            )
            
            if memory_result.success:
                print("✅ 项目信息已存储到AI记忆")
        except asyncio.TimeoutError:
            print("⏰ 存储到记忆超时，跳过")
        except Exception as e:
            print(f"❌ 存储记忆失败: {e}")
        
        # 使用思考工具分析收集的信息 - 添加超时控制
        thinking_results = {}
        
        thinking_tasks = [
            ("completeness", "think_about_collected_information", "分析信息完整性"),
            ("task_adherence", "think_about_task_adherence", "评估任务执行"),
            ("completion_status", "think_about_whether_you_are_done", "评估完成状态")
        ]
        
        for key, method_name, description in thinking_tasks:
            try:
                print(f"🤔 {description}...")
                method = getattr(self.client, method_name)
                result = await asyncio.wait_for(method(), timeout=15.0)  # 减少超时时间
                if result.success:
                    # 仅存储简化的结果，避免复杂对象
                    thinking_results[key] = {"completed": True, "timestamp": asyncio.get_event_loop().time()}
                    print(f"✅ {description}")
                else:
                    print(f"⚠️  {description} 失败: {result.message}")
            except asyncio.TimeoutError:
                print(f"⏰ {description} 超时，跳过")
                continue
            except Exception as e:
                print(f"❌ {description} 出错: {e}")
                continue
        
        self.analysis_results['ai_thinking'] = thinking_results
    
    async def generate_summary(self) -> str:
        """生成项目总结"""
        print("\n📝 生成项目总结...")
        
        # 获取项目统计信息
        stats = self._calculate_project_stats()
        
        # 准备总结内容
        summary_parts = []
        
        # 项目基本信息
        summary_parts.append("# 🚀 项目分析总结")
        summary_parts.append("=" * 50)
        summary_parts.append("")
        
        # 项目概览
        summary_parts.append("## 📊 项目概览")
        summary_parts.append(f"- **项目路径**: {self.client.get_current_project()}")
        summary_parts.append(f"- **文件总数**: {stats.get('total_files', 0)}")
        summary_parts.append(f"- **Python文件**: {stats.get('python_files', 0)}")
        summary_parts.append(f"- **目录数量**: {stats.get('total_dirs', 0)}")
        summary_parts.append("")
        
        # 代码结构分析
        if 'symbols' in self.project_info:
            summary_parts.append("## 🏗️ 代码结构")
            symbols_info = self._analyze_symbols()
            for info in symbols_info:
                summary_parts.append(f"- {info}")
            summary_parts.append("")
        
        # 项目模式
        if 'patterns' in self.analysis_results:
            summary_parts.append("## 🔍 发现的模式")
            patterns_info = self._analyze_patterns()
            for info in patterns_info:
                summary_parts.append(f"- {info}")
            summary_parts.append("")
        
        # AI分析洞察
        if 'ai_thinking' in self.analysis_results:
            summary_parts.append("## 🤖 AI分析洞察")
            ai_insights = self._extract_ai_insights()
            for insight in ai_insights:
                summary_parts.append(f"- {insight}")
            summary_parts.append("")
        
        # 建议和下一步
        summary_parts.append("## 💡 建议和下一步")
        recommendations = self._generate_recommendations()
        for rec in recommendations:
            summary_parts.append(f"- {rec}")
        
        return "\n".join(summary_parts)
    
    def _calculate_project_stats(self) -> dict:
        """计算项目统计信息"""
        stats = {}
        
        if 'structure' in self.project_info:
            structure_data = self.project_info['structure']
            if isinstance(structure_data, dict) and 'structure' in structure_data:
                result = structure_data['structure']
                if hasattr(result, 'content') and result.content:
                    try:
                        content_text = result.content[0].text
                        import json
                        data = json.loads(content_text)
                        
                        stats['total_files'] = len(data.get('files', []))
                        stats['total_dirs'] = len(data.get('dirs', []))
                        
                        python_files = [f for f in data.get('files', []) if f.endswith('.py')]
                        stats['python_files'] = len(python_files)
                    except:
                        pass
        
        return stats
    
    def _analyze_symbols(self) -> list:
        """分析代码符号信息"""
        insights = []
        
        if 'symbols' in self.project_info:
            symbols_data = self.project_info['symbols']
            if isinstance(symbols_data, dict) and 'result' in symbols_data:
                try:
                    result = symbols_data['result']
                    if hasattr(result, 'content') and result.content:
                        content_text = result.content[0].text
                        import json
                        symbols = json.loads(content_text)
                        
                        total_classes = 0
                        total_functions = 0
                        files_with_classes = 0
                        
                        for file_path, file_symbols in symbols.items():
                            has_classes = False
                            for symbol in file_symbols:
                                if symbol.get('kind') == 5:  # Class
                                    total_classes += 1
                                    has_classes = True
                                elif symbol.get('kind') == 12:  # Function
                                    total_functions += 1
                            
                            if has_classes:
                                files_with_classes += 1
                        
                        insights.append(f"**总类数量**: {total_classes}")
                        insights.append(f"**总函数数量**: {total_functions}")
                        insights.append(f"**包含类的文件**: {files_with_classes}")
                        insights.append(f"**分析的文件数**: {len(symbols)}")
                        
                except Exception as e:
                    insights.append(f"符号分析出现问题: {str(e)}")
        
        return insights
    
    def _analyze_patterns(self) -> list:
        """分析代码模式"""
        patterns = []
        
        if 'patterns' in self.analysis_results:
            pattern_data = self.analysis_results['patterns']
            
            for pattern_name, pattern_result in pattern_data.items():
                if isinstance(pattern_result, dict) and 'result' in pattern_result:
                    try:
                        result = pattern_result['result']
                        if hasattr(result, 'content') and result.content:
                            content_text = result.content[0].text
                            
                            if pattern_name == "classes":
                                patterns.append(f"**类定义**: 发现代码中的类结构")
                            elif pattern_name == "functions":
                                patterns.append(f"**函数定义**: 发现代码中的函数结构")
                            elif pattern_name == "async_functions":
                                patterns.append(f"**异步函数**: 项目使用异步编程模式")
                            elif pattern_name == "tests":
                                patterns.append(f"**测试代码**: 项目包含测试代码")
                            elif pattern_name == "main_functions":
                                patterns.append(f"**主入口**: 发现可执行脚本入口")
                    except:
                        pass
        
        return patterns
    
    def _extract_ai_insights(self) -> list:
        """提取AI分析洞察"""
        insights = []
        
        if 'ai_thinking' in self.analysis_results:
            thinking_data = self.analysis_results['ai_thinking']
            
            # 提取完整性分析
            if 'completeness' in thinking_data:
                insights.append("**信息完整性**: AI已评估项目信息收集的完整性")
            
            # 提取任务执行分析
            if 'task_adherence' in thinking_data:
                insights.append("**任务执行**: AI已评估分析任务的执行情况")
            
            # 提取完成状态
            if 'completion_status' in thinking_data:
                insights.append("**完成状态**: AI已评估项目分析的完成程度")
            
            insights.append("**AI驱动**: 本次分析使用了Serena的AI思考能力")
        
        return insights
    
    def _generate_recommendations(self) -> list:
        """生成建议"""
        recommendations = [
            "继续使用Serena进行深度代码分析",
            "利用Serena的记忆系统存储分析结果",
            "使用符号搜索功能探索代码关系",
            "考虑使用Serena的代码编辑功能进行重构",
            "定期运行项目分析以跟踪变化"
        ]
        
        # 基于项目特点添加特定建议
        stats = self._calculate_project_stats()
        if stats.get('python_files', 0) > 20:
            recommendations.append("大型项目建议使用Serena的索引功能提升性能")
        
        if 'async_functions' in self.analysis_results.get('patterns', {}):
            recommendations.append("项目使用异步编程，建议关注异步代码的性能优化")
        
        return recommendations

async def main():
    """主函数"""
    print("🤖 Serena项目智能总结器")
    print("=" * 40)
    
    # 获取项目路径
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = str(Path.cwd())
    
    # 验证项目路径
    path = Path(project_path)
    if not path.exists():
        print(f"❌ 项目路径不存在: {project_path}")
        sys.exit(1)
    
    if not path.is_dir():
        print(f"❌ 项目路径不是目录: {project_path}")
        sys.exit(1)
    
    print(f"📂 分析项目: {path.absolute()}")
    
    try:
        # 使用Serena客户端
        async with SerenaClientContext(SerenaClient()) as client:
            if not client.is_connected():
                print("❌ 无法连接到Serena MCP服务器")
                print("💡 请确保Serena已正确安装")
                return
            
            print("✅ 已连接到Serena")
            
            # 创建项目总结器
            summarizer = ProjectSummarizer(client)
            
            # 执行分析流程
            print("\n🔄 开始分析流程...")
            
            # 收集项目信息
            if not await summarizer.collect_project_info(str(path.absolute())):
                print("❌ 项目信息收集失败")
                return
            
            # 分析项目模式
            await summarizer.analyze_project_patterns()
            
            # 执行AI智能分析 - 添加超时控制
            try:
                await asyncio.wait_for(
                    summarizer.perform_intelligent_analysis(), 
                    timeout=120.0  # 2分钟超时
                )
            except asyncio.TimeoutError:
                print("⏰ AI智能分析超时，继续生成基础总结")
            except Exception as e:
                print(f"❌ AI智能分析出错: {e}，继续生成基础总结")
            
            # 生成总结
            summary = await summarizer.generate_summary()
            
            # 显示总结
            print("\n" + "="*60)
            print(summary)
            print("="*60)
            
            # 保存总结到文件
            output_file = path / "PROJECT_SUMMARY.md"
            output_file.write_text(summary, encoding='utf-8')
            print(f"\n💾 总结已保存到: {output_file}")
            
            # 将总结存储到Serena记忆中 - 添加超时控制
            try:
                await asyncio.wait_for(
                    client.write_memory("final_project_summary", summary),
                    timeout=15.0
                )
                print("🧠 总结已存储到Serena记忆系统")
            except asyncio.TimeoutError:
                print("⏰ 存储到Serena记忆超时")
            except Exception as e:
                print(f"❌ 存储到Serena记忆失败: {e}")
            
            print("\n🎉 项目分析完成！")
            
    except KeyboardInterrupt:
        print("\n⏹️ 分析被用户中断")
    except Exception as e:
        print(f"❌ 分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())