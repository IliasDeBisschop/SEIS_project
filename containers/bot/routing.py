from enum import Enum, auto
import requests
import time
import threading

class BotState(Enum):
    GET_TASK = auto()
    POSITION_IN_ROW = auto()
    TURN_VERTICAL = auto()
    POSITION_IN_COLOM = auto()
    PICKUP_ITEM = auto()
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

class BotStateMachine:
    def __init__(self):
        self.state = BotState.GET_TASK
        self.previous_state = None
        self.pickup_timer = None
        self.timer_expired = False

    def transition_to(self, new_state):
        if not isinstance(new_state, BotState):
            raise ValueError("Invalid state")
        print(f"Transitioning from {self.state.name} to {new_state.name}")
        self.state = new_state

    def handle_event(self, event, bot_coordinates=None, angle=None):
        """
        Handle events by calling the appropriate state-specific function based on the current state.
        """

        global wait_end_time

        # Check if the bot is still waiting
        if time.time() < wait_end_time:
            print("Still waiting...")
            return (0, 0)  # Stop movement while waiting

        if self.state == BotState.GET_TASK:
            return self.get_task()
        elif self.state == BotState.POSITION_IN_ROW:
            return self.position_in_row(bot_coordinates=bot_coordinates)
        elif self.state == BotState.POSITION_IN_COLOM:
            return self.position_in_colom(bot_coordinates=bot_coordinates)
        elif self.state == BotState.PICKUP_ITEM:
            return self.pickup_item()
        elif self.state == BotState.RETURNING_TO_COLOM:
            return self.returning_to_colom(bot_coordinates=bot_coordinates)
        elif self.state == BotState.RETURNING_TO_STATION:
            return self.returning_to_station(bot_coordinates=bot_coordinates)
        elif self.state == BotState.WAITING:
            return self.wait(BotState.WAITING)
        elif self.state == BotState.RESOLVING_CONFLICT:
            return self.resolving_conflict()
        elif self.state == BotState.TURN_VERTICAL:
            return self.turn_vertical(bot_coordinates=bot_coordinates, angle=angle)
        elif self.state == BotState.TURN_HORIZONTAL:
            return self.turn_horizontal(bot_coordinates=bot_coordinates, angle=angle)
        elif self.state == BotState.WAITING_FROM_WEBAPP:
            return (0,0)
        else:
            print(f"No action defined for state {self.state.name}")
            return (0, 0)  # Default motor speeds (stop)

    def get_task(self):
        global task
        BOT_ID = "bot1"  # Unique ID of the bot
        SERVER_URL = "http://server:5000"  # Server URL

        # If there is no task, request a new one from the server
        if task is None:
            response = requests.get(f"{SERVER_URL}/bot/{BOT_ID}/get_task")
            if response.status_code == 200:
                task = response.json().get("task")
                print(f"New task assigned: {task}")
                self.transition_to(BotState.POSITION_IN_ROW)
                return (max_speed, max_speed)  
            else:
                print("Failed to get task.")
                return (0, 0)  

        # If there is a task, complete it and request a new one
        response = requests.post(f"{SERVER_URL}/bot/{BOT_ID}/complete_task")
        if response.status_code == 200:
            print("Task completed successfully.")
            response = requests.get(f"{SERVER_URL}/bot/{BOT_ID}/get_task")
            if response.status_code == 200:
                task = response.json().get("task")
                print(f"New task assigned: {task}")
                self.transition_to(BotState.POSITION_IN_ROW)
                return (max_speed, max_speed)
            else:
                print("Failed to get new task.")
        else:
            print("Failed to complete task.")

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

        print(f"Desired angle: {desired_angle}, Current angle: {angle}")
        
        if abs(desired_angle-angle)<=treshold_angle:
            print("Turned to the correct angle.")
            self.transition_to(BotState.POSITION_IN_COLOM)
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
            print("distance is", (task["y"]-bot_coordinates[1]))
            if abs(task["y"]-bot_coordinates[1]) > 0.05:
                return (-max_speed, -max_speed)
            return (-0.5, -0.5)
        
        if abs(task["y"]-bot_coordinates[1]) > 0.05:
            print("distance is", (task["y"]-bot_coordinates[1]))

            return (max_speed, max_speed)
        return (0.5, 0.5)


    def pickup_item(self):
        print("Picking up item...")
        return self.wait(BotState.RETURNING_TO_COLOM)

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
            print("distance is", (task["end_y"]-bot_coordinates[1]))
            if abs(task["end_y"]-bot_coordinates[1]) > 0.05:
                return (-max_speed, -max_speed)
            return (-0.5, -0.5)
        
        if abs(task["end_y"]-bot_coordinates[1]) > 0.05:
            print("distance is", (task["end_y"]-bot_coordinates[1]))

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
            self.previous_state = self.state 
            self.state = BotState.WAITING_FROM_WEBAPP
        else:
            self.state = self.previous_state
            self.previous_state = None


# Example usage
if __name__ == "__main__":
    bot = BotStateMachine()