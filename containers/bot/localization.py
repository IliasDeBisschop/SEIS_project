import cv2
import matplotlib.pyplot as plt

class GPSLocalization:
    def __init__(self, map_image_path):
        """
        Initialize the GPSLocalization class with the path to the map image.
        """
        self.map_image_path = map_image_path

    def visualize_localization(self, gps_data, output_path="localization_visualization.png"):
        """
        Visualize the robot's position on the map using GPS data.

        Args:
            gps_data (dict): A dictionary containing GPS coordinates in the format:
                             {"gps": {"x": float, "y": float, "z": float}}
            output_path (str): Path to save the visualization image.
        """
        # Load the map image
        map_image = cv2.imread(self.map_image_path, cv2.IMREAD_COLOR)
        if map_image is None:
            raise FileNotFoundError(f"Map image '{self.map_image_path}' not found or cannot be read.")

        # Map dimensions in meters
        map_width_meters = 16  # Width of the room in meters
        map_height_meters = 9  # Height of the room in meters

        # Get map image dimensions
        map_height_pixels, map_width_pixels, _ = map_image.shape

        # Convert GPS coordinates to pixel coordinates
        gps_x, gps_y = gps_data["gps"]["x"], gps_data["gps"]["y"]
        pixel_x = int((gps_x / map_width_meters) * map_width_pixels)
        pixel_y = int((1 - (gps_y / map_height_meters)) * map_height_pixels)  # Invert Y-axis for image coordinates

        # Draw the robot's position as a red dot
        cv2.circle(map_image, (pixel_x, pixel_y), 10, (0, 0, 255), -1)  # Red dot with radius 10 pixels

        # Save the visualization
        cv2.imwrite(output_path, map_image)
        print(f"Localization visualization saved to {output_path}")

        # Optionally display the visualization
        plt.imshow(cv2.cvtColor(map_image, cv2.COLOR_BGR2RGB))
        plt.title("Localization Visualization")
        plt.axis("off")
        plt.show()