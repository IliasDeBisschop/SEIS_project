# GMapping SLAM

GMapping SLAM is a project that implements the GMapping algorithm for simultaneous localization and mapping using LiDAR data. This project is designed to provide a robust solution for mapping environments and localizing a robot within that environment.

## Project Structure

The project is organized as follows:

```
gmapping-slam
├── src
│   ├── main.py                # Entry point of the application
│   ├── slam
│   │   ├── gmapping.py        # Implementation of the GMapping SLAM algorithm
│   │   └── __init__.py        # Marks the slam directory as a package
│   ├── lidar
│   │   ├── preprocessing.py    # Functions for preprocessing LiDAR data
│   │   └── __init__.py        # Marks the lidar directory as a package
│   └── utils
│       ├── visualization.py     # Functions for visualizing SLAM results
│       └── __init__.py        # Marks the utils directory as a package
├── requirements.txt            # Lists project dependencies
├── .gitignore                  # Specifies files to ignore by Git
└── README.md                   # Documentation for the project
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd gmapping-slam
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python src/main.py
   ```

## Usage

- The application initializes the SLAM process and manages the flow of the program.
- LiDAR data is preprocessed to convert polar coordinates to Cartesian coordinates and filter invalid data.
- The GMapping algorithm is applied to create a map of the environment and localize the robot.
- Visualization tools are provided to plot the map and the robot's trajectory.

## Overview of GMapping SLAM Implementation

The GMapping algorithm is a popular method for SLAM that uses particle filters to estimate the robot's position and build a map of the environment. This implementation leverages LiDAR data for accurate mapping and localization.

For more detailed information on the individual components, please refer to the respective files in the `src` directory.