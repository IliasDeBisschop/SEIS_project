import math

def preprocess_lidar_data(range_image):
    """Convert LiDAR data from polar to Cartesian coordinates."""
    points = []
    angle_increment = 2 * math.pi / len(range_image)  # Assuming 360-degree LiDAR
    for i, distance in enumerate(range_image):
        if distance < 10.0:  # Ignore invalid or infinite values
            angle = i * angle_increment
            x = distance * math.cos(angle)
            y = distance * math.sin(angle)
            points.append((x, y))
    return points


def filter_invalid_data(range_image):
    """Filter out invalid LiDAR data."""
    return [distance for distance in range_image if distance >= 0]  # Example filter


def convert_to_cartesian(range_image):
    """Convert filtered LiDAR data to Cartesian coordinates."""
    filtered_data = filter_invalid_data(range_image)
    return preprocess_lidar_data(filtered_data)