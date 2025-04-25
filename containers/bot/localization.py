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
                # Calculate position
                angle = (i * 2 * np.pi / 360) - np.pi
                x = distance * np.cos(angle)
                y = distance * np.sin(angle)

                # Add node with position
                self.graph.add_node(i, pos=(x, y))
                
                # Add edge to the previous node if it exists
                if i > 0 and self.graph.has_node(i - 1):
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

    def visualize_localization(self, clusters, image_path="image_low_pixels.png", output_path="localization_visualization.png"):
        """Visualize the estimated position on a given image."""
        # Load the image
        try:
            img = Image.open(image_path)
        except FileNotFoundError:
            raise ValueError(f"Image file '{image_path}' not found.")
        
        # Convert the image to a numpy array for plotting
        img_array = np.array(img)

        # Plot the image
        plt.figure(figsize=(10, 10))
        plt.imshow(img_array, extent=[0, img_array.shape[1], 0, img_array.shape[0]])
        
        # Estimate the position
        x, y = self.get_estimated_position(clusters)
        
        # Adjust coordinates if necessary (e.g., flip y-axis for image coordinates)
        y = img_array.shape[0] - y  # Flip y-axis for image coordinates
        
        # Plot the estimated position
        plt.scatter([x], [y], color='red', label='Estimated Position', s=100, marker='x')

        # Add labels and legend
        plt.xlabel("X Coordinate")
        plt.ylabel("Y Coordinate")
        plt.title("Localization Visualization")
        plt.legend()
        plt.grid(False)  # Disable grid for image-based visualization

        # Save the visualization
        plt.savefig(output_path)
        plt.close()
