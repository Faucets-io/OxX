import os
import json
import random
import string
import logging
import asyncio
import uuid
import io
from datetime import datetime
from typing import Dict, List, Optional, Union

# Discord imports
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Admin configuration
ADMIN_IDS_STR = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = [int(admin_id.strip()) for admin_id in ADMIN_IDS_STR.split(',') if admin_id.strip().isdigit()]

# Get primary admin ID, handling the placeholder text case
primary_admin_str = os.getenv('PRIMARY_ADMIN_ID', '0')
try:
    PRIMARY_ADMIN_ID = int(primary_admin_str)
except ValueError:
    logger.warning(f"Invalid PRIMARY_ADMIN_ID in .env file: {primary_admin_str}")
    PRIMARY_ADMIN_ID = 0

# For backward compatibility
ADMIN_ID = PRIMARY_ADMIN_ID

# Constants
CONFIG_FILE = "config.json"
COUPON_LENGTH = 12  # Length of coupon code

# Default values (will be overridden by config.json)
WELCOME_BONUS = 200  # Welcome bonus in Naira
REFERRAL_BONUS = 200  # Referral bonus in Naira
WITHDRAWAL_THRESHOLD = 1000  # Minimum balance required for withdrawal
MINIMUM_REFERRALS = 4  # Minimum number of referrals required for withdrawal
COUPON_PRICE = 500  # Price of coupon in Naira
AUTO_APPROVE_WITHDRAWALS = False  # Whether to auto-approve withdrawals
ADMIN_NOTIFICATION_CHANNEL_ID = None  # Channel ID for admin notifications
MAX_WITHDRAWAL_DAILY = 5000  # Maximum daily withdrawal amount
PAYMENT_METHODS = {"bank_transfer": True, "mobile_money": False}  # Available payment methods
SYSTEM_ANNOUNCEMENTS = {"enabled": True, "message": "Welcome to KashFlow!"}  # System announcements
DEMO_MODE_ENABLED = True  # Whether demo mode is enabled for new users
DEMO_BALANCE = 1500  # Demo balance to show in demo mode
DEMO_REFERRALS = 6  # Demo referral count to show in demo mode

# Bot status control
BOT_ENABLED_FOR_USERS = True  # Bot status flag

# Configuration management functions
def load_config() -> Dict:
    """Load configuration from config.json file."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        else:
            # If config file doesn't exist, create it with default values
            config = {
                "welcome_bonus": WELCOME_BONUS,
                "referral_bonus": REFERRAL_BONUS,
                "withdrawal_threshold": WITHDRAWAL_THRESHOLD,
                "minimum_referrals": MINIMUM_REFERRALS,
                "tutorial_enabled": TUTORIAL_ENABLED,
                "tutorial_timeout": TUTORIAL_TIMEOUT,
                "auto_approve_withdrawals": AUTO_APPROVE_WITHDRAWALS,
                "admin_notification_channel_id": ADMIN_NOTIFICATION_CHANNEL_ID,
                "max_withdrawal_daily": MAX_WITHDRAWAL_DAILY,
                "payment_methods": PAYMENT_METHODS,
                "system_announcements": SYSTEM_ANNOUNCEMENTS,
                "coupon_price": COUPON_PRICE,
                "bot_enabled_for_users": BOT_ENABLED_FOR_USERS,
                "demo_mode_enabled": DEMO_MODE_ENABLED,
                "demo_balance": DEMO_BALANCE,
                "demo_referrals": DEMO_REFERRALS
            }
            save_config(config)
            return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}

def save_config(config: Dict) -> bool:
    """Save configuration to config.json file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False

def update_config(key: str, value) -> bool:
    """Update a specific configuration value."""
    try:
        config = load_config()
        
        # Handle nested keys with dot notation (e.g., "payment_methods.bank_transfer")
        if "." in key:
            parts = key.split(".")
            current = config
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    current[part] = value
                else:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
        else:
            config[key] = value
            
        return save_config(config)
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return False

def apply_config() -> None:
    """Apply configuration values from config.json to global variables."""
    global WELCOME_BONUS, REFERRAL_BONUS, WITHDRAWAL_THRESHOLD, MINIMUM_REFERRALS
    global TUTORIAL_ENABLED, TUTORIAL_TIMEOUT, AUTO_APPROVE_WITHDRAWALS
    global ADMIN_NOTIFICATION_CHANNEL_ID, MAX_WITHDRAWAL_DAILY
    global PAYMENT_METHODS, SYSTEM_ANNOUNCEMENTS, COUPON_PRICE
    global BOT_ENABLED_FOR_USERS, DEMO_MODE_ENABLED, DEMO_BALANCE, DEMO_REFERRALS
    
    config = load_config()
    if config:
        WELCOME_BONUS = config.get("welcome_bonus", WELCOME_BONUS)
        REFERRAL_BONUS = config.get("referral_bonus", REFERRAL_BONUS)
        WITHDRAWAL_THRESHOLD = config.get("withdrawal_threshold", WITHDRAWAL_THRESHOLD)
        MINIMUM_REFERRALS = config.get("minimum_referrals", MINIMUM_REFERRALS)
        TUTORIAL_ENABLED = config.get("tutorial_enabled", TUTORIAL_ENABLED)
        TUTORIAL_TIMEOUT = config.get("tutorial_timeout", TUTORIAL_TIMEOUT)
        AUTO_APPROVE_WITHDRAWALS = config.get("auto_approve_withdrawals", AUTO_APPROVE_WITHDRAWALS)
        ADMIN_NOTIFICATION_CHANNEL_ID = config.get("admin_notification_channel_id", ADMIN_NOTIFICATION_CHANNEL_ID)
        MAX_WITHDRAWAL_DAILY = config.get("max_withdrawal_daily", MAX_WITHDRAWAL_DAILY)
        PAYMENT_METHODS = config.get("payment_methods", PAYMENT_METHODS)
        SYSTEM_ANNOUNCEMENTS = config.get("system_announcements", SYSTEM_ANNOUNCEMENTS)
        COUPON_PRICE = config.get("coupon_price", COUPON_PRICE)
        BOT_ENABLED_FOR_USERS = config.get("bot_enabled_for_users", BOT_ENABLED_FOR_USERS)
        DEMO_MODE_ENABLED = config.get("demo_mode_enabled", DEMO_MODE_ENABLED)
        DEMO_BALANCE = config.get("demo_balance", DEMO_BALANCE)
        DEMO_REFERRALS = config.get("demo_referrals", DEMO_REFERRALS)
        
        logger.info(f"Configuration loaded: Welcome bonus={WELCOME_BONUS}, Referral bonus={REFERRAL_BONUS}")

# Contact information - These are not part of the dynamic config
WHATSAPP_COMMUNITY_LINK = "https://chat.whatsapp.com/JMp6tB5yMTq1dMBYttIZOj"
SUPPORT_EMAIL = "contactkashflow@yahoo.com"

# Tutorial settings - These will be overridden by config
TUTORIAL_ENABLED = True  # Enable/disable tutorial feature
TUTORIAL_TIMEOUT = 300   # Seconds before tutorial times out (5 minutes)

# Apply configuration after all defaults are defined
apply_config()

# File paths
USERS_FILE = 'users.json'
COUPONS_FILE = 'coupons.json'
TRANSACTIONS_FILE = 'transactions.json'

# Create files if they don't exist
for file_path in [USERS_FILE, COUPONS_FILE, TRANSACTIONS_FILE]:
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump({}, f)

# Bot setup with minimal required intents for slash commands
intents = discord.Intents.default()
# We explicitly disable privileged intents to ensure the bot works without them
intents.message_content = False
intents.members = False
intents.presences = False

# Create the bot with only slash commands in mind
bot = commands.Bot(command_prefix='!', intents=intents, description="KashFlow Referral Bot")

# User data structure
class User:
    def __init__(
        self, 
        id: int, 
        username: str, 
        balance: int = 0, 
        referred_by: Optional[int] = None,
        bank_name: str = "", 
        bank_account_number: str = "", 
        bank_account_name: str = "",
        referral_count: int = 0
    ):
        self.id = id
        self.username = username
        self.balance = balance
        self.referred_by = referred_by
        self.bank_name = bank_name
        self.bank_account_number = bank_account_number
        self.bank_account_name = bank_account_name
        self.referral_count = referral_count
        self.created_at = datetime.now().isoformat()
        
        # Initialize tutorial progress
        self.tutorial_step = 0
        self.tutorial_completed = False
        self.tutorial_last_interaction = None

    def to_dict(self) -> Dict:
        data = {
            "id": self.id,
            "username": self.username,
            "balance": self.balance,
            "referred_by": self.referred_by,
            "bank_name": self.bank_name,
            "bank_account_number": self.bank_account_number,
            "bank_account_name": self.bank_account_name,
            "referral_count": self.referral_count,
            "created_at": self.created_at
        }
        # Add tutorial progress data
        if hasattr(self, 'tutorial_step'):
            data["tutorial_step"] = self.tutorial_step
        if hasattr(self, 'tutorial_completed'):
            data["tutorial_completed"] = self.tutorial_completed
        if hasattr(self, 'tutorial_last_interaction'):
            data["tutorial_last_interaction"] = self.tutorial_last_interaction
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        user = cls(
            id=data["id"],
            username=data["username"],
            balance=data["balance"],
            referred_by=data.get("referred_by"),
            bank_name=data.get("bank_name", ""),
            bank_account_number=data.get("bank_account_number", ""),
            bank_account_name=data.get("bank_account_name", ""),
            referral_count=data.get("referral_count", 0)
        )
        user.created_at = data.get("created_at", datetime.now().isoformat())
        # Add tutorial progress tracking
        user.tutorial_step = data.get("tutorial_step", 0)
        user.tutorial_completed = data.get("tutorial_completed", False)
        user.tutorial_last_interaction = data.get("tutorial_last_interaction", None)
        return user

# Data management functions
def load_users() -> Dict[int, User]:
    try:
        with open(USERS_FILE, 'r') as f:
            users_data = json.load(f)
            return {int(user_id): User.from_dict(user_data) for user_id, user_data in users_data.items()}
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_users(users: Dict[int, User]) -> None:
    users_data = {str(user_id): user.to_dict() for user_id, user in users.items()}
    with open(USERS_FILE, 'w') as f:
        json.dump(users_data, f, indent=4)

def load_coupons() -> Dict[str, bool]:
    try:
        with open(COUPONS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_coupons(coupons: Dict[str, bool]) -> None:
    with open(COUPONS_FILE, 'w') as f:
        json.dump(coupons, f, indent=4)

def generate_coupon_code(suffix: str = "") -> str:
    """Generate a random coupon code with optional suffix."""
    length = COUPON_LENGTH - len(suffix) if suffix else COUPON_LENGTH
    chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choice(chars) for _ in range(length))
    return code + suffix if suffix else code

def is_valid_coupon(coupon_code: str) -> bool:
    """Check if a coupon code is valid and unused."""
    coupons = load_coupons()
    return coupon_code in coupons and not coupons[coupon_code]

def mark_coupon_used(coupon_code: str) -> None:
    """Mark a coupon code as used."""
    coupons = load_coupons()
    if coupon_code in coupons:
        coupons[coupon_code] = True
        save_coupons(coupons)

def get_user(user_id: int) -> Optional[User]:
    """Get a user by ID from the database."""
    users = load_users()
    return users.get(user_id)

def add_user(user: User) -> None:
    """Add or update a user in the database."""
    users = load_users()
    users[user.id] = user
    save_users(users)

def delete_user(user_id: int) -> None:
    """Delete a user from the database."""
    users = load_users()
    if user_id in users:
        del users[user_id]
        save_users(users)

def calculate_total_balance() -> int:
    """Calculate the total balance of all users."""
    users = load_users()
    return sum(user.balance for user in users.values())

def create_bot_enable_view(interaction_user_id: int) -> Optional[discord.ui.View]:
    """
    Creates a view with an Enable Bot button if the user is an admin.
    
    Args:
        interaction_user_id: The ID of the user who triggered the interaction
        
    Returns:
        A discord.ui.View with the Enable Bot button, or None if user is not an admin
    """
    # Only create view for admins
    if not is_admin(interaction_user_id):
        return None
    
    view = discord.ui.View(timeout=None)
    enable_button = discord.ui.Button(
        style=discord.ButtonStyle.success,
        label="Enable Bot for Users",
        custom_id="quick_enable_bot"
    )
    
    async def quick_enable_callback(enable_interaction: discord.Interaction):
        try:
            # Double-check admin status
            if not is_admin(enable_interaction.user.id):
                await enable_interaction.response.send_message(
                    "You are not authorized to enable the bot.",
                    ephemeral=True
                )
                return
            
            # Enable the bot
            global BOT_ENABLED_FOR_USERS
            BOT_ENABLED_FOR_USERS = True
            
            # Save the updated status to configuration
            update_config("bot_enabled_for_users", BOT_ENABLED_FOR_USERS)
            
            # Confirm to the admin
            await enable_interaction.response.send_message(
                "✅ Bot has been enabled for all users.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error in quick_enable_callback: {e}")
            if not enable_interaction.response.is_done():
                try:
                    await enable_interaction.response.send_message(
                        "Something went wrong. Please try again.",
                        ephemeral=True
                    )
                except:
                    pass
    
    enable_button.callback = quick_enable_callback
    view.add_item(enable_button)
    return view

