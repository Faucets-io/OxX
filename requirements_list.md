# KashFlow Discord Bot - Requirements List

## Core Discord Bot Dependencies
- discord.py>=2.5.2 - Discord API wrapper for Python
- python-dotenv>=1.1.0 - Environment variable management
- PyNaCl>=1.5.0 - Voice support for Discord

## Web Server Dependencies
- flask>=3.1.0 - Web framework for keep-alive server
- gunicorn>=23.0.0 - Production WSGI HTTP server

## Database Dependencies
- flask-sqlalchemy>=3.1.1 - SQL database integration with Flask
- psycopg2-binary>=2.9.10 - PostgreSQL database adapter
- email-validator>=2.2.0 - Email validation for users

## Utility Dependencies
- asyncio>=3.4.3 - Asynchronous I/O, event loop, and coroutines
- python-dateutil>=2.8.2 - Extensions to the standard datetime module
- uuid>=1.30 - UUID generation for transaction tracking

## Installation Instructions

These dependencies are specified in the project's `requirements.txt` file and can be installed using:

```bash
pip install -r requirements.txt
```

## Environment Requirements
- Python 3.11 or higher

## Environment Variables Required
- DISCORD_TOKEN: Your Discord bot token
- PRIMARY_ADMIN_ID: Discord user ID for the primary administrator
- ADMIN_IDS: Comma-separated list of additional admin Discord user IDs
- SESSION_SECRET: Random string for session security