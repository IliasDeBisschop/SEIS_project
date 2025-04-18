import asyncio
from lidar.preprocessing import preprocess_lidar_data
from slam.gmapping import GMapping
import websockets
import json

async def handle_connection(websocket, path):
    print("Bot connected.")
    try:
        slam = GMapping()  # Initialize the GMapping SLAM algorithm
        while True:
            # Receive LiDAR data from the bot
            lidar_data = await websocket.recv()
            lidar_data = json.loads(lidar_data)
            print(f"Received LiDAR data: {lidar_data['lidar']}")

            # Preprocess LiDAR data
            processed_data = preprocess_lidar_data(lidar_data['lidar'])

            # Update SLAM with the processed data
            slam.update(processed_data)

            # Generate motor commands based on SLAM results
            motor_commands = slam.get_motor_commands()

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