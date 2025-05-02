from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import random
import threading
import time

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])  # Enable CORS for all origins

ROWS = 20  # Example: Total number of rows
COLUMNS = 6  # Example: Total number of columns
INTERVAL = 10  # Example: Frequency of task generation in seconds
MAX_TASKS = 3  # Maximum number of tasks to generate per interval
max_tasks = 20  # Maximum number of tasks in que

bot_tasks = {
    "bot1": None,
    "bot2": None,
    "bot3": None,
}
bot_hall_cordinates = {
    "bot1": (0.25, 5.1),
    "bot2": (0.25, 4.5),
    "bot3": (0.25, 3.9),
}

# Global list to store tasks
tasks = []

# Define the bot endpoints
BOT_ENDPOINTS = {
    "bot1": "http://bot1:5000",
    "bot2": "http://bot2:5000",
    "bot3": "http://bot3:5000",
}
def getWorldCoordinates(row, column):
    """Convert (row, column) to world coordinates."""
    x,y = (7.5/2)-2.1+0.6*(row%10), -4.2+ (9/2) + 0.6*column
    if row >= 10:
        y += 5
    return (x,y)



def generate_random_task():
    """Generate a random (row, column) tuple."""
    row = random.randint(0, ROWS - 1)
    column = random.randint(0, COLUMNS - 1)
    return (row, column)

def generate_tasks_at_interval():
    """Generate a random number of tasks at a specified interval."""
    global tasks
    while True:
        if len(tasks) >= max_tasks:  # Check if the queue has reached the maximum limit
            print(f"Task queue is full ({len(tasks)} tasks). No new tasks generated.")
        else:
            num_tasks = random.randint(0, MAX_TASKS)  # Random number of tasks
            if num_tasks > max_tasks - len(tasks):
                num_tasks = max_tasks - len(tasks)
            new_tasks = [generate_random_task() for _ in range(num_tasks)]
            tasks.extend(new_tasks)
            print(f"Generated {num_tasks} tasks: {new_tasks}")
            print(f"Current tasks: {tasks}")
        time.sleep(INTERVAL)  # Wait for the next interval

# Map container IP addresses to container names
CONTAINER_IP_MAP = {
    "172.18.0.2": "bot1",
    "172.18.0.3": "bot2",
    "172.18.0.4": "bot3",
}
@app.route("/bot/<bot_id>/get_bot_task", methods=["GET"])
def get_bot_task(bot_id):
    """Get the current task for a specific bot."""
    if bot_id not in BOT_ENDPOINTS:
        return jsonify({"error": "Invalid bot ID"}), 400

    # Check if the bot has a task assigned
    task = bot_tasks.get(bot_id)
    if task is not None:
        return jsonify({"task": {"row": task[0], "column": task[1]}})
    return jsonify({"error": "No task assigned to this bot"}), 404

@app.route("/bot/get_bot_id", methods=["GET"])
def get_bot_id():
    """Retrieve the bot ID based on the requestor's IP address."""
    client_ip = request.remote_addr
    bot_id = CONTAINER_IP_MAP.get(client_ip, None)

    if bot_id is None:
        return jsonify({"error": "Unknown bot"}), 400

    return jsonify({"bot_id": bot_id})

@app.route("/bot/get_task", methods=["GET"])
def get_task():
    """Assign the oldest task to a bot based on the requestor's IP address."""
    global tasks, bot_tasks

    # Get the IP address of the requesting container
    client_ip = request.remote_addr
    bot_id = CONTAINER_IP_MAP.get(client_ip, None)

    if bot_id is None:
        return jsonify({"error": "Unknown bot"}), 400

    print(f"Task request from bot: {bot_id} (IP: {client_ip})")

    # First, try to find a task in a row where no other bot is working
    for task in tasks:
        row, column = task
        if all(assigned_task is None or assigned_task[0]%10 != row%10 for assigned_task in bot_tasks.values()):  # Check if the row is free
            # Assign the task to the bot
            bot_tasks[bot_id] = task
            tasks.remove(task)  # Remove the task from the list
            x_cord, y_cord = getWorldCoordinates(row, column)
            print(f"##### Bot {bot_id} assigned to task at row {row}, column {column} (world coordinates: {x_cord}, {y_cord})")
            return jsonify({"task": {"x": x_cord, "y": y_cord, "end_x": bot_hall_cordinates[bot_id][0], "end_y": bot_hall_cordinates[bot_id][1]}})

    # If no free rows are available, assign the oldest task regardless of row
    if tasks:
        task = tasks.pop(0)  # Get and remove the oldest task
        row, column = task
        bot_tasks[bot_id] = task  # Assign the full task to the bot
        x_cord, y_cord = getWorldCoordinates(row, column)
        return jsonify({"task": {"x": x_cord, "y": y_cord, "end_x": bot_hall_cordinates[bot_id][0], "end_y": bot_hall_cordinates[bot_id][1]}})

    # If no tasks are available at all, return an error
    return jsonify({"error": "No available tasks"}), 404

