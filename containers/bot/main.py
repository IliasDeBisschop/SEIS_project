import asyncio
import websockets
import json
from localization import MarkovClusteringLocalization
import cv2
import numpy as np


async def handle_connection(websocket, path):
    print("Bot connected.")
    # Initialize the localization system
    mcl = MarkovClusteringLocalization("image_low_pixels.png")

    try:
        while True:
            # Receive LiDAR data from the bot
            lidar_data = await websocket.recv()
            lidar_data = json.loads(lidar_data)
            print(f"Received LiDAR data size: {len(lidar_data['lidar'])}")

            # Build graph from LiDAR data
            mcl.build_graph_from_lidar(lidar_data['lidar'])

            # Visualize the lines detected in the graph
            graph_lines_output_path = "./output/graph_lines_visualization.png"
            mcl.visualize_lines_in_graph(output_path=graph_lines_output_path)
            print(f"Graph lines visualization saved to {graph_lines_output_path}")

            # Visualize localization and save to file
            localization_output_path = "./output/localization_visualization.png"
            mcl.visualize_localization(lidar_data['lidar'], output_path=localization_output_path)
            print(f"Localization visualization saved to {localization_output_path}")

            # Generate motor commands (placeholder)
            motor_commands = {
                "left_speed": 1.0,  # Example: Move forward
                "right_speed": 1.0
            }

            # Send motor commands back to the bot
            await websocket.send(json.dumps(motor_commands))
    except websockets.ConnectionClosed:
        print("Connection to bot lost.")
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()  # Log the full stack trace

# Start the WebSocket server
start_server = websockets.serve(handle_connection, "0.0.0.0", 5001)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()


def detect_lines_in_map(self, upscale_factor=1000):
    """Detect lines in the map using Hough Transform with increased tolerance."""
    map_image = cv2.imread(self.map_image_path, cv2.IMREAD_GRAYSCALE)
    if map_image is None:
        raise FileNotFoundError(f"Map image '{self.map_image_path}' not found or cannot be read.")
    
    # Upscale the map for better resolution
    map_image = cv2.resize(map_image, (map_image.shape[1] * upscale_factor, map_image.shape[0] * upscale_factor))
    
    # Apply Canny edge detection
    edges = cv2.Canny(map_image, 50, 150, apertureSize=3)
    
    # Detect lines using Hough Transform with increased tolerance
    lines = cv2.HoughLinesP(
        edges,
        rho=1,  # Distance resolution of the accumulator in pixels
        theta=np.pi / 180,  # Angle resolution of the accumulator in radians
        threshold=50,  # Lower threshold for line detection (increased tolerance)
        minLineLength=20,  # Minimum length of a line segment (increased tolerance)
        maxLineGap=15  # Maximum gap between line segments to treat them as a single line (increased tolerance)
    )
    
    if lines is not None:
        for line in lines:
            for x1, y1, x2, y2 in line:
                x1 = int((x1 * upscale_factor) + map_image.shape[1] // 2)
                y1 = int((-y1 * upscale_factor) + map_image.shape[0] // 2)
                x2 = int((x2 * upscale_factor) + map_image.shape[1] // 2)
                y2 = int((-y2 * upscale_factor) + map_image.shape[0] // 2)
    
    return lines