import asyncio
import websockets
import json
import sys
import requests  # Import requests for HTTP communication
from localization import GPSLocalization
# from routing import BotStateMachine  

task = None  


async def handle_connection(websocket, path):
    print("Bot connected.")
    # Initialize the GPS localization system
    gps_localization = GPSLocalization("image_low_pixels.png")
    # bot_state_machine = BotStateMachine()  # Initialize the bot state machine

    global task  # Zorg ervoor dat de globale task-variabele wordt gebruikt

    try:
        while True:
            # Receive data from the bot
            data = await websocket.recv()
            data = json.loads(data)

            # Extract angle and coordinates
            angle = gps_localization.angle_calculator(data)
            x, y = gps_localization.calculate_coordinates(data)
            print(f"Coordinates: ({x}, {y}), Angle: {angle}")
            gps_localization.visualize_localization(data)  
            # Handle the event and get motor commands

            # motor_commands = bot_state_machine.handle_event(
            #     event="start",  # Example event; replace with actual event logic
            #     bot_coordinates=(x, y),
            #     task=task,  # Replace with actual task if available
            #     angle=angle
            # )

            motor_commands = [6.67, 6.67]  

            # Send motor commands back to the bot
            motor_commands_json = {
                "left_speed": motor_commands[0],
                "right_speed": motor_commands[1]
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