@app.route("/bot/<bot_id>/complete_task", methods=["POST"])
def complete_task(bot_id):
    """Mark a task as completed and free up the bot's task."""
    global bot_tasks

    if bot_id not in BOT_ENDPOINTS:
        print(f"Invalid bot ID: {bot_id}")
        return jsonify({"error": "Invalid bot ID"}), 400

    # Free up the task for the bot
    bot_tasks[bot_id] = None
    print(f"Bot {bot_id} has completed its task.")
    return jsonify({"message": f"Bot {bot_id} has completed its task and is now free."})

@app.route("/tasks", methods=["GET"])
def get_all_tasks():
    """Return a list of all tasks."""
    global tasks
    formatted_tasks = []
    # Include tasks currently assigned to bots
    for bot_id, task in bot_tasks.items():
        if task is not None:
            formatted_tasks.append({
                "id": f"{bot_id}_task",
                "row": task[0],
                "column": task[1],
                "status": "In Progress"
            })
    # Format tasks as a list of dictionaries with IDs, rows, columns, and statuses
    formatted_tasks.extend([
        {"id": index + 1, "row": task[0], "column": task[1], "status": "Pending"}
        for index, task in enumerate(tasks)
    ])
    return jsonify(formatted_tasks)

@app.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    """Delete a task by its ID."""
    global tasks, bot_tasks

    # Controleer of de taak-ID verwijst naar een taak die aan een bot is toegewezen
    for bot_id, task in bot_tasks.items():
        if task is not None and f"{bot_id}_task" == task_id:
            bot_tasks[bot_id] = None  # Maak de taak vrij
            return jsonify({"message": f"Task {task_id} assigned to {bot_id} has been deleted."}), 200

    # Controleer of de taak-ID verwijst naar een taak in de wachtrij
    try:
        task_index = int(task_id) - 1  # Converteer taak-ID naar index
        if 0 <= task_index < len(tasks):
            deleted_task = tasks.pop(task_index)
            return jsonify({"message": f"Task {task_id} at row {deleted_task[0]}, column {deleted_task[1]} has been deleted."}), 200
    except ValueError:
        pass  # Ongeldige taak-ID

    return jsonify({"error": "Task not found"}), 404

@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    """Update a task's row and column."""
    global tasks

    if 0 <= task_id - 1 < len(tasks):
        task = tasks[task_id - 1]
        data = request.json
        row = data.get("row")
        column = data.get("column")

        # Controleer of row en column geldig zijn
        if row is not None and column is not None:
            row = int(row)
            column = int(column)
            if 0 <= row < ROWS and 0 <= column < COLUMNS:
                tasks[task_id - 1] = (row, column)  # Update row en column
                return jsonify({"message": f"Task {task_id} has been updated."}), 200
            return jsonify({"error": "Row or column out of bounds"}), 400
        return jsonify({"error": "Invalid data"}), 400
    return jsonify({"error": "Task not found"}), 404

@app.route("/tasks", methods=["POST"])
def create_task():
    """Create a new task with specified row and column."""
    global tasks

    data = request.json
    row = data.get("row")
    column = data.get("column")

    # Controleer of row en column geldig zijn
    if row is not None and column is not None:
        row = int(row)
        column = int(column)
        if 0 <= row < ROWS and 0 <= column < COLUMNS:
            tasks.append((row, column))  # Voeg de nieuwe taak toe
            return jsonify({"message": f"Task at row {row}, column {column} has been created."}), 201
        return jsonify({"error": "Row or column out of bounds"}), 400
    return jsonify({"error": "Invalid data"}), 400

@app.route("/")
def home():
    return "Server is running and connected to bots!"

@app.route("/bot/<bot_id>/control", methods=["POST"])
def control_bot(bot_id):
    if bot_id not in BOT_ENDPOINTS:
        return jsonify({"error": "Invalid bot ID"}), 400

    # Forward the control command to the specified bot
    bot_url = BOT_ENDPOINTS[bot_id]
    try:
        response = requests.post(f"{bot_url}/control", json=request.json)
        return jsonify({"bot_response": response.json()})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Start the task generation in a separate thread
    task_thread = threading.Thread(target=generate_tasks_at_interval, daemon=True)
    task_thread.start()
    app.run(host="0.0.0.0", port=5000)