def clear_used_coupons() -> int:
    """Clear all used coupons and return count of cleared coupons."""
    coupons = load_coupons()
    used_coupons = [code for code, used in coupons.items() if used]
    for code in used_coupons:
        del coupons[code]
    save_coupons(coupons)
    return len(used_coupons)

# Animation and notification utilities
async def send_animated_message(destination, frames, duration=2.0, final_frame=None, ephemeral=False):
    """
    Send an animated message by quickly editing the message with different frames.
    
    Parameters:
    - destination: The Discord channel or user to send the message to
    - frames: List of strings representing animation frames
    - duration: Total duration of animation in seconds
    - final_frame: Final message to display after animation (if None, last frame is used)
    - ephemeral: Whether the message should be ephemeral (only works with interaction responses)
    
    Returns:
    - The final message object
    """
    if not frames:
        return None
        
    # Calculate delay between frames
    frame_count = len(frames)
    delay = duration / frame_count
    
    # Send first frame
    if isinstance(destination, discord.Interaction):
        if destination.response.is_done():
            message = await destination.followup.send(frames[0], ephemeral=ephemeral)
        else:
            await destination.response.send_message(frames[0], ephemeral=ephemeral)
            message = await destination.original_response()
    else:
        message = await destination.send(frames[0])
    
    # Animate by editing the message
    for frame in frames[1:]:
        await asyncio.sleep(delay)
        try:
            await message.edit(content=frame)
        except discord.NotFound:
            # Message might have been deleted
            return None
        except Exception as e:
            logger.error(f"Error editing animated message: {e}")
            break
    
    # Set final frame if provided
    if final_frame is not None:
        try:
            await message.edit(content=final_frame)
        except Exception as e:
            logger.error(f"Error setting final frame: {e}")
    
    return message

# Animation frame generators
def generate_loading_frames(message, duration=3, width=10):
    """Generate loading animation frames."""
    symbols = ["⬜", "⬛"]
    frames = []
    
    for i in range(width + 1):
        bar = symbols[1] * i + symbols[0] * (width - i)
        percentage = int((i / width) * 100)
        frames.append(f"{message}\n\n`[{bar}] {percentage}%`")
    
    return frames

def generate_success_animation(message):
    """Generate success animation frames."""
    frames = [
        f"⬜⬜⬜\n⬜⬜⬜\n⬜⬜⬜\n\n{message}",
        f"⬜⬜⬜\n⬜🟩⬜\n⬜⬜⬜\n\n{message}",
        f"⬜⬜⬜\n⬜🟩⬜\n⬜🟩⬜\n\n{message}",
        f"⬜⬜⬜\n⬜🟩⬜\n⬜🟩🟩\n\n{message}",
        f"⬜⬜⬜\n⬜🟩🟩\n⬜🟩🟩\n\n{message}",
        f"⬜🟩⬜\n⬜🟩🟩\n⬜🟩🟩\n\n{message}",
        f"🟩🟩⬜\n⬜🟩🟩\n⬜🟩🟩\n\n{message}",
        f"🟩🟩🟩\n⬜🟩🟩\n⬜🟩🟩\n\n{message}",
        f"🟩🟩🟩\n🟩🟩🟩\n⬜🟩🟩\n\n{message}",
        f"🟩🟩🟩\n🟩🟩🟩\n🟩🟩🟩\n\n{message}",
        f"✅\n\n{message}"
    ]
    return frames

def generate_error_animation(message):
    """Generate error animation frames."""
    frames = [
        f"⬜⬜⬜\n⬜⬜⬜\n⬜⬜⬜\n\n{message}",
        f"🟥⬜⬜\n⬜⬜⬜\n⬜⬜🟥\n\n{message}",
        f"🟥⬜🟥\n⬜⬜⬜\n🟥⬜🟥\n\n{message}",
        f"🟥⬜🟥\n⬜🟥⬜\n🟥⬜🟥\n\n{message}",
        f"🟥⬜🟥\n⬜🟥⬜\n🟥⬜🟥\n\n{message}",
        f"🟥🟥🟥\n🟥🟥🟥\n🟥🟥🟥\n\n{message}",
        f"❌\n\n{message}"
    ]
    return frames

def generate_coins_animation(amount, message):
    """Generate coin animation frames for payments/rewards."""
    base_frames = [
        "💰",
        "💰💰",
        "💰💰💰",
        "💰💰💰💰",
        "💰💰💰💰💰",
    ]
    
    frames = []
    for frame in base_frames:
        frames.append(f"{frame}\n\n**{amount} naira**\n{message}")
    
    # Final frame with sparkles
    frames.append(f"✨💰💰💰💰💰✨\n\n**{amount} naira**\n{message}")
    
    return frames

# Tutorial animation frames
def generate_tutorial_frames(message):
    """Generate tutorial animation frames."""
    frames = [
        f"⭐\n\n{message}",
        f"⭐⭐\n\n{message}",
        f"⭐⭐⭐\n\n{message}",
        f"✨⭐⭐⭐✨\n\n{message}",
        f"✨⭐⭐⭐✨\n\n{message}",
        f"✨⭐⭐⭐✨\n\n{message}",
        f"🎓\n\n{message}"
    ]
    return frames

# Tutorial step management functions
def update_tutorial_progress(user_id: int, step: int = None, completed: bool = None) -> Optional[User]:
    """Update tutorial progress for a user and save changes."""
    user = get_user(user_id)
    if not user:
        return None
        
    if step is not None:
        user.tutorial_step = step
        
    if completed is not None:
        user.tutorial_completed = completed
        
    # Update last interaction time
    user.tutorial_last_interaction = datetime.now().isoformat()
    
    # Save changes
    add_user(user)
    return user
    
def get_tutorial_content(step: int) -> Dict:
    """Get content for a specific tutorial step."""
    tutorial_steps = {
        0: {
            "title": "Welcome to KashFlow!",
            "content": f"Let's get you started with KashFlow, your referral rewards platform! I'll guide you through the basics.\n\n**What we'll cover:**\n• Understanding the dashboard\n• Setting up your account\n• Referring friends\n• Withdrawing funds",
            "next_label": "Start Tutorial",
            "skip_label": "Skip Tutorial"
        },
        1: {
            "title": "Step 1: Your Dashboard",
            "content": f"This is your dashboard where you can see your current balance and referral count.\n\n• Current balance shows how much you've earned\n• You get **{WELCOME_BONUS}** naira when you register\n• Each referral earns you **{REFERRAL_BONUS}** naira\n• You need **{MINIMUM_REFERRALS}** referrals to withdraw",
            "next_label": "Next Step",
            "back_label": "Previous"
        },
        2: {
            "title": "Step 2: Setting Up Your Account",
            "content": "Before you can make withdrawals, you need to set up your bank information:\n\n• Click on \"Set Bank Information\" in your dashboard\n• Enter your bank name, account number, and account name\n• This is where your funds will be sent during withdrawal",
            "next_label": "Next Step",
            "back_label": "Previous"
        },
        3: {
            "title": "Step 3: Referring Friends",
            "content": f"Time to earn some rewards! Here's how to refer friends:\n\n• Click \"Copy ID to Refer\" in your dashboard\n• Share your referral ID with friends\n• When they register using your ID, you get **{REFERRAL_BONUS}** naira\n• Each friend also gets **{WELCOME_BONUS}** naira as welcome bonus",
            "next_label": "Next Step",
            "back_label": "Previous"
        },
        4: {
            "title": "Step 4: Withdrawing Funds",
            "content": f"Ready to cash out? Here's how withdrawals work:\n\n• You need at least **{WITHDRAWAL_THRESHOLD}** naira balance\n• You must have at least **{MINIMUM_REFERRALS}** referrals\n• Click \"Withdraw\" in your dashboard\n• Funds will be sent to your registered bank account\n• An admin will process your request",
            "next_label": "Next Step",
            "back_label": "Previous"
        },
        5: {
            "title": "Tutorial Complete!",
            "content": f"Congratulations! You now know how to use KashFlow.\n\n• Remember to share your referral ID\n• Each referral = **{REFERRAL_BONUS}** naira\n• Need help? Use the /help command\n• Join our WhatsApp community: {WHATSAPP_COMMUNITY_LINK}\n\nGood luck and happy earning!",
            "finish_label": "Finish Tutorial",
            "back_label": "Previous"
        }
    }
    
    return tutorial_steps.get(step, tutorial_steps[0])

# Transaction management functions
def create_demo_dashboard_view() -> discord.ui.View:
    """Create a demonstration dashboard for potential users to see how the system works."""
    view = discord.ui.View(timeout=None)
    
    # Create buttons with demonstration callbacks
    
    # Demo Copy referral ID button
    demo_copy_button = discord.ui.Button(
        style=discord.ButtonStyle.primary,
        label="Copy ID to Refer (Demo)",
        custom_id="demo_copy_id"
    )
    
    async def demo_copy_callback(interaction: discord.Interaction):
        # Generate a fake referral ID for demonstration
        demo_id = str(interaction.user.id)
        await interaction.response.send_message(
            f"**DEMO MODE**: In the real app, your referral ID ({demo_id}) would be copied to your clipboard.\n\n"
            f"You would share this ID with friends. When they register using your ID, "
            f"you earn {REFERRAL_BONUS} naira for each referral!",
            ephemeral=True
        )
    
    demo_copy_button.callback = demo_copy_callback
    view.add_item(demo_copy_button)
    
    # Demo Check balance button
    demo_balance_button = discord.ui.Button(
        style=discord.ButtonStyle.secondary,
        label="Check Balance (Demo)",
        custom_id="demo_check_balance"
    )
    
    async def demo_balance_callback(interaction: discord.Interaction):
        # Show demo balance information
        demo_message = (
            f"**DEMO MODE**: This shows how your balance information would appear.\n\n"
            f"Current Balance: **{DEMO_BALANCE}** naira\n"
            f"Referral Count: **{DEMO_REFERRALS}**\n"
            f"Welcome Bonus: **{WELCOME_BONUS}** naira\n"
            f"Referral Bonus: **{REFERRAL_BONUS}** naira per referral\n\n"
            f"In this demo, you've earned {WELCOME_BONUS} naira as a welcome bonus and "
            f"{DEMO_REFERRALS} × {REFERRAL_BONUS} = {DEMO_REFERRALS * REFERRAL_BONUS} naira from referrals."
        )
        
        # Generate coin animation for demonstration
        frames = generate_coins_animation(DEMO_BALANCE, "Checking your demo balance...")
        await interaction.response.defer(ephemeral=True)
        await send_animated_message(
            interaction,
            frames,
            duration=2.0,
            final_frame=demo_message,
            ephemeral=True
        )
    
    demo_balance_button.callback = demo_balance_callback
    view.add_item(demo_balance_button)
    
    # Demo Withdraw button
    demo_withdraw_button = discord.ui.Button(
        style=discord.ButtonStyle.success,
        label="Withdraw (Demo)",
        custom_id="demo_withdraw"
    )
    
    async def demo_withdraw_callback(interaction: discord.Interaction):
        # Check if demo balance meets requirements
        if DEMO_REFERRALS >= MINIMUM_REFERRALS and DEMO_BALANCE >= WITHDRAWAL_THRESHOLD:
            # Show successful withdrawal message
            await interaction.response.defer(ephemeral=True)
            success_message = (
                f"**DEMO MODE**: Withdrawal demonstration\n\n"
                f"You've met the withdrawal requirements with {DEMO_REFERRALS} referrals and {DEMO_BALANCE} naira balance.\n\n"
                f"In the real app, you would enter your withdrawal amount and receive payment through your configured bank account."
            )
            frames = generate_success_animation(success_message)
            await send_animated_message(
                interaction,
                frames,
                duration=2.0,
                final_frame=success_message,
                ephemeral=True
            )
        else:
            # Show requirements not met message
            requirements_message = (
                f"**DEMO MODE**: Withdrawal requirements not met\n\n"
                f"To withdraw, you need:\n"
                f"• Minimum {MINIMUM_REFERRALS} referrals (you have {DEMO_REFERRALS} in this demo)\n"
                f"• Minimum {WITHDRAWAL_THRESHOLD} naira balance (you have {DEMO_BALANCE} in this demo)\n\n"
                f"In the real app, you would need to meet these requirements before withdrawing."
            )
            frames = generate_error_animation(requirements_message)
            await interaction.response.defer(ephemeral=True)
            await send_animated_message(
                interaction,
                frames,
                duration=2.0,
                final_frame=requirements_message,
                ephemeral=True
            )
    
    demo_withdraw_button.callback = demo_withdraw_callback
    view.add_item(demo_withdraw_button)
    
    # Demo Set bank button
    demo_bank_button = discord.ui.Button(
        style=discord.ButtonStyle.secondary,
        label="Set Bank Info (Demo)",
        custom_id="demo_set_bank"
    )
    
    async def demo_bank_callback(interaction: discord.Interaction):
        # Show demo bank info modal message
        await interaction.response.send_message(
            f"**DEMO MODE**: In the real app, this would open a form where you can set your bank information for withdrawals.\n\n"
            f"You would enter:\n"
            f"• Bank Name\n"
            f"• Account Number\n"
            f"• Account Name\n\n"
            f"This information is saved securely and used only for processing your withdrawal requests.",
            ephemeral=True
        )
    
    demo_bank_button.callback = demo_bank_callback
    view.add_item(demo_bank_button)
    
    # Register button to exit demo mode
    register_button = discord.ui.Button(
        style=discord.ButtonStyle.danger,
        label="Exit Demo & Register",
        custom_id="exit_demo_register"
    )
    
    async def register_callback(interaction: discord.Interaction):
        # Show registration modal
        register_modal = RegisterModal(title="Register")
        await interaction.response.send_modal(register_modal)
    
    register_button.callback = register_callback
    view.add_item(register_button)
    
    return view

