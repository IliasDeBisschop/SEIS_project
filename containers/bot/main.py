import asyncio
import websockets
import json
import sys
import requests  # Import requests for HTTP communication
from localization import GPSLocalization
from routing import BotStateMachine
from flask import Flask, request, jsonify
import threading
from concurrent.futures import ThreadPoolExecutor  # Import ThreadPoolExecutor
from flask_cors import CORS  # Import CORS

task = None  
bot_state_machine = BotStateMachine()
iteration = 0  

app = Flask(__name__)
CORS(app)  # Sta alle origins toe

@app.route("/control", methods=["POST"])
def control_robot():
    bot_state_machine.webAppControl()
    return jsonify({"message": "Control command received."})

# ThreadPoolExecutor for running visualization in a separate thread
executor = ThreadPoolExecutor(max_workers=1)

async def handle_connection(websocket, path):
    print("Bot connected.")
    # Initialize the GPS localization system
    gps_localization = GPSLocalization("image_low_pixels.png")
     
    try:
        while True:
            # Send a ping to keep the connection alive
            await websocket.ping()

            # Receive data from the bot
            data = await websocket.recv()
            data = json.loads(data)

            # Extract angle and coordinates
            angle = gps_localization.angle_calculator(data)
            x, y = gps_localization.calculate_coordinates(data)

            # Run visualization every 5th iteration
            global iteration
            iteration = (iteration + 1) % 5
            if iteration == 0:
                # Use ThreadPoolExecutor to run visualization in a separate thread
                executor.submit(gps_localization.visualize_localization, data)

            # Handle the event and get motor commands
            motor_commands = bot_state_machine.handle_event(
                event="start",  # Example event; replace with actual event logic
                bot_coordinates=(x, y),
                angle=angle,
                lidar_data=data["lidar"]  # Assuming lidar_data is part of the received data
            )

            # Send motor commands back to the bot
            motor_commands_json = {
                "left_speed": motor_commands[0],
                "right_speed": motor_commands[1]
            }
            await websocket.send(json.dumps(motor_commands_json))
    except websockets.ConnectionClosed:
        print("Connection to bot lost.")
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()  # Log the full stack trace


# Start the WebSocket server
start_server = websockets.serve(handle_connection, "0.0.0.0", 5001)
print("WebSocket server created on ws://0.0.0.0:5001")  # Log WebSocket creation

# Run both Flask and WebSocket servers concurrently
async def run_servers():
    # Run the WebSocket server
    await start_server
    # Keep the event loop running
    while True:
        await asyncio.sleep(1)

# Start Flask in a separate thread
def run_flask():
    app.run(host="0.0.0.0", port=5002)

# Run Flask in a separate thread and WebSocket in the event loop
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    asyncio.get_event_loop().run_until_complete(run_servers())