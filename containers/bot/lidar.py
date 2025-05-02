import math

class LidarProcessor:
    def __init__(self, max_distance=10.0, angle_range=80):
        """
        Initialize the LidarProcessor with a maximum valid distance and angle range.
        :param max_distance: Maximum valid distance for LiDAR measurements.
        :param angle_range: Range of angles (in degrees) to consider symmetrically around 0 and 180 degrees.
        """
        self.max_distance = max_distance
        self.angle_range = angle_range

    def lidar_to_points(self, lidar_data, robot_position, robot_orientation):
        """
        Convert LiDAR data to a list of points in the robot's coordinate system.
        :param lidar_data: List of distances from the LiDAR sensor.
        :param robot_position: Tuple (x, y) representing the robot's position.
        :param robot_orientation: Robot's orientation in radians.
        :return: List of (x, y) points.
        """
        points = []
        for angle, distance in enumerate(lidar_data):
            if distance < self.max_distance:  # Only valid measurements
                rad = math.radians(angle) + robot_orientation
                x = robot_position[0] + distance * math.cos(rad)
                y = robot_position[1] + distance * math.sin(rad)
                points.append((x, y))
        return points

    def is_object_getting_closer(self, lidar_data_1, lidar_data_2, direction_is_front=True):
        """
        Determine if an object is getting closer to the LiDAR scanner in a given direction
        and if there is something directly in front or back based on the direction.
        :param lidar_data_1: First set of LiDAR data (previous scan).
        :param lidar_data_2: Second set of LiDAR data (current scan).
        :param direction_is_front: Boolean indicating whether to check the front (True) or back (False).
        :return: True if an object is getting closer or something is directly in the specified direction, False otherwise.
        """
        # Determine the total number of rays in the LiDAR data
        num_rays = len(lidar_data_2)
        middle_index = num_rays // 2  # Middle index represents the front
    
        # Define the angle range for the front or back
        if direction_is_front:
            angle_range = range(middle_index - self.angle_range, middle_index + self.angle_range + 1)  # Symmetric around the middle (front)
            straight_index = middle_index  # Straight ahead for the front
        else:
            angle_range = range(-self.angle_range, self.angle_range + 1)  # Symmetric around 0 degrees (back)
            straight_index = 0  # Straight ahead for the back
    
        # Normalize the angle range to valid indices
        angle_range = [i % num_rays for i in angle_range]
    
        # Check if there is something directly in the specified direction
        if straight_index < len(lidar_data_2) and lidar_data_2[straight_index] < self.max_distance:
            print(f"Object detected directly in the specified direction at distance: {lidar_data_2[straight_index]}")
            return True
    
        # Check if an object is getting closer in the specified angle range
        for angle in angle_range:
            if angle < len(lidar_data_1) and angle < len(lidar_data_2):
                distance_1 = lidar_data_1[angle]
                distance_2 = lidar_data_2[angle]
    
                # Check if the object is getting closer
                if distance_2 + 0.0005 < distance_1 and distance_1 < self.max_distance:
                    print(f"Object getting closer: {distance_1} -> {distance_2} at angle {angle}")
                    return True
    
        return False