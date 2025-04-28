import asyncio
import websockets
import json
import sys
from localization import GPSLocalization


async def handle_connection(websocket, path):
    print("Bot connected.")
    # Initialize the GPS localization system
    gps_localization = GPSLocalization("image_low_pixels.png")

    try:
        while True:
            # Receive GPS data from the bot
            gps_data = await websocket.recv()
            gps_data = json.loads(gps_data)
            print(f"Received GPS data: {gps_data}")
            sys.stdout.flush()

            # Visualize localization and save to file
            localization_output_path = "./output/localization_visualization.png"
            gps_localization.visualize_localization(gps_data, output_path=localization_output_path)
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
print("WebSocket server created on ws://0.0.0.0:5001")  # Log WebSocket creation

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()