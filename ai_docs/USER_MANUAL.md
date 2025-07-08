# CodeAnalysis 用户使用手册

## 目录
- [快速开始](#快速开始)
- [安装与配置](#安装与配置)
- [基础功能](#基础功能)
- [高级功能](#高级功能)
- [命令行界面](#命令行界面)
- [编程接口](#编程接口)
- [配置选项](#配置选项)
- [故障排除](#故障排除)
- [最佳实践](#最佳实践)

## 快速开始

### 5分钟快速体验

```bash
# 1. 克隆项目
git clone <repository-url>
cd CodeAnalysis

# 2. 安装依赖
pip install -r requirements.txt

# 3. 快速分析示例项目
python main.py analyze sample_project --detect-communities

# 4. 生成完整报告
python main.py analyze sample_project --detect-communities --generate-report
```

### 核心概念

- **代码分析**: 提取Python项目中的类、函数、模块信息
- **知识图谱**: 基于代码关系构建的网络图
- **社区检测**: 识别代码中功能相关的模块组
- **AI增强**: 使用DeepSeek语言模型进行智能分析

## 安装与配置

### 系统要求

- Python 3.8+
- 操作系统: Linux, macOS, Windows
- 内存: 最少2GB，推荐4GB+
- 磁盘: 500MB可用空间

### 安装步骤

#### 1. 基础安装

```bash
# 安装核心依赖
pip install -r requirements.txt
```

#### 2. 可选依赖（推荐）

```bash
# 安装高级社区检测算法
pip install leidenalg python-louvain
```

#### 3. DeepSeek AI配置（可选）

创建`.env`文件：

```bash
cp .env.template .env
# 编辑.env文件，设置DEEPSEEK_API_KEY
```

`.env`文件示例：
```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_MAX_TOKENS=8192
DEEPSEEK_TEMPERATURE=0
```

### 验证安装

```bash
# 系统自检
python main.py test --test-sample

# 测试DeepSeek API（如果配置了）
python main.py test --test-deepseek
```

## 基础功能

### 1. 项目结构分析

#### 快速分析
```bash
# 基础结构分析
python main.py analyze /path/to/your/project
```

输出示例：
```
📊 CODE ANALYSIS SUMMARY
============================================================
📁 Project Path: /path/to/your/project
📄 Total Files: 15
🏗️  Total Classes: 25
⚙️  Total Functions: 120
🔗 Graph Nodes: 145
🔗 Graph Edges: 68
```

#### 详细信息
- **Files**: 扫描到的Python文件数量
- **Classes**: 提取的类定义数量
- **Functions**: 提取的函数定义数量
- **Graph Nodes**: 知识图谱中的节点数
- **Graph Edges**: 节点间的关系连接数

### 2. 社区检测

#### 基本社区检测
```bash
# 使用默认算法（Leiden）
python main.py analyze project_path --detect-communities
```

#### 选择特定算法
```bash
# Leiden算法（推荐，质量最高）
python main.py analyze project_path --detect-communities --algorithm leiden

# Louvain算法（速度快）
python main.py analyze project_path --detect-communities --algorithm louvain

# Label Propagation算法（最快）
python main.py analyze project_path --detect-communities --algorithm label_propagation

# Girvan-Newman算法（层次结构）
python main.py analyze project_path --detect-communities --algorithm girvan_newman
```

#### 社区检测结果解读
```
🏘️  COMMUNITY DETECTION RESULTS
============================================================
🔍 Algorithm: leiden
🏘️  Communities Found: 8
📈 Modularity Score: 0.745

📋 Community Details:
Community    Size   Cohesion   Coupling  
----------------------------------------
0            12     0.667      0.250     
1            8      0.750      0.125     
2            15     0.533      0.300     
```

- **Communities Found**: 检测到的社区数量
- **Modularity Score**: 模块度评分（0-1，越高越好）
- **Size**: 社区内节点数量
- **Cohesion**: 内聚度（社区内部连接密度）
- **Coupling**: 耦合度（与其他社区的连接密度）

### 3. 报告生成

#### 生成完整报告
```bash
python main.py analyze project_path \
  --detect-communities \
  --generate-report \
  --output-dir ./analysis_results
```

#### 生成的文件
- `analysis_output/analysis_report.md` - 自然语言分析报告（固定文件名）
- `analysis_output/analysis_results.json` - 结构化数据（固定文件名）

#### 输出目录管理
- 每次分析前自动清空 `analysis_output` 目录
- 确保始终获得最新的分析结果
- 避免旧文件累积和混淆

## 高级功能

### 1. AI增强分析

#### 启用DeepSeek AI
```bash
python main.py analyze project_path \
  --enable-deepseek \
  --detect-communities \
  --generate-report
```

#### AI分析结果
- **功能描述**: 每个社区的AI生成功能说明
- **有意义命名**: 自动生成的社区名称（如"智能体处理模块"）
- **架构模式**: 识别的设计模式
- **设计质量评分**: 1-10分的质量评分
- **重构建议**: AI生成的优化建议
- **功能标签**: 代码功能分类标签

#### 性能优化（重要改进）
- **并发处理**: 20个并发请求，显著提升分析速度
- **智能过滤**: 只分析大型社区（≥5成员），减少99.5%的API调用
- **执行时间**: 从16+小时优化到几分钟
- **缓存机制**: LangChain SQLite缓存避免重复分析

### 2. 智能社区命名（新功能）

#### 功能概述
CodeAnalysis 2.0 新增了智能社区命名功能，能够为代码社区生成有意义的名称，替代传统的数字编号（如"Community 25"）。**现在支持两种命名模式：DeepSeek API智能命名（推荐）和本地模式匹配命名。**

#### 启用智能命名
```bash
# 启用DeepSeek API智能命名的完整分析
python main.py analyze project_path \
  --enable-deepseek \
  --detect-communities \
  --generate-report
```

#### 命名模式

##### 🚀 模式一：DeepSeek API智能命名（推荐）
使用DeepSeek API结合并发技术为社区生成智能名称：

**特点：**
- **AI驱动**: 基于代码上下文理解生成语义化名称
- **并发处理**: 支持8-20个并发API请求，快速完成命名
- **智能过滤**: 只对有意义的社区（≥5成员）调用API，节省资源
- **高准确性**: 准确率>90%，名称更贴合代码实际功能

**配置：**
```env
USE_DEEPSEEK_NAMING=true                    # 启用DeepSeek命名
DEEPSEEK_MAX_CONCURRENT_REQUESTS=8          # 并发请求数
DEEPSEEK_REQUEST_DELAY=0.1                  # 请求间延迟
MIN_COMMUNITY_SIZE_FOR_AI=5                 # 最小命名社区大小
```

**性能优势：**
- 并发处理显著提升速度
- 只对有意义社区命名，避免资源浪费
- LangChain缓存机制避免重复调用

##### 🔧 模式二：本地模式匹配命名（备用）
基于预定义模式和关键词匹配生成名称：

**特点：**
- **离线运行**: 无需API调用，完全本地处理
- **快速响应**: 毫秒级命名速度
- **模式丰富**: 内置数百个功能关键词映射
- **自动降级**: DeepSeek API不可用时自动启用

#### 命名策略
系统使用分层策略生成有意义的名称：

**DeepSeek API模式：**
1. **上下文理解**: AI分析代码功能、文件结构、函数关系
2. **语义提取**: 提取核心功能概念和业务逻辑
3. **智能生成**: 生成2-6个字符的简洁中文名称
4. **质量保证**: 自动验证和优化生成结果

**本地模式匹配：**
1. **功能描述分析**: 从AI生成的功能描述中提取核心关键词
2. **功能标签组合**: 基于代码的实际功能标签生成名称
3. **文件路径分析**: 提取模块名称（如`agent`、`performance`、`message`）
4. **代码元素分析**: 基于类名和函数名的语义聚类
5. **架构模式**: 仅在缺乏功能信息时作为后备方案

#### 命名示例
```
传统命名 → DeepSeek API智能命名 → 本地模式匹配
Community 0  → "用户认证"              → "智能体验证处理模块"
Community 1  → "数据压缩"              → "消息压缩优化模块"  
Community 5  → "性能监控"              → "性能监控分析模块"
Community 12 → "工作流程"              → "工作流管理系统"
```

#### 配置选项
```env
# 命名模式选择
ENABLE_MEANINGFUL_COMMUNITY_NAMES=true  # 启用智能命名
USE_DEEPSEEK_NAMING=true                # 优先使用DeepSeek API（推荐）

# DeepSeek API 并发设置
DEEPSEEK_MAX_CONCURRENT_REQUESTS=8      # 并发请求数（推荐4-12）
DEEPSEEK_REQUEST_DELAY=0.1              # 请求间延迟（秒）
MIN_COMMUNITY_SIZE_FOR_AI=5             # AI命名最小社区大小

# 通用命名设置
COMMUNITY_NAME_LANGUAGE=zh              # 命名语言（zh/en/auto）
COMMUNITY_NAME_STYLE=descriptive        # 命名风格（descriptive/technical/simple）
```

#### 性能对比
| 特性 | DeepSeek API模式 | 本地模式匹配 |
|------|------------------|--------------|
| 准确性 | >90% | ~85% |
| 速度 | 2-5秒（并发） | <1秒 |
| 网络依赖 | 需要 | 无需 |
| 成本 | API调用费用 | 免费 |
| 语义理解 | 深度理解 | 模式匹配 |

#### 命名质量
- **语义准确**: DeepSeek AI深度理解代码上下文
- **简洁明了**: 2-6个字符，便于记忆和理解
- **功能导向**: 名称直接反映代码的实际功能
- **一致性**: 同类功能使用一致的命名风格
- **多语言**: 支持中英文命名

#### 报告中的展示
生成的报告将显示格式为：
```markdown
### 智能体验证模块 (Community 0)

**功能描述:** 
负责智能体的输入验证、状态分类和数据处理功能...

**架构模式:** service_layer
**设计质量评分:** 8/10
**重构建议:**
- 建议统一验证逻辑到ValidationService类
- 使用装饰器模式简化验证流程

**功能标签:** validation, agent, processing
**外部依赖:** logging, config, typing

**相关文件（模块）:**
- `AgentFrameWork/core/agent_base.py`
- `AgentFrameWork/enhancedAgent_v2.py`
- `AgentFrameWork/utils/validation.py`
```

#### 相关文件显示功能 (新增)
每个社区现在会显示其包含的所有相关文件和模块：

- **智能路径显示**: 自动简化文件路径，显示项目相对路径
- **去重处理**: 自动合并重复的文件路径
- **排序显示**: 按字母顺序显示文件列表
- **代码格式**: 使用代码块格式清晰展示文件路径

### 3. 算法比较

#### 比较所有算法
```bash
python main.py compare project_path
```

#### 比较特定算法
```bash
python main.py compare project_path \
  --algorithms leiden louvain label_propagation
```

#### 保存比较结果
```bash
python main.py compare project_path \
  --save-comparison \
  --output-dir ./comparison_results
```

### 3. 图导出

#### 导出知识图谱
```bash
python main.py analyze project_path \
  --export-graph \
  --graph-format graphml
```

支持的格式：
- `graphml` - GraphML格式（推荐，兼容性好）
- `gexf` - GEXF格式（Gephi可用）
- `json` - JSON格式（编程友好）
- `edgelist` - 边列表格式（简单格式）

## 实际项目分析示例

### AgentFramework项目分析
以下是分析大型实际项目的完整命令示例：

#### 基础分析（不使用AI）
```bash
python main.py analyze /home/guci/aiProjects/AgentFrameWork --detect-communities --generate-report --algorithm leiden --output-dir agentframework_complete_analysis
```

#### AI增强分析
```bash
python main.py analyze /home/guci/aiProjects/AgentFrameWork --detect-communities --generate-report --enable-deepseek --algorithm leiden --output-dir agentframework_complete_analysis
```

**分析结果**：
- 项目规模：225个Python文件，3217个代码元素
- 模块化度：0.957（优秀架构）
- 分析时间：约17秒（性能优化后）
- 生成报告：自然语言Markdown、JSON格式

## 缓存管理

### LangChain缓存机制
CodeAnalysis 使用 LangChain 的 SQLite 缓存来提高 AI 分析性能。相同的代码分析请求会被缓存，显著减少重复分析的时间。

### 缓存配置
```env
# 在.env文件中配置
ENABLE_CACHE=true                    # 启用/禁用缓存
CACHE_DATABASE_PATH=.langchain.db    # 缓存数据库路径
```

### 缓存管理命令
```bash
# 查看缓存信息
python main.py cache info

# 清空缓存
python main.py cache clear
```

### 缓存性能优势
- **首次分析**: 正常API调用时间（10-20秒/文件）
- **缓存命中**: 近乎即时响应（<1秒）
- **存储空间**: 缓存文件通常为几MB到几十MB

### 何时清空缓存
- 升级 DeepSeek 模型版本
- 更改分析提示词
- 缓存文件过大影响性能
- 需要获取最新的AI分析结果

## 命令行界面

### 主要命令

#### analyze - 分析命令
```bash
python main.py analyze PROJECT_PATH [OPTIONS]
```

选项：
- `--detect-communities` - 启用社区检测
- `--algorithm {leiden,louvain,girvan_newman,label_propagation}` - 选择算法
- `--resolution FLOAT` - 分辨率参数（默认1.0）
- `--generate-report` - 生成报告
- `--output-dir DIR` - 输出目录
- `--export-graph` - 导出图
- `--graph-format FORMAT` - 图格式
- `--enable-deepseek` - 启用AI分析

#### compare - 比较命令
```bash
python main.py compare PROJECT_PATH [OPTIONS]
```

选项：
- `--algorithms ALGO [ALGO ...]` - 指定算法
- `--save-comparison` - 保存比较结果
- `--output-dir DIR` - 输出目录

#### test - 测试命令
```bash
python main.py test [OPTIONS]
```

选项：
- `--test-deepseek` - 测试DeepSeek API
- `--test-sample` - 测试示例项目

#### cache - 缓存管理命令
```bash
python main.py cache {info,clear}
```

操作：
- `info` - 显示缓存信息
- `clear` - 清空缓存数据库

### 全局选项

- `--verbose, -v` - 详细输出
- `--log-level {DEBUG,INFO,WARNING,ERROR}` - 日志级别

### 使用示例

```bash
# 基础分析
python main.py analyze /home/user/my_project

# 完整分析流程
python main.py analyze /home/user/my_project \
  --detect-communities \
  --algorithm leiden \
  --generate-report \
  --output-dir ./results \
  --verbose

# AI增强的深度分析
python main.py analyze /home/user/my_project \
  --enable-deepseek \
  --detect-communities \
  --generate-report

# 算法性能比较
python main.py compare /home/user/my_project \
  --algorithms leiden louvain \
  --save-comparison

# 缓存管理
python main.py cache info    # 查看缓存信息
python main.py cache clear   # 清空缓存
```

## 编程接口

### 基础使用

```python
from code_analysis import CodeAnalysis

# 创建分析器实例
analyzer = CodeAnalysis("/path/to/project")

# 执行基础分析
results = analyzer.analyze_project()

# 获取分析摘要
summary = analyzer.get_summary()
print(f"发现 {summary['total_classes']} 个类")
print(f"发现 {summary['total_functions']} 个函数")
```

### 社区检测

```python
# 使用默认算法
communities = analyzer.detect_communities()

# 指定算法和参数
communities = analyzer.detect_communities(
    algorithm='leiden',
    resolution=1.2
)

# 分析社区结构
stats = analyzer.analyze_community_structure(communities['communities'])

# 比较多种算法
comparison = analyzer.compare_community_algorithms(['leiden', 'louvain'])
best_algorithm = comparison['best_algorithm']
```

### AI增强分析

```python
# 启用DeepSeek分析
analyzer = CodeAnalysis("/path/to/project", enable_deepseek=True)

# 执行AI增强分析
results = analyzer.analyze_project()

# 访问AI分析结果
for element_id, element in results['code_elements'].items():
    semantic_info = element.get('semantic_info', {})
    if semantic_info:
        print(f"功能: {semantic_info.get('functionality')}")
        print(f"复杂度: {semantic_info.get('complexity')}/10")
        print(f"质量: {semantic_info.get('quality')}/10")
```

### 报告生成

```python
# 生成完整报告
report_files = analyzer.generate_report(
    output_dir="./analysis_output",
    include_communities=True
)

# 访问生成的文件
html_report = report_files.get('html_report')
json_export = report_files.get('json_export')
visualization = report_files.get('community_visualization')
```

### 图操作

```python
# 导出图
analyzer.export_graph('project_graph.graphml', 'graphml')

# 直接访问NetworkX图
graph = analyzer.graph
print(f"节点数: {len(graph.nodes)}")
print(f"边数: {len(graph.edges)}")

# 自定义图分析
import networkx as nx
centrality = nx.betweenness_centrality(graph)
most_central = max(centrality, key=centrality.get)
print(f"最中心的节点: {most_central}")
```

## 配置选项

### 环境变量配置

在`.env`文件中配置：

```env
# DeepSeek API配置
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_MAX_TOKENS=8192
DEEPSEEK_TEMPERATURE=0

# 分析设置
MAX_FILE_SIZE=1000000  # 最大文件大小（字节）
ANALYSIS_TIMEOUT=300   # 分析超时时间（秒）

# 可视化设置已移除 - 仅生成文本报告

# 缓存设置
ENABLE_CACHE=true
CACHE_TTL=3600  # 缓存生存时间（秒）

# AI分析并发设置（性能优化）
DEEPSEEK_MAX_CONCURRENT_REQUESTS=20  # 最大并发请求数（推荐：4-20）
DEEPSEEK_REQUEST_DELAY=0.1          # 请求间延迟（秒）
MIN_COMMUNITY_SIZE_FOR_AI=5         # AI分析的最小社区大小（推荐：2-5）

# 社区命名设置（新功能）
ENABLE_MEANINGFUL_COMMUNITY_NAMES=true  # 启用有意义的社区名称
COMMUNITY_NAME_LANGUAGE=zh              # 命名语言（zh/en/auto）
COMMUNITY_NAME_STYLE=descriptive        # 命名风格（descriptive/technical/simple）

# 日志设置
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### 性能调优

#### 大型项目优化
```env
# 限制文件大小，跳过超大文件
MAX_FILE_SIZE=500000

# 调整分析超时
ANALYSIS_TIMEOUT=600

# 启用缓存
ENABLE_CACHE=true
CACHE_TTL=7200
```

## 故障排除

### 常见问题

#### 1. 安装问题

**错误**: `ModuleNotFoundError: No module named 'leidenalg'`
```bash
# 解决方案：安装可选依赖
pip install leidenalg python-louvain plotly
```

**错误**: `ImportError: No module named 'community'`
```bash
# 解决方案：安装python-louvain
pip install python-louvain
```

#### 2. DeepSeek API问题

**错误**: `ValueError: DEEPSEEK_API_KEY environment variable is required`
```bash
# 解决方案：配置API密钥
echo "DEEPSEEK_API_KEY=your_key_here" >> .env
```

**错误**: API连接超时
```bash
# 解决方案：检查网络连接和API密钥
python main.py test --test-deepseek
```

#### 3. 内存问题

**错误**: `MemoryError` 或进程被杀死
```bash
# 解决方案：限制文件大小
export MAX_FILE_SIZE=200000
python main.py analyze project_path
```

#### 4. 报告生成问题

**错误**: 报告生成失败
```bash
# 解决方案：检查输出目录权限
chmod 755 analysis_output
python main.py analyze project_path --generate-report
```

### 调试技巧

#### 启用详细日志
```bash
python main.py analyze project_path --verbose --log-level DEBUG
```

#### 检查配置
```python
from code_analysis import CodeAnalysis
from deepseek_analyzer import DeepSeekAnalyzer

# 检查DeepSeek配置
try:
    analyzer = DeepSeekAnalyzer()
    print(f"API Key: {analyzer.api_key[:8]}...")
    print(f"Available: {analyzer.is_available()}")
except Exception as e:
    print(f"DeepSeek配置错误: {e}")
```

#### 测试小项目
```bash
# 使用示例项目测试
python main.py analyze sample_project --detect-communities
```

### 性能监控

#### 内存使用监控
```python
import psutil
import os

def monitor_memory():
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"内存使用: {memory_mb:.1f} MB")

# 在分析过程中调用
analyzer = CodeAnalysis("large_project")
monitor_memory()
results = analyzer.analyze_project()
monitor_memory()
```

#### 分析时间统计
```python
import time

start_time = time.time()
analyzer = CodeAnalysis("project_path")
results = analyzer.analyze_project()
analysis_time = time.time() - start_time

print(f"分析时间: {analysis_time:.2f} 秒")
print(f"每文件平均: {analysis_time / results['total_files']:.2f} 秒")
```

## 最佳实践

### 1. 项目分析流程

#### 日常快速分析
```bash
# 快速结构检查（适合CI/CD）
python main.py analyze project_path --detect-communities
```

#### 深度代码审查
```bash
# 完整AI增强分析（适合代码评审）
python main.py analyze project_path \
  --enable-deepseek \
  --detect-communities \
  --generate-report
```

#### 架构重构指导
```bash
# 算法比较分析（选择最佳社区划分）
python main.py compare project_path --save-comparison
```

### 2. 团队协作

#### 共享配置
```bash
# 团队共享配置模板
cp .env.template .env.team
# 团队成员复制并配置自己的API密钥
cp .env.team .env
```

#### 标准化报告
```bash
# 使用固定参数生成一致的报告
python main.py analyze project_path \
  --detect-communities \
  --algorithm leiden \
  --resolution 1.0 \
  --generate-report \
  --output-dir "./reports/$(date +%Y%m%d)"
```

### 3. 持续集成

#### GitLab CI示例
```yaml
code_analysis:
  stage: analysis
  script:
    - pip install -r requirements.txt
    - python main.py analyze . --detect-communities --generate-report
    - python main.py compare . --save-comparison
  artifacts:
    paths:
      - analysis_output/
    expire_in: 1 week
```

#### GitHub Actions示例
```yaml
- name: Code Analysis
  run: |
    pip install -r requirements.txt
    python main.py analyze . \
      --detect-communities \
      --generate-report \
      --output-dir ./analysis
    
- name: Upload Analysis Results
  uses: actions/upload-artifact@v3
  with:
    name: analysis-results
    path: ./analysis/
```

### 4. 大型项目处理

#### 分批处理
```python
import os
from pathlib import Path

def analyze_large_project(project_path, batch_size=10):
    """分批分析大型项目"""
    project = Path(project_path)
    subdirs = [d for d in project.iterdir() if d.is_dir()]
    
    results = []
    for i in range(0, len(subdirs), batch_size):
        batch = subdirs[i:i+batch_size]
        for subdir in batch:
            try:
                analyzer = CodeAnalysis(str(subdir))
                result = analyzer.analyze_project()
                results.append(result)
            except Exception as e:
                print(f"分析失败: {subdir} - {e}")
    
    return results
```

#### 增量分析
```python
def incremental_analysis(project_path, last_analysis_time):
    """增量分析，只分析修改过的文件"""
    import git
    
    repo = git.Repo(project_path)
    
    # 获取自上次分析以来修改的文件
    changed_files = []
    for item in repo.index.diff(None):
        if item.a_path.endswith('.py'):
            changed_files.append(item.a_path)
    
    # 只分析修改的文件
    if changed_files:
        analyzer = CodeAnalysis(project_path)
        # 自定义分析逻辑...
```

### 5. 质量阈值

#### 设置质量标准
```python
def check_quality_standards(analysis_results):
    """检查代码质量标准"""
    standards = {
        'max_communities': 20,  # 最大社区数
        'min_modularity': 0.3,  # 最小模块度
        'max_coupling': 0.7,    # 最大耦合度
        'min_cohesion': 0.3     # 最小内聚度
    }
    
    # 检查逻辑...
    issues = []
    
    if len(analysis_results.get('communities', {})) > standards['max_communities']:
        issues.append("社区数量过多，考虑重构")
    
    return issues
```

### 6. 自动化建议

#### 生成重构建议
```python
def generate_refactoring_suggestions(communities_result):
    """基于社区检测结果生成重构建议"""
    suggestions = []
    
    for community_id, details in communities_result['statistics']['community_details'].items():
        if details['size'] > 20:
            suggestions.append(f"社区{community_id}过大，建议拆分为子模块")
        
        if details['coupling'] > 0.7:
            suggestions.append(f"社区{community_id}耦合度过高，建议解耦")
        
        if details['cohesion'] < 0.3:
            suggestions.append(f"社区{community_id}内聚度过低，建议重组")
    
    return suggestions
```

---

## 技术支持

### 联系方式
- 项目仓库: [GitHub Repository]
- 问题反馈: [Issues页面]
- 文档更新: [Wiki页面]

### 社区
- 讨论区: [Discussions]
- 贡献指南: [CONTRIBUTING.md]
- 更新日志: [CHANGELOG.md]

---

*本手册持续更新，最新版本请查看项目仓库*