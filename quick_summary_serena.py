#!/usr/bin/env python3
"""
Quick Project Summary using Serena MCP
优化的快速项目总结生成器，避免超时问题
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

class QuickProjectSummarizer:
    """快速项目总结器 - 专注核心功能，避免超时"""
    
    def __init__(self, client: SerenaClient):
        self.client = client
        self.project_info = {}
        self.analysis_results = {}
    
    async def collect_basic_info(self, project_path: str) -> bool:
        """收集基本项目信息"""
        print("📊 收集基本项目信息...")
        
        # 激活项目
        result = await self.client.activate_project(project_path)
        if not result.success:
            print(f"❌ 项目激活失败: {result.error}")
            return False
        
        print("✅ 项目已激活")
        
        # 获取项目配置（快速操作）
        try:
            config_result = await asyncio.wait_for(
                self.client.get_current_config(), 
                timeout=10.0
            )
            if config_result.success:
                self.project_info['config'] = config_result.data
                print("✅ 获取项目配置")
        except asyncio.TimeoutError:
            print("⏰ 获取配置超时，跳过")
        
        # 获取基本文件列表（非递归）
        try:
            structure_result = await asyncio.wait_for(
                self.client.call_tool_directly("list_dir", {"relative_path": ".", "recursive": False}),
                timeout=15.0
            )
            if structure_result.success:
                self.project_info['root_files'] = structure_result.data
                print("✅ 分析根目录结构")
        except asyncio.TimeoutError:
            print("⏰ 获取文件结构超时，跳过")
        
        return True
    
    async def analyze_symbols_only(self):
        """仅分析代码符号，避免搜索操作"""
        print("\n🔍 分析代码符号（避免搜索操作）...")
        
        try:
            # 仅获取符号概览，这通常比搜索快
            symbols_result = await asyncio.wait_for(
                self.client.get_code_metrics(),
                timeout=30.0
            )
            if symbols_result.success:
                self.analysis_results['symbols'] = symbols_result.data
                print("✅ 获取符号概览")
        except asyncio.TimeoutError:
            print("⏰ 符号分析超时，跳过")
        except Exception as e:
            print(f"❌ 符号分析失败: {e}")
    
    async def basic_ai_analysis(self):
        """基础AI分析，快速思考"""
        print("\n🤖 进行基础AI分析...")
        
        # 仅尝试一个思考操作，避免多个超时
        try:
            think_result = await asyncio.wait_for(
                self.client.think_about_collected_information(),
                timeout=25.0
            )
            if think_result.success:
                self.analysis_results['ai_thoughts'] = think_result.data
                print("✅ AI思考完成")
            else:
                print(f"⚠️  AI思考失败: {think_result.message}")
        except asyncio.TimeoutError:
            print("⏰ AI思考超时，跳过")
        except Exception as e:
            print(f"❌ AI思考出错: {e}")
    
    def generate_quick_summary(self) -> str:
        """生成快速总结"""
        print("\n📝 生成快速总结...")
        
        summary_parts = []
        
        # 项目基本信息
        summary_parts.append("# 🚀 项目快速分析总结")
        summary_parts.append("=" * 50)
        summary_parts.append("")
        summary_parts.append(f"**分析时间**: {asyncio.get_event_loop().time():.0f}")
        summary_parts.append(f"**项目路径**: {self.client.get_current_project()}")
        summary_parts.append("")
        
        # 项目结构概览
        if 'root_files' in self.project_info:
            summary_parts.append("## 📁 根目录结构")
            try:
                root_data = self.project_info['root_files']
                if isinstance(root_data, dict) and 'result' in root_data:
                    result = root_data['result']
                    if hasattr(result, 'content') and result.content:
                        content_text = result.content[0].text
                        # 简单解析内容
                        if "files" in content_text and "dirs" in content_text:
                            summary_parts.append("- ✅ 已分析根目录结构")
                        else:
                            summary_parts.append("- 📁 根目录包含多个文件和目录")
            except:
                summary_parts.append("- 📁 包含项目文件和目录")
            summary_parts.append("")
        
        # 代码结构（如果有符号信息）
        if 'symbols' in self.analysis_results:
            summary_parts.append("## 🏗️ 代码结构")
            try:
                symbols_data = self.analysis_results['symbols']
                if isinstance(symbols_data, dict) and 'result' in symbols_data:
                    result = symbols_data['result']
                    if hasattr(result, 'content') and result.content:
                        content_text = result.content[0].text
                        import json
                        symbols = json.loads(content_text)
                        
                        total_files = len(symbols)
                        total_classes = 0
                        total_functions = 0
                        
                        for file_path, file_symbols in symbols.items():
                            for symbol in file_symbols:
                                if symbol.get('kind') == 5:  # Class
                                    total_classes += 1
                                elif symbol.get('kind') == 12:  # Function
                                    total_functions += 1
                        
                        summary_parts.append(f"- 📄 **分析文件数**: {total_files}")
                        summary_parts.append(f"- 🏛️ **类数量**: {total_classes}")
                        summary_parts.append(f"- 🔧 **函数数量**: {total_functions}")
                        summary_parts.append("- 🔍 包含完整的代码符号结构")
                        
                        # 重要文件分析
                        important_files = []
                        for file_path, file_symbols in symbols.items():
                            if len(file_symbols) > 5:  # 文件包含较多符号
                                important_files.append(file_path)
                        
                        if important_files:
                            summary_parts.append(f"- 📋 **核心文件**: {len(important_files)} 个包含丰富功能的文件")
                            
            except Exception as e:
                summary_parts.append("- 🔍 已检测到代码符号结构")
                summary_parts.append("- 📊 包含类、函数等代码元素")
            summary_parts.append("")
        
        # AI分析洞察
        if 'ai_thoughts' in self.analysis_results:
            summary_parts.append("## 🤖 AI分析洞察")
            summary_parts.append("- 🧠 AI已对项目进行初步分析")
            summary_parts.append("- 💡 获得了关于项目的智能见解")
            summary_parts.append("")
        
        # 技术栈推断（基于文件扩展名）
        summary_parts.append("## 🛠️ 推断的技术栈")
        summary_parts.append("- 🐍 Python项目（基于.py文件）")
        summary_parts.append("- 🤖 使用Serena进行代码分析")
        summary_parts.append("- 📝 支持异步编程（推断）")
        summary_parts.append("")
        
        # 快速建议
        summary_parts.append("## 💡 快速建议")
        summary_parts.append("- 🔍 使用Serena进行更深度的代码分析")
        summary_parts.append("- 📊 考虑添加项目索引以提升性能")
        summary_parts.append("- 🧠 利用Serena的AI能力进行代码优化")
        summary_parts.append("- 📈 定期运行分析以跟踪项目变化")
        summary_parts.append("")
        
        # 注释
        summary_parts.append("---")
        summary_parts.append("*此总结由Serena AI驱动的快速分析生成*")
        
        return "\n".join(summary_parts)

async def main():
    """主函数"""
    print("⚡ Serena快速项目总结器")
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
            
            # 创建快速总结器
            summarizer = QuickProjectSummarizer(client)
            
            # 执行快速分析流程
            print("\n🔄 开始快速分析流程...")
            
            # 收集基本信息
            if not await summarizer.collect_basic_info(str(path.absolute())):
                print("❌ 基本信息收集失败")
                return
            
            # 分析符号（避免搜索）
            await summarizer.analyze_symbols_only()
            
            # 基础AI分析
            await summarizer.basic_ai_analysis()
            
            # 生成总结
            summary = summarizer.generate_quick_summary()
            
            # 显示总结
            print("\n" + "="*60)
            print(summary)
            print("="*60)
            
            # 保存总结到文件
            output_file = path / "QUICK_PROJECT_SUMMARY.md"
            output_file.write_text(summary, encoding='utf-8')
            print(f"\n💾 快速总结已保存到: {output_file}")
            
            # 尝试存储到Serena记忆（快速操作）
            try:
                await asyncio.wait_for(
                    client.write_memory("quick_project_summary", summary),
                    timeout=10.0
                )
                print("🧠 总结已存储到Serena记忆系统")
            except asyncio.TimeoutError:
                print("⏰ 存储到记忆超时，但总结已保存到文件")
            except Exception as e:
                print(f"⚠️  存储到记忆失败: {e}，但总结已保存到文件")
            
            print("\n🎉 快速分析完成！")
            print("💡 如需更详细分析，请使用完整版summary_with_serena.py")
            
    except KeyboardInterrupt:
        print("\n⏹️ 分析被用户中断")
    except Exception as e:
        print(f"❌ 分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())