def load_transactions() -> Dict[str, Dict]:
    """Load transactions from file."""
    try:
        with open(TRANSACTIONS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_transactions(transactions: Dict[str, Dict]) -> None:
    """Save transactions to file."""
    with open(TRANSACTIONS_FILE, 'w') as f:
        json.dump(transactions, f, indent=4)

def save_transaction(transaction_id: str, transaction_data: Dict) -> None:
    """Save a single transaction."""
    transactions = load_transactions()
    transactions[transaction_id] = transaction_data
    save_transactions(transactions)

def get_transaction(transaction_id: str) -> Optional[Dict]:
    """Get a transaction by ID."""
    transactions = load_transactions()
    return transactions.get(transaction_id)

def update_transaction_status(transaction_id: str, status: str) -> None:
    """Update the status of a transaction."""
    transactions = load_transactions()
    if transaction_id in transactions:
        transactions[transaction_id]["status"] = status
        transactions[transaction_id]["updated_at"] = datetime.now().isoformat()
        save_transactions(transactions)
        
def get_pending_transactions() -> Dict[str, Dict]:
    """Get all pending transactions."""
    transactions = load_transactions()
    return {tid: tdata for tid, tdata in transactions.items() if tdata.get("status") == "pending"}

# Transaction callback functions
async def transaction_confirm_callback(interaction: discord.Interaction):
    """Handle confirmation of a pending transaction."""
    try:
        # Verify admin permissions
        if interaction.user.id != PRIMARY_ADMIN_ID:
            await interaction.response.send_message("Only the primary admin can confirm transactions.", ephemeral=True)
            return
        
        # Extract transaction ID from custom_id
        custom_id = interaction.data["custom_id"]
        transaction_id = custom_id.split("_")[-1]
        
        # Get transaction data
        transaction = get_transaction(transaction_id)
        if not transaction:
            await interaction.response.send_message("Transaction not found.", ephemeral=True)
            return
        
        # Update transaction status
        if transaction["status"] != "pending":
            await interaction.response.send_message(f"Transaction is already {transaction['status']}.", ephemeral=True)
            return
        
        # Update transaction status
        update_transaction_status(transaction_id, "completed")
        
        # Get timestamp for confirmation
        confirmation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Respond to admin
        await interaction.response.send_message(
            f"✅ Transaction **{transaction_id}** confirmed!\n\n" +
            f"Amount: {transaction['amount']} naira\n" +
            f"User: {transaction['username']} (ID: {transaction['user_id']})\n" +
            f"Bank: {transaction['bank_name']}\n" +
            f"Account: {transaction['bank_account_number']} ({transaction['bank_account_name']})\n" +
            f"Confirmation Time: {confirmation_time}",
            ephemeral=True
        )
        
        # Try to notify the user with animation
        try:
            user_obj = await bot.fetch_user(int(transaction["user_id"]))
            if user_obj:
                # Prepare the message content
                message_content = (
                    f"Amount: {transaction['amount']} naira\n" +
                    f"Transaction ID: {transaction_id}\n" +
                    f"Bank: {transaction['bank_name']}\n" +
                    f"Account: {transaction['bank_account_number']} ({transaction['bank_account_name']})\n" +
                    f"Confirmation Time: {confirmation_time}\n\n" +
                    f"Your account has been cleared. Thank you for using KashFlow!\n" +
                    f"You can register again with a new coupon code."
                )
                
                # Generate success animation frames
                frames = generate_coins_animation(transaction['amount'], message_content)
                
                # Final celebratory message
                final_frame = f"💰 **WITHDRAWAL SUCCESSFUL!** 💰\n\n{message_content}"
                
                # Send animated notification
                await send_animated_message(user_obj, frames, duration=3.0, final_frame=final_frame)
        except Exception as e:
            logger.error(f"Failed to notify user about transaction confirmation: {e}")
    except Exception as e:
        logger.error(f"Error in transaction_confirm_callback: {e}")
        # If the interaction has not been responded to yet, respond with an error message
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
            except:
                # If all else fails, try to send a followup message
                try:
                    await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
                except:
                    pass

async def transaction_decline_callback(interaction: discord.Interaction):
    """Handle declining of a pending transaction."""
    try:
        # Verify admin permissions
        if interaction.user.id != PRIMARY_ADMIN_ID:
            await interaction.response.send_message("Only the primary admin can decline transactions.", ephemeral=True)
            return
        
        # Extract transaction ID from custom_id
        custom_id = interaction.data["custom_id"]
        transaction_id = custom_id.split("_")[-1]
        
        # Get transaction data
        transaction = get_transaction(transaction_id)
        if not transaction:
            await interaction.response.send_message("Transaction not found.", ephemeral=True)
            return
        
        # Check if transaction is still pending
        if transaction["status"] != "pending":
            await interaction.response.send_message(f"Transaction is already {transaction['status']}.", ephemeral=True)
            return
        
        # Update transaction status
        update_transaction_status(transaction_id, "declined")
        
        # Get timestamp for decline
        decline_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Respond to admin
        await interaction.response.send_message(
            f"❌ Transaction **{transaction_id}** declined.\n\n" +
            f"Amount: {transaction['amount']} naira\n" +
            f"User: {transaction['username']} (ID: {transaction['user_id']})\n" +
            f"Decline Time: {decline_time}",
            ephemeral=True
        )
        
        # Try to notify the user with animation
        try:
            user_obj = await bot.fetch_user(int(transaction["user_id"]))
            if user_obj:
                # Prepare the message content
                message_content = (
                    f"Your withdrawal of {transaction['amount']} naira has been declined.\n\n" +
                    f"Transaction ID: {transaction_id}\n" +
                    f"Decline Time: {decline_time}\n\n" +
                    f"Please contact an admin for more information."
                )
                
                # Generate error animation frames
                frames = generate_error_animation(message_content)
                
                # Final error message
                final_frame = f"❌ **TRANSACTION DECLINED** ❌\n\n{message_content}"
                
                # Send animated notification
                await send_animated_message(user_obj, frames, duration=2.0, final_frame=final_frame)
        except Exception as e:
            logger.error(f"Failed to notify user about transaction decline: {e}")
    except Exception as e:
        logger.error(f"Error in transaction_decline_callback: {e}")
        # If the interaction has not been responded to yet, respond with an error message
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
            except:
                # If all else fails, try to send a followup message
                try:
                    await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
                except:
                    pass

# UI Components
def create_user_dashboard_view(user_id: int) -> discord.ui.View:
    """Create the dashboard view for regular users."""
    view = discord.ui.View(timeout=None)
    
    # Copy referral ID button
    button_copy_id = discord.ui.Button(
        style=discord.ButtonStyle.primary,
        label="Copy ID to Refer",
        custom_id=f"copy_id_{user_id}"
    )
    button_copy_id.callback = copy_id_callback
    view.add_item(button_copy_id)
    
    # Check balance button
    button_check_balance = discord.ui.Button(
        style=discord.ButtonStyle.secondary,
        label="Check Balance",
        custom_id=f"check_balance_{user_id}"
    )
    button_check_balance.callback = check_balance_callback
    view.add_item(button_check_balance)
    
    # Withdraw button
    button_withdraw = discord.ui.Button(
        style=discord.ButtonStyle.success,
        label="Withdraw",
        custom_id=f"withdraw_{user_id}"
    )
    button_withdraw.callback = withdraw_callback
    view.add_item(button_withdraw)
    
    # Set bank info button
    button_set_bank = discord.ui.Button(
        style=discord.ButtonStyle.secondary,
        label="Set Bank Information",
        custom_id=f"set_bank_{user_id}"
    )
    button_set_bank.callback = set_bank_callback
    view.add_item(button_set_bank)
    
    return view

async def admin_config_callback(interaction: discord.Interaction):
    """Handle showing the configuration options."""
    try:
        if not is_admin(interaction.user.id):
            await interaction.response.send_message("You are not authorized to use admin commands.", ephemeral=True)
            return
        
        # Load the current configuration
        config = load_config()
        
        # Create a view with buttons for each configurable setting
        view = discord.ui.View(timeout=None)
        
        # Add buttons for common settings
        common_settings = [
            ("welcome_bonus", "Welcome Bonus"),
            ("referral_bonus", "Referral Bonus"),
            ("withdrawal_threshold", "Withdrawal Threshold"),
            ("minimum_referrals", "Minimum Referrals"),
            ("coupon_price", "Coupon Price"),
            ("tutorial_enabled", "Tutorial Enabled")
        ]
        
        for setting_key, label in common_settings:
            button = discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label=label,
                custom_id=f"config_{setting_key}"
            )
            
            # We need to create a unique callback for each button
            async def make_callback(setting_key=setting_key):
                async def callback(button_interaction: discord.Interaction):
                    if not is_admin(button_interaction.user.id):
                        await button_interaction.response.send_message("You are not authorized to use admin commands.", ephemeral=True)
                        return
                    
                    # Get current value
                    current_value = config.get(setting_key, globals().get(setting_key.upper(), None))
                    
                    # Show modal to edit the setting
                    modal = ConfigSettingsModal(setting_key, current_value)
                    await button_interaction.response.send_modal(modal)
                
                return callback
            
            button.callback = await make_callback()
            view.add_item(button)
        
        # Add Advanced Settings button
        advanced_button = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Advanced Settings",
            custom_id="config_advanced"
        )
        
        async def advanced_callback(adv_interaction: discord.Interaction):
            if not is_admin(adv_interaction.user.id):
                await adv_interaction.response.send_message("You are not authorized to use admin commands.", ephemeral=True)
                return
            
            # Show dropdown for advanced settings
            options = [
                discord.SelectOption(label="Tutorial Timeout", value="tutorial_timeout"),
                discord.SelectOption(label="Auto-Approve Withdrawals", value="auto_approve_withdrawals"),
                discord.SelectOption(label="Max Daily Withdrawal", value="max_withdrawal_daily"),
                discord.SelectOption(label="System Announcements Enabled", value="system_announcements.enabled"),
                discord.SelectOption(label="System Announcement Message", value="system_announcements.message")
            ]
            
            # Create select menu
            select = discord.ui.Select(
                placeholder="Select a setting to configure",
                options=options,
                custom_id="advanced_setting_select"
            )
            
            async def select_callback(select_interaction: discord.Interaction):
                setting_key = select_interaction.data["values"][0]
                
                # Get the current value based on the key (handle nested keys)
                if "." in setting_key:
                    parts = setting_key.split(".")
                    current = config
                    for part in parts:
                        if part in current:
                            current = current[part]
                        else:
                            current = None
                            break
                    current_value = current
                else:
                    current_value = config.get(setting_key, globals().get(setting_key.upper(), None))
                
                # Show modal to edit the setting
                modal = ConfigSettingsModal(setting_key, current_value)
                await select_interaction.response.send_modal(modal)
            
            select.callback = select_callback
            
            # Create view with select menu
            select_view = discord.ui.View(timeout=None)
            select_view.add_item(select)
            
            await adv_interaction.response.send_message(
                "Select an advanced setting to configure:",
                view=select_view,
                ephemeral=True
            )
        
        advanced_button.callback = advanced_callback
        view.add_item(advanced_button)
        
        # Add a button to export the current config
        export_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Export Configuration",
            custom_id="config_export"
        )
        
        async def export_callback(export_interaction: discord.Interaction):
            if not is_admin(export_interaction.user.id):
                await export_interaction.response.send_message("You are not authorized to use admin commands.", ephemeral=True)
                return
            
            # Format the configuration for display
            config_formatted = json.dumps(config, indent=2)
            
            # If the config is too long, send as a file
            if len(config_formatted) > 1900:
                file = discord.File(
                    fp=io.StringIO(config_formatted),
                    filename="config.json"
                )
                await export_interaction.response.send_message(
                    "Current configuration:",
                    file=file,
                    ephemeral=True
                )
            else:
                await export_interaction.response.send_message(
                    f"Current configuration:```json\n{config_formatted}\n```",
                    ephemeral=True
                )
        
        export_button.callback = export_callback
        view.add_item(export_button)
        
        # Send the view with configuration options
        await interaction.response.send_message(
            "**Bot Configuration**\n\n" +
            "Select a setting to configure:",
            view=view,
            ephemeral=True
        )
    except Exception as e:
        logger.error(f"Error in admin_config_callback: {e}")
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
            except:
                pass

