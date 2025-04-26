import numpy as np
import markov_clustering as mc
import networkx as nx
from scipy.sparse import csr_matrix  # Import for sparse matrix conversion
import matplotlib.pyplot as plt  # Import for visualization
from PIL import Image  # Import for image handling
import cv2  # Import for image processing
from scipy.spatial.transform import Rotation as R

class MarkovClusteringLocalization:
    def __init__(self, map_image_path):
        # Load the map image (placeholder, as clustering doesn't directly use the map)
        self.map_image_path = map_image_path
        self.graph = None

    def build_graph_from_lidar(self, lidar_data, distance_threshold=0.2):
        """Build a graph from LiDAR data with a distance threshold for connecting points."""
        self.graph = nx.Graph()
        for i, distance in enumerate(lidar_data):
            if distance > 0 and distance < 10.0:  # Ignore invalid, zero, or infinite values
                try:
                    # Calculate angle in radians
                    angle = (i * 2 * np.pi / 360) - np.pi

                    # Calculate position
                    x = distance * np.cos(angle) * 100
                    y = distance * np.sin(angle) * 100

                    # Add node with position
                    self.graph.add_node(i, pos=(x, y))

                    # Add edge to the previous node if it exists and is within the distance threshold
                    if i > 0 and self.graph.has_node(i - 1):
                        prev_x, prev_y = self.graph.nodes[i - 1]['pos']
                        if np.linalg.norm([x - prev_x, y - prev_y]) <= distance_threshold * 100:
                            self.graph.add_edge(i - 1, i)
                except Exception as e:
                    print(f"Error processing node {i}: {e}")
                    raise

        self.graph.add_node(1000, pos=(0, 0))  # Add a node for the robot's position

    def detect_lines_in_graph(self):
        """Detect lines in the graph."""
        lines = []
        for edge in self.graph.edges:
            node1, node2 = edge
            pos1 = self.graph.nodes[node1]['pos']
            pos2 = self.graph.nodes[node2]['pos']
            lines.append((pos1, pos2))
        return lines

    def detect_lines_in_graph(self, angle_tolerance=np.pi / 18, distance_tolerance=0.1):
        """Detect lines in the graph and group nearby lines into larger segments."""
        lines = []
        for edge in self.graph.edges:
            node1, node2 = edge
            pos1 = np.array(self.graph.nodes[node1]['pos'])
            pos2 = np.array(self.graph.nodes[node2]['pos'])
            lines.append((pos1, pos2))

        # Group lines based on angle and distance
        grouped_lines = []
        while lines:
            base_line = lines.pop(0)
            base_start, base_end = base_line
            group = [base_line]

            remaining_lines = []
            for other_line in lines:
                other_start, other_end = other_line

                # Calculate angles of the lines
                base_angle = np.arctan2(base_end[1] - base_start[1], base_end[0] - base_start[0])
                other_angle = np.arctan2(other_end[1] - other_start[1], other_end[0] - other_start[0])

                # Check if the angles are similar
                if abs(base_angle - other_angle) < angle_tolerance:
                    # Check if the lines are close in distance
                    if (np.linalg.norm(base_start - other_start) < distance_tolerance or
                        np.linalg.norm(base_end - other_end) < distance_tolerance):
                        group.append(other_line)
                    else:
                        remaining_lines.append(other_line)
                else:
                    remaining_lines.append(other_line)

            # Update the lines list to exclude processed lines
            lines = remaining_lines

            # Merge the group into a single line
            all_points = np.vstack([line[0] for line in group] + [line[1] for line in group])
            min_point = np.min(all_points, axis=0)
            max_point = np.max(all_points, axis=0)
            grouped_lines.append((min_point, max_point))

        return grouped_lines

    def align_lines(self, graph_lines, map_lines, upscale_factor=1):
        """Align graph lines with map lines using scaling and rotation."""
        # Extract points from graph lines
        graph_points = []
        for line in graph_lines:
            graph_points.append(line[0])
            graph_points.append(line[1])
        graph_points = np.array(graph_points)

        # Extract points from map lines
        map_points = []
        for line in map_lines:
            x1, y1, x2, y2 = line[0]
            map_points.append((x1, y1))
            map_points.append((x2, y2))
        map_points = np.array(map_points)

        # Debug: Print original points
        print("Original Graph Points:", graph_points)
        print("Original Map Points:", map_points)

        # Compute centroids
        graph_centroid = np.mean(graph_points, axis=0)
        map_centroid = np.mean(map_points, axis=0)

        # Center the points
        graph_points_centered = graph_points - graph_centroid
        map_points_centered = map_points - map_centroid

        # Debug: Print centroids
        print("Graph Centroid:", graph_centroid)
        print("Map Centroid:", map_centroid)

        # Compute scaling factor
        graph_scale = np.linalg.norm(graph_points_centered) / len(graph_points_centered)
        map_scale = np.linalg.norm(map_points_centered) / len(map_points_centered)
        scale = map_scale / graph_scale

        # Scale the graph points
        graph_points_scaled = graph_points_centered * scale

        # Debug: Print scaling factor and scaled points
        print("Scaling Factor:", scale)
        print("Scaled Graph Points:", graph_points_scaled)

        # Compute rotation matrix using Singular Value Decomposition (SVD)
        H = np.dot(map_points_centered.T, graph_points_scaled)
        U, _, Vt = np.linalg.svd(H)
        R_matrix = np.dot(U, Vt)

        # Debug: Print rotation matrix
        print("Rotation Matrix:", R_matrix)

        # Apply rotation
        graph_points_aligned = np.dot(graph_points_scaled, R_matrix.T)

        # Translate back to map centroid
        graph_points_aligned += map_centroid

        # Debug: Print aligned points
        print("Aligned Graph Points:", graph_points_aligned)

        return graph_points_aligned

    def visualize_alignment(self, graph_lines, map_lines, aligned_graph_points, upscale_factor=1, output_path="alignment_visualization.png"):
        """Visualize the alignment of graph lines and map lines."""
        map_image = cv2.imread(self.map_image_path, cv2.IMREAD_COLOR)
        if map_image is None:
            raise FileNotFoundError(f"Map image '{self.map_image_path}' not found or cannot be read.")

        # Upscale the map for better visualization
        map_image = cv2.resize(map_image, (map_image.shape[1] * upscale_factor, map_image.shape[0] * upscale_factor), interpolation=cv2.INTER_NEAREST)

        # Draw map lines
        for line in map_lines:
            x1, y1, x2, y2 = line[0]
            x1, y1, x2, y2 = int(x1 * upscale_factor), int(y1 * upscale_factor), int(x2 * upscale_factor), int(y2 * upscale_factor)
            cv2.line(map_image, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Green lines for map

        # Draw aligned graph lines
        for i in range(0, len(aligned_graph_points), 2):
            x1, y1 = aligned_graph_points[i]
            x2, y2 = aligned_graph_points[i + 1]
            x1, y1, x2, y2 = int(x1 * upscale_factor), int(y1 * upscale_factor), int(x2 * upscale_factor), int(y2 * upscale_factor)
            cv2.line(map_image, (x1, y1), (x2, y2), (255, 0, 0), 2)  # Blue lines for graph

        # Save the visualization
        cv2.imwrite(output_path, map_image)
        print(f"Alignment visualization saved to {output_path}")

        # Optionally display the visualization
        plt.imshow(cv2.cvtColor(map_image, cv2.COLOR_BGR2RGB))
        plt.title("Alignment Visualization")
        plt.axis("off")
        plt.show()

    def visualize_localization(self, lidar_data, output_path="localization_visualization.png"):
        """Visualize the LiDAR data and graph on the map."""
        if self.graph is None:
            raise ValueError("Graph has not been built yet.")

        # Load the map image
        map_image = cv2.imread("image_low_pixels.png", cv2.IMREAD_COLOR)
        if map_image is None:
            raise FileNotFoundError("Map image 'image_low_pixels.png' not found or cannot be read.")

        # Upscale the map for better visualization
        upscale_factor = 1
        map_image = cv2.resize(map_image, (map_image.shape[1] * upscale_factor, map_image.shape[0] * upscale_factor), interpolation=cv2.INTER_NEAREST)

        # Get the robot's position (node ID 1000)
        robot_x, robot_y = self.graph.nodes[1000]['pos']
        robot_x = int((robot_x * upscale_factor) + map_image.shape[1] // 2)
        robot_y = int((-robot_y * upscale_factor) + map_image.shape[0] // 2)

        # Draw the robot's position
        cv2.circle(map_image, (robot_x, robot_y), 5, (0, 0, 255), -1)  # Red dot for the bot

        # Map LiDAR data onto the map
        for i, distance in enumerate(lidar_data):
            if distance > 0 and distance < 10.0:  # Ignore invalid or infinite values
                # Calculate angle in radians
                angle = (i * 2 * np.pi / 360) - np.pi

                # Convert polar coordinates to Cartesian coordinates
                x = distance * np.cos(angle)
                y = distance * np.sin(angle)

                # Scale and translate the coordinates to match the map
                x = int((x * upscale_factor) + map_image.shape[1] // 2)
                y = int((-y * upscale_factor) + map_image.shape[0] // 2)

                # Draw a line from the robot to the LiDAR point
                cv2.line(map_image, (robot_x, robot_y), (x, y), (0, 255, 0), 1)  # Green line for LiDAR

                # Draw the LiDAR point
                cv2.circle(map_image, (x, y), 2, (255, 0, 0), -1)  # Blue dot for LiDAR point

        # Save the visualization
        cv2.imwrite(output_path, map_image)
        print(f"Localization visualization saved to {output_path}")

        # Optionally display the visualization
        plt.imshow(cv2.cvtColor(map_image, cv2.COLOR_BGR2RGB))
        plt.title("Localization Visualization on Map")
        plt.axis("off")
        plt.show()

    def visualize_lines_in_graph(self, output_path="graph_lines_visualization.png", upscale_factor=1, line_thickness=1):
        """Visualize the lines detected in the graph, with all lines in blue and thicker."""
        if self.graph is None:
            raise ValueError("Graph has not been built yet.")

        # Create a blank image for visualization
        map_image = np.zeros((500 * upscale_factor, 500 * upscale_factor, 3), dtype=np.uint8)

        # Get the robot's position (node ID 1000)
        robot_x, robot_y = self.graph.nodes[1000]['pos']
        robot_x = int((robot_x * upscale_factor) + map_image.shape[1] // 2)
        robot_y = int((-robot_y * upscale_factor) + map_image.shape[0] // 2)

        # Draw the robot's position
        cv2.circle(map_image, (robot_x, robot_y), 5, (0, 0, 255), -1)  # Red dot for the bot

        # Get the lines from the graph
        lines = self.detect_lines_in_graph()

        # Define the color for all lines (blue)
        color = ( 0,255, 0)  # Blue

        # Draw each line with the same color and increased thickness
        for line in lines:
            (x1, y1), (x2, y2) = line
            x1 = int((x1 * upscale_factor) + map_image.shape[1] // 2)
            y1 = int((-y1 * upscale_factor) + map_image.shape[0] // 2)
            x2 = int((x2 * upscale_factor) + map_image.shape[1] // 2)
            y2 = int((-y2 * upscale_factor) + map_image.shape[0] // 2)

            # Draw the line with the specified thickness
            cv2.line(map_image, (x1, y1), (x2, y2), color, line_thickness)

        # Save the visualization
        cv2.imwrite(output_path, map_image)
        print(f"Graph lines visualization saved to {output_path}")

        # Optionally display the visualization
        plt.imshow(cv2.cvtColor(map_image, cv2.COLOR_BGR2RGB))
        plt.title("Graph Lines Visualization")
        plt.axis("off")
        plt.show()

    def visualize_points_in_graph(self, output_path="graph_points_visualization.png", upscale_factor=10, point_size=5):
        """Visualize the points detected in the graph without connecting them with lines."""
        if self.graph is None:
            raise ValueError("Graph has not been built yet.")

        # Create a blank image for visualization
        map_image = np.zeros((500 * upscale_factor, 500 * upscale_factor, 3), dtype=np.uint8)

        # Get the robot's position (node ID 1000)
        robot_x, robot_y = self.graph.nodes[1000]['pos']
        robot_x = int((robot_x * upscale_factor) + map_image.shape[1] // 2)
        robot_y = int((-robot_y * upscale_factor) + map_image.shape[0] // 2)

        # Draw the robot's position
        cv2.circle(map_image, (robot_x, robot_y), point_size, (0, 0, 255), -1)  # Red dot for the bot

        # Draw each point in the graph
        for node, data in self.graph.nodes(data=True):
            if node == 1000:  # Skip the robot's position
                continue
            x, y = data['pos']
            x = int((x * upscale_factor) + map_image.shape[1] // 2)
            y = int((-y * upscale_factor) + map_image.shape[0] // 2)

            # Draw the point as a filled circle
            cv2.circle(map_image, (x, y), point_size, (255, 0, 0), -1)  # Blue dot for LiDAR points

        # Save the visualization
        cv2.imwrite(output_path, map_image)
        print(f"Graph points visualization saved to {output_path}")

        # Optionally display the visualization
        plt.imshow(cv2.cvtColor(map_image, cv2.COLOR_BGR2RGB))
        plt.title("Graph Points Visualization")
        plt.axis("off")
        plt.show()
