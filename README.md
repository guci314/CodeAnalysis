# CodeAnalysis

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Tests](https://img.shields.io/badge/Tests-32%20passed-brightgreen.svg)
![Coverage](https://img.shields.io/badge/Coverage-100%25-brightgreen.svg)

**智能Python代码结构分析平台**

*让代码结构可视化，让架构优化数据化*

[快速开始](#快速开始) • [功能特性](#功能特性) • [文档](#文档) • [示例](#示例)

</div>

---

## 🎯 项目简介

CodeAnalysis是一个专业的**Python代码静态分析工具**，结合传统图算法与现代AI技术，为开发者提供深度的代码理解和架构优化建议。

### 核心价值
- 📊 **量化分析**: 将代码结构转化为可量化的指标
- 🔍 **深度理解**: AI驱动的代码语义理解
- 🏗️ **架构优化**: 基于社区检测的重构建议
- 📈 **持续改进**: 支持CI/CD集成的质量监控

## ✨ 功能特性

### 🔍 智能代码分析
- **结构提取**: 自动识别类、函数、模块及其关系
- **复杂度评估**: 多维度代码质量和复杂度指标
- **依赖分析**: 深度分析代码间的调用和继承关系
- **AI语义理解**: DeepSeek驱动的代码功能和质量评估

### 🏘️ 社区检测算法
- **Leiden算法**: 高质量社区检测（推荐）
- **Louvain算法**: 快速模块度优化
- **Girvan-Newman**: 层次结构分析
- **Label Propagation**: 超快速处理

### 📊 可视化报告
- **HTML综合报告**: 专业级分析报告
- **交互式图表**: Plotly驱动的网络可视化
- **静态图像**: 社区结构和指标图表
- **多格式导出**: JSON、GraphML等格式支持

### 🛠️ 开发体验
- **命令行工具**: 完整的CLI界面
- **Python API**: 灵活的编程接口
- **智能缓存**: LangChain SQLite缓存显著提升重复分析性能
- **配置管理**: 环境变量和参数配置
- **错误处理**: 完善的异常处理和降级机制

## 🚀 快速开始

### 系统要求
- Python 3.8+
- 2GB+ RAM (推荐4GB+)
- 500MB 磁盘空间

### 安装步骤

```bash
# 1. 克隆项目
git clone <repository-url>
cd CodeAnalysis

# 2. 安装核心依赖
pip install -r requirements.txt

# 3. 安装可选依赖（推荐）
pip install leidenalg python-louvain plotly

# 4. 配置AI功能（可选）
cp .env.template .env
# 编辑 .env 文件，设置 DEEPSEEK_API_KEY
```

### 30秒体验

```bash
# 快速分析示例项目
python main.py analyze sample_project --detect-communities

# 生成完整报告
python main.py analyze sample_project --detect-communities --generate-report

# AI增强分析（需配置API key）
python main.py analyze sample_project --enable-deepseek --detect-communities
```

## 📖 使用示例

### 基本分析

```bash
# 分析项目结构
python main.py analyze /path/to/your/project

# 包含社区检测的完整分析
python main.py analyze /path/to/your/project --detect-communities --generate-report

# 使用特定算法进行社区检测
python main.py analyze /path/to/your/project --detect-communities --algorithm leiden
```

### 算法比较

```bash
# 比较所有社区检测算法
python main.py compare /path/to/your/project

# 比较特定算法
python main.py compare /path/to/your/project --algorithms leiden louvain

# 保存比较结果
python main.py compare /path/to/your/project --save-comparison
```

### 系统测试

```bash
# 测试DeepSeek API连接
python main.py test --test-deepseek

# 测试示例项目
python main.py test --test-sample

# 完整测试
python main.py test --test-deepseek --test-sample

# 缓存管理
python main.py cache info    # 查看缓存状态
python main.py cache clear   # 清空缓存
```

## 编程接口

### 基本使用

```python
from code_analysis import CodeAnalysis

# 初始化分析器
analyzer = CodeAnalysis("/path/to/your/project")

# 执行分析
results = analyzer.analyze_project()

# 获取摘要
summary = analyzer.get_summary()
print(f"发现 {summary['total_classes']} 个类，{summary['total_functions']} 个函数")

# 社区检测
communities = analyzer.detect_communities(algorithm='leiden')
print(f"检测到 {communities['num_communities']} 个社区")

# 生成报告
report_files = analyzer.generate_report()
print(f"报告已生成: {report_files}")
```

### 高级功能

```python
# 比较算法
comparison = analyzer.compare_community_algorithms(['leiden', 'louvain'])
best_algorithm = comparison['best_algorithm']

# 导出图
analyzer.export_graph('project_graph.graphml', 'graphml')

# 自定义社区分析
community_stats = analyzer.analyze_community_structure(communities['communities'])
```

## 配置选项

环境变量配置（.env文件）:

```bash
# DeepSeek API配置
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_MAX_TOKENS=8192
DEEPSEEK_TEMPERATURE=0

# 分析设置
MAX_FILE_SIZE=1000000
ANALYSIS_TIMEOUT=300

# 可视化设置
PLOT_DPI=300
PLOT_STYLE=seaborn
FIGURE_SIZE_WIDTH=12
FIGURE_SIZE_HEIGHT=8
```

## 输出文件

分析完成后，会在输出目录生成以下文件：

- `analysis_report_*.html` - 完整的HTML分析报告
- `analysis_results_*.json` - JSON格式的分析结果
- `communities_*.png` - 社区可视化图
- `community_metrics_*.png` - 社区指标图表
- `interactive_graph_*.html` - 交互式图表（如果安装了Plotly）

## 支持的算法

### 社区检测算法

1. **Leiden算法** (默认): 高质量的社区检测，适用于大规模网络
2. **Louvain算法**: 快速的模块度优化算法
3. **Girvan-Newman算法**: 基于边介数的层次聚类
4. **Label Propagation**: 标签传播算法，速度快

### 选择建议

- **大型项目**: 使用Leiden算法，质量最高
- **快速分析**: 使用Label Propagation算法
- **层次结构**: 使用Girvan-Newman算法
- **平衡选择**: 使用Louvain算法

## 测试

运行测试套件:

```bash
# 运行所有测试
python -m pytest test_code_analysis.py -v

# 运行特定测试类
python -m pytest test_code_analysis.py::TestCodeAnalysis -v

# 运行集成测试
python -m pytest test_code_analysis.py::TestIntegration -v
```

## 示例项目

项目包含一个示例项目（`sample_project/`），包含：

- 数据处理模块
- API服务模块  
- 配置管理模块
- 工具函数模块
- 数据模型模块

可以使用此示例项目测试功能：

```bash
python main.py analyze sample_project --detect-communities --generate-report
```

## 故障排除

### 常见问题

1. **DeepSeek API错误**
   - 检查API密钥是否正确设置
   - 验证网络连接
   - 查看API使用限制

2. **社区检测失败**
   - 检查是否安装了相关算法库（leidenalg, python-louvain）
   - 尝试使用label_propagation算法作为备选

3. **可视化问题**
   - 检查matplotlib配置
   - 尝试不同的图像后端

4. **内存不足**
   - 调整MAX_FILE_SIZE限制大文件
   - 使用--verbose查看详细错误信息

### 日志调试

```bash
# 启用详细日志
python main.py analyze /path/to/project --verbose --log-level DEBUG
```

## 性能优化

- **大型项目**: 设置合适的MAX_FILE_SIZE限制
- **并行处理**: 未来版本将支持多进程分析
- **缓存**: DeepSeek分析结果会被缓存

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

[MIT License](LICENSE)

## 📊 性能表现

| 项目规模 | 文件数 | 快速分析 | AI增强分析 | 内存使用 |
|----------|--------|----------|------------|----------|
| 小型项目 | <50 | <5秒 | <2分钟 | <100MB |
| 中型项目 | 50-500 | <30秒 | <10分钟 | <500MB |
| 大型项目 | 500+ | <2分钟 | 分批处理 | <2GB |

## 📚 文档

- 📖 **[用户手册](USER_MANUAL.md)** - 详细的使用指南和配置说明
- 🏗️ **[架构文档](ARCHITECTURE.md)** - 系统设计和技术架构
- 📋 **[项目总结](PROJECT_SUMMARY.md)** - 项目概览和技术特色
- 🧪 **[设计文档](代码分析.md)** - 原始设计文档和类设计

## 🧪 测试验证

```bash
# 运行完整测试套件
python -m pytest test_code_analysis.py -v

# 系统功能测试
python main.py test --test-sample --test-deepseek

# 性能基准测试
python main.py analyze sample_project --detect-communities
```

**测试结果**: ✅ 32个测试用例全部通过

## 🤝 贡献指南

我们欢迎各种形式的贡献！

### 贡献方式
- 🐛 **报告Bug**: 通过Issues报告问题
- 💡 **功能建议**: 提出新功能想法
- 📝 **文档改进**: 完善文档和示例
- 🔧 **代码贡献**: 提交Pull Request

### 开发环境
```bash
# 1. Fork项目并克隆
git clone <your-fork-url>
cd CodeAnalysis

# 2. 创建开发分支
git checkout -b feature/your-feature

# 3. 安装开发依赖
pip install -r requirements.txt
pip install -e .

# 4. 运行测试
python -m pytest test_code_analysis.py

# 5. 提交更改
git commit -m "feat: add your feature"
git push origin feature/your-feature
```

## 📄 许可证

本项目采用 **MIT许可证** - 详见 [LICENSE](LICENSE) 文件

## 🔗 相关链接

- 📧 **问题反馈**: [GitHub Issues]
- 💬 **讨论交流**: [GitHub Discussions]
- 📖 **在线文档**: [Project Wiki]
- 🎯 **发展路线**: [Roadmap]

## ⭐ 致谢

感谢以下开源项目的支持：
- [NetworkX](https://networkx.org/) - 图论算法库
- [DeepSeek](https://www.deepseek.com/) - AI语言模型
- [Plotly](https://plotly.com/) - 交互式可视化
- [Matplotlib](https://matplotlib.org/) - 静态图表

## 📈 项目统计

- 🌟 **Star数**: 欢迎Star支持
- 🍴 **Fork数**: 欢迎Fork使用
- 📊 **下载量**: 持续增长中
- 🎯 **活跃度**: 积极维护更新

---

<div align="center">

**如果这个项目对你有帮助，请给一个⭐️支持！**

*CodeAnalysis - 让代码结构可视化，让架构优化数据化*

</div>