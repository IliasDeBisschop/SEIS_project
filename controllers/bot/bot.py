from controller import Robot
import struct
import websocket
import time
import json

# Initialize the Webots robot
robot = Robot()
timestep = int(robot.getBasicTimeStep())

# Initialize devices
lds = robot.getDevice("LDS-01")  # LiDAR sensor
lds.enable(timestep)

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
            # Read LiDAR data
            range_image = [value if value != float('inf') else 10.0 for value in lds.getRangeImage()]

            # Send LiDAR data to the container
            try:
                # Serialize the LiDAR data as JSON
                lidar_data = json.dumps({"lidar": range_image})
                ws.send(lidar_data)
                print(f"Sent LiDAR data: {range_image}")
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