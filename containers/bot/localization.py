import cv2
import numpy as np
import math
import random

# Schaalfactor (0.05m per pixel)
SCALE = 0.05

# Laad de map en converteer naar een binair grid
def load_map(filepath):
    map_image = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
    _, binary_map = cv2.threshold(map_image, 127, 1, cv2.THRESH_BINARY_INV)
    return binary_map, map_image

# Converteer LiDAR-data naar (x, y) coördinaten in wereldruimte
def lidar_to_points(lidar_data, robot_position, robot_orientation):
    points = []
    for angle, distance in enumerate(lidar_data):
        if distance < 10.0:  # Alleen geldige metingen
            rad = math.radians(angle) + robot_orientation
            x = robot_position[0] + distance * math.cos(rad)
            y = robot_position[1] + distance * math.sin(rad)
            points.append((x, y))
    return points

# Partikelklasse voor Monte Carlo Localization
class Particle:
    def __init__(self, x, y, theta, weight=1.0):
        self.x = x
        self.y = y
        self.theta = theta
        self.weight = weight

# Bereken de waarschijnlijkheid van een partikel op basis van LiDAR-data
def calculate_weight(particle, lidar_data, binary_map):
    weight = 0
    for (distance, angle) in lidar_data:
        if distance < 10.0:  # Alleen geldige metingen
            rad = math.radians(angle) + particle.theta
            end_x = particle.x + distance * math.cos(rad)
            end_y = particle.y + distance * math.sin(rad)
            if raytrace((particle.x, particle.y), (end_x, end_y), binary_map):
                weight += 1  # Positieve bijdrage voor een goede match

    # Exponentiële schaal voor gewichten
    weight = max(weight, 0.1)
    weight = math.exp(weight)
    print(f"Particle ({particle.x}, {particle.y}) weight: {weight}")
    return weight

# Update partikels op basis van LiDAR-data
def update_particles(particles, lidar_data, binary_map):
    for particle in particles:
        particle.weight = calculate_weight(particle, lidar_data, binary_map)

# Her-sampling van partikels op basis van hun gewichten
def resample_particles(particles):
    weights = np.array([p.weight for p in particles], dtype=np.float64)
    total_weight = np.sum(weights)
    if total_weight == 0:
        print("All weights are zero! Assigning equal weights.")
        weights = np.ones(len(particles))  # Gelijke gewichten toewijzen
    else:
        weights /= total_weight  # Normaliseer gewichten
    print(f"Normalized weights: {weights}")
    new_particles = random.choices(particles, weights=weights, k=len(particles))
    return [Particle(p.x, p.y, p.theta) for p in new_particles]

# Initialiseer partikels willekeurig in de map
def initialize_particles(num_particles, binary_map, initial_position=None):
    particles = []
    for _ in range(num_particles):
        if initial_position:
            x = random.uniform(initial_position[0] - 1, initial_position[0] + 1)
            y = random.uniform(initial_position[1] - 1, initial_position[1] + 1)
        else:
            x = random.uniform(0, binary_map.shape[1] * SCALE)
            y = random.uniform(0, binary_map.shape[0] * SCALE)
        theta = random.uniform(0, 2 * math.pi)
        particles.append(Particle(x, y, theta))
    return particles

# Vraag de geschatte wereldcoördinaten op (gemiddelde van partikels)
def get_estimated_position(particles):
    x = np.mean([p.x for p in particles])
    y = np.mean([p.y for p in particles])
    theta = np.mean([p.theta for p in particles])
    return x, y, theta

# Sla een afbeelding op van de map met een "X" op de geschatte positie
def save_map_with_robot_position(map_image, particles, output_filepath):
    # Maak een kopie van de originele map
    map_with_robot = cv2.cvtColor(map_image, cv2.COLOR_GRAY2BGR)

    estimated_position = get_estimated_position(particles)
    # Converteer wereldcoördinaten naar pixelcoördinaten
    map_x = int(estimated_position[0] / SCALE)
    map_y = int(estimated_position[1] / SCALE)

    # Zet een rode pixel op de geschatte positie
    color = (0, 0, 255)  # Rood
    map_with_robot[map_y, map_x] = color

    # Teken alle partikels in blauw, met intensiteit afhankelijk van het aantal partikels op die locatie
    particle_density = np.zeros_like(map_image, dtype=np.float32)
    for particle in particles:
        px = int(particle.x / SCALE)
        py = int(particle.y / SCALE)
        if 0 <= px < particle_density.shape[1] and 0 <= py < particle_density.shape[0]:
            # Maak een 5x5 vierkant rond de partikelpositie
            for dx in range(-15, 16):
                for dy in range(-15, 16):
                    nx, ny = px + dx, py + dy
                    if 0 <= nx < particle_density.shape[1] and 0 <= ny < particle_density.shape[0]:
                        particle_density[ny, nx] += 1

    # Normaliseer de dichtheid en schaal naar 0-255
    particle_density = (particle_density / np.max(particle_density) * 255).astype(np.uint8)
    particle_density_colored = cv2.applyColorMap(particle_density, cv2.COLORMAP_JET)

    # Combineer de dichtheid met de originele map
    map_with_robot = cv2.addWeighted(map_with_robot, 0.7, particle_density_colored, 0.3, 0)

    # Sla de afbeelding op
    cv2.imwrite(output_filepath, map_with_robot)

def raytrace(start, end, binary_map):
    """Volg een straal van start naar end en retourneer het eerste obstakel."""
    x0, y0 = int(start[0] / SCALE), int(start[1] / SCALE)
    x1, y1 = int(end[0] / SCALE), int(end[1] / SCALE)

    # Bresenham's line algorithm
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        if 0 <= x0 < binary_map.shape[1] and 0 <= y0 < binary_map.shape[0]:
            if binary_map[y0, x0] == 0:  # Obstakel gevonden
                if (x0, y0) == (x1, y1):  # Eindpunt bereikt
                    return True
                break
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy

    return False 

# Interface klasse voor lokalisatie
class LocalizationInterface:
    def __init__(self, map_filepath, num_particles=100):
        self.binary_map, self.map_image = load_map(map_filepath)
        self.particles = initialize_particles(num_particles, self.binary_map)

    def process_lidar_data(self, lidar_data):
        update_particles(self.particles, lidar_data, self.binary_map)
        self.particles = resample_particles(self.particles)
        estimated_position = get_estimated_position(self.particles)
        return estimated_position

    def save_visualization(self, output_filepath):
        """
        Sla een visualisatie van de map op met de geschatte robotpositie.
        """

        # Sla de map op met de geschatte positie
        save_map_with_robot_position(self.map_image, self.particles, output_filepath)
        print(f"Map met robotpositie opgeslagen als '{output_filepath}'")