def create_admin_dashboard_view() -> discord.ui.View:
    """Create the dashboard view for admins."""
    view = discord.ui.View(timeout=None)
    
    # Start button
    button_start = discord.ui.Button(
        style=discord.ButtonStyle.primary,
        label="Start",
        custom_id="admin_start"
    )
    button_start.callback = admin_start_callback
    view.add_item(button_start)
    
    # Configuration button
    button_config = discord.ui.Button(
        style=discord.ButtonStyle.primary,
        label="Configure Settings",
        custom_id="admin_config"
    )
    button_config.callback = admin_config_callback
    view.add_item(button_config)
    
    # View users button
    button_view_users = discord.ui.Button(
        style=discord.ButtonStyle.secondary,
        label="View Users",
        custom_id="admin_view_users"
    )
    button_view_users.callback = admin_view_users_callback
    view.add_item(button_view_users)
    
    # Generate coupons button
    button_generate = discord.ui.Button(
        style=discord.ButtonStyle.success,
        label="Generate Coupons",
        custom_id="admin_generate"
    )
    button_generate.callback = admin_generate_callback
    view.add_item(button_generate)
    
    # Clear used coupons button
    button_clear_used = discord.ui.Button(
        style=discord.ButtonStyle.danger,
        label="Clear Used Coupons",
        custom_id="admin_clear_used"
    )
    button_clear_used.callback = admin_clear_used_callback
    view.add_item(button_clear_used)
    
    # View balance button
    button_view_balance = discord.ui.Button(
        style=discord.ButtonStyle.secondary,
        label="View Total Balance",
        custom_id="admin_view_balance"
    )
    button_view_balance.callback = admin_view_balance_callback
    view.add_item(button_view_balance)
    
    # View pending transactions button
    button_pending_transactions = discord.ui.Button(
        style=discord.ButtonStyle.primary,
        label="View Pending Transactions",
        custom_id="admin_view_pending"
    )
    button_pending_transactions.callback = admin_view_pending_transactions_callback
    view.add_item(button_pending_transactions)
    
    # Toggle bot status button
    bot_status_label = "Disable Bot" if BOT_ENABLED_FOR_USERS else "Enable Bot"
    bot_status_style = discord.ButtonStyle.danger if BOT_ENABLED_FOR_USERS else discord.ButtonStyle.success
    button_toggle_bot = discord.ui.Button(
        style=bot_status_style,
        label=bot_status_label,
        custom_id="admin_toggle_bot"
    )
    button_toggle_bot.callback = admin_toggle_bot_status_callback
    view.add_item(button_toggle_bot)
    
    return view

# Tutorial UI View
class TutorialView(discord.ui.View):
    def __init__(self, user_id: int, step: int = 0):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.step = step
        self.max_steps = 5
        
        # Get content for current step
        content = get_tutorial_content(self.step)
        
        # Add buttons based on current step
        if self.step == 0:  # First step (welcome)
            # Next button (Start Tutorial)
            next_button = discord.ui.Button(
                style=discord.ButtonStyle.primary,
                label=content["next_label"],
                custom_id=f"tutorial_next_{user_id}"
            )
            next_button.callback = self.next_callback
            self.add_item(next_button)
            
            # Skip button
            skip_button = discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label=content["skip_label"],
                custom_id=f"tutorial_skip_{user_id}"
            )
            skip_button.callback = self.skip_callback
            self.add_item(skip_button)
        
        elif self.step == self.max_steps:  # Last step
            # Back button
            back_button = discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label=content["back_label"],
                custom_id=f"tutorial_back_{user_id}"
            )
            back_button.callback = self.back_callback
            self.add_item(back_button)
            
            # Finish button
            finish_button = discord.ui.Button(
                style=discord.ButtonStyle.success,
                label=content["finish_label"],
                custom_id=f"tutorial_finish_{user_id}"
            )
            finish_button.callback = self.finish_callback
            self.add_item(finish_button)
            
        else:  # Middle steps
            # Back button
            back_button = discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label=content["back_label"],
                custom_id=f"tutorial_back_{user_id}"
            )
            back_button.callback = self.back_callback
            self.add_item(back_button)
            
            # Next button
            next_button = discord.ui.Button(
                style=discord.ButtonStyle.primary,
                label=content["next_label"],
                custom_id=f"tutorial_next_{user_id}"
            )
            next_button.callback = self.next_callback
            self.add_item(next_button)
    
    async def next_callback(self, interaction: discord.Interaction):
        # Verify user ID
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This tutorial is not for you.", ephemeral=True)
            return
            
        # Update step
        new_step = min(self.step + 1, self.max_steps)
        
        # Update user progress in database
        update_tutorial_progress(self.user_id, step=new_step)
        
        # Get content for new step
        content = get_tutorial_content(new_step)
        
        # Create animated message for tutorial
        message = f"# {content['title']}\n\n{content['content']}"
        frames = generate_tutorial_frames(message)
        
        # Create new view for this step
        new_view = TutorialView(self.user_id, new_step)
        
        # Send animated tutorial update
        await interaction.response.defer()
        await send_animated_message(
            interaction, 
            frames, 
            duration=1.5, 
            final_frame=message
        )
        # Send the new view as a followup
        await interaction.followup.send(view=new_view)
    
    async def back_callback(self, interaction: discord.Interaction):
        # Verify user ID
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This tutorial is not for you.", ephemeral=True)
            return
            
        # Update step
        new_step = max(self.step - 1, 0)
        
        # Update user progress in database
        update_tutorial_progress(self.user_id, step=new_step)
        
        # Get content for new step
        content = get_tutorial_content(new_step)
        
        # Create animated message for tutorial
        message = f"# {content['title']}\n\n{content['content']}"
        frames = generate_tutorial_frames(message)
        
        # Create new view for this step
        new_view = TutorialView(self.user_id, new_step)
        
        # Send animated tutorial update
        await interaction.response.defer()
        await send_animated_message(
            interaction, 
            frames, 
            duration=1.5, 
            final_frame=message
        )
        # Send the new view as a followup
        await interaction.followup.send(view=new_view)
    
    async def skip_callback(self, interaction: discord.Interaction):
        # Verify user ID
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This tutorial is not for you.", ephemeral=True)
            return
            
        # Mark tutorial as completed in database
        update_tutorial_progress(self.user_id, completed=True)
        
        # Show dashboard instead
        user = get_user(self.user_id)
        
        await interaction.response.send_message(
            f"**Tutorial skipped. Welcome to your dashboard, {interaction.user.name}!**\n\n" +
            f"Current Balance: **{user.balance}** naira\n" +
            f"Referral Count: **{user.referral_count}**\n" +
            f"Withdrawal Requirements: **{MINIMUM_REFERRALS}** referrals & **{WITHDRAWAL_THRESHOLD}** naira minimum\n\n" +
            "**Dashboard Controls**:\n" +
            "• **Copy ID to Refer**: Get your referral ID to share with others\n" +
            "• **Check Balance**: View your current balance and referral count\n" +
            f"• **Withdraw**: Request withdrawal when eligible ({MINIMUM_REFERRALS} referrals & {WITHDRAWAL_THRESHOLD} naira minimum)\n" +
            "• **Set Bank Information**: Update your bank details for withdrawals",
            view=create_user_dashboard_view(self.user_id),
            ephemeral=False
        )
    
    async def finish_callback(self, interaction: discord.Interaction):
        # Verify user ID
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This tutorial is not for you.", ephemeral=True)
            return
            
        # Mark tutorial as completed in database
        update_tutorial_progress(self.user_id, completed=True)
        
        # Show congratulations message with animation
        message = "# 🎉 Tutorial Complete! 🎉\n\nYou've completed the KashFlow tutorial. You now have all the knowledge to start earning rewards by referring friends!\n\nRemember, each referral earns you additional naira. Good luck!"
        frames = generate_success_animation(message)
        
        # Send animated congratulations message
        await interaction.response.defer()
        await send_animated_message(
            interaction, 
            frames, 
            duration=2.0, 
            final_frame=message
        )
        
        # Show dashboard as followup
        user = get_user(self.user_id)
        await interaction.followup.send(
            f"**Welcome to your dashboard, {interaction.user.name}!**\n\n" +
            f"Current Balance: **{user.balance}** naira\n" +
            f"Referral Count: **{user.referral_count}**\n" +
            f"Withdrawal Requirements: **{MINIMUM_REFERRALS}** referrals & **{WITHDRAWAL_THRESHOLD}** naira minimum\n\n" +
            "**Dashboard Controls**:\n" +
            "• **Copy ID to Refer**: Get your referral ID to share with others\n" +
            "• **Check Balance**: View your current balance and referral count\n" +
            f"• **Withdraw**: Request withdrawal when eligible ({MINIMUM_REFERRALS} referrals & {WITHDRAWAL_THRESHOLD} naira minimum)\n" +
            "• **Set Bank Information**: Update your bank details for withdrawals",
            view=create_user_dashboard_view(self.user_id),
            ephemeral=False
        )

class RegisterModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.add_item(
            discord.ui.TextInput(
                label="Coupon Code",
                placeholder="Enter your coupon code",
                custom_id="coupon_code",
                required=True
            )
        )
        
        self.add_item(
            discord.ui.TextInput(
                label="Referral ID (Optional)",
                placeholder="Enter referral ID if you have one",
                custom_id="referral_id",
                required=False
            )
        )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        coupon_code = self.children[0].value
        referral_id_str = self.children[1].value
        
        # Check if coupon code is valid
        if not is_valid_coupon(coupon_code):
            await interaction.followup.send("Invalid or already used coupon code.", ephemeral=True)
            return
        
        # Check if user already exists
        users = load_users()
        user_id = interaction.user.id
        
        if user_id in users:
            await interaction.followup.send("You're already registered. Use the dashboard.", ephemeral=True)
            return
        
        # Process referral
        referred_by = None
        if referral_id_str:
            try:
                referred_by = int(referral_id_str)
                # Ensure referrer exists and is not self
                if referred_by == user_id:
                    await interaction.followup.send("You cannot refer yourself.", ephemeral=True)
                    return
                
                if referred_by not in users:
                    await interaction.followup.send("Invalid referral ID.", ephemeral=True)
                    return
            except ValueError:
                await interaction.followup.send("Invalid referral ID format.", ephemeral=True)
                return
        
        # Create user
        user = User(
            id=user_id,
            username=interaction.user.name,
            balance=WELCOME_BONUS,  # Welcome bonus
            referred_by=referred_by
        )
        
        # Add referral bonus to referrer
        if referred_by:
            referrer = users[referred_by]
            referrer.balance += REFERRAL_BONUS
            referrer.referral_count += 1
            users[referred_by] = referrer
            save_users(users)
            
            # Try to notify the referrer with animation
            try:
                referrer_user = await bot.fetch_user(referred_by)
                if referrer_user:
                    message = (
                        f"You just earned a referral bonus for referring {interaction.user.name}!\n" +
                        f"Your new balance is {referrer.balance} naira.\n" +
                        f"Your referral count is now {referrer.referral_count}.\n\n" +
                        f"Keep sharing your referral ID to earn more!"
                    )
                    
                    # Generate coins animation frames
                    frames = generate_coins_animation(REFERRAL_BONUS, message)
                    
                    # Add sparkle animation at the end
                    final_frame = f"🎉 **REFERRAL BONUS RECEIVED!** 🎉\n\n" + message
                    
                    # Send the animated notification
                    await send_animated_message(referrer_user, frames, duration=3.0, final_frame=final_frame)
            except Exception as e:
                logger.error(f"Failed to notify referrer about bonus: {e}")
        
        # Mark coupon as used
        mark_coupon_used(coupon_code)
        
        # Save new user
        add_user(user)
        
        # Create dashboard view
        view = create_user_dashboard_view(user_id)
        
        # Prepare welcome message
        welcome_message = (
            f"Registration successful! You received {WELCOME_BONUS} naira as welcome bonus." +
            (f" Your referrer received {REFERRAL_BONUS} naira." if referred_by else "")
        )
        
        # Generate success animation frames
        frames = generate_coins_animation(WELCOME_BONUS, welcome_message)
        
        # Final frame with complete dashboard instructions
        final_frame = (
            f"✅ {welcome_message}\n\n" +
            "**Your Dashboard Controls**: \n" +
            "• **Copy ID to Refer**: Get your referral ID to share with others\n" +
            "• **Check Balance**: View your current balance and referral count\n" +
            f"• **Withdraw**: Request withdrawal when eligible ({MINIMUM_REFERRALS} referrals & {WITHDRAWAL_THRESHOLD} naira minimum)\n" +
            "• **Set Bank Information**: Update your bank details for withdrawals"
        )
        
        # Send animated welcome message
        await send_animated_message(
            interaction, 
            frames, 
            duration=3.0, 
            final_frame=final_frame, 
            ephemeral=False
        )
        
        # Add dashboard buttons separately since we used animation
        dashboard_message = await interaction.followup.send(
            "Your Dashboard Controls:",
            view=view,
            ephemeral=False
        )
        
        # Start tutorial if enabled
        if TUTORIAL_ENABLED:
            try:
                # Get tutorial content for first step
                tutorial_step = 0
                tutorial_content = get_tutorial_content(tutorial_step)
                
                # Create message content
                message = f"# {tutorial_content['title']}\n\n{tutorial_content['content']}"
                
                # Create tutorial view
                tutorial_view = TutorialView(user_id, tutorial_step)
                
                # Send tutorial message with animation
                frames = generate_tutorial_frames(message)
                
                # Send animated tutorial introduction
                await send_animated_message(
                    interaction.user,  # Send DM to user
                    frames,
                    duration=2.0,
                    final_frame=message
                )
                
                # Send view as a followup
                await interaction.user.send(view=tutorial_view)
                
                # Update user's tutorial progress
                update_tutorial_progress(user_id, step=tutorial_step)
                
                # Send instruction to check DMs
                await interaction.followup.send(
                    "📚 **Check your DMs for an interactive tutorial!** I've sent you a step-by-step guide to help you get started with KashFlow.",
                    ephemeral=False
                )
            except Exception as e:
                logger.error(f"Failed to start tutorial for user {user_id}: {e}")
                # If we can't DM the user, show tutorial in the channel
                await interaction.followup.send(
                    "I couldn't send you a DM. Please make sure your privacy settings allow DMs from server members.",
                    ephemeral=True
                )

