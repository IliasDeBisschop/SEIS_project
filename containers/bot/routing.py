from enum import Enum, auto
import requests
import time
import threading
from lidar import LidarProcessor

class BotState(Enum):
    GET_TASK = auto()
    POSITION_IN_ROW = auto()
    TURN_VERTICAL = auto()
    CHECKING_TRAFFIC1 = auto()
    POSITION_IN_COLOM = auto()
    PICKUP_ITEM = auto()
    RETURN_HALL = auto()
    CHECKING_TRAFFIC2 = auto()
    RETURNING_TO_COLOM = auto()
    TURN_HORIZONTAL = auto()
    RETURNING_TO_STATION = auto()
    WAITING = auto()
    RESOLVING_CONFLICT = auto()
    WAITING_FROM_WEBAPP = auto()

theshold = 0.005  
task = None  # Global variable to store the task
Collected= False
treshold_angle = 0.1  # Angle threshold for turning
wait_end_time = 0
max_speed = 6.67  # Maximum speed of the bot in cm/s
max_turn_speed = 5  # Maximum turning speed in rad/s
first_lidar_data = None  # Placeholder for the first LiDAR data
LidarProcessor = LidarProcessor(max_distance=10.0)  # Initialize the LidarProcessor
start_top_shelfs = 5.35  # Starting point for top shelves
start_bottom_shelfs = 3.65  # Starting point for bottom shelves
bot_id = None  # Placeholder for bot ID

