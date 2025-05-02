import asyncio
import websockets
import json
import sys
import requests  # Import requests for HTTP communication
from localization import GPSLocalization
from routing import BotStateMachine
from flask import Flask, request, jsonify
import threading
from flask_cors import CORS  # Import CORS


task = None  
gps_localization = GPSLocalization()
bot_state_machine = BotStateMachine()
iteration = 0  
stuck_counter = 0  # Counter for stuck detection

app = Flask(__name__)
CORS(app)  # Sta alle origins toe

@app.route("/control", methods=["POST"])
def control_robot():
    bot_state_machine.webAppControl()
    return jsonify({"message": "Control command received."})

@app.route("/coordinates", methods=["GET"])
def get_coordinates():
    """Return the current coordinates of the robot."""
    # Hier kun je de logica toevoegen om de huidige coördinaten van de robot te berekenen
    x, y = gps_localization.getCoordinates()
    return jsonify({"x": x, "y": y})

async def handle_connection(websocket, path):
    print("Bot connected.")
    # Initialize the GPS localization system
     
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

            # Handle the event and get motor commands
            motor_commands = bot_state_machine.handle_event(
                event="start",  # Example event; replace with actual event logic
                bot_coordinates=(x, y),
                angle=angle,
                lidar_data=data["lidar"]  # Assuming lidar_data is part of the received data
            )
            global stuck_counter
            # Check motor speeds and lidar data
            if stuck_counter == -1:
                motor_commands = [0, 0]
            elif motor_commands[0] < 0 and motor_commands[1] < 0:
                print(data["lidar"][0])
                if data["lidar"][0] < 0.2:
                    motor_commands = [0,0]
                    stuck_counter += 1
                else:
                    stuck_counter = 0
 
            elif motor_commands[0] > 0 and motor_commands[1] > 0:
                middle_index = len(data["lidar"]) // 2
                print(data["lidar"][middle_index])
                if data["lidar"][middle_index] < 0.2:
                    motor_commands = [0,0]
                    stuck_counter += 1  
                else:
                    stuck_counter = 0
            if stuck_counter > 100:
                print("Stuck detected!")
                stuck_counter = 0
                succes =bot_state_machine.bot_stuck()
                if succes:
                    stuck_counter = -1
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