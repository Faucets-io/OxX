
from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Discord bot is running! This web server keeps it alive."

def run():
    # Use port 8080 to avoid conflicts with main Flask app
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    try:
        t = Thread(target=run)
        t.daemon = True  # This ensures the thread stops when the main program stops
        t.start()
    except Exception as e:
        print(f"Error starting keep_alive thread: {e}")