class BotStateMachine:
    def __init__(self):
        self.state = BotState.GET_TASK
        self.previous_state = None
        self.bot_id = None  # Initialize bot_id
        self.register_bot()  # Register the bot with the server

    def register_bot(self):
        """Register the bot with the server and get a unique ID."""
        SERVER_URL = "http://server:5000"  # Server URL
        response = requests.post(f"{SERVER_URL}/bot/register")
        if response.status_code == 200:
            self.bot_id = response.json().get("bot_id")
            print(f"Bot registered with ID: {self.bot_id}")
        else:
            print("Failed to register bot.")
            raise Exception("Bot registration failed.")
        

    def bot_stuck(self):
        SERVER_URL = "http://server:5000"  # Server URL
        response = requests.post(f"{SERVER_URL}/bot/stuck", json={"bot_id": self.bot_id})
        if response.status_code == 200:
            print(f"confirmed stuck")
            return 1
        else:
            print("Failed to stuck")
            return 0

        
    def transition_to(self, new_state):
        if not isinstance(new_state, BotState):
            raise ValueError("Invalid state")
        print(f"Transitioning from {self.state} to {new_state}")
        self.state = new_state

    def handle_event(self, event, bot_coordinates=None, angle=None, lidar_data=None):
        """
        Handle events by calling the appropriate state-specific function based on the current state.
        """
        global wait_end_time
    
        # Check if the bot is still waiting
        if time.time() < wait_end_time:
            print("Still waiting...")
            return (0, 0)  # Stop movement while waiting
    
        # Define a dictionary mapping states to their corresponding methods
        state_actions = {
            BotState.GET_TASK: lambda: self.get_task(),
            BotState.POSITION_IN_ROW: lambda: self.position_in_row(bot_coordinates=bot_coordinates),
            BotState.POSITION_IN_COLOM: lambda: self.position_in_colom(bot_coordinates=bot_coordinates),
            BotState.PICKUP_ITEM: lambda: self.pickup_item(),
            BotState.RETURNING_TO_COLOM: lambda: self.returning_to_colom(bot_coordinates=bot_coordinates),
            BotState.RETURNING_TO_STATION: lambda: self.returning_to_station(bot_coordinates=bot_coordinates),
            BotState.WAITING: lambda: self.wait(BotState.WAITING),
            BotState.RESOLVING_CONFLICT: lambda: self.resolving_conflict(),
            BotState.TURN_VERTICAL: lambda: self.turn_vertical(bot_coordinates=bot_coordinates, angle=angle),
            BotState.TURN_HORIZONTAL: lambda: self.turn_horizontal(bot_coordinates=bot_coordinates, angle=angle),
            BotState.CHECKING_TRAFFIC1: lambda: self.check_for_traffic(bot_coordinates=bot_coordinates, lidar_data=lidar_data),
            BotState.CHECKING_TRAFFIC2: lambda: self.check_for_traffic(bot_coordinates=bot_coordinates, lidar_data=lidar_data),
            BotState.RETURN_HALL: lambda: self.return_hall(bot_coordinates=bot_coordinates),
            BotState.WAITING_FROM_WEBAPP: lambda: (0, 0)  # Stop the bot while waiting for web app command
        }
    
        # Call the appropriate function based on the current state
        action = state_actions.get(self.state, lambda: self.default_action())
        return action()
    
    def default_action(self):
        """
        Default action for undefined states.
        """
        print(f"No action defined for state {self.state.name}")
        return (0, 0)  # Default motor speeds (stop)

    def get_task(self):
        global task
        SERVER_URL = "http://server:5000"  # Server URL

        # Request a new task from the server
        if task is None:
            response = requests.get(f"{SERVER_URL}/bot/get_task", params={"bot_id": self.bot_id})
            print(f"Debug: Server response: {response.status_code}, {response.text}")
            if response.status_code == 200:
                task = response.json().get("task")
                print(f"New task assigned: {task}")
                self.transition_to(BotState.POSITION_IN_ROW)
                return (max_speed, max_speed)
            else:
                print("Failed to get task.")
                return (0, 0)

        # If there is a task, complete it and request a new one
        response = requests.post(f"{SERVER_URL}/bot/{self.bot_id}/complete_task")
        if response.status_code == 200:
            print("Task completed successfully.")
            response = requests.get(f"{SERVER_URL}/bot/get_task", params={"bot_id": self.bot_id})
            if response.status_code == 200:
                task = response.json().get("task")
                print(f"New task assigned: {task}")
                self.transition_to(BotState.POSITION_IN_ROW)
                return (max_speed, max_speed)
            else:
                print("Failed to get new task.")
        else:
            print("Failed to complete task.")

        return (0, 0)  # Stop motors if task retrieval fails

    def position_in_row(self, bot_coordinates=None):
        global task
        if task is None or bot_coordinates is None:
            print("Error: Task or bot coordinates are None.")
            return (0, 0)  # Stop the bot if data is missing

        # Check if the bot has reached the correct row
        if abs(task["x"] - bot_coordinates[0]) <= theshold:
            print("Reached the correct row.")
            self.transition_to(BotState.TURN_VERTICAL)
            return (0, 0)  # Stop motors
        elif task["x"] > bot_coordinates[0]:
            return (max_speed, max_speed)  # Forward motor speeds
        else:
            return (-max_speed, -max_speed)  # Backward motor speeds
        
    def turn_vertical(self, bot_coordinates=None, angle=None):
        global task


        if task is None or bot_coordinates is None:
            print("Error: Task or bot coordinates are None.")
            return (0, 0)
        desired_angle = 90  # Desired angle for vertical position

        
        if abs(desired_angle-angle)<=treshold_angle:
            print("Turned to the correct angle.")
            self.transition_to(BotState.CHECKING_TRAFFIC1)
            return (0, 0)
        elif desired_angle>angle:
            return (-max_turn_speed, max_turn_speed)
        else:
            return (0.05, -0.05)

    def position_in_colom(self, bot_coordinates=None):
        global task
        if task is None or bot_coordinates is None:
            print("Error: Task or bot coordinates are None.")
            return (0, 0)  # Stop the bot if data is missing

        # Check if the bot has reached the correct row
        if abs(task["y"] - bot_coordinates[1]) <= theshold:
            print("Reached the correct row.")
            self.transition_to(BotState.PICKUP_ITEM)
            return (0, 0)  # Stop motors
        elif (task["y"] <  bot_coordinates[1]):
            if abs(task["y"]-bot_coordinates[1]) > 0.05:
                return (-max_speed, -max_speed)
            return (-0.5, -0.5)
        
        if abs(task["y"]-bot_coordinates[1]) > 0.05:

            return (max_speed, max_speed)
        return (0.5, 0.5)


    def pickup_item(self):
        print("Picking up item...")
        return self.wait(BotState.RETURN_HALL)
    

    def return_hall(self, bot_coordinates=None):
        global task
        if task is None or bot_coordinates is None:
            print("Error: Task or bot coordinates are None.")
            return (0, 0)  # Stop the bot if data is missing
        
        go_to_y = 0
        if bot_coordinates[1] >4.5:
            go_to_y = start_top_shelfs
        else:
            go_to_y = start_bottom_shelfs

        if abs(go_to_y - bot_coordinates[1]) <= theshold:
            print("Reached the correct row.")
            self.transition_to(BotState.CHECKING_TRAFFIC2)
            return (0, 0)  # Stop motors
        elif (go_to_y <  bot_coordinates[1]):
            print("distance is", (go_to_y-bot_coordinates[1]))
            if abs(go_to_y-bot_coordinates[1]) > 0.05:
                return (-max_speed, -max_speed)
            return (-0.5, -0.5)
        
        if abs(go_to_y-bot_coordinates[1]) > 0.05:
            print("distance is", (go_to_y-bot_coordinates[1]))

            return (max_speed, max_speed)
        return (0.5, 0.5)

    def returning_to_colom(self, bot_coordinates=None):
        global task
        if task is None or bot_coordinates is None:
            print("Error: Task or bot coordinates are None.")
            return (0, 0)  # Stop the bot if data is missing

        if abs(task["end_y"] - bot_coordinates[1]) <= theshold:
            print("Reached the correct row.")
            self.transition_to(BotState.TURN_HORIZONTAL)
            return (0, 0)  # Stop motors
        elif (task["end_y"] <  bot_coordinates[1]):
            if abs(task["end_y"]-bot_coordinates[1]) > 0.05:
                return (-max_speed, -max_speed)
            return (-0.5, -0.5)
        
        if abs(task["end_y"]-bot_coordinates[1]) > 0.05:

            return (max_speed, max_speed)
        return (0.5, 0.5)
        

    def turn_horizontal(self, bot_coordinates=None, angle=None):
        desired_angle = 0

        print(f"Desired angle: {desired_angle}, Current angle: {angle}")
        
        if abs(desired_angle-angle)<=treshold_angle:
            print("Turned to the correct angle.")
            self.transition_to(BotState.RETURNING_TO_STATION)
            return (0, 0)
        elif desired_angle<angle:
            return (max_turn_speed, -max_turn_speed)
        else:
            return (-0.05, 0.05)


    def returning_to_station(self, bot_coordinates=None):
        global task
        if task is None or bot_coordinates is None:
            print("Error: Task or bot coordinates are None.")
            return (0, 0)  # Stop the bot if data is missing

        if abs(task["end_x"] - bot_coordinates[0]) <= theshold:
            print("Returned to the station.")
            return self.wait(BotState.GET_TASK)
        elif bot_coordinates[0] > task["end_x"]:
            print("Returning to the station...")
            return (-max_speed, -max_speed)
        else:
            return (1, 1)  # Backward motor speeds

    def resolving_conflict(self):
        print("Resolving conflict...")
        return (0, 0)  # Stop the bot while resolving conflict

    def wait(self, state, waitTime=2):
        """
        Wait for a specified amount of time before transitioning to the next state.
        """
        global wait_end_time

        # Set the end time for waiting
        wait_end_time = time.time() + waitTime
        print(f"Waiting for {waitTime} seconds...")
        self.transition_to(state)
        return (0, 0)  # Stop movement while waiting

    def webAppControl(self):
        if self.previous_state is None:
            print("waiting for webapp")
            self.previous_state = self.state 
            self.transition_to(BotState.WAITING_FROM_WEBAPP)
        else:
            self.transition_to(self.previous_state)
            self.previous_state = None



    def check_for_traffic(self,bot_coordinates, lidar_data=None):
        global first_lidar_data

        if lidar_data is None:
            print("Debug: No LiDAR data provided.")
            return (0, 0)

        if first_lidar_data is None:
            print("Debug: Storing initial LiDAR data.")
            first_lidar_data = lidar_data
            return self.wait(self.state, waitTime=0.5)  # Wait for 0.5 seconds before the next scan 


        if self.state == BotState.CHECKING_TRAFFIC1:
            if bot_coordinates[1] > task["y"]:
                driving_forward = False
            else:
                driving_forward = True
        else:
            if bot_coordinates[1] > task["end_y"]:
                driving_forward = False
            else:
                driving_forward = True


        print("Debug: Checking if object is getting closer.")
        if LidarProcessor.is_object_getting_closer(first_lidar_data, lidar_data, direction_is_front=driving_forward):
            print("Debug: Object detected in front, stopping the bot.")
            first_lidar_data = lidar_data  # Update the first LiDAR data
            return self.wait(self.state, waitTime=0.5)
        else:
            print("Debug: No object detected, continuing.")
            if self.state == BotState.CHECKING_TRAFFIC1:
                print("Debug: Transitioning to POSITION_IN_COLOM.")
                self.transition_to(BotState.POSITION_IN_COLOM)
            else:
                print("Debug: Transitioning to RETURNING_TO_COLOM.")
                self.transition_to(BotState.RETURNING_TO_COLOM)
            return (0, 0)
        
    
# Example usage
if __name__ == "__main__":
    bot = BotStateMachine()