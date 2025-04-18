import matplotlib.pyplot as plt

def plot_map(occupancy_grid, robot_position=None):
    plt.imshow(occupancy_grid, cmap='gray', origin='lower')
    if robot_position is not None:
        plt.plot(robot_position[0], robot_position[1], 'ro')  # Robot position in red
    plt.title("SLAM Occupancy Grid")
    plt.xlabel("X-axis")
    plt.ylabel("Y-axis")
    plt.colorbar(label='Occupancy Probability')
    plt.show()

def plot_trajectory(trajectory):
    plt.figure()
    plt.plot(trajectory[:, 0], trajectory[:, 1], 'b-')  # Trajectory in blue
    plt.title("Robot Trajectory")
    plt.xlabel("X-axis")
    plt.ylabel("Y-axis")
    plt.axis('equal')
    plt.grid()
    plt.show()