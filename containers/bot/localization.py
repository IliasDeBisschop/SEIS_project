import numpy as np
import markov_clustering as mc
import networkx as nx
from scipy.sparse import csr_matrix  # Import for sparse matrix conversion
import matplotlib.pyplot as plt  # Import for visualization
from PIL import Image  # Import for image handling

class MarkovClusteringLocalization:
    def __init__(self, map_image_path):
        # Load the map image (placeholder, as clustering doesn't directly use the map)
        self.map_image_path = map_image_path
        self.graph = None

    def build_graph_from_lidar(self, lidar_data):
        """Build a graph from LiDAR data."""
        self.graph = nx.Graph()
        for i, distance in enumerate(lidar_data):
            if distance > 0 and distance < 10.0:  # Ignore invalid, zero, or infinite values
                try:
                    # Calculate angle in radians
                    angle = (i * 2 * np.pi / 360) - np.pi
                    
                    # Calculate position
                    x = distance * np.cos(angle)
                    y = distance * np.sin(angle)

                    # Add node with position
                    self.graph.add_node(i, pos=(x, y))
                    
                    # Add edge to the previous node if it exists
                    if i > 0 and self.graph.has_node(i - 1):
                        self.graph.add_edge(i - 1, i, weight=1.0 / distance)
                except Exception as e:
                    print(f"Error processing node {i}: {e}")
                    raise

    def perform_clustering(self):
        """Perform Markov Clustering on the graph."""
        if self.graph is None:
            raise ValueError("Graph has not been built yet.")
        
        try:
            # Convert the graph to a sparse array and then to a sparse matrix
            # Debugging sparse matrix
            sparse_array = nx.to_scipy_sparse_array(self.graph)
            matrix = csr_matrix(sparse_array)  # Convert to a sparse matrix
            
            # Run Markov Clustering
            result = mc.run_mcl(matrix)
            clusters = mc.get_clusters(result)
            print(f"Clusters found: {clusters}")
            return clusters
        except Exception as e:
            print(f"Error during clustering: {e}")
            raise

    def get_estimated_position(self, clusters):
        """Estimate the robot's position based on clusters."""
        largest_cluster = max(clusters, key=len)
        # Filter nodes that exist in the graph
        valid_nodes = [node for node in largest_cluster if node in self.graph.nodes]
        missing_nodes = [node for node in largest_cluster if node not in self.graph.nodes]
        if missing_nodes:
            print(f"Missing nodes: {missing_nodes}")
        
        if not valid_nodes:
            raise ValueError("No valid nodes found in the largest cluster.")
        
        positions = [self.graph.nodes[node]['pos'] for node in valid_nodes]
        x = np.mean([pos[0] for pos in positions])
        y = np.mean([pos[1] for pos in positions])
        return x, y

    def visualize_localization(self, clusters, output_path="localization_visualization.png"):
        """Visualize the estimated position on the graph."""
        if self.graph is None:
            raise ValueError("Graph has not been built yet.")
        
        # Estimate the position
        x, y = self.get_estimated_position(clusters)
        
        # Plot the graph
        plt.figure(figsize=(10, 10))
        pos = nx.get_node_attributes(self.graph, 'pos')  # Get node positions
        nx.draw(self.graph, pos, with_labels=False, node_size=50, node_color='blue', edge_color='gray')
        
        # Plot the estimated position
        plt.scatter([x], [y], color='red', label='Estimated Position', s=100, marker='x')
        
        # Add labels and legend
        plt.xlabel("X Coordinate")
        plt.ylabel("Y Coordinate")
        plt.title("Localization Visualization on Graph")
        plt.legend()
        plt.grid(False)  # Disable grid for graph-based visualization

        # Save the visualization
        plt.savefig(output_path)
        plt.close()
