import cv2
import math
import matplotlib.pyplot as plt
import threading

class GPSLocalization:
    def __init__(self):
        self.coordinates = (0, 0)

    def getCoordinates(self):
        return self.coordinates

    def calculate_coordinates(self, gps_data):
        """
        Calculate the pixel coordinates on the map image from GPS data.

        Args:
            gps_data (dict): A dictionary containing GPS coordinates in the format:
                             {"gps": {"x": float, "y": float, "z": float}}

        Returns:
            tuple: x and y coordinates in in meters.
        """
        gps_coordinates = [gps_data["gps"]["x"] + 7.5 / 2, gps_data["gps"]["y"] + 9 / 2, gps_data["gps"]["z"]]

        # Convert GPS coordinates to pixel coordinates
        gps_x, gps_y = gps_coordinates[0], gps_coordinates[1]
        self.coordinates = (gps_x, gps_y)
        return gps_x, gps_y

    def angle_calculator(self, gps_data):
        compass_x = gps_data["compass"]["x"]
        compass_y = gps_data["compass"]["y"]
        angle = -math.atan2(compass_y, compass_x) + math.radians(90)
        return math.degrees(angle)
