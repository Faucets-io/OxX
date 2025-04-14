from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return "This server hosts a Discord bot. The bot runs as a separate service."

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)