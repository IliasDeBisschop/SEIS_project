import asyncio
import websockets
import json
import sys
import requests  # Import requests for HTTP communication
from localization import GPSLocalization

task = None  

BOT_ID = "bot1"  # Unieke ID van de bot
SERVER_URL = "http://server:5000"  # URL van de server

async def handle_connection(websocket, path):
    print("Bot connected.")
    # Initialize the GPS localization system
    gps_localization = GPSLocalization("image_low_pixels.png")

    global task  # Zorg ervoor dat de globale task-variabele wordt gebruikt

    try:
        while True:
            if task is None:
                # Vraag een nieuwe taak aan bij de server
                response = requests.get(f"{SERVER_URL}/bot/{BOT_ID}/get_task")
                if response.status_code == 200:
                    task = response.json().get("task")
                    print(f"Nieuwe taak ontvangen: {task}")
                else:
                    print(f"Geen taak beschikbaar: {response.json().get('error')}")
                    await asyncio.sleep(5)  # Wacht even voordat je opnieuw probeert
                    continue
                        
            sys.stdout.flush()

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