from breezyslam.algorithms import RMHC_SLAM
from breezyslam.sensors import Laser
import numpy as np

class Slam:
    def __init__(self):
        # Initialiseer de SLAM-systemen met een kaartgrootte en resolutie
        map_size_pixels = 100
        map_size_meters = 10.0
        self.slam = RMHC_SLAM(Laser(360, 10), map_size_pixels, map_size_meters)
        self.map = bytearray(map_size_pixels * map_size_pixels)
        self.pose = [0, 0, 0]  # Startpositie: [x, y, theta]

    def update(self, lidar_data):
        # Update SLAM met LiDAR-gegevens
        distances = [d[0] for d in lidar_data]
        self.slam.update(distances)
        self.pose = self.slam.getpos()  # Haal de bijgewerkte pose op
        print(f"Updated pose: {self.pose}")

    def get_map(self):
        self.slam.getmap(self.map)  # Haal de kaart op
        return self.map

    def get_pose(self):
        return self.pose

def main():
    slam = Slam()
    # Simuleer LiDAR-gegevens: lijst van (afstand, hoek)
    lidar_data = [(10, np.pi / 4), (15, np.pi / 2), (20, np.pi)]
    slam.update(lidar_data)
    print("Final pose:", slam.get_pose())
    print("Final map:")
    print(slam.get_map())

if __name__ == "__main__":
    main()