import asyncio
import websockets
import json
from localization import MonteCarloLocalization


async def handle_connection(websocket, path):
    print("Bot connected.")
    # Initialize the localization system with the map
    mcl = MonteCarloLocalization("output_image_processed.jpg", num_particles=100)

    try:
        while True:
            # Receive LiDAR data from the bot
            lidar_data = await websocket.recv()
            lidar_data = json.loads(lidar_data)
            print(f"Received LiDAR data: {lidar_data['lidar']}")

            # Update localization with the LiDAR data
            mcl.update_particles(lidar_data['lidar'])
            mcl.resample_particles()
            estimated_position = mcl.get_estimated_position()
            print(f"Estimated position: {estimated_position}")

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
        print(f"Error: {e}")

# Start the WebSocket server
start_server = websockets.serve(handle_connection, "0.0.0.0", 5001)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()