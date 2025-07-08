#\!/usr/bin/env python3
"""
AgentFrameWork 社区分析数据访问脚本

使用方法:
    python analyze_data.py --help
    python analyze_data.py --summary
    python analyze_data.py --core-communities
    python analyze_data.py --hierarchy --resolution 0.01
"""

import json
import argparse
from pathlib import Path

class AnalysisDataReader:
    def __init__(self, data_dir='.'):
        self.data_dir = Path(data_dir)
        
    def load_json(self, filename):
        """加载JSON文件"""
        file_path = self.data_dir / filename
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def show_summary(self):
        """显示项目摘要"""
        summary = self.load_json('project_summary.json')
        index = self.load_json('index.json')
        
        print("🏗️ AgentFrameWork 项目摘要")
        print("=" * 50)
        print(f"📁 项目路径: {summary['project_path']}")
        print(f"⏰ 分析时间: {summary['analysis_time']}")
        print()
        
        print("📊 规模统计:")
        graph_info = summary['graph_info']
        print(f"  - 代码节点: {graph_info['nodes']:,}")
        print(f"  - 连接边数: {graph_info['edges']:,}")
        print(f"  - 连接密度: {graph_info['density']:.6f}")
        print(f"  - 平均度数: {graph_info['avg_degree']:.2f}")
        
    def show_core_communities(self):
        """显示核心社区"""
        core = self.load_json('core_communities.json')
        
        print("🎯 核心子系统分析")
        print("=" * 50)
        print(f"总核心社区数: {core['total_core_communities']}")
        print()
        
        communities = core['core_communities']
        for comm_id, details in sorted(communities.items(), 
                                     key=lambda x: x[1]['size'], reverse=True)[:10]:
            print(f"子系统 {comm_id}:")
            print(f"  - 规模: {details['size']} 个组件")
            print(f"  - 内聚度: {details['cohesion']:.3f}")
            print(f"  - 耦合度: {details['coupling']:.3f}")
            print(f"  - 示例节点: {', '.join(details['nodes'][:3])}...")
            print()
    
    def show_hierarchy(self, resolution=None):
        """显示层次结构"""
        hierarchy = self.load_json('hierarchical_communities.json')
        
        print("🌳 层次社区结构")
        print("=" * 50)
        
        if resolution:
            key = f'resolution_{resolution}'
            if key in hierarchy:
                data = hierarchy[key]
                print(f"分辨率 {resolution}:")
                print(f"  - 社区数: {data['num_communities']}")
                print(f"  - 模块度: {data['modularity']:.3f}")
                
                # 显示大型社区
                details = data['statistics']['community_details']
                large_communities = [(k, v) for k, v in details.items() if v['size'] > 5]
                if large_communities:
                    print(f"  - 大型社区 (>5个节点): {len(large_communities)} 个")
                    for comm_id, detail in sorted(large_communities, 
                                                 key=lambda x: x[1]['size'], reverse=True)[:5]:
                        print(f"    • 社区{comm_id}: {detail['size']}个节点")
            else:
                print(f"❌ 分辨率 {resolution} 的数据不存在")
        else:
            print("所有分辨率级别:")
            for key, data in hierarchy.items():
                res = data['resolution']
                print(f"  - 分辨率 {res:4.2f}: {data['num_communities']:4d} 个社区, 模块度 {data['modularity']:.3f}")
    
    def show_algorithms(self):
        """显示算法比较"""
        comparison = self.load_json('algorithm_comparison.json')
        
        print("⚡ 算法比较结果")
        print("=" * 50)
        
        for algo, result in comparison.items():
            if 'error' in result:
                print(f"{algo}: ❌ {result['error']}")
            else:
                print(f"{algo}:")
                print(f"  - 社区数: {result['num_communities']}")
                print(f"  - 模块度: {result['modularity']:.3f}")
                
def main():
    parser = argparse.ArgumentParser(description='AgentFrameWork 社区分析数据查看器')
    parser.add_argument('--summary', action='store_true', help='显示项目摘要')
    parser.add_argument('--core-communities', action='store_true', help='显示核心社区')
    parser.add_argument('--hierarchy', action='store_true', help='显示层次结构')
    parser.add_argument('--algorithms', action='store_true', help='显示算法比较')
    parser.add_argument('--resolution', type=float, help='指定分辨率级别')
    parser.add_argument('--data-dir', default='.', help='数据目录路径')
    
    args = parser.parse_args()
    
    reader = AnalysisDataReader(args.data_dir)
    
    if args.summary:
        reader.show_summary()
    elif args.core_communities:
        reader.show_core_communities()
    elif args.hierarchy:
        reader.show_hierarchy(args.resolution)
    elif args.algorithms:
        reader.show_algorithms()
    else:
        print("请指定要查看的内容，使用 --help 查看帮助")

if __name__ == '__main__':
    main()
