# Discord Referral Bot

A Discord bot with referral system, coupon management, and user reward tracking. This bot allows users to earn rewards by referring others and provides an admin dashboard for coupon generation and user management.

## Features

### User Features
- Registration with coupon code and optional referral ID
- Welcome bonus of 200 naira for new users
- Referral bonus of 200 naira when someone uses your referral ID
- User dashboard with:
  - Copy referral ID
  - Check balance
  - Withdraw funds
  - Set bank information

### Admin Features
- View all registered users
- Generate unique coupon codes
- Clear used coupon codes
- View total balance across all users

## Setup

1. **Create a Discord Bot**:
   - Go to the [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Navigate to the "Bot" tab and create a bot
   - Copy the bot token

2. **Configure Environment Variables**:
   - Create a `.env` file with:
     ```
     DISCORD_TOKEN=your_discord_bot_token
     ADMIN_ID=your_discord_user_id
     ```

3. **Invite the Bot to Your Server**:
   - Go to OAuth2 > URL Generator in the Developer Portal
   - Select the scopes: `bot` and `applications.commands`
   - Select permissions: Send Messages, Use Slash Commands, Use External Emojis (minimum)
   - Use the generated URL to add the bot to your server

4. **Start the Bot**:
   - Run `python main.py`

## Usage

### Admin Commands
- `/admin` - Access the admin dashboard
  - Generate coupon codes for users to register
  - View all registered users and their details
  - Clear used coupon codes
  - View total balance

### User Commands
- `/start` - Register or access your dashboard
- `/dashboard` - View your dashboard

### Referral Process
1. Admin generates coupon codes
2. User A registers with a coupon code
3. User A shares their referral ID
4. User B registers with a coupon code and User A's referral ID
5. Both users receive 200 naira bonus

### Withdrawal Process
1. User accumulates at least 1000 naira (4 referrals + welcome bonus)
2. User sets bank information
3. User requests withdrawal
4. Admin receives bank details and amount
5. User account is deleted after withdrawal

## Data Storage
- User data is stored in `users.json`
- Coupon codes are stored in `coupons.json`