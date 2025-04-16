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
WELCOME_BONUS = 200  # Welcome bonus in Naira
REFERRAL_BONUS = 200  # Referral bonus in Naira
WITHDRAWAL_THRESHOLD = 1000  # Minimum balance required for withdrawal
MINIMUM_REFERRALS = 4  # Minimum number of referrals required for withdrawal
COUPON_PRICE = 500  # Price of coupon in Naira
COUPON_LENGTH = 12  # Length of coupon code

# Bot status control
BOT_ENABLED_FOR_USERS = True  # Bot status flag

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

    def to_dict(self) -> Dict:
        return {
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

def clear_used_coupons() -> int:
    """Clear all used coupons and return count of cleared coupons."""
    coupons = load_coupons()
    used_coupons = [code for code, used in coupons.items() if used]
    for code in used_coupons:
        del coupons[code]
    save_coupons(coupons)
    return len(used_coupons)

# Transaction management functions
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
        
        # Try to notify the user
        try:
            user = await bot.fetch_user(int(transaction["user_id"]))
            if user:
                await user.send(
                    f"❌ Your withdrawal of {transaction['amount']} naira has been declined.\n\n" +
                    f"Transaction ID: {transaction_id}\n" +
                    f"Decline Time: {decline_time}\n\n" +
                    f"Please contact an admin for more information."
                )
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
            
            # Try to notify the referrer
            try:
                referrer_user = await bot.fetch_user(referred_by)
                if referrer_user:
                    await referrer_user.send(
                        f"🎉 **REFERRAL BONUS RECEIVED!**\n\n" +
                        f"You just earned {REFERRAL_BONUS} naira for referring {interaction.user.name}!\n" +
                        f"Your new balance is {referrer.balance} naira.\n" +
                        f"Your referral count is now {referrer.referral_count}.\n\n" +
                        f"Keep sharing your referral ID to earn more!"
                    )
            except Exception as e:
                logger.error(f"Failed to notify referrer about bonus: {e}")
        
        # Mark coupon as used
        mark_coupon_used(coupon_code)
        
        # Save new user
        add_user(user)
        
        # Create dashboard view
        view = create_user_dashboard_view(user_id)
        
        # Send dashboard with instructions
        await interaction.followup.send(
            f"✅ Registration successful! You received {WELCOME_BONUS} naira as welcome bonus." +
            (f" Your referrer received {REFERRAL_BONUS} naira." if referred_by else "") +
            "\n\n**Your Dashboard Controls**: \n" +
            "• **Copy ID to Refer**: Get your referral ID to share with others\n" +
            "• **Check Balance**: View your current balance and referral count\n" +
            f"• **Withdraw**: Request withdrawal when eligible ({MINIMUM_REFERRALS} referrals & {WITHDRAWAL_THRESHOLD} naira minimum)\n" +
            "• **Set Bank Information**: Update your bank details for withdrawals",
            view=view,
            ephemeral=False
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
            f"Your current balance is: {user.balance} naira\n" +
            f"Referral count: {user.referral_count} (need {MINIMUM_REFERRALS} to withdraw)\n" +
            f"Withdrawal threshold: {WITHDRAWAL_THRESHOLD} naira",
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
        
        # Register the views with the bot
        bot.add_view(user_view)
        bot.add_view(admin_view)
        
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
            if existing_commands and len(existing_commands) >= 3:  # We expect 3 commands: start, dashboard, admin
                logger.info(f"Found {len(existing_commands)} existing commands. No need to sync.")
                logger.info("Bot is now fully operational!")
                return

            # If we need to sync
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
    # Check if bot is disabled for non-admins
    if not BOT_ENABLED_FOR_USERS and not is_admin(interaction.user.id):
        await interaction.response.send_message(
            "⚠️ The bot is currently disabled for maintenance. Please try again later.",
            ephemeral=True
        )
        return
        
    # Check if user is already registered
    user = get_user(interaction.user.id)
    
    if user:
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
            view=create_user_dashboard_view(interaction.user.id),
            ephemeral=False
        )
    else:
        # Show registration modal
        register_modal = RegisterModal(title="Register")
        await interaction.response.send_modal(register_modal)

@bot.tree.command(name="dashboard", description="View your dashboard")
async def dashboard(interaction: discord.Interaction):
    """Show the user dashboard for existing users."""
    # Check if bot is disabled for non-admins
    if not BOT_ENABLED_FOR_USERS and not is_admin(interaction.user.id):
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
    
    await interaction.response.send_message(
        f"**Admin Dashboard - {admin_type}**\n\n" +
        "• **Start**: Show admin dashboard\n" +
        "• **View Users**: See all registered users and their details\n" +
        "• **Generate Coupons**: Create new coupon codes for users\n" +
        "• **Clear Used**: Remove used coupon codes from the system\n" +
        "• **View Balance**: Check total balance across all users\n" +
        f"{coupon_note}\n\n" +
        f"**Bot Invite Link**:\n{invite_link}\n" +
        "You can share this link to invite the bot to other servers.",
        view=create_admin_dashboard_view(),
        ephemeral=True
    )

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
