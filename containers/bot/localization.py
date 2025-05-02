import cv2
import math
import matplotlib.pyplot as plt
import threading

class GPSLocalization:
    def __init__(self, map_image_path):
        """
        Initialize the GPSLocalization class with the path to the map image.
        """
        self.map_image_path = map_image_path
        self.lock = threading.Lock()  # Add a lock

    def calculate_coordinates(self, gps_data):
        """
        Calculate the pixel coordinates on the map image from GPS data.

        Args:
            gps_data (dict): A dictionary containing GPS coordinates in the format:
                             {"gps": {"x": float, "y": float, "z": float}}

        Returns:
            tuple: Pixel coordinates (pixel_x, pixel_y).
        """
        resolution = 0.5 / 100  # 0.5 cm per pixel
        gps_coordinates = [gps_data["gps"]["x"] + 7.5 / 2, gps_data["gps"]["y"] + 9 / 2, gps_data["gps"]["z"]]

        # Convert GPS coordinates to pixel coordinates
        gps_x, gps_y = gps_coordinates[0], gps_coordinates[1]
        x = int(gps_x / resolution)
        y = int(gps_y / resolution)

        return x/200, y/200 #this is in 0.5cm from the bottom left      

    def visualize_localization(self, gps_data, output_path="output/localization_visualization.png"):
        """
        Visualize the robot's position on the map using GPS data.

        Args:
            gps_data (dict): A dictionary containing GPS coordinates in the format:
                             {"gps": {"x": float, "y": float, "z": float}}
            output_path (str): Path to save the visualization image.
        """
        with self.lock:  # Ensure only one thread can execute this block at a time
            # Load the map image
            map_image = cv2.imread(self.map_image_path, cv2.IMREAD_COLOR)
            if map_image is None:
                raise FileNotFoundError(f"Map image '{self.map_image_path}' not found or cannot be read.")

            # Calculate pixel coordinates
            pixel_x, pixel_y = self.calculate_coordinates(gps_data)
            # Draw the robot's position as a red dot
            cv2.circle(map_image, (int(pixel_x*200),int( 1800 - pixel_y*200)), 20, (0, 0, 255), -1)  # Red dot with radius 10 pixels

            # Save the visualization
            success = cv2.imwrite(output_path, map_image)
            if not success:
                print(f"Failed to save the image to {output_path}")

    def angle_calculator(self, gps_data):
        compass_x = gps_data["compass"]["x"]
        compass_y = gps_data["compass"]["y"]
        angle = -math.atan2(compass_y, compass_x) + math.radians(90)
        return math.degrees(angle)
