import os
import json
import random
import string
import logging
import asyncio
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
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

# Constants
WELCOME_BONUS = 200  # Welcome bonus in Naira
REFERRAL_BONUS = 200  # Referral bonus in Naira
WITHDRAWAL_THRESHOLD = 1000  # Minimum balance required for withdrawal
COUPON_PRICE = 500  # Price of coupon in Naira
COUPON_LENGTH = 12  # Length of coupon code

# File paths
USERS_FILE = 'users.json'
COUPONS_FILE = 'coupons.json'

# Create files if they don't exist
for file_path in [USERS_FILE, COUPONS_FILE]:
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
            "• **Withdraw**: Request withdrawal when eligible (need 1000 naira minimum)\n" +
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
    custom_id = interaction.data["custom_id"]
    user_id = int(custom_id.split("_")[-1])
    
    if interaction.user.id != user_id:
        await interaction.response.send_message("This is not your dashboard.", ephemeral=True)
        return
    
    await interaction.response.send_message(
        f"Your referral ID is: `{user_id}`\nShare this ID with new users to earn referral bonuses!",
        ephemeral=True
    )

async def check_balance_callback(interaction: discord.Interaction):
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
        f"Referral count: {user.referral_count}\n" +
        f"Withdrawal threshold: {WITHDRAWAL_THRESHOLD} naira",
        ephemeral=True
    )

async def withdraw_callback(interaction: discord.Interaction):
    custom_id = interaction.data["custom_id"]
    user_id = int(custom_id.split("_")[-1])
    
    if interaction.user.id != user_id:
        await interaction.response.send_message("This is not your dashboard.", ephemeral=True)
        return
    
    user = get_user(user_id)
    if not user:
        await interaction.response.send_message("User not found.", ephemeral=True)
        return
    
    # Check if user is eligible for withdrawal
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
    
    # Send withdrawal notification to admin
    admin = await bot.fetch_user(ADMIN_ID)
    if admin:
        await admin.send(
            f"**WITHDRAWAL REQUEST**\n" +
            f"User: {user.username} (ID: {user.id})\n" +
            f"Amount: {user.balance} naira\n" +
            f"Bank Name: {user.bank_name}\n" +
            f"Account Number: {user.bank_account_number}\n" +
            f"Account Name: {user.bank_account_name}\n" +
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    
    # Delete user
    delete_user(user_id)
    
    await interaction.response.send_message(
        f"Your withdrawal request for {user.balance} naira has been submitted. " +
        "Your bank details have been sent to the admin. " +
        "You will receive your payment shortly. " +
        "Your account has been cleared. You can register again with a new coupon code when you're ready.",
        ephemeral=False
    )

async def set_bank_callback(interaction: discord.Interaction):
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

async def admin_start_callback(interaction: discord.Interaction):
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message("You are not authorized to use admin commands.", ephemeral=True)
        return
    
    await interaction.response.send_message(
        "Admin Dashboard",
        view=create_admin_dashboard_view(),
        ephemeral=True
    )

async def admin_view_users_callback(interaction: discord.Interaction):
    if interaction.user.id != ADMIN_ID:
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

async def admin_generate_callback(interaction: discord.Interaction):
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message("You are not authorized to use admin commands.", ephemeral=True)
        return
    
    # Show generate coupons modal
    generate_modal = GenerateCouponsModal()
    await interaction.response.send_modal(generate_modal)

async def admin_clear_used_callback(interaction: discord.Interaction):
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message("You are not authorized to use admin commands.", ephemeral=True)
        return
    
    cleared_count = clear_used_coupons()
    
    await interaction.response.send_message(
        f"Cleared {cleared_count} used coupons.",
        ephemeral=True
    )

async def admin_view_balance_callback(interaction: discord.Interaction):
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message("You are not authorized to use admin commands.", ephemeral=True)
        return
    
    total_balance = calculate_total_balance()
    users = load_users()
    
    await interaction.response.send_message(
        f"Total balance across all {len(users)} users: {total_balance} naira",
        ephemeral=True
    )

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
    # Check if user is already registered
    user = get_user(interaction.user.id)
    
    if user:
        await interaction.response.send_message(
            f"**Welcome back {interaction.user.name}!**\n\n" +
            f"Current Balance: **{user.balance}** naira\n" +
            f"Referral Count: **{user.referral_count}**\n" +
            f"Withdrawal Threshold: **{WITHDRAWAL_THRESHOLD}** naira\n\n" +
            "**Dashboard Controls**:\n" +
            "• **Copy ID to Refer**: Get your referral ID to share with others\n" +
            "• **Check Balance**: View your current balance and referral count\n" +
            "• **Withdraw**: Request withdrawal when eligible (need 1000 naira minimum)\n" +
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
        f"Withdrawal Threshold: **{WITHDRAWAL_THRESHOLD}** naira\n\n" +
        "**Dashboard Controls**:\n" +
        "• **Copy ID to Refer**: Get your referral ID to share with others\n" +
        "• **Check Balance**: View your current balance and referral count\n" +
        "• **Withdraw**: Request withdrawal when eligible (need 1000 naira minimum)\n" +
        "• **Set Bank Information**: Update your bank details for withdrawals",
        view=create_user_dashboard_view(interaction.user.id),
        ephemeral=False
    )

@bot.tree.command(name="admin", description="Access admin dashboard")
async def admin(interaction: discord.Interaction):
    """Admin dashboard for managing users and coupons."""
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message("You are not authorized to use admin commands.", ephemeral=True)
        return
    
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
    
    await interaction.response.send_message(
        "**Admin Dashboard**\n\n" +
        "• **Start**: Show admin dashboard\n" +
        "• **View Users**: See all registered users and their details\n" +
        "• **Generate Coupons**: Create new coupon codes for users\n" +
        "• **Clear Used**: Remove used coupon codes from the system\n" +
        "• **View Balance**: Check total balance across all users\n\n" +
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
    
    if not ADMIN_ID:
        logger.warning("No admin ID found in .env file. Admin features will not work correctly.")
    
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
