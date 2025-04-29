from controller import Robot
import websocket
import time
import json

# Initialize the Webots robot
robot = Robot()
timestep = int(robot.getBasicTimeStep())

# Initialize devices
gps = robot.getDevice("gps")  # GPS sensor
gps.enable(timestep)


compas = robot.getDevice("compass")  # Compass sensor
compas.enable(timestep)

left_motor = robot.getDevice("left wheel motor")
right_motor = robot.getDevice("right wheel motor")
left_motor.setPosition(float('inf'))
right_motor.setPosition(float('inf'))

# WebSocket configuration
WS_URL = "ws://127.0.0.1:5001"  # WebSocket server address

def connect_to_container():
    """Establish a WebSocket connection to the container."""
    while True:
        try:
            ws = websocket.create_connection(WS_URL)
            print(f"Connected to container at {WS_URL}")
            return ws
        except Exception as e:
            print(f"Error connecting to container: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)

while True:
    ws = connect_to_container()
    try:
        while robot.step(timestep) != -1:
            # Read GPS data
            gps_values = gps.getValues()
            compass_values = compas.getValues()
            data = {
                "gps": {"x": gps_values[0], "y": gps_values[1], "z": gps_values[2]},
                "compass": {"x": compass_values[0], "y": compass_values[1], "z": compass_values[2]}
            }
            # Send GPS data to the container
            try:
                # Serialize the GPS data as JSON
                data_json = json.dumps(data)
                ws.send(data_json)
            except Exception as e:
                print(f"Error sending data to container: {e}")
                break

            # Receive motor commands from the container
            try:
                motor_data = ws.recv()
                if not motor_data:
                    print("Connection to container lost.")
                    break

                # Deserialize motor commands
                motor_commands = json.loads(motor_data)
                left_speed = motor_commands["left_speed"]
                right_speed = motor_commands["right_speed"]

                # Apply motor speeds
                left_motor.setVelocity(left_speed)
                right_motor.setVelocity(right_speed)
            except Exception as e:
                print(f"Error receiving motor commands: {e}")
                break
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        ws.close()
        print("WebSocket closed. Reconnecting...")