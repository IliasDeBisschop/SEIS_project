from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Define the bot endpoints
BOT_ENDPOINTS = {
    "bot1": "http://bot1:5000",
    "bot2": "http://bot2:5000",
    "bot3": "http://bot3:5000",
}

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