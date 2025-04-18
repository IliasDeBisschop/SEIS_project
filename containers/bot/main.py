import asyncio
import websockets
import json
import math
from sensor_msgs.msg import LaserScan
import rospy

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


async def handle_connection(websocket, path):
    print("Bot connected.")
    try:
        while True:
            # Receive LiDAR data from the bot
            lidar_data = await websocket.recv()
            lidar_data = json.loads(lidar_data)
            print(f"Received LiDAR data: {lidar_data['lidar']}")

            # Process LiDAR data and generate motor commands
            motor_commands = {
                "left_speed": 1.0,  # Example: Move forward
                "right_speed": 1.0
            }

            # Send motor commands back to the bot
            await websocket.send(json.dumps(motor_commands))
    except websockets.ConnectionClosed:
        print("Connection to bot lost.")
    except Exception as e:
        print(f"Error: {e}")

# Start the WebSocket server
start_server = websockets.serve(handle_connection, "0.0.0.0", 5001)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()