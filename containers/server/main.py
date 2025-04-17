from flask import Flask, request, jsonify
import requests
import random
import threading
import time

app = Flask(__name__)

ROWS = 20  # Example: Total number of rows
COLUMNS = 6  # Example: Total number of columns
INTERVAL = 10  # Example: Frequency of task generation in seconds
MAX_TASKS = 3  # Maximum number of tasks to generate per interval

bot_rows = {
    "bot1": None,
    "bot2": None,
    "bot3": None,
}

# Global list to store tasks
tasks = []

# Define the bot endpoints
BOT_ENDPOINTS = {
    "bot1": "http://bot1:5000",
    "bot2": "http://bot2:5000",
    "bot3": "http://bot3:5000",
}

def generate_random_task():
    """Generate a random (row, column) tuple."""
    row = random.randint(0, ROWS - 1)
    column = random.randint(0, COLUMNS - 1)
    return (row, column)

def generate_tasks_at_interval():
    """Generate a random number of tasks at a specified interval."""
    global tasks
    while True:
        num_tasks = random.randint(0, MAX_TASKS)  # Random number of tasks
        new_tasks = [generate_random_task() for _ in range(num_tasks)]
        tasks.extend(new_tasks)
        print(f"Generated {num_tasks} tasks: {new_tasks}")
        print (f"Current tasks: {tasks}")
        time.sleep(INTERVAL)  # Wait for the next interval

# Start the task generation in a separate thread
task_thread = threading.Thread(target=generate_tasks_at_interval, daemon=True)
task_thread.start()

@app.route("/bot/<bot_id>/get_task", methods=["GET"])
def get_task(bot_id):
    """Assign the oldest task to a bot. Prefer tasks in rows where no other bot is working, but fall back to any task if necessary."""
    global tasks, bot_rows

    if bot_id not in BOT_ENDPOINTS:
        return jsonify({"error": "Invalid bot ID"}), 400

    # First, try to find a task in a row where no other bot is working
    for task in tasks:
        row, column = task
        if row not in bot_rows.values():  # Check if the row is free
            # Assign the task to the bot
            bot_rows[bot_id] = row
            tasks.remove(task)  # Remove the task from the list
            return jsonify({"task": {"row": row, "column": column}})

    # If no free rows are available, assign the oldest task regardless of row
    if tasks:
        task = tasks.pop(0)  # Get and remove the oldest task
        row, column = task
        bot_rows[bot_id] = row  # Assign the row to the bot
        return jsonify({"task": {"row": row, "column": column}})

    # If no tasks are available at all, return an error
    return jsonify({"error": "No available tasks"}), 404


@app.route("/bot/<bot_id>/complete_task", methods=["POST"])
def complete_task(bot_id):
    """Mark a task as completed and free up the bot's row."""
    global bot_rows

    if bot_id not in BOT_ENDPOINTS:
        return jsonify({"error": "Invalid bot ID"}), 400

    # Free up the row for the bot
    bot_rows[bot_id] = None
    return jsonify({"message": f"Bot {bot_id} has completed its task and is now free."})

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
    app.run(host="0.0.0.0", port=5000)