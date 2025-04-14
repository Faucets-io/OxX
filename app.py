from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return "This server keeps the Discord bot alive. The bot runs as a separate service."