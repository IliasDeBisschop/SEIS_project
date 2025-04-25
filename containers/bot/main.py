import asyncio
import websockets
import json
from localization import MarkovClusteringLocalization
import matplotlib.pyplot as plt


async def handle_connection(websocket, path):
    print("Bot connected.")
    # Initialize the localization system
    mcl = MarkovClusteringLocalization("output_image_processed.jpg")

    async def visualize_task(clusters):
        """Run the visualization in a separate asyncio task."""
        # Voorbeeld: Maak een eenvoudige plot
        plt.figure()
        plt.scatter([c[0] for c in clusters], [c[1] for c in clusters])
        plt.title("Localization Clusters")
        plt.savefig("/output/visualization.png")  # Opslaan in een gedeeld volume
        plt.close()
    try:
        while True:
            # Receive LiDAR data from the bot
            lidar_data = await websocket.recv()
            lidar_data = json.loads(lidar_data)
            print(f"Received LiDAR data: {lidar_data['lidar']}")

            # Build graph and perform clustering
            mcl.build_graph_from_lidar(lidar_data['lidar'])
            clusters = mcl.perform_clustering()
            estimated_position = mcl.get_estimated_position(clusters)
            print(f"Estimated position: {estimated_position}")

            # Visualize localization in a separate task
            visualize_task(clusters)

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