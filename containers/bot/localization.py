import math
import cv2
import numpy as np

pixel_size = 0.3  # Size of each pixel in meters (example value, adjust as needed)


class MonteCarloLocalization:
    def __init__(self, map_image_path, num_particles=100):
        # Load the map image
        self.map = cv2.imread(map_image_path, cv2.IMREAD_GRAYSCALE)
        self.map = cv2.threshold(self.map, 127, 255, cv2.THRESH_BINARY)[1]  # Convert to binary
        self.num_particles = num_particles
        self.particles = self.initialize_particles()

    def initialize_particles(self):
        """Initialize particles randomly on the map."""
        particles = []
        height, width = self.map.shape
        for _ in range(self.num_particles):
            while True:
                x = np.random.randint(0, width)
                y = np.random.randint(0, height)
                theta = np.random.uniform(0, 2 * math.pi)
                if self.map[y, x] == 255:  # Ensure the particle is in free space
                    particles.append((x, y, theta))
                    break
        return particles

    def update_particles(self, lidar_data):
        weights = []
        for particle in self.particles:
            x, y, theta = particle
            weight = self.calculate_particle_weight(x, y, theta, lidar_data)
            weights.append(weight)

        # Normalize weights
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        else:
            weights = [1 / len(self.particles)] * len(self.particles)

        # Update particles with weights
        self.particles = [(p[0], p[1], p[2], w) for p, w in zip(self.particles, weights)]

    def calculate_particle_weight(self, x, y, theta, lidar_data):
        """Calculate the weight of a particle based on LiDAR data."""
        weight = 1.0
        for i, distance in enumerate(lidar_data):
            if distance < 10.0:  # Ignore invalid or infinite values
                # Calculate the expected distance from the particle's position
                expected_distance = self.get_expected_distance(x, y, theta, i)
                # Compare the expected distance with the actual distance
                weight *= math.exp(-((distance - expected_distance) ** 2) / (2 * 0.5 ** 2))  # Gaussian
        return weight

    def get_expected_distance(self, x, y, theta, lidar_angle_index):
        """Calculate the expected distance to an obstacle from a particle's position."""
        # Placeholder: Implement raycasting or lookup on the map
        return 5.0  # Example: Return a constant value for now

    def resample_particles(self):
        """Resample particles based on their weights."""
        # Placeholder: Implement particle resampling
        pass

    def get_estimated_position(self):
        """Estimate the robot's position based on the particles."""
        x = np.mean([p[0] for p in self.particles])
        y = np.mean([p[1] for p in self.particles])
        theta = np.mean([p[2] for p in self.particles])
        return x, y, theta