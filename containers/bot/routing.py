from enum import Enum, auto

import requests
import time
import threading

class BotState(Enum):
    GET_TASK = auto()
    POSITION_IN_ROW = auto()
    POSITION_IN_COLOM = auto()
    PICKUP_ITEM = auto()
    RETURNING_TO_COLOM = auto()
    RETURNING_TO_STATION = auto()
    WAITING = auto()
    RESOLVING_CONFLICT = auto()

theshold = 0.005  


class BotStateMachine:
    def __init__(self):
        self.state = BotState.GET_TASK
        self.pickup_timer = None
        self.timer_expired = False

    def transition_to(self, new_state):
        if not isinstance(new_state, BotState):
            raise ValueError("Invalid state")
        print(f"Transitioning from {self.state.name} to {new_state.name}")
        self.state = new_state

    def handle_event(self, event):
        match (self.state, event):
            case (BotState.WAITING, "start"):
                self.transition_to(BotState.POSITION_IN_ROW)
            case (BotState.POSITION_IN_ROW, "reached_row"):
                self.transition_to(BotState.POSITION_IN_COLOM)
            case (BotState.POSITION_IN_COLOM, "pickup"):
                self.transition_to(BotState.PICKUP_ITEM)
            case (BotState.PICKUP_ITEM, "return_to_colom"):
                self.transition_to(BotState.RETURNING_TO_COLOM) 
            case (BotState.RETURNING_TO_COLOM, "return_to_station"):
                self.transition_to(BotState.RETURNING_TO_STATION)
            case (BotState.RETURNING_TO_STATION, "wait"):
                self.transition_to(BotState.WAITING)
            case (_, "conflict"):
                self.transition_to(BotState.RESOLVING_CONFLICT)
            case (BotState.RESOLVING_CONFLICT, "resolved"):
                self.transition_to(BotState.WAITING)
            case _:
                print(f"No transition defined for state {self.state.name} with event '{event}'")

    # Lege functies voor elke state
    def get_task(self, task=None):
        BOT_ID = "bot1"  # Unieke ID van de bot
        SERVER_URL = "http://server:5000"  # URL van de server

        # Als er geen taak is, vraag dan een nieuwe taak aan de server
        if task is None:
            # Vraag een taak aan de server
            response = requests.get(f"{SERVER_URL}/bot/{BOT_ID}/get_task")
            if response.status_code == 200:
                task = response.json().get("task")
                print(f"New task assigned: {task}")
                self.transition_to(BotState.POSITION_IN_ROW)
                return (6.67, 6.67)  
            else:
                print("Failed to get task.")
                return (0, 0)  

        # Als er een taak is, voltooi deze dan en vraag een nieuwe taak aan
        response = requests.post(f"{SERVER_URL}/bot/{BOT_ID}/complete_task")
        if response.status_code == 200:
            print("Task completed successfully.")
            response = requests.get(f"{SERVER_URL}/bot/{BOT_ID}/get_task")
            if response.status_code == 200:
                task = response.json().get("task")
                print(f"New task assigned: {task}")
                self.transition_to(BotState.POSITION_IN_ROW)
                return (6.67, 6.67)
            else:
                print("Failed to get new task.")
        else:
            print("Failed to complete task.")
            
            
        
    def position_in_row(self, task=None, bot_cordinates=None):
        pass
        # vooruit rijden naar de kolom
        if (task[0] - bot_cordinates[0] <= theshold):
            # stop met rijden
            # stuur naar de server dat je in de kolom bent aangekomen
            self.transition_to(BotState.POSITION_IN_COLOM)
            return (0,0) # stop met rijden
        else:
            # nog steeds vooruit rijden
            return (6.67, 6.67)  

    def position_in_colom(self, task=None, bot_cordinates=None):
        pass
        if(task[1] - bot_cordinates[1] <= theshold):
            # stop met rijden
            # stuur naar de server dat je in de kolom bent aangekomen
            self.transition_to(BotState.PICKUP_ITEM)
            return (0,0)
        else:
            # nog steeds vooruit rijden
            return (6.67, 6.67)
        
    def pickup_item(self, task=None, bot_cordinates=None):
        return self.wait(self, BotState.RETURNING_TO_COLOM)
    
    def _timer_expired_callback(self):
        print("Pickup timer expired.")
        self.timer_expired = True

    def returning_to_colom(self, task=None, bot_cordinates=None):
        pass
        
        if(task[3] - bot_cordinates[1] <= theshold):
            # stop met rijden
            # stuur naar de server dat je in de kolom bent aangekomen
            self.transition_to(BotState.RETURNING_TO_STATION)
            return (0,0)
        else:
            # nog steeds vooruit rijden
            return (6.67, 6.67)

    def returning_to_station(self, task=None, bot_cordinates=None):
        pass
        if(task[2] - bot_cordinates[0] <= theshold):
            # stop met rijden
            # stuur naar de server dat je in de kolom bent aangekomen
            self.transition_to(BotState.PICKUP_ITEM)
            return (0,0)
        else:
            # nog steeds vooruit rijden
            return (6.67, 6.67)

    def waiting(self):
        return self.wait(self, BotState.WAITING)

    def resolving_conflict(self):
        pass #eest achteruit rijden wachten tot de andere bot weg is en dan weer vooruit rijden

    def wait(self, state, waitTime=2):
        waitingTime = 2  # seconds
        if self.pickup_timer is None or not self.pickup_timer.is_alive():
            # Start a new timer in a separate thread
            print("Starting item pickup timer...")
            self.timer_expired = False
            self.pickup_timer = threading.Timer(waitingTime, self._timer_expired_callback)
            self.pickup_timer.start()
            return (0, 0)  # Stop movement while waiting for the timer
        elif self.timer_expired:
            # Timer has expired, perform the next action
            print("Item pickup complete. Timer expired.")
            self.timer_expired = False  # Reset the timer state
            self.pickup_timer = None  # Allow the timer to restart
            self.transition_to(state)
            return (0, 0)  # Stop movement after pickup
        else:
            # Timer is still running
            print("Pickup timer is still running...")
            return (0, 0)  # Stop movement while waiting for the timer

# Example usage
if __name__ == "__main__":
    bot = BotStateMachine()
    bot.handle_event("start")
    bot.handle_event("reached_row")
    bot.handle_event("pickup")
    bot.handle_event("return_to_colom")
    bot.handle_event("return_to_station")
    bot.handle_event("wait")
    bot.handle_event("conflict")
    bot.handle_event("resolved")