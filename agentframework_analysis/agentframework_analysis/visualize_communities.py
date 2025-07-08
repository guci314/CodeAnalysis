#!/usr/bin/env python3
"""
Community Visualization Script
Create comprehensive visualizations for the community analysis data
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns
import numpy as np
import pandas as pd
from pathlib import Path
import networkx as nx
from collections import defaultdict, Counter
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8')
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_data():
    """Load all analysis data files"""
    data = {}
    
    # Load hierarchical communities
    with open('hierarchical_communities.json', 'r') as f:
        data['hierarchical'] = json.load(f)
    
    # Load core communities
    with open('core_communities.json', 'r') as f:
        data['core'] = json.load(f)
    
    # Load algorithm comparison
    with open('algorithm_comparison.json', 'r') as f:
        data['algorithms'] = json.load(f)
    
    # Load graph data
    with open('graph.json', 'r') as f:
        data['graph'] = json.load(f)
        
    return data

def create_hierarchy_chart(hierarchical_data):
    """Create hierarchy structure visualization"""
    resolutions = []
    num_communities = []
    modularity_scores = []
    
    for level_key, level_data in hierarchical_data.items():
        if level_key.startswith('resolution_'):
            resolutions.append(level_data['resolution'])
            num_communities.append(level_data['num_communities'])
            modularity_scores.append(level_data['modularity'])
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Communities vs Resolution
    ax1.plot(resolutions, num_communities, 'o-', color='#2E86AB', linewidth=2, markersize=8)
    ax1.set_xlabel('Resolution Parameter', fontsize=12)
    ax1.set_ylabel('Number of Communities', fontsize=12)
    ax1.set_title('Community Count vs Resolution', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Modularity vs Resolution
    ax2.plot(resolutions, modularity_scores, 'o-', color='#A23B72', linewidth=2, markersize=8)
    ax2.set_xlabel('Resolution Parameter', fontsize=12)
    ax2.set_ylabel('Modularity Score', fontsize=12)
    ax2.set_title('Modularity vs Resolution', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('hierarchy_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return fig

def create_community_size_chart(core_data):
    """Create community size distribution chart"""
    communities = list(core_data['core_communities'].values())
    sizes = [comm['size'] for comm in communities]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Size distribution histogram
    ax1.hist(sizes, bins=min(15, len(set(sizes))), color='#F18F01', alpha=0.7, edgecolor='black')
    ax1.set_xlabel('Community Size (Number of Files)', fontsize=12)
    ax1.set_ylabel('Frequency', fontsize=12)
    ax1.set_title('Community Size Distribution', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Top 10 largest communities
    top_communities = sorted(communities, key=lambda x: x['size'], reverse=True)[:10]
    names = [f"Community {i+1}" for i in range(len(top_communities))]
    sizes_top = [comm['size'] for comm in top_communities]
    
    bars = ax2.bar(names, sizes_top, color='#C73E1D', alpha=0.8)
    ax2.set_xlabel('Communities', fontsize=12)
    ax2.set_ylabel('Number of Files', fontsize=12)
    ax2.set_title('Top 10 Largest Communities', fontsize=14, fontweight='bold')
    ax2.tick_params(axis='x', rotation=45)
    
    # Add value labels on bars
    for bar, size in zip(bars, sizes_top):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{size}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('community_sizes.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return fig

def create_algorithm_comparison(algo_data):
    """Create algorithm comparison visualization"""
    algorithms = list(algo_data.keys())
    metrics = ['num_communities', 'modularity', 'execution_time']
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    
    for i, metric in enumerate(metrics):
        values = [algo_data[algo][metric] for algo in algorithms]
        
        bars = axes[i].bar(algorithms, values, color=colors[i], alpha=0.8)
        axes[i].set_title(f'{metric.replace("_", " ").title()}', fontsize=14, fontweight='bold')
        axes[i].tick_params(axis='x', rotation=45)
        
        # Add value labels
        for bar, value in zip(bars, values):
            height = bar.get_height()
            axes[i].text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{value:.3f}' if isinstance(value, float) else f'{value}',
                        ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('algorithm_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return fig

def create_cohesion_coupling_scatter(core_data):
    """Create cohesion vs coupling scatter plot"""
    communities = list(core_data['core_communities'].values())
    
    cohesion_scores = []
    coupling_scores = []
    sizes = []
    
    for comm in communities:
        cohesion_scores.append(comm['cohesion'])
        coupling_scores.append(comm['coupling'])
        sizes.append(comm['size'])
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create scatter plot with size-based bubbles
    scatter = ax.scatter(cohesion_scores, coupling_scores, s=[s*20 for s in sizes], 
                        c=sizes, cmap='viridis', alpha=0.6, edgecolors='black')
    
    ax.set_xlabel('Cohesion Score', fontsize=12)
    ax.set_ylabel('Coupling Score', fontsize=12)
    ax.set_title('Community Cohesion vs Coupling\n(Bubble size = Community size)', 
                fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Add colorbar
    cbar = plt.colorbar(scatter)
    cbar.set_label('Community Size', fontsize=12)
    
    # Add quadrant labels
    ax.axhline(y=np.median(coupling_scores), color='red', linestyle='--', alpha=0.5)
    ax.axvline(x=np.median(cohesion_scores), color='red', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig('cohesion_coupling.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return fig

def create_network_topology(graph_data, core_data):
    """Create simplified network topology visualization"""
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Create a simplified visualization showing community structure
    communities = list(core_data['core_communities'].values())
    
    # Create a circular layout for communities
    angles = np.linspace(0, 2*np.pi, len(communities), endpoint=False)
    
    colors = plt.cm.Set3(np.linspace(0, 1, len(communities)))
    
    for i, (comm, angle) in enumerate(zip(communities, angles)):
        # Position for this community
        center_x = 5 * np.cos(angle)
        center_y = 5 * np.sin(angle)
        
        # Draw community as a circle
        circle = plt.Circle((center_x, center_y), 
                          radius=min(2, comm['size']/10), 
                          color=colors[i], alpha=0.7)
        ax.add_patch(circle)
        
        # Add label
        ax.text(center_x, center_y, f"C{i+1}\n{comm['size']}", 
                ha='center', va='center', fontweight='bold', fontsize=10)
    
    ax.set_xlim(-8, 8)
    ax.set_ylim(-8, 8)
    ax.set_aspect('equal')
    ax.set_title('Community Structure Overview\n(Circle size = Community size)', 
                fontsize=16, fontweight='bold')
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig('network_topology.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return fig

def create_statistics_dashboard(data):
    """Create comprehensive statistics dashboard"""
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    axes = axes.flatten()
    
    # 1. Project Overview
    ax = axes[0]
    communities = list(data['core']['core_communities'].values())
    stats = [
        ('Total Files', len(data['graph']['nodes'])),
        ('Total Dependencies', len(data['graph']['links'])),
        ('Communities Found', len(communities)),
        ('Average Community Size', np.mean([c['size'] for c in communities]))
    ]
    
    y_pos = np.arange(len(stats))
    values = [stat[1] for stat in stats]
    bars = ax.barh(y_pos, values, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
    ax.set_yticks(y_pos)
    ax.set_yticklabels([stat[0] for stat in stats])
    ax.set_title('Project Overview', fontsize=14, fontweight='bold')
    
    for i, (bar, value) in enumerate(zip(bars, values)):
        ax.text(bar.get_width() + max(values)*0.01, bar.get_y() + bar.get_height()/2,
                f'{value:.1f}' if isinstance(value, float) else f'{value}',
                va='center', fontweight='bold')
    
    # 2. Community Size Distribution
    ax = axes[1]
    sizes = [comm['size'] for comm in communities]
    ax.hist(sizes, bins=10, color='#F18F01', alpha=0.7, edgecolor='black')
    ax.set_title('Community Size Distribution', fontsize=14, fontweight='bold')
    ax.set_xlabel('Size')
    ax.set_ylabel('Count')
    
    # 3. Modularity by Resolution
    ax = axes[2]
    resolutions = [level_data['resolution'] for level_key, level_data in data['hierarchical'].items() if level_key.startswith('resolution_')]
    modularities = [level_data['modularity'] for level_key, level_data in data['hierarchical'].items() if level_key.startswith('resolution_')]
    ax.plot(resolutions, modularities, 'o-', color='#A23B72', linewidth=2)
    ax.set_title('Modularity vs Resolution', fontsize=14, fontweight='bold')
    ax.set_xlabel('Resolution')
    ax.set_ylabel('Modularity')
    
    # 4. Algorithm Performance
    ax = axes[3]
    algos = list(data['algorithms'].keys())
    times = [data['algorithms'][algo]['execution_time'] for algo in algos]
    bars = ax.bar(algos, times, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
    ax.set_title('Algorithm Execution Time', fontsize=14, fontweight='bold')
    ax.set_ylabel('Time (seconds)')
    ax.tick_params(axis='x', rotation=45)
    
    # 5. Cohesion vs Coupling
    ax = axes[4]
    cohesion = [comm['cohesion'] for comm in communities]
    coupling = [comm['coupling'] for comm in communities]
    ax.scatter(cohesion, coupling, alpha=0.6, s=60, color='#96CEB4')
    ax.set_title('Cohesion vs Coupling', fontsize=14, fontweight='bold')
    ax.set_xlabel('Cohesion')
    ax.set_ylabel('Coupling')
    
    # 6. Top Communities
    ax = axes[5]
    top_comms = sorted(communities, key=lambda x: x['size'], reverse=True)[:8]
    names = [f"C{i+1}" for i in range(len(top_comms))]
    sizes = [comm['size'] for comm in top_comms]
    bars = ax.bar(names, sizes, color='#C73E1D', alpha=0.8)
    ax.set_title('Top 8 Communities by Size', fontsize=14, fontweight='bold')
    ax.set_ylabel('Files')
    
    plt.tight_layout()
    plt.savefig('statistics_dashboard.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return fig

def main():
    """Main visualization function"""
    print("🎨 Loading community analysis data...")
    data = load_data()
    
    print("📊 Creating visualizations...")
    
    # Create all visualizations
    create_hierarchy_chart(data['hierarchical'])
    print("✅ Hierarchy analysis chart created")
    
    create_community_size_chart(data['core'])
    print("✅ Community size distribution chart created")
    
    create_algorithm_comparison(data['algorithms'])
    print("✅ Algorithm comparison chart created")
    
    create_cohesion_coupling_scatter(data['core'])
    print("✅ Cohesion vs coupling scatter plot created")
    
    create_network_topology(data['graph'], data['core'])
    print("✅ Network topology visualization created")
    
    create_statistics_dashboard(data)
    print("✅ Statistics dashboard created")
    
    print("\n🎉 All visualizations completed!")
    print("Generated files:")
    print("- hierarchy_analysis.png")
    print("- community_sizes.png") 
    print("- algorithm_comparison.png")
    print("- cohesion_coupling.png")
    print("- network_topology.png")
    print("- statistics_dashboard.png")

if __name__ == "__main__":
    main()