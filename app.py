from flask import Flask, redirect, render_template_string
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('main_app')

app = Flask(__name__)

@app.route('/')
def index():
    # HTML template for the main page
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>KashFlow Bot</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
                color: #333;
                text-align: center;
            }
            .main-card {
                background-color: #fff;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                padding: 30px;
                margin-top: 50px;
            }
            h1 {
                color: #2c3e50;
            }
            .status-button {
                display: inline-block;
                background-color: #4CAF50;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 4px;
                font-weight: bold;
                margin-top: 20px;
                transition: background-color 0.3s;
            }
            .status-button:hover {
                background-color: #45a049;
            }
            .footer {
                margin-top: 50px;
                color: #777;
                font-size: 0.9em;
            }
        </style>
    </head>
    <body>
        <div class="main-card">
            <h1>KashFlow Discord Bot</h1>
            <p>Your Discord bot is running in the background.</p>
            <p>You can close this tab and the bot will continue to operate.</p>
            
            <a href="/bot-status" class="status-button">View Bot Status</a>
        </div>
        
        <div class="footer">
            KashFlow Referral Bot | Running on Replit | &copy; 2025
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/bot-status')
def bot_status():
    # Redirect to the keep-alive status page
    ports_to_try = [8080, 8000, 3000, 5050]
    
    for port in ports_to_try:
        # We're making a simple redirect - the keep_alive server will handle the actual status page
        return redirect(f"http://{os.environ.get('REPL_SLUG', 'localhost')}.{os.environ.get('REPL_OWNER', 'repl')}.repl.co:{port}")
    
    # If all ports failed, show an error
    return "Could not connect to the bot status page. Please check if the bot is running."

if __name__ == "__main__":
    # This only runs when app.py is executed directly, not when imported
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)