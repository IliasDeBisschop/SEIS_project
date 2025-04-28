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

        resolution = 0.5/100 # 0.5 cm per pixel
        gps_coordinates = [gps_data["gps"]["x"] + 7.5/2, gps_data["gps"]["y"] + 9/2, gps_data["gps"]["z"]]


        # Convert GPS coordinates to pixel coordinates
        gps_x, gps_y = gps_coordinates[0], gps_coordinates[1]  # Assuming gps_data is a list of [x, y, z]
        pixel_x = int(gps_x / resolution)
        pixel_y = int(gps_y / resolution)

        # Draw the robot's position as a red dot
        print(f"GPS Coordinates: ({gps_x}, {gps_y}) -> Pixel Coordinates: ({pixel_x}, {pixel_y})")
        cv2.circle(map_image, (pixel_x, 1800 - pixel_y), 20, (0, 0, 255), -1)  # Red dot with radius 10 pixels

        # Save the visualization
        cv2.imwrite(output_path, map_image)
        print(f"Localization visualization saved to {output_path}")
