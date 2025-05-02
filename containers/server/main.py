from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import random
import threading
import time
import logging
import cv2

# Disable Flask's default logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])  # Enable CORS for all origins

ROWS = 20  # Example: Total number of rows
COLUMNS = 6  # Example: Total number of columns
INTERVAL = 10  # Example: Frequency of task generation in seconds
MAX_TASKS = 3  # Maximum number of tasks to generate per interval
max_tasks = 20  # Maximum number of tasks in que
bot_counter = 0


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
    "bot1": "http://bot1:5002",
    "bot2": "http://bot2:5004",
    "bot3": "http://bot3:5006",
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
        elif len(tasks) == 0:
            new_tasks = [generate_random_task() for _ in range(3)]
            tasks.extend(new_tasks)
        else:
            num_tasks = random.randint(0, MAX_TASKS)  # Random number of tasks
            if num_tasks > max_tasks - len(tasks):
                num_tasks = max_tasks - len(tasks)
            new_tasks = [generate_random_task() for _ in range(num_tasks)]
            tasks.extend(new_tasks)
        time.sleep(INTERVAL)  # Wait for the next interval

# Map container ports to bot names
CONTAINER_PORT_MAP = {
    "5001": "bot1",
    "5002": "bot2",
    "5003": "bot3",
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

@app.route("/bot/register", methods=["POST"])
def register_bot():
    """Register a new bot and assign a unique ID."""
    global bot_tasks, bot_counter

    # Increment the bot counter to generate a new bot ID
    bot_counter += 1
    bot_id = f"bot{bot_counter}"

    # Register the new bot
    bot_tasks[bot_id] = None  # Initialize the bot's row as None

    print(f"Registered new bot: {bot_id}")
    return jsonify({"bot_id": bot_id})

@app.route("/bot/get_task", methods=["GET"])
def get_task():
    """Assign the oldest task to a bot based on its bot_id."""
    global tasks, bot_tasks
    # Extract the bot_id from the query parameters
    bot_id = request.args.get("bot_id")
    if not bot_id or bot_id not in bot_tasks:
        print(f"Error: Unknown bot ID: {bot_id}")
        return jsonify({"error": f"Unknown bot ID: {bot_id}"}), 400

    print(f"Task request from bot: {bot_id}")

    # Probeer een taak toe te wijzen
    for task in tasks:
        row, column = task
        if all(assigned_task is None or assigned_task[0] % 10 != row % 10 for assigned_task in bot_tasks.values()):
            bot_tasks[bot_id] = task
            tasks.remove(task)
            x_cord, y_cord = getWorldCoordinates(row, column)
            print(f"##### Bot {bot_id} assigned to task at row {row}, column {column} (world coordinates: {x_cord}, {y_cord})")
            return jsonify({"task": {"x": x_cord, "y": y_cord, "end_x": bot_hall_cordinates[bot_id][0], "end_y": bot_hall_cordinates[bot_id][1]}})

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

@app.route("/vizualizeBots", methods=["GET"])
def vizualize_bots():
    """Retrieve the coordinates of all bots and return them in an array."""
    bot_coordinates = []
    map_image_path = "img/map.png"  # Path to the map image
    output_path = "img/map_with_bots.png"  # Path to save the output image

    for bot_id, endpoint in BOT_ENDPOINTS.items():
        try:
            response = requests.get(f"{endpoint}/coordinates", timeout=5)
            if response.status_code == 200:
                data = response.json()
                bot_coordinates.append({
                    "bot_id": bot_id,
                    "x": data.get("x"),
                    "y": data.get("y")
                })
                print(f"Bot {bot_id} coordinates: {data.get('x')}, {data.get('y')}")
            else:
                bot_coordinates.append({
                    "bot_id": bot_id,
                    "error": f"Failed to retrieve coordinates (status code: {response.status_code})"
                })
        except requests.exceptions.RequestException as e:
            bot_coordinates.append({
                "bot_id": bot_id,
                "error": f"Failed to connect to bot endpoint: {str(e)}"
            })
            map_image = cv2.imread(map_image_path, cv2.IMREAD_COLOR)
            if map_image is None:
                raise FileNotFoundError(f"Map image '{map_image_path}' not found or cannot be read.")
            colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0)]  # Red, Green, Blue

            for index, bot in enumerate(bot_coordinates):
                if "x" in bot and "y" in bot:
                    # Calculate pixel coordinates
                    pixel_x = bot["x"]
                    pixel_y = bot["y"]
                    # Draw the robot's position as a dot with a unique color
                    color = colors[index % len(colors)]  # Cycle through the colors

                    cv2.circle(map_image, (int(pixel_x * 200), int(1800 - pixel_y * 200)), 20, color, -1)  # Dot with radius 10 pixels

            # Save the visualization
            success = cv2.imwrite(output_path, map_image)
            if not success:
                print(f"Failed to save the image to {output_path}")
    return jsonify(bot_coordinates) 

    

@app.route("/")
def home():
    return "Server is running and connected to bots!"

if __name__ == "__main__":
    # Start the task generation in a separate thread
    task_thread = threading.Thread(target=generate_tasks_at_interval, daemon=True)
    task_thread.start()
    app.run(host="0.0.0.0", port=5000)