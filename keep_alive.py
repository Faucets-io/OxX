
from flask import Flask, render_template_string
from threading import Thread
import os
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('keep_alive')

app = Flask(__name__)

# Status tracking
start_time = time.time()
ping_count = 0

@app.route('/')
def home():
    global ping_count
    ping_count += 1
    uptime = int(time.time() - start_time)
    
    # HTML with minimal styling
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>KashFlow Bot Status</title>
        <meta http-equiv="refresh" content="30">
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
                color: #333;
            }
            .status-card {
                background-color: #fff;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                padding: 20px;
                margin-bottom: 20px;
            }
            .status-indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background-color: #4CAF50;
                margin-right: 8px;
            }
            h1 {
                color: #2c3e50;
                margin-top: 0;
            }
            .info-row {
                display: flex;
                justify-content: space-between;
                margin: 10px 0;
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
            }
            .info-label {
                font-weight: bold;
                color: #555;
            }
            .footer {
                font-size: 0.8em;
                text-align: center;
                margin-top: 40px;
                color: #777;
            }
        </style>
    </head>
    <body>
        <div class="status-card">
            <h1><span class="status-indicator"></span> KashFlow Bot Status</h1>
            
            <div class="info-row">
                <span class="info-label">Status:</span>
                <span>Online</span>
            </div>
            
            <div class="info-row">
                <span class="info-label">Uptime:</span>
                <span>{{ uptime_str }}</span>
            </div>
            
            <div class="info-row">
                <span class="info-label">Ping Count:</span>
                <span>{{ ping_count }}</span>
            </div>
            
            <div class="info-row">
                <span class="info-label">Keep-Alive:</span>
                <span>Active (refreshes every 30s)</span>
            </div>
        </div>
        
        <div class="status-card">
            <h2>How it works:</h2>
            <p>This page helps keep your Discord bot running even when you close the Replit tab.</p>
            <p>The automatic refresh pings the server every 30 seconds to prevent it from sleeping.</p>
            <p>You can bookmark this page and check it anytime to verify your bot is still running.</p>
        </div>
        
        <div class="footer">
            KashFlow Referral Bot | Powered by Flask | &copy; 2025
        </div>
    </body>
    </html>
    """
    
    # Format uptime nicely
    days, remainder = divmod(uptime, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    uptime_str = ""
    if days > 0:
        uptime_str += f"{days} days, "
    uptime_str += f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    return render_template_string(html, uptime_str=uptime_str, ping_count=ping_count)

@app.route('/ping')
def ping():
    return "pong"

def run():
    # Try a different port if 8080 is taken
    ports_to_try = [8080, 8000, 3000, 5050]
    
    for port in ports_to_try:
        try:
            logger.info(f"Starting keep-alive server on port {port}")
            app.run(host='0.0.0.0', port=port, debug=False)
            # If we get here, the server started successfully
            return
        except OSError as e:
            logger.warning(f"Port {port} is in use, trying another port: {e}")
    
    # If all ports failed
    logger.error("Failed to start keep-alive server on any port")

def keep_alive():
    try:
        logger.info("Starting keep-alive service")
        t = Thread(target=run)
        t.daemon = True  # This ensures the thread stops when the main program stops
        t.start()
        logger.info("Keep-alive thread started successfully")
    except Exception as e:
        logger.error(f"Error starting keep_alive thread: {e}")
