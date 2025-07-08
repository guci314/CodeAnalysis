"""
Community Detection Module for Code Analysis
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import networkx as nx
from networkx.algorithms import community as nx_community
import numpy as np

# Import community detection algorithms
try:
    import leidenalg
    import igraph as ig
    LEIDEN_AVAILABLE = True
except ImportError:
    LEIDEN_AVAILABLE = False
    logging.warning("leidenalg not available, Leiden algorithm will be disabled")

try:
    import community as community_louvain
    LOUVAIN_AVAILABLE = True
except ImportError:
    LOUVAIN_AVAILABLE = False
    logging.warning("python-louvain not available, Louvain algorithm will be disabled")


class CommunityDetector:
    """
    Community detection algorithms for analyzing code structure.
    """
    
    def __init__(self, graph: nx.Graph):
        """
        Initialize community detector with a NetworkX graph.
        
        Args:
            graph: NetworkX graph representing code structure
        """
        self.graph = graph
        self.logger = logging.getLogger(__name__)
        
        # Validate graph
        if not isinstance(graph, nx.Graph):
            raise ValueError("Graph must be a NetworkX Graph instance")
        
        if len(graph.nodes) == 0:
            raise ValueError("Graph cannot be empty")
        
        self.logger.info(f"Community detector initialized with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
    
    def detect_communities(self, algorithm: str = 'leiden', **kwargs) -> Dict[str, Any]:
        """
        Detect communities in the code graph using specified algorithm.
        
        Args:
            algorithm: Algorithm to use ('leiden', 'louvain', 'girvan_newman', 'label_propagation')
            **kwargs: Additional parameters for the algorithm
            
        Returns:
            Dictionary containing community detection results
        """
        self.logger.info(f"Detecting communities using {algorithm} algorithm")
        
        if algorithm == 'leiden':
            return self._detect_leiden(**kwargs)
        elif algorithm == 'louvain':
            return self._detect_louvain(**kwargs)
        elif algorithm == 'girvan_newman':
            return self._detect_girvan_newman(**kwargs)
        elif algorithm == 'label_propagation':
            return self._detect_label_propagation(**kwargs)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
    
    def _detect_leiden(self, resolution: float = 1.0, **kwargs) -> Dict[str, Any]:
        """
        Detect communities using Leiden algorithm.
        
        Args:
            resolution: Resolution parameter for community detection
            
        Returns:
            Dictionary containing community results
        """
        if not LEIDEN_AVAILABLE:
            self.logger.warning("Leiden algorithm not available, falling back to Louvain")
            return self._detect_louvain(resolution=resolution, **kwargs)
        
        try:
            # Convert NetworkX graph to igraph
            g = ig.Graph.from_networkx(self.graph)
            
            # Apply Leiden algorithm
            if resolution != 1.0:
                # Use CPMVertexPartition for custom resolution
                partition = leidenalg.find_partition(g, leidenalg.CPMVertexPartition, 
                                                   resolution_parameter=resolution)
            else:
                # Use ModularityVertexPartition for default resolution
                partition = leidenalg.find_partition(g, leidenalg.ModularityVertexPartition)
            
            # Convert back to NetworkX node format
            communities = {}
            for i, community_id in enumerate(partition.membership):
                node_name = list(self.graph.nodes())[i]
                communities[node_name] = community_id
            
            # Calculate modularity
            modularity = partition.modularity
            
            # Analyze community structure
            community_stats = self._analyze_community_structure(communities)
            
            return {
                'algorithm': 'leiden',
                'communities': communities,
                'modularity': modularity,
                'num_communities': len(set(communities.values())),
                'statistics': community_stats,
                'parameters': {'resolution': resolution}
            }
            
        except Exception as e:
            self.logger.error(f"Leiden algorithm failed: {e}")
            return self._detect_louvain(resolution=resolution, **kwargs)
    
    def _detect_louvain(self, resolution: float = 1.0, **kwargs) -> Dict[str, Any]:
        """
        Detect communities using Louvain algorithm.
        
        Args:
            resolution: Resolution parameter for community detection
            
        Returns:
            Dictionary containing community results
        """
        if not LOUVAIN_AVAILABLE:
            self.logger.warning("Louvain algorithm not available, falling back to label propagation")
            return self._detect_label_propagation(**kwargs)
        
        try:
            # Apply Louvain algorithm
            communities = community_louvain.best_partition(self.graph, resolution=resolution)
            
            # Calculate modularity
            modularity = community_louvain.modularity(communities, self.graph)
            
            # Analyze community structure
            community_stats = self._analyze_community_structure(communities)
            
            return {
                'algorithm': 'louvain',
                'communities': communities,
                'modularity': modularity,
                'num_communities': len(set(communities.values())),
                'statistics': community_stats,
                'parameters': {'resolution': resolution}
            }
            
        except Exception as e:
            self.logger.error(f"Louvain algorithm failed: {e}")
            return self._detect_label_propagation(**kwargs)
    
    def _detect_girvan_newman(self, k: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        """
        Detect communities using Girvan-Newman algorithm.
        
        Args:
            k: Number of communities to find (optional)
            
        Returns:
            Dictionary containing community results
        """
        try:
            # Apply Girvan-Newman algorithm
            communities_generator = nx_community.girvan_newman(self.graph)
            
            if k is None:
                # Find optimal number of communities by modularity
                best_communities = None
                best_modularity = -1
                
                for communities in communities_generator:
                    if len(communities) > len(self.graph.nodes) // 2:
                        break
                    
                    # Convert to node-community mapping
                    node_communities = {}
                    for i, community in enumerate(communities):
                        for node in community:
                            node_communities[node] = i
                    
                    modularity = nx_community.modularity(self.graph, communities)
                    
                    if modularity > best_modularity:
                        best_modularity = modularity
                        best_communities = node_communities
                
                communities = best_communities or {}
                modularity = best_modularity
            else:
                # Get specific number of communities
                communities_list = None
                for i, communities_list in enumerate(communities_generator):
                    if len(communities_list) == k:
                        break
                
                if communities_list:
                    communities = {}
                    for i, community in enumerate(communities_list):
                        for node in community:
                            communities[node] = i
                    
                    modularity = nx_community.modularity(self.graph, communities_list)
                else:
                    communities = {}
                    modularity = 0.0
            
            # Analyze community structure
            community_stats = self._analyze_community_structure(communities)
            
            return {
                'algorithm': 'girvan_newman',
                'communities': communities,
                'modularity': modularity,
                'num_communities': len(set(communities.values())) if communities else 0,
                'statistics': community_stats,
                'parameters': {'k': k}
            }
            
        except Exception as e:
            self.logger.error(f"Girvan-Newman algorithm failed: {e}")
            return self._get_default_communities()
    
    def _detect_label_propagation(self, **kwargs) -> Dict[str, Any]:
        """
        Detect communities using Label Propagation algorithm.
        
        Returns:
            Dictionary containing community results
        """
        try:
            # Apply Label Propagation algorithm
            communities_generator = nx_community.label_propagation_communities(self.graph)
            communities_list = list(communities_generator)
            
            # Convert to node-community mapping
            communities = {}
            for i, community in enumerate(communities_list):
                for node in community:
                    communities[node] = i
            
            # Calculate modularity
            modularity = nx_community.modularity(self.graph, communities_list)
            
            # Analyze community structure
            community_stats = self._analyze_community_structure(communities)
            
            return {
                'algorithm': 'label_propagation',
                'communities': communities,
                'modularity': modularity,
                'num_communities': len(communities_list),
                'statistics': community_stats,
                'parameters': {}
            }
            
        except Exception as e:
            self.logger.error(f"Label Propagation algorithm failed: {e}")
            return self._get_default_communities()
    
    def _analyze_community_structure(self, communities: Dict[str, int]) -> Dict[str, Any]:
        """
        Analyze the structure of detected communities.
        
        Args:
            communities: Dictionary mapping nodes to community IDs
            
        Returns:
            Dictionary containing community analysis
        """
        if not communities:
            return {
                'num_communities': 0,
                'community_sizes': [],
                'avg_community_size': 0,
                'largest_community': 0,
                'smallest_community': 0,
                'community_cohesion': {},
                'community_coupling': {},
                'community_details': {}
            }
        
        # Group nodes by community
        community_nodes = {}
        for node, community_id in communities.items():
            if community_id not in community_nodes:
                community_nodes[community_id] = []
            community_nodes[community_id].append(node)
        
        # Calculate community sizes
        community_sizes = [len(nodes) for nodes in community_nodes.values()]
        
        # Calculate cohesion and coupling for each community
        community_cohesion = {}
        community_coupling = {}
        community_details = {}
        
        for community_id, nodes in community_nodes.items():
            # Cohesion: internal edges / possible internal edges
            internal_edges = 0
            possible_internal_edges = len(nodes) * (len(nodes) - 1) // 2
            
            for node1 in nodes:
                for node2 in nodes:
                    if node1 != node2 and self.graph.has_edge(node1, node2):
                        internal_edges += 1
            
            internal_edges //= 2  # Each edge counted twice
            
            cohesion = internal_edges / possible_internal_edges if possible_internal_edges > 0 else 0
            community_cohesion[community_id] = cohesion
            
            # Coupling: external edges / total edges for community
            external_edges = 0
            total_edges = 0
            
            for node in nodes:
                node_edges = len(self.graph.edges(node))
                total_edges += node_edges
                
                for neighbor in self.graph.neighbors(node):
                    if neighbor not in nodes:
                        external_edges += 1
            
            coupling = external_edges / total_edges if total_edges > 0 else 0
            community_coupling[community_id] = coupling
            
            # Community details
            community_details[community_id] = {
                'size': len(nodes),
                'nodes': nodes,
                'cohesion': cohesion,
                'coupling': coupling,
                'internal_edges': internal_edges,
                'external_edges': external_edges,
                'total_edges': total_edges
            }
        
        return {
            'num_communities': len(community_nodes),
            'community_sizes': community_sizes,
            'avg_community_size': np.mean(community_sizes) if community_sizes else 0,
            'largest_community': max(community_sizes) if community_sizes else 0,
            'smallest_community': min(community_sizes) if community_sizes else 0,
            'community_cohesion': community_cohesion,
            'community_coupling': community_coupling,
            'community_details': community_details
        }
    
    def get_community_recommendations(self, communities: Dict[str, int], 
                                    statistics: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on community analysis.
        
        Args:
            communities: Dictionary mapping nodes to community IDs
            statistics: Community analysis statistics
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Check for overly large communities
        if statistics['largest_community'] > 20:
            recommendations.append(
                f"最大社区包含{statistics['largest_community']}个节点，考虑进一步拆分"
            )
        
        # Check for overly small communities
        num_communities = statistics.get('num_communities', len(set(communities.values())))
        if statistics['smallest_community'] < 3 and num_communities > 1:
            recommendations.append(
                f"存在只有{statistics['smallest_community']}个节点的小社区，可能需要合并"
            )
        
        # Check cohesion and coupling
        community_details = statistics.get('community_details', {})
        
        for community_id, details in community_details.items():
            if details['cohesion'] < 0.3:
                recommendations.append(
                    f"社区{community_id}内聚度较低({details['cohesion']:.2f})，建议重构以提高模块化"
                )
            
            if details['coupling'] > 0.7:
                recommendations.append(
                    f"社区{community_id}耦合度较高({details['coupling']:.2f})，建议解耦以降低依赖"
                )
        
        # Check overall modularity
        # This would be passed from the main detection result
        
        return recommendations
    
    def _get_default_communities(self) -> Dict[str, Any]:
        """
        Get default community structure when algorithms fail.
        
        Returns:
            Default community results
        """
        # Put each node in its own community
        communities = {node: i for i, node in enumerate(self.graph.nodes())}
        
        return {
            'algorithm': 'default',
            'communities': communities,
            'modularity': 0.0,
            'num_communities': len(communities),
            'statistics': self._analyze_community_structure(communities),
            'parameters': {}
        }
    
    def compare_algorithms(self, algorithms: List[str] = None) -> Dict[str, Any]:
        """
        Compare multiple community detection algorithms.
        
        Args:
            algorithms: List of algorithm names to compare
            
        Returns:
            Dictionary containing comparison results
        """
        if algorithms is None:
            algorithms = ['leiden', 'louvain', 'girvan_newman', 'label_propagation']
        
        results = {}
        
        for algorithm in algorithms:
            try:
                result = self.detect_communities(algorithm)
                results[algorithm] = result
            except Exception as e:
                self.logger.error(f"Algorithm {algorithm} failed: {e}")
                results[algorithm] = {'error': str(e)}
        
        # Find best algorithm by modularity
        best_algorithm = None
        best_modularity = -1
        
        for algorithm, result in results.items():
            if 'modularity' in result:
                if result['modularity'] > best_modularity:
                    best_modularity = result['modularity']
                    best_algorithm = algorithm
        
        return {
            'results': results,
            'best_algorithm': best_algorithm,
            'best_modularity': best_modularity
        }