class BankInfoModal(discord.ui.Modal):
    def __init__(self, user_id: int, *args, **kwargs):
        super().__init__(title="Set Bank Information", *args, **kwargs)
        self.user_id = user_id
        
        self.add_item(
            discord.ui.TextInput(
                label="Bank Name",
                placeholder="Enter your bank name",
                custom_id="bank_name",
                required=True
            )
        )
        
        self.add_item(
            discord.ui.TextInput(
                label="Account Number",
                placeholder="Enter your account number",
                custom_id="account_number",
                required=True
            )
        )
        
        self.add_item(
            discord.ui.TextInput(
                label="Account Name",
                placeholder="Enter your account name",
                custom_id="account_name",
                required=True
            )
        )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            
            user = get_user(self.user_id)
            if not user:
                await interaction.followup.send("User not found.", ephemeral=True)
                return
            
            # Validate input fields
            if not all([self.children[0].value, self.children[1].value, self.children[2].value]):
                await interaction.followup.send("Please fill in all bank information fields.", ephemeral=True)
                return
                
            # Update bank information
            user.bank_name = self.children[0].value.strip()
            user.bank_account_number = self.children[1].value.strip()
            user.bank_account_name = self.children[2].value.strip()
            
            # Save updated user
            add_user(user)
            logger.info(f"Bank information updated for user {user.id}")
            
            await interaction.followup.send(
                "Bank information updated successfully!",
                view=create_user_dashboard_view(self.user_id),
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error updating bank information: {e}")
            await interaction.followup.send(
                "An error occurred while saving your bank information. Please try again.",
                ephemeral=True
            )

class ConfigSettingsModal(discord.ui.Modal):
    def __init__(self, setting_key: str, current_value, *args, **kwargs):
        super().__init__(title=f"Configure {setting_key.replace('_', ' ').title()}", *args, **kwargs)
        self.setting_key = setting_key
        
        # Get the display name and description based on the setting key
        setting_info = {
            "welcome_bonus": {
                "label": "Welcome Bonus (naira)",
                "placeholder": "Amount given to new users upon registration",
                "type": "int"
            },
            "referral_bonus": {
                "label": "Referral Bonus (naira)",
                "placeholder": "Amount earned per successful referral",
                "type": "int"
            },
            "withdrawal_threshold": {
                "label": "Withdrawal Threshold (naira)",
                "placeholder": "Minimum balance required to withdraw",
                "type": "int"
            },
            "minimum_referrals": {
                "label": "Minimum Referrals",
                "placeholder": "Minimum referrals needed to withdraw",
                "type": "int"
            },
            "tutorial_enabled": {
                "label": "Tutorial Enabled (true/false)",
                "placeholder": "Whether the tutorial feature is enabled",
                "type": "bool"
            },
            "tutorial_timeout": {
                "label": "Tutorial Timeout (seconds)",
                "placeholder": "How long before tutorial times out",
                "type": "int"
            },
            "auto_approve_withdrawals": {
                "label": "Auto-Approve Withdrawals (true/false)",
                "placeholder": "Whether to automatically approve withdrawals",
                "type": "bool"
            },
            "max_withdrawal_daily": {
                "label": "Max Daily Withdrawal (naira)",
                "placeholder": "Maximum daily withdrawal amount",
                "type": "int"
            },
            "coupon_price": {
                "label": "Coupon Price (naira)",
                "placeholder": "Price of each coupon code",
                "type": "int"
            },
            "system_announcements.message": {
                "label": "System Announcement Message",
                "placeholder": "Message to show to users",
                "type": "str"
            },
            "system_announcements.enabled": {
                "label": "System Announcements Enabled (true/false)",
                "placeholder": "Whether to show system announcements",
                "type": "bool"
            }
        }
        
        # Get the info for this setting
        info = setting_info.get(setting_key, {
            "label": setting_key.replace("_", " ").title(),
            "placeholder": "Enter the new value",
            "type": "str"
        })
        
        # Convert current value to string
        str_value = str(current_value).lower() if info["type"] == "bool" else str(current_value)
        
        # Add the text input
        self.add_item(discord.ui.TextInput(
            label=info["label"],
            placeholder=info["placeholder"],
            required=True,
            default=str_value,
            custom_id="value"
        ))
        
        # Store the value type
        self.value_type = info["type"]
        
    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Only allow admins to change settings
            if not is_admin(interaction.user.id):
                await interaction.response.send_message(
                    "You are not authorized to change system settings.",
                    ephemeral=True
                )
                return
            
            # Get the new value
            new_value_str = self.children[0].value.strip()
            
            # Convert to the appropriate type
            if self.value_type == "int":
                try:
                    new_value = int(new_value_str)
                except ValueError:
                    await interaction.response.send_message(
                        "Invalid value. Please enter a valid integer.",
                        ephemeral=True
                    )
                    return
            elif self.value_type == "bool":
                new_value_lower = new_value_str.lower()
                if new_value_lower in ("true", "yes", "1", "on"):
                    new_value = True
                elif new_value_lower in ("false", "no", "0", "off"):
                    new_value = False
                else:
                    await interaction.response.send_message(
                        "Invalid value. Please enter 'true' or 'false'.",
                        ephemeral=True
                    )
                    return
            else:
                new_value = new_value_str
                
            # Update the configuration
            success = update_config(self.setting_key, new_value)
            
            if success:
                # Apply the new configuration
                apply_config()
                
                # Show success message
                await interaction.response.send_message(
                    f"✅ Successfully updated `{self.setting_key}` to `{new_value}`.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"❌ Failed to update setting. Please try again.",
                    ephemeral=True
                )
        except Exception as e:
            logger.error(f"Error in ConfigSettingsModal.on_submit: {e}")
            if not interaction.response.is_done():
                try:
                    await interaction.response.send_message(
                        "Something went wrong. Please try again.",
                        ephemeral=True
                    )
                except:
                    pass

class GenerateCouponsModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs):
        super().__init__(title="Generate Coupons", *args, **kwargs)
        
        self.add_item(
            discord.ui.TextInput(
                label="Number of Coupons",
                placeholder="Enter number of coupons to generate",
                custom_id="num_coupons",
                required=True
            )
        )
        
        self.add_item(
            discord.ui.TextInput(
                label="Suffix (Optional)",
                placeholder="Optional suffix for coupon codes",
                custom_id="suffix",
                required=False
            )
        )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            num_coupons = int(self.children[0].value)
            if num_coupons <= 0 or num_coupons > 100:
                await interaction.followup.send("Please enter a valid number between 1 and 100.", ephemeral=True)
                return
        except ValueError:
            await interaction.followup.send("Please enter a valid number.", ephemeral=True)
            return
        
        suffix = self.children[1].value
        
        # Generate coupons
        coupons = load_coupons()
        new_coupons = []
        
        for _ in range(num_coupons):
            while True:
                coupon_code = generate_coupon_code(suffix)
                if coupon_code not in coupons:
                    coupons[coupon_code] = False  # Mark as unused
                    new_coupons.append(coupon_code)
                    break
        
        save_coupons(coupons)
        
        # Format output
        coupon_list = "\n".join(new_coupons)
        
        # Create file if list is too long
        if len(coupon_list) > 1900:
            file_content = "\n".join(new_coupons)
            file = discord.File(
                fp=io.StringIO(file_content),
                filename="coupons.txt"
            )
            await interaction.followup.send(
                f"Generated {num_coupons} coupons. See attached file.",
                file=file,
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"Generated {num_coupons} coupons:\n```\n{coupon_list}\n```",
                ephemeral=True
            )

# Button Callbacks
async def copy_id_callback(interaction: discord.Interaction):
    try:
        custom_id = interaction.data["custom_id"]
        user_id = int(custom_id.split("_")[-1])
        
        if interaction.user.id != user_id:
            await interaction.response.send_message("This is not your dashboard.", ephemeral=True)
            return
        
        await interaction.response.send_message(
            f"Your referral ID is: `{user_id}`\nShare this ID with new users to earn referral bonuses!",
            ephemeral=True
        )
    except Exception as e:
        logger.error(f"Error in copy_id_callback: {e}")
        # If the interaction has not been responded to yet, respond with an error message
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
            except:
                # If all else fails, try to send a followup message
                try:
                    await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
                except:
                    pass

async def check_balance_callback(interaction: discord.Interaction):
    try:
        custom_id = interaction.data["custom_id"]
        user_id = int(custom_id.split("_")[-1])
        
        if interaction.user.id != user_id:
            await interaction.response.send_message("This is not your dashboard.", ephemeral=True)
            return
        
        user = get_user(user_id)
        if not user:
            await interaction.response.send_message("User not found.", ephemeral=True)
            return
        
        await interaction.response.send_message(
            f"Your current balance is: ₦{user.balance}\n" +
            f"Referral count: {user.referral_count} (need {MINIMUM_REFERRALS} to withdraw)\n" +
            f"Withdrawal threshold: ₦{WITHDRAWAL_THRESHOLD}",
            ephemeral=True
        )
    except Exception as e:
        logger.error(f"Error in check_balance_callback: {e}")
        # If the interaction has not been responded to yet, respond with an error message
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
            except:
                # If all else fails, try to send a followup message
                try:
                    await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
                except:
                    pass

async def withdraw_callback(interaction: discord.Interaction):
    try:
        custom_id = interaction.data["custom_id"]
        user_id = int(custom_id.split("_")[-1])
        
        if interaction.user.id != user_id:
            await interaction.response.send_message("This is not your dashboard.", ephemeral=True)
            return
        
        user = get_user(user_id)
        if not user:
            await interaction.response.send_message("User not found.", ephemeral=True)
            return
        
        # Check if user has minimum required referrals
        if user.referral_count < MINIMUM_REFERRALS:
            await interaction.response.send_message(
                f"You need at least {MINIMUM_REFERRALS} referrals to withdraw. " +
                f"Your current referral count is {user.referral_count}.",
                ephemeral=True
            )
            return
        
        # Check if user is eligible for withdrawal based on balance
        if user.balance < WITHDRAWAL_THRESHOLD:
            await interaction.response.send_message(
                f"You need at least {WITHDRAWAL_THRESHOLD} naira to withdraw. " +
                f"Your current balance is {user.balance} naira.",
                ephemeral=True
            )
            return
        
        # Check if bank information is set
        if not user.bank_name or not user.bank_account_number or not user.bank_account_name:
            await interaction.response.send_message(
                "Please set your bank information before withdrawing.",
                ephemeral=True
            )
            return
        
        # Create a transaction record before user deletion
        transaction_id = str(uuid.uuid4())[:8]  # Generate a short unique ID
        transaction_data = {
            "id": transaction_id,
            "user_id": user.id,
            "username": user.username,
            "amount": user.balance,
            "bank_name": user.bank_name,
            "bank_account_number": user.bank_account_number,
            "bank_account_name": user.bank_account_name,
            "referral_count": user.referral_count,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }
        
        # Save transaction record
        save_transaction(transaction_id, transaction_data)
        
        # Create confirmation view with buttons
        view = discord.ui.View(timeout=None)
        
        # Confirm button
        confirm_button = discord.ui.Button(
            style=discord.ButtonStyle.success,
            label="Confirm Transaction",
            custom_id=f"confirm_transaction_{transaction_id}"
        )
        confirm_button.callback = transaction_confirm_callback
        view.add_item(confirm_button)
        
        # Decline button
        decline_button = discord.ui.Button(
            style=discord.ButtonStyle.danger,
            label="Decline Transaction",
            custom_id=f"decline_transaction_{transaction_id}"
        )
        decline_button.callback = transaction_decline_callback
        view.add_item(decline_button)
        
        # Process the withdrawal
        try:
            # Check if PRIMARY_ADMIN_ID is properly configured
            if PRIMARY_ADMIN_ID and PRIMARY_ADMIN_ID != 0:
                # If PRIMARY_ADMIN_ID is configured, send notification to admin
                try:
                    admin = await bot.fetch_user(PRIMARY_ADMIN_ID)
                    if admin:
                        await admin.send(
                            f"**PENDING WITHDRAWAL REQUEST** (ID: {transaction_id})\n" +
                            f"User: {user.username} (ID: {user.id})\n" +
                            f"Amount: {user.balance} naira\n" +
                            f"Referral Count: {user.referral_count}\n" +
                            f"Bank Name: {user.bank_name}\n" +
                            f"Account Number: {user.bank_account_number}\n" +
                            f"Account Name: {user.bank_account_name}\n" +
                            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                            view=view
                        )
                        logger.info(f"Withdrawal notification sent to admin for transaction {transaction_id}")
                    else:
                        logger.warning(f"Admin user with ID {PRIMARY_ADMIN_ID} not found, but proceeding with withdrawal")
                except Exception as e:
                    logger.error(f"Failed to send admin notification, but proceeding with withdrawal: {e}")
            else:
                logger.warning("PRIMARY_ADMIN_ID not configured, proceeding with withdrawal without admin notification")
            
            # Mark transaction as approved automatically if no PRIMARY_ADMIN_ID is set
            if not PRIMARY_ADMIN_ID or PRIMARY_ADMIN_ID == 0:
                transaction_data["status"] = "approved"
                save_transaction(transaction_id, transaction_data)
                logger.info(f"Transaction {transaction_id} auto-approved due to missing PRIMARY_ADMIN_ID")
            
            # Delete the user account - we now do this whether or not admin notification succeeded
            delete_user(user_id)
            
            # Send confirmation to user
            await interaction.response.send_message(
                f"✅ Your withdrawal request for {user.balance} naira is pending admin approval.\n" +
                f"Transaction ID: {transaction_id}\n" +
                "You will receive a confirmation message once approved.\n" +
                "Please wait while we process your withdrawal.",
                ephemeral=False
            )
            
        except Exception as e:
            logger.error(f"Error processing withdrawal: {e}")
            await interaction.response.send_message(
                "We couldn't process your withdrawal at this moment. Please try again later or contact support.",
                ephemeral=True
            )
            # Delete the transaction record since it failed
            transactions = load_transactions()
            if transaction_id in transactions:
                transactions.pop(transaction_id)
                save_transactions(transactions)
    except Exception as e:
        logger.error(f"Error in withdraw_callback: {e}")
        # If the interaction has not been responded to yet, respond with an error message
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
            except:
                # If all else fails, try to send a followup message
                try:
                    await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
                except:
                    pass

