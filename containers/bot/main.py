import asyncio
import websockets
import json
from localization import LocalizationInterface
import matplotlib.pyplot as plt
import math

# Define the process_lidar_data function
def process_lidar_data(lidar_data):
    """
    Processes raw LiDAR data into a list of tuples (distance, angle).
    This is a placeholder implementation.
    """
    lidar_tuples = []
    for i, distance in enumerate(lidar_data):
        angle = (i * (360 / len(lidar_data))) - 90
        if angle < 0:
            angle += 360
        lidar_tuples.append((distance, angle))
    return lidar_tuples


async def handle_connection(websocket, path):
    print("Bot connected.")
    # Initialize the localization system
    localization = LocalizationInterface("image_low_pixels.png", num_particles=100)
       
    try:
            # Receive LiDAR data from the bot
            lidar_data = await websocket.recv()
            lidar_data = json.loads(lidar_data)

            # Process LiDAR data
            lidar_tuples = process_lidar_data(lidar_data['lidar'])

            # Build graph and perform clustering
            estimated_position = localization.process_lidar_data(lidar_tuples)
            print(f"Geschatte positie: x={estimated_position[0]:.2f}, y={estimated_position[1]:.2f}, theta={math.degrees(estimated_position[2]):.2f} graden")

            # Sla de visualisatie op
            output_path = "./output/localization_visualization.png"
            print(f"Localization visualization saved to {output_path}")
            localization.save_visualization(output_path)

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
        traceback.print_exc()  # Log de volledige stacktrace

# Start the WebSocket server
start_server = websockets.serve(handle_connection, "0.0.0.0", 5001)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()