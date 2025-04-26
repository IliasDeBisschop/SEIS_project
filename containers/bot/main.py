import asyncio
import websockets
import json
from localization import MarkovClusteringLocalization
import matplotlib.pyplot as plt


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

            # Build graph and perform clustering
            mcl.build_graph_from_lidar(lidar_data['lidar'])
            clusters = mcl.perform_clustering()
            estimated_position = mcl.get_estimated_position(clusters)
            print(f"Estimated position: {estimated_position}")

             # Visualize localization and save to file
            output_path = "./output/localization_visualization.png"
            mcl.visualize_localization(clusters, output_path=output_path)
            print(f"Localization visualization saved to {output_path}")

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