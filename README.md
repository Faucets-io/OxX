# KashFlow Discord Bot

A Discord bot designed to enhance community engagement through a dynamic referral system, comprehensive coupon management, and user reward tracking.

## Features

- User registration with coupon codes
- Referral system with tracking
- Balance management for users
- Withdrawal functionality with bank information collection
- Admin dashboard for generating coupons and managing users

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Discord.py library

### Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/kashflow-discord-bot.git
cd kashflow-discord-bot
```

2. Install the required packages:
```bash
pip install discord.py python-dotenv flask gunicorn
```

3. Create a `.env` file in the root directory with the following content:
```
DISCORD_TOKEN=your_discord_bot_token
ADMIN_ID=your_discord_user_id
```

4. Create initial data files:
```bash
echo "{}" > users.json
echo "{}" > coupons.json
```

### Running the Bot

Start the bot with:
```bash
python main.py
```

### Running on Termux

1. Install Termux from the Play Store or F-Droid
2. Set up Python in Termux:
```bash
pkg update && pkg upgrade
pkg install python git
```

3. Clone and set up the bot:
```bash
git clone https://github.com/yourusername/kashflow-discord-bot.git
cd kashflow-discord-bot
pip install discord.py python-dotenv flask
```

4. Create the .env file as mentioned above
5. Run the bot:
```bash
python main.py
```

6. To keep the bot running after closing Termux, use:
```bash
nohup python main.py &
```

## Bot Commands

- `/start` - Register with a coupon code or view your dashboard
- `/dashboard` - View your user dashboard
- `/admin` - Access admin controls (only for authorized users)

## Dashboard Features

### User Dashboard
- Copy your referral ID to share with others
- Check your current balance and referral count
- Withdraw your balance when eligible
- Set your bank information for withdrawals

### Admin Dashboard
- View all registered users
- Generate new coupon codes
- Clear used coupon codes
- View total system balance