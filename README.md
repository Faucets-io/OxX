# KashFlow Discord Bot

A Discord bot designed to enhance community engagement through a dynamic referral system, comprehensive coupon management, and user reward tracking.

## Key Features

- **Referral System**: Users earn bonuses when they refer new members
- **Coupon Management**: Admin-controlled coupon code generation
- **Withdrawal System**: Users can withdraw funds after 4 successful referrals
- **Two-Tier Admin System**: Primary admin with exclusive coupon generation rights

## 🔄 24/7 Operation on Replit

This bot is designed to run continuously on Replit, even when you close the browser tab or shutdown your computer.

### Keep-Alive System

The bot includes a robust keep-alive system with the following features:

1. **Auto-Restart**: The bot automatically restarts if it crashes
2. **Status Dashboard**: Monitor your bot's uptime and performance at any time
3. **Multiple Port Fallback**: The system tries multiple ports to ensure connectivity

### How to Keep Your Bot Running

1. Start the bot using the "run_discord_bot" workflow in Replit
2. Access the status page by clicking the "Run" button
3. The bot will continue running even when you:
   - Close the browser tab
   - Log out of Replit
   - Shut down your computer

4. You can check your bot's status anytime by revisiting the Replit project

## ⚙️ Setup Instructions

1. **Environment Variables**: Copy `.env.example` to `.env` and fill in:
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   PRIMARY_ADMIN_ID=your_discord_user_id_here
   ADMIN_IDS=comma,separated,discord,ids
   SESSION_SECRET=random_string_here
   ```

2. **Primary Admin ID**: This must be your Discord user ID (enable Developer Mode in Discord settings → right-click your username → Copy ID)

3. **Secondary Admins**: These admins can use all features except generating coupon codes

## 💰 Withdrawal System

The withdrawal system has been configured with these rules:

1. Users must complete at least 4 referrals to be eligible for withdrawal
2. Users must have a minimum balance of 1000 naira
3. Users must set their bank information before withdrawing
4. Upon withdrawal, the user's account is deleted and a pending withdrawal notification is sent to the primary admin

## 🔐 Admin System

### Primary Admin (You)
- Can generate coupon codes (exclusive feature)
- Can view all users and their details
- Can clear used coupons
- Can view total system balance

### Secondary Admins
- Can view users and their details
- Can clear used coupons
- Can view total system balance
- CANNOT generate coupon codes (restricted feature)

## Bot Commands

- `/start` - Register with a coupon code or view your dashboard
- `/dashboard` - View your user dashboard
- `/admin` - Access admin controls (only for authorized users)

## User Dashboard Features
- Copy your referral ID to share with others
- Check your current balance and referral count
- Withdraw your balance when eligible (4 referrals & 1000 naira minimum)
- Set your bank information for withdrawals