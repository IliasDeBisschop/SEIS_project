import numpy as np
import markov_clustering as mc
import networkx as nx
from scipy.sparse import csr_matrix  # Import for sparse matrix conversion
import matplotlib.pyplot as plt  # Import for visualization

class MarkovClusteringLocalization:
    def __init__(self, map_image_path):
        # Load the map image (placeholder, as clustering doesn't directly use the map)
        self.map_image_path = map_image_path
        self.graph = None

    def build_graph_from_lidar(self, lidar_data):
        """Build a graph from LiDAR data."""
        self.graph = nx.Graph()
        for i, distance in enumerate(lidar_data):
            if distance < 10.0:  # Ignore invalid or infinite values
                # Add nodes and edges based on LiDAR data
                self.graph.add_node(i, pos=(distance * np.cos(i), distance * np.sin(i)))
                if i > 0:
                    self.graph.add_edge(i - 1, i, weight=1.0 / distance)

    def perform_clustering(self):
        """Perform Markov Clustering on the graph."""
        if self.graph is None:
            raise ValueError("Graph has not been built yet.")
        
        # Convert the graph to a sparse array and then to a sparse matrix
        sparse_array = nx.to_scipy_sparse_array(self.graph)
        matrix = csr_matrix(sparse_array)  # Convert to a sparse matrix
        
        # Run Markov Clustering
        result = mc.run_mcl(matrix)
        clusters = mc.get_clusters(result)
        return clusters

    def get_estimated_position(self, clusters):
        """Estimate the robot's position based on clusters."""
        # Placeholder: Use the largest cluster's centroid as the estimated position
        largest_cluster = max(clusters, key=len)
        positions = [self.graph.nodes[node]['pos'] for node in largest_cluster]
        x = np.mean([pos[0] for pos in positions])
        y = np.mean([pos[1] for pos in positions])
        return x, y

    def visualize_localization(self, clusters):
        """Visualize the graph and clusters."""
        if self.graph is None:
            raise ValueError("Graph has not been built yet.")
        
        # Plot the graph
        plt.figure(figsize=(10, 10))
        pos = nx.get_node_attributes(self.graph, 'pos')  # Get node positions
        nx.draw(self.graph, pos, node_size=50, with_labels=False, alpha=0.7)

        # Highlight clusters
        colors = plt.cm.rainbow(np.linspace(0, 1, len(clusters)))
        for cluster, color in zip(clusters, colors):
            cluster_positions = [pos[node] for node in cluster]
            cluster_x = [p[0] for p in cluster_positions]
            cluster_y = [p[1] for p in cluster_positions]
            plt.scatter(cluster_x, cluster_y, color=color, label=f"Cluster {clusters.index(cluster)}", s=100)

        plt.title("Localization Visualization")
        plt.xlabel("X Position")
        plt.ylabel("Y Position")
        plt.legend()
        plt.show()