async def set_bank_callback(interaction: discord.Interaction):
    try:
        custom_id = interaction.data["custom_id"]
        user_id = int(custom_id.split("_")[-1])
        
        if interaction.user.id != user_id:
            await interaction.response.send_message("This is not your dashboard.", ephemeral=True)
            return
        
        user = get_user(user_id)
        if not user:
            await interaction.response.send_message("User not found.", ephemeral=True)
            return
        
        # Show bank info modal
        bank_modal = BankInfoModal(user_id=user_id)
        await interaction.response.send_modal(bank_modal)
    except Exception as e:
        logger.error(f"Error in set_bank_callback: {e}")
        # If the interaction has not been responded to yet, respond with an error message
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
            except:
                # If all else fails, try to send a followup message
                try:
                    await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
                except:
                    pass

# Helper function to check if a user is an admin
def is_admin(user_id: int) -> bool:
    """Check if a user is an admin."""
    return user_id in ADMIN_IDS or user_id == PRIMARY_ADMIN_ID

async def admin_start_callback(interaction: discord.Interaction):
    try:
        if not is_admin(interaction.user.id):
            await interaction.response.send_message("You are not authorized to use admin commands.", ephemeral=True)
            return
        
        await interaction.response.send_message(
            "Admin Dashboard",
            view=create_admin_dashboard_view(),
            ephemeral=True
        )
    except Exception as e:
        logger.error(f"Error in admin_start_callback: {e}")
        # If the interaction has not been responded to yet, respond with an error message
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
            except:
                # If all else fails, try to send a followup message
                try:
                    await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
                except:
                    pass

async def admin_view_users_callback(interaction: discord.Interaction):
    try:
        if not is_admin(interaction.user.id):
            await interaction.response.send_message("You are not authorized to use admin commands.", ephemeral=True)
            return
        
        users = load_users()
        if not users:
            await interaction.response.send_message("No users found.", ephemeral=True)
            return
        
        # Format user info
        user_info = []
        for user_id, user in users.items():
            user_info.append(
                f"**User: {user.username} (ID: {user.id})**\n" +
                f"Balance: {user.balance} naira\n" +
                f"Referral Count: {user.referral_count}\n" +
                f"Referred By: {user.referred_by}\n" +
                f"Bank Name: {user.bank_name}\n" +
                f"Account Number: {user.bank_account_number}\n" +
                f"Account Name: {user.bank_account_name}\n" +
                f"Created At: {user.created_at}\n"
            )
        
        # Split messages if too long
        messages = []
        current_message = ""
        
        for info in user_info:
            if len(current_message) + len(info) > 1900:
                messages.append(current_message)
                current_message = info
            else:
                current_message += info + "\n"
        
        if current_message:
            messages.append(current_message)
        
        # Send messages
        for i, message in enumerate(messages):
            await interaction.followup.send(
                f"User List (Part {i+1}/{len(messages)}):\n{message}",
                ephemeral=True
            ) if i > 0 else await interaction.response.send_message(
                f"User List (Part {i+1}/{len(messages)}):\n{message}",
                ephemeral=True
            )
    except Exception as e:
        logger.error(f"Error in admin_view_users_callback: {e}")
        # If the interaction has not been responded to yet, respond with an error message
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
            except:
                # If all else fails, try to send a followup message
                try:
                    await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
                except:
                    pass

async def admin_generate_callback(interaction: discord.Interaction):
    try:
        # Check if PRIMARY_ADMIN_ID is properly configured
        if not PRIMARY_ADMIN_ID or PRIMARY_ADMIN_ID == 0:
            await interaction.response.send_message(
                "The PRIMARY_ADMIN_ID is not configured. Any admin can generate coupon codes temporarily.",
                ephemeral=True
            )
            # Allow any admin to generate coupons if PRIMARY_ADMIN_ID is not set
            if not is_admin(interaction.user.id):
                await interaction.followup.send("However, you are not an admin.", ephemeral=True)
                return
        else:
            # Only the primary admin can generate coupon codes if PRIMARY_ADMIN_ID is set
            if interaction.user.id != PRIMARY_ADMIN_ID:
                await interaction.response.send_message("Only the primary admin can generate coupon codes.", ephemeral=True)
                return
        
        # Show generate coupons modal
        generate_modal = GenerateCouponsModal()
        await interaction.response.send_modal(generate_modal)
    except Exception as e:
        logger.error(f"Error in admin_generate_callback: {e}")
        # If the interaction has not been responded to yet, respond with an error message
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
            except:
                # If all else fails, try to send a followup message
                try:
                    await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
                except:
                    pass

async def admin_clear_used_callback(interaction: discord.Interaction):
    try:
        if not is_admin(interaction.user.id):
            await interaction.response.send_message("You are not authorized to use admin commands.", ephemeral=True)
            return
        
        cleared_count = clear_used_coupons()
        
        await interaction.response.send_message(
            f"Cleared {cleared_count} used coupons.",
            ephemeral=True
        )
    except Exception as e:
        logger.error(f"Error in admin_clear_used_callback: {e}")
        # If the interaction has not been responded to yet, respond with an error message
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
            except:
                # If all else fails, try to send a followup message
                try:
                    await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
                except:
                    pass

async def admin_view_balance_callback(interaction: discord.Interaction):
    try:
        if not is_admin(interaction.user.id):
            await interaction.response.send_message("You are not authorized to use admin commands.", ephemeral=True)
            return
        
        total_balance = calculate_total_balance()
        users = load_users()
        
        await interaction.response.send_message(
            f"Total balance across all {len(users)} users: {total_balance} naira",
            ephemeral=True
        )
    except Exception as e:
        logger.error(f"Error in admin_view_balance_callback: {e}")
        # If the interaction has not been responded to yet, respond with an error message
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
            except:
                # If all else fails, try to send a followup message
                try:
                    await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
                except:
                    pass

async def admin_view_pending_transactions_callback(interaction: discord.Interaction):
    """Handle viewing all pending transactions."""
    try:
        if not is_admin(interaction.user.id):
            await interaction.response.send_message("You are not authorized to use admin commands.", ephemeral=True)
            return
        
        pending_transactions = get_pending_transactions()
        
        if not pending_transactions:
            await interaction.response.send_message(
                "There are no pending transactions.",
                ephemeral=True
            )
            return
        
        # Format the pending transactions
        pending_list = []
        for tid, tdata in pending_transactions.items():
            pending_list.append(
                f"ID: **{tid}**\n"
                f"User: {tdata['username']} ({tdata['user_id']})\n"
                f"Amount: {tdata['amount']} naira\n"
                f"Bank: {tdata['bank_name']}\n"
                f"Account: {tdata['bank_account_number']} ({tdata['bank_account_name']})\n"
                f"Time: {tdata.get('timestamp', 'Unknown')}\n"
                "--------------------"
            )
            
        # Create the message with confirmation buttons for each transaction
        message = f"**{len(pending_transactions)} Pending Transactions**\n\n"
        
        # Split into chunks if necessary
        if len(pending_list) > 5:
            message += f"Showing first 5 of {len(pending_list)} transactions:\n\n"
            pending_list = pending_list[:5]
        
        message += "\n".join(pending_list)
        
        # Create a view with buttons for each transaction
        view = discord.ui.View(timeout=None)
        
        # Add approve all button
        approve_all_button = discord.ui.Button(
            style=discord.ButtonStyle.success,
            label=f"Approve All ({len(pending_transactions)} Transactions)",
            custom_id="admin_approve_all"
        )
        approve_all_button.callback = admin_approve_all_transactions_callback
        view.add_item(approve_all_button)
        
        # Send the response with the view
        await interaction.response.send_message(
            message,
            view=view,
            ephemeral=True
        )
    except Exception as e:
        logger.error(f"Error in admin_view_pending_transactions_callback: {e}")
        # If the interaction has not been responded to yet, respond with an error message
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
            except:
                # If all else fails, try to send a followup message
                try:
                    await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
                except:
                    pass

async def admin_approve_all_transactions_callback(interaction: discord.Interaction):
    """Handle approving all pending transactions."""
    try:
        if not is_admin(interaction.user.id):
            await interaction.response.send_message("You are not authorized to use admin commands.", ephemeral=True)
            return
        
        # Get all pending transactions
        pending_transactions = get_pending_transactions()
        
        if not pending_transactions:
            await interaction.response.send_message(
                "There are no pending transactions to approve.",
                ephemeral=True
            )
            return
        
        # Approve all pending transactions
        approved_count = 0
        transaction_details = []
        confirmation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for transaction_id, transaction in pending_transactions.items():
            # Update transaction status
            update_transaction_status(transaction_id, "completed")
            approved_count += 1
            
            # Add transaction details to list
            transaction_details.append(
                f"ID: {transaction_id}\n"
                f"User: {transaction['username']} ({transaction['user_id']})\n"
                f"Amount: {transaction['amount']} naira"
            )
            
            # Try to notify the user
            try:
                user = await bot.fetch_user(int(transaction["user_id"]))
                if user:
                    await user.send(
                        f"💰 **WITHDRAWAL SUCCESSFUL!**\n\n" +
                        f"Amount: {transaction['amount']} naira\n" +
                        f"Transaction ID: {transaction_id}\n" +
                        f"Bank: {transaction['bank_name']}\n" +
                        f"Account: {transaction['bank_account_number']} ({transaction['bank_account_name']})\n" +
                        f"Confirmation Time: {confirmation_time}\n\n" +
                        f"Your account has been cleared. Thank you for using KashFlow!\n" +
                        f"You can register again with a new coupon code."
                    )
            except Exception as e:
                logger.error(f"Failed to notify user about transaction confirmation: {e}")
        
        # Send confirmation message
        details = "\n\n".join(transaction_details[:5])
        if len(transaction_details) > 5:
            details += f"\n\n...and {len(transaction_details) - 5} more transactions"
            
        await interaction.response.send_message(
            f"✅ Approved {approved_count} transactions successfully!\n\n{details}",
            ephemeral=True
        )
    except Exception as e:
        logger.error(f"Error in admin_approve_all_transactions_callback: {e}")
        # If the interaction has not been responded to yet, respond with an error message
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
            except:
                # If all else fails, try to send a followup message
                try:
                    await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
                except:
                    pass

async def admin_toggle_bot_status_callback(interaction: discord.Interaction):
    """Handle toggling the bot's status (enabled/disabled for users)."""
    try:
        if not is_admin(interaction.user.id):
            await interaction.response.send_message("You are not authorized to use admin commands.", ephemeral=True)
            return
        
        global BOT_ENABLED_FOR_USERS
        BOT_ENABLED_FOR_USERS = not BOT_ENABLED_FOR_USERS
        
        # Save the updated status to configuration
        update_config("bot_enabled_for_users", BOT_ENABLED_FOR_USERS)
        
        status = "enabled" if BOT_ENABLED_FOR_USERS else "disabled"
        await interaction.response.send_message(
            f"✅ Bot is now {status} for regular users. " +
            (f"Users can now use the bot normally." if BOT_ENABLED_FOR_USERS else 
             f"Only admins can use the bot until you enable it again."),
            ephemeral=True
        )
    except Exception as e:
        logger.error(f"Error in admin_toggle_bot_status_callback: {e}")
        # If the interaction has not been responded to yet, respond with an error message
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
            except:
                # If all else fails, try to send a followup message
                try:
                    await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
                except:
                    pass

# Add button persistence - this is crucial for working without privileged intents
@bot.event
async def on_ready():
    logger.info(f"Bot is ready! Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info(f"Bot is in {len(bot.guilds)} guild(s)")
    
    # Make sure persistent views are synced
    try:
        # Create the persistent views
        user_view = discord.ui.View(timeout=None)
        admin_view = discord.ui.View(timeout=None)

        # Register the buttons for user dashboard
        copy_id_button = discord.ui.Button(style=discord.ButtonStyle.primary, label="Copy ID to Refer", custom_id="copy_id")
        check_balance_button = discord.ui.Button(style=discord.ButtonStyle.secondary, label="Check Balance", custom_id="check_balance")
        withdraw_button = discord.ui.Button(style=discord.ButtonStyle.success, label="Withdraw", custom_id="withdraw")
        set_bank_button = discord.ui.Button(style=discord.ButtonStyle.secondary, label="Set Bank Information", custom_id="set_bank")
        
        # Register buttons for admin dashboard
        admin_start_button = discord.ui.Button(style=discord.ButtonStyle.primary, label="Start", custom_id="admin_start")
        admin_view_users_button = discord.ui.Button(style=discord.ButtonStyle.secondary, label="View Users", custom_id="admin_view_users")
        admin_generate_button = discord.ui.Button(style=discord.ButtonStyle.success, label="Generate Coupons", custom_id="admin_generate")
        admin_clear_used_button = discord.ui.Button(style=discord.ButtonStyle.danger, label="Clear Used Coupons", custom_id="admin_clear_used") 
        admin_view_balance_button = discord.ui.Button(style=discord.ButtonStyle.secondary, label="View Total Balance", custom_id="admin_view_balance")
        admin_invite_link_button = discord.ui.Button(style=discord.ButtonStyle.url, label="Get Invite Link", custom_id="admin_invite_link")
        
        # Add callbacks to persistent views
        copy_id_button.callback = copy_id_callback
        check_balance_button.callback = check_balance_callback
        withdraw_button.callback = withdraw_callback
        set_bank_button.callback = set_bank_callback
        
        admin_start_button.callback = admin_start_callback
        admin_view_users_button.callback = admin_view_users_callback
        admin_generate_button.callback = admin_generate_callback
        admin_clear_used_button.callback = admin_clear_used_callback
        admin_view_balance_button.callback = admin_view_balance_callback
        
        # Add callbacks for our new admin buttons
        admin_view_pending_button = discord.ui.Button(style=discord.ButtonStyle.primary, label="View Pending Transactions", custom_id="admin_view_pending")
        admin_toggle_bot_button = discord.ui.Button(
            style=discord.ButtonStyle.danger if BOT_ENABLED_FOR_USERS else discord.ButtonStyle.success,
            label="Disable Bot" if BOT_ENABLED_FOR_USERS else "Enable Bot", 
            custom_id="admin_toggle_bot"
        )
        admin_view_pending_button.callback = admin_view_pending_transactions_callback
        admin_toggle_bot_button.callback = admin_toggle_bot_status_callback
        
        # Add the buttons to views
        user_view.add_item(copy_id_button)
        user_view.add_item(check_balance_button)
        user_view.add_item(withdraw_button)
        user_view.add_item(set_bank_button)
        
        admin_view.add_item(admin_start_button)
        admin_view.add_item(admin_view_users_button)
        admin_view.add_item(admin_generate_button)
        admin_view.add_item(admin_clear_used_button)
        admin_view.add_item(admin_view_balance_button)
        admin_view.add_item(admin_view_pending_button)
        admin_view.add_item(admin_toggle_bot_button)
        
        # Generate bot invite link with proper permissions
        permissions = discord.Permissions(
            send_messages=True,
            embed_links=True,
            attach_files=True,
            read_messages=True,
            read_message_history=True,
            add_reactions=True,
            use_application_commands=True  # Correct permission for slash commands
        )
        invite_link = discord.utils.oauth_url(bot.user.id, permissions=permissions, scopes=("bot", "applications.commands"))
        
        # Update the invite link button with the actual URL
        admin_invite_link_button = discord.ui.Button(
            style=discord.ButtonStyle.link, 
            label="Get Invite Link", 
            url=invite_link
        )
        admin_view.add_item(admin_invite_link_button)
        
        # Create help view with dashboard button (but we'll set callback separately)
        help_view = discord.ui.View(timeout=None)
        help_dashboard_button = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Go to Dashboard",
            custom_id="help_dashboard"
        )
        
        # Define the callback function for the help dashboard button
        async def help_dashboard_callback(interaction):
            user = get_user(interaction.user.id)
            if user:
                await interaction.response.send_message(
                    f"**Your Dashboard**\n\n" +
                    f"Current Balance: **{user.balance}** naira\n" +
                    f"Referral Count: **{user.referral_count}**\n" +
                    f"Withdrawal Requirements: **{MINIMUM_REFERRALS}** referrals & **{WITHDRAWAL_THRESHOLD}** naira minimum\n\n" +
                    "**Dashboard Controls**:\n" +
                    "• **Copy ID to Refer**: Get your referral ID to share with others\n" +
                    "• **Check Balance**: View your current balance and referral count\n" +
                    f"• **Withdraw**: Request withdrawal when eligible ({MINIMUM_REFERRALS} referrals & {WITHDRAWAL_THRESHOLD} naira minimum)\n" +
                    "• **Set Bank Information**: Update your bank details for withdrawals",
                    view=create_user_dashboard_view(interaction.user.id),
                    ephemeral=False
                )
            else:
                await interaction.response.send_message(
                    "You're not registered yet. Use /start to register with a coupon code.",
                    ephemeral=True
                )
        
        # Assign callback and add button to view
        help_dashboard_button.callback = help_dashboard_callback
        help_view.add_item(help_dashboard_button)
        
        # Register all views with the bot
        bot.add_view(user_view)
        bot.add_view(admin_view)
        bot.add_view(help_view)
        
        logger.info("Persistent views registered successfully")
    except Exception as e:
        logger.error(f"Error registering persistent views: {e}")
        
    # Retry command sync a few times with increasing delays
    retry_delays = [1, 5, 15, 30]  # More attempts with longer delays
    for i, delay in enumerate(retry_delays):
        try:
            logger.info(f"Attempting to sync commands (attempt {i+1}/{len(retry_delays)})...")
            await asyncio.sleep(delay)  # Wait before trying to sync
            
            # First try fetching existing commands to avoid unnecessary syncs
            existing_commands = await bot.tree.fetch_commands()
            if existing_commands and len(existing_commands) >= 4:  # We expect 4 commands: start, dashboard, admin, help
                logger.info(f"Found {len(existing_commands)} existing commands. No need to sync.")
                logger.info("Bot is now fully operational!")
                return
            
            # Force sync to ensure new commands are added
            logger.info("Syncing commands to ensure all are available...")
            synced = await bot.tree.sync()
            logger.info(f"Successfully synced {len(synced)} command(s)")
            logger.info("Bot is now fully operational!")
            return  # Exit if successful
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limit error
                retry_after = e.retry_after if hasattr(e, 'retry_after') else 60  # Increased default wait time
                logger.warning(f"Rate limited. Retrying in {retry_after} seconds...")
                await asyncio.sleep(retry_after)
                # Don't count rate limits against our retry attempts
                continue
            else:
                logger.error(f"HTTP error while syncing commands: {e}")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    
    # Even if we couldn't sync commands, the bot should still be functional
    # for users who already have access to the commands
    logger.warning("Could not sync commands after multiple attempts. Bot will continue to run, but slash commands may not be immediately available to new guilds.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    
    logger.error(f"Command error: {error}")
    await ctx.send(f"An error occurred: {error}")

# Slash Commands
@bot.tree.command(name="start", description="Start using the bot")
async def start(interaction: discord.Interaction):
    """Start command for new users to register with a coupon code."""
    # Check if bot is disabled
    if not BOT_ENABLED_FOR_USERS:
        # For admins, show enable button
        if is_admin(interaction.user.id):
            view = create_bot_enable_view(interaction.user.id)
            await interaction.response.send_message(
                "⚠️ The bot is currently disabled for regular users.\n\n" +
                "As an admin, you can continue to use all commands, or you can enable the bot for all users.",
                view=view,
                ephemeral=True
            )
        else:
            # For regular users, just show the disabled message
            await interaction.response.send_message(
                "⚠️ The bot is currently disabled for maintenance. Please try again later.",
                ephemeral=True
            )
        return
        
    # Check if user is already registered
    user = get_user(interaction.user.id)
    
    if user:
        # Create dashboard view
        view = create_user_dashboard_view(interaction.user.id)
        
        # Add tutorial button if tutorial is enabled
        if TUTORIAL_ENABLED:
            # Create tutorial button
            tutorial_button = discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label="Start Tutorial",
                custom_id=f"restart_tutorial_{interaction.user.id}"
            )
            
            # Define callback for tutorial button
            async def restart_tutorial_callback(tutorial_interaction: discord.Interaction):
                # Verify user
                if tutorial_interaction.user.id != interaction.user.id:
                    await tutorial_interaction.response.send_message(
                        "This is not your dashboard.", 
                        ephemeral=True
                    )
                    return
                
                try:
                    # Reset tutorial progress
                    update_tutorial_progress(interaction.user.id, step=0, completed=False)
                    
                    # Get tutorial content for first step
                    tutorial_step = 0
                    tutorial_content = get_tutorial_content(tutorial_step)
                    
                    # Create message content
                    message = f"# {tutorial_content['title']}\n\n{tutorial_content['content']}"
                    
                    # Create tutorial view
                    tutorial_view = TutorialView(interaction.user.id, tutorial_step)
                    
                    # Create animation frames
                    frames = generate_tutorial_frames(message)
                    
                    # Send animated response
                    await tutorial_interaction.response.defer()
                    await send_animated_message(
                        tutorial_interaction,
                        frames,
                        duration=1.5,
                        final_frame=message
                    )
                    
                    # Send view as a followup
                    await tutorial_interaction.followup.send(view=tutorial_view)
                    
                except Exception as e:
                    logger.error(f"Failed to restart tutorial for user {interaction.user.id}: {e}")
                    await tutorial_interaction.response.send_message(
                        "An error occurred while starting the tutorial. Please try again.",
                        ephemeral=True
                    )
            
            # Set callback
            tutorial_button.callback = restart_tutorial_callback
            
            # Add button to view
            view.add_item(tutorial_button)
        
        # Send dashboard with the view
        await interaction.response.send_message(
            f"**Welcome back {interaction.user.name}!**\n\n" +
            f"Current Balance: **{user.balance}** naira\n" +
            f"Referral Count: **{user.referral_count}**\n" +
            f"Withdrawal Requirements: **{MINIMUM_REFERRALS}** referrals & **{WITHDRAWAL_THRESHOLD}** naira minimum\n\n" +
            "**Dashboard Controls**:\n" +
            "• **Copy ID to Refer**: Get your referral ID to share with others\n" +
            "• **Check Balance**: View your current balance and referral count\n" +
            f"• **Withdraw**: Request withdrawal when eligible ({MINIMUM_REFERRALS} referrals & {WITHDRAWAL_THRESHOLD} naira minimum)\n" +
            "• **Set Bank Information**: Update your bank details for withdrawals",
            view=view,
            ephemeral=False
        )
    else:
        # Check if demo mode is enabled
        if DEMO_MODE_ENABLED:
            # Create demo options view
            demo_view = discord.ui.View()
            
            # Try demo button
            try_demo_button = discord.ui.Button(
                style=discord.ButtonStyle.primary,
                label="Try Demo Mode",
                custom_id="try_demo_mode"
            )
            
            async def try_demo_callback(demo_interaction: discord.Interaction):
                # Check if it's the same user
                if demo_interaction.user.id != interaction.user.id:
                    await demo_interaction.response.send_message("This is not your demo.", ephemeral=True)
                    return
                
                # Generate demo welcome message
                demo_welcome_message = (
                    f"# 🚀 Welcome to KashFlow Demo Mode! 🚀\n\n"
                    f"**This is a demonstration of KashFlow's referral system.**\n\n"
                    f"In this demo, you'll see how the app works with a simulated balance of **{DEMO_BALANCE}** naira "
                    f"and **{DEMO_REFERRALS}** referrals.\n\n"
                    f"• **Welcome Bonus**: {WELCOME_BONUS} naira when you register\n"
                    f"• **Referral Bonus**: {REFERRAL_BONUS} naira for each person you refer\n"
                    f"• **Withdrawal Threshold**: {WITHDRAWAL_THRESHOLD} naira minimum balance\n"
                    f"• **Referral Requirement**: {MINIMUM_REFERRALS} referrals minimum\n\n"
                    f"Try all the features below, and click 'Exit Demo & Register' when you're ready to create a real account!"
                )
                
                # Create demo dashboard
                demo_dashboard = create_demo_dashboard_view()
                
                # Send welcome message with animation
                frames = generate_tutorial_frames(demo_welcome_message)
                await demo_interaction.response.defer()
                await send_animated_message(
                    demo_interaction,
                    frames,
                    duration=2.0,
                    final_frame=demo_welcome_message
                )
                
                # Send dashboard buttons separately
                await demo_interaction.followup.send(
                    "**Demo Dashboard Controls**:",
                    view=demo_dashboard,
                    ephemeral=False
                )
            
            try_demo_button.callback = try_demo_callback
            demo_view.add_item(try_demo_button)
            
            # Register directly button
            register_button = discord.ui.Button(
                style=discord.ButtonStyle.success,
                label="Register with Coupon",
                custom_id="register_directly"
            )
            
            async def register_callback(reg_interaction: discord.Interaction):
                # Check if it's the same user
                if reg_interaction.user.id != interaction.user.id:
                    await reg_interaction.response.send_message("This is not your registration.", ephemeral=True)
                    return
                
                # Show registration modal
                register_modal = RegisterModal(title="Register")
                await reg_interaction.response.send_modal(register_modal)
            
            register_button.callback = register_callback
            demo_view.add_item(register_button)
            
            # Send options message
            await interaction.response.send_message(
                f"# Welcome to KashFlow! 👋\n\n"
                f"KashFlow is a referral rewards system where you can earn naira by referring friends.\n\n"
                f"• Get **{WELCOME_BONUS}** naira welcome bonus when you register\n"
                f"• Earn **{REFERRAL_BONUS}** naira for each friend you refer\n"
                f"• Withdraw when you reach **{WITHDRAWAL_THRESHOLD}** naira and **{MINIMUM_REFERRALS}** referrals\n\n"
                f"You can try a demo of the system first, or register right away with a coupon code.",
                view=demo_view,
                ephemeral=False
            )
        else:
            # Show registration modal (demo mode disabled)
            register_modal = RegisterModal(title="Register")
            await interaction.response.send_modal(register_modal)

@bot.tree.command(name="dashboard", description="View your dashboard")
async def dashboard(interaction: discord.Interaction):
    """Show the user dashboard for existing users."""
    # Check if bot is disabled
    if not BOT_ENABLED_FOR_USERS:
        # For admins, show enable button
        if is_admin(interaction.user.id):
            view = create_bot_enable_view(interaction.user.id)
            await interaction.response.send_message(
                "⚠️ The bot is currently disabled for regular users.\n\n" +
                "As an admin, you can continue to use all commands, or you can enable the bot for all users.",
                view=view,
                ephemeral=True
            )
        else:
            # For regular users, just show the disabled message
            await interaction.response.send_message(
                "⚠️ The bot is currently disabled for maintenance. Please try again later.",
                ephemeral=True
            )
        return
        
    user = get_user(interaction.user.id)
    
    if not user:
        await interaction.response.send_message(
            "You're not registered yet. Use /start to register with a coupon code.",
            ephemeral=True
        )
        return
    
    # Create dashboard view
    view = create_user_dashboard_view(interaction.user.id)
    
    # Add tutorial button if tutorial is enabled
    if TUTORIAL_ENABLED:
        # Create tutorial button
        tutorial_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Start Tutorial",
            custom_id=f"restart_tutorial_{interaction.user.id}"
        )
        
        # Define callback for tutorial button
        async def restart_tutorial_callback(tutorial_interaction: discord.Interaction):
            # Verify user
            if tutorial_interaction.user.id != interaction.user.id:
                await tutorial_interaction.response.send_message(
                    "This is not your dashboard.", 
                    ephemeral=True
                )
                return
            
            try:
                # Reset tutorial progress
                update_tutorial_progress(interaction.user.id, step=0, completed=False)
                
                # Get tutorial content for first step
                tutorial_step = 0
                tutorial_content = get_tutorial_content(tutorial_step)
                
                # Create message content
                message = f"# {tutorial_content['title']}\n\n{tutorial_content['content']}"
                
                # Create tutorial view
                tutorial_view = TutorialView(interaction.user.id, tutorial_step)
                
                # Create animation frames
                frames = generate_tutorial_frames(message)
                
                # Send animated response
                await tutorial_interaction.response.defer()
                await send_animated_message(
                    tutorial_interaction,
                    frames,
                    duration=1.5,
                    final_frame=message
                )
                
                # Send view as a followup
                await tutorial_interaction.followup.send(view=tutorial_view)
                
            except Exception as e:
                logger.error(f"Failed to restart tutorial for user {interaction.user.id}: {e}")
                await tutorial_interaction.response.send_message(
                    "An error occurred while starting the tutorial. Please try again.",
                    ephemeral=True
                )
        
        # Set callback
        tutorial_button.callback = restart_tutorial_callback
        
        # Add button to view
        view.add_item(tutorial_button)
    
    # Send dashboard with the view
    await interaction.response.send_message(
        f"**Your Dashboard**\n\n" +
        f"Current Balance: **₦{user.balance}**\n" +
        f"Referral Count: **{user.referral_count}**\n" +
        f"Withdrawal Requirements: **{MINIMUM_REFERRALS}** referrals & **₦{WITHDRAWAL_THRESHOLD}** minimum\n\n" +
        "**Dashboard Controls**:\n" +
        "• **Copy ID to Refer**: Get your referral ID to share with others\n" +
        "• **Check Balance**: View your current balance and referral count\n" +
        f"• **Withdraw**: Request withdrawal when eligible ({MINIMUM_REFERRALS} referrals & {WITHDRAWAL_THRESHOLD} naira minimum)\n" +
        "• **Set Bank Information**: Update your bank details for withdrawals",
        view=view,
        ephemeral=False
    )

@bot.tree.command(name="admin", description="Access admin dashboard")
async def admin(interaction: discord.Interaction):
    """Admin dashboard for managing users and coupons."""
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("You are not authorized to use admin commands.", ephemeral=True)
        return
        
    # Get if this is the primary admin
    is_primary = interaction.user.id == PRIMARY_ADMIN_ID
    
    # Generate bot invite link with proper permissions
    permissions = discord.Permissions(
        send_messages=True,
        embed_links=True,
        attach_files=True,
        read_messages=True,
        read_message_history=True,
        add_reactions=True,
        use_application_commands=True  # Correct permission for slash commands
    )
    invite_link = discord.utils.oauth_url(bot.user.id, permissions=permissions, scopes=("bot", "applications.commands"))
    
    # Customize message based on primary/secondary admin status
    admin_type = "Primary Admin (Full Access)" if is_primary else "Secondary Admin (Limited Access)"
    coupon_note = "" if is_primary else "\n**Note:** Only the primary admin can generate coupon codes."
    
    # Bot status message
    bot_status = "ENABLED" if BOT_ENABLED_FOR_USERS else "DISABLED"
    
    await interaction.response.send_message(
        f"**Admin Dashboard - {admin_type}**\n\n" +
        "• **Start**: Show admin dashboard\n" +
        "• **View Users**: See all registered users and their details\n" +
        "• **Generate Coupons**: Create new coupon codes for users\n" +
        "• **Clear Used**: Remove used coupon codes from the system\n" +
        "• **View Balance**: Check total balance across all users\n" +
        "• **View Pending Transactions**: See and manage pending withdrawals\n" +
        f"• **{'Disable' if BOT_ENABLED_FOR_USERS else 'Enable'} Bot**: Currently {bot_status} for users\n" +
        f"{coupon_note}\n\n" +
        f"**Bot Invite Link**:\n{invite_link}\n" +
        "You can share this link to invite the bot to other servers.",
        view=create_admin_dashboard_view(),
        ephemeral=True
    )

# Add help command
@bot.tree.command(name="help", description="Get help and contact information")
async def help_command(interaction: discord.Interaction):
    """Show help and contact information."""
    # Check if bot is disabled
    if not BOT_ENABLED_FOR_USERS:
        # For admins, show enable button
        if is_admin(interaction.user.id):
            view = create_bot_enable_view(interaction.user.id)
            await interaction.response.send_message(
                "⚠️ The bot is currently disabled for regular users.\n\n" +
                "As an admin, you can continue to use all commands, or you can enable the bot for all users.",
                view=view,
                ephemeral=True
            )
        else:
            # For regular users, just show the disabled message
            await interaction.response.send_message(
                "⚠️ The bot is currently disabled for maintenance. Please try again later.",
                ephemeral=True
            )
        return
    
    # Generate help message with contact info
    help_message = (
        "# 📚 KashFlow Bot Help\n\n"
        "**KashFlow** is a referral rewards system where you can earn naira by referring new users.\n\n"
        "## 🤝 How It Works\n"
        f"• Get **₦{WELCOME_BONUS}** welcome bonus when you register\n"
        f"• Earn **₦{REFERRAL_BONUS}** for each person you refer\n"
        f"• Withdraw when you reach **₦{WITHDRAWAL_THRESHOLD}** and have **{MINIMUM_REFERRALS}** referrals\n\n"
        "## 📝 Commands\n"
        "• **/start** - Register or view your dashboard\n"
        "• **/dashboard** - Check your balance and referrals\n"
        "• **/help** - Show this help message\n\n"
        "## 📱 Community & Support\n"
        f"• **WhatsApp Community**: [Join here]({WHATSAPP_COMMUNITY_LINK})\n"
        f"• **Support Email**: {SUPPORT_EMAIL}\n\n"
        "Share your referral ID with friends to earn rewards! Use the buttons below to get started."
    )
    
    # Create view with dashboard and referral links
    view = discord.ui.View(timeout=None)
    
    # Dashboard button
    dashboard_button = discord.ui.Button(
        style=discord.ButtonStyle.primary,
        label="Go to Dashboard",
        custom_id="help_dashboard"
    )
    
    # WhatsApp link
    whatsapp_button = discord.ui.Button(
        style=discord.ButtonStyle.link,
        label="Join WhatsApp Community",
        url=WHATSAPP_COMMUNITY_LINK
    )
    
    # Set callback for dashboard button
    async def dashboard_callback(dashboard_interaction):
        user = get_user(dashboard_interaction.user.id)
        if user:
            # User exists, show dashboard with tutorial button
            view = create_user_dashboard_view(dashboard_interaction.user.id)
            
            # Add tutorial button if tutorial is enabled
            if TUTORIAL_ENABLED:
                # Create tutorial button
                tutorial_button = discord.ui.Button(
                    style=discord.ButtonStyle.secondary,
                    label="Start Tutorial",
                    custom_id=f"restart_tutorial_{dashboard_interaction.user.id}"
                )
                
                # Define callback for tutorial button
                async def restart_tutorial_callback(tutorial_interaction: discord.Interaction):
                    # Verify user
                    if tutorial_interaction.user.id != dashboard_interaction.user.id:
                        await tutorial_interaction.response.send_message(
                            "This is not your dashboard.", 
                            ephemeral=True
                        )
                        return
                    
                    try:
                        # Reset tutorial progress
                        update_tutorial_progress(dashboard_interaction.user.id, step=0, completed=False)
                        
                        # Get tutorial content for first step
                        tutorial_step = 0
                        tutorial_content = get_tutorial_content(tutorial_step)
                        
                        # Create message content
                        message = f"# {tutorial_content['title']}\n\n{tutorial_content['content']}"
                        
                        # Create tutorial view
                        tutorial_view = TutorialView(dashboard_interaction.user.id, tutorial_step)
                        
                        # Create animation frames
                        frames = generate_tutorial_frames(message)
                        
                        # Send animated response
                        await tutorial_interaction.response.defer()
                        await send_animated_message(
                            tutorial_interaction,
                            frames,
                            duration=1.5,
                            final_frame=message
                        )
                        
                        # Send view as a followup
                        await tutorial_interaction.followup.send(view=tutorial_view)
                        
                    except Exception as e:
                        logger.error(f"Failed to restart tutorial for user {dashboard_interaction.user.id}: {e}")
                        await tutorial_interaction.response.send_message(
                            "An error occurred while starting the tutorial. Please try again.",
                            ephemeral=True
                        )
                
                # Set callback
                tutorial_button.callback = restart_tutorial_callback
                
                # Add button to view
                view.add_item(tutorial_button)
            
            # Send dashboard with the view
            await dashboard_interaction.response.send_message(
                f"**Your Dashboard**\n\n" +
                f"Current Balance: **{user.balance}** naira\n" +
                f"Referral Count: **{user.referral_count}**\n" +
                f"Withdrawal Requirements: **{MINIMUM_REFERRALS}** referrals & **{WITHDRAWAL_THRESHOLD}** naira minimum\n\n" +
                "**Dashboard Controls**:\n" +
                "• **Copy ID to Refer**: Get your referral ID to share with others\n" +
                "• **Check Balance**: View your current balance and referral count\n" +
                f"• **Withdraw**: Request withdrawal when eligible ({MINIMUM_REFERRALS} referrals & {WITHDRAWAL_THRESHOLD} naira minimum)\n" +
                "• **Set Bank Information**: Update your bank details for withdrawals",
                view=view,
                ephemeral=False
            )
        else:
            # User doesn't exist, prompt to register
            await dashboard_interaction.response.send_message(
                "You're not registered yet. Use /start to register with a coupon code.",
                ephemeral=True
            )
    
    dashboard_button.callback = dashboard_callback
    
    # Add buttons to view
    view.add_item(dashboard_button)
    view.add_item(whatsapp_button)
    
    # Send help message with buttons
    await interaction.response.send_message(help_message, view=view, ephemeral=False)

# Import here to avoid circular imports
import io

# Import from app.py for gunicorn
from app import app

# Import keep_alive for running in thread
from keep_alive import keep_alive

# Run the bot
if __name__ == "__main__":
    if not TOKEN:
        logger.error("No Discord token found in .env file")
        exit(1)
    
    if not PRIMARY_ADMIN_ID:
        logger.warning("No primary admin ID found in .env file. Admin features will not work correctly.")
    else:
        logger.info(f"Primary admin ID configured: {PRIMARY_ADMIN_ID}")
        
    if ADMIN_IDS:
        logger.info(f"Additional admin IDs configured: {len(ADMIN_IDS)}")
    
    try:
        # Start the keep-alive server in a separate thread
        keep_alive()
        logger.info("Keep-alive server started successfully")
        
        # Run the Discord bot (this blocks until the bot stops)
        logger.info("Starting Discord bot...")
        bot.run(TOKEN)
    except Exception as e:
        logger.error(f"Failed to start services: {e}")
        raise
