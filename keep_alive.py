from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Discord bot is running! This web server keeps it alive."

def run():
    # Use port 8080 to avoid conflicts with gunicorn on port 5000
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    try:
        t = Thread(target=run)
        t.daemon = True
        t.start()
    except Exception as e:
        print(f"Error starting keep_alive thread: {e}")
        # The bot will still run even if the keep_alive thread fails