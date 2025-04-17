import os
import json
import random
import logging
from typing import List, Dict, Optional
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Dictionary of predefined responses for different income-related questions
# These will be used as fallback responses when OpenAI API is not available
PREDEFINED_RESPONSES = {
    "referral": [
        "🌟 **Growing with Referrals**: Share your referral ID with friends and family! For each person who joins using your ID, you'll earn ₦200. The more people you refer, the more you earn.",
        "🚀 **Referral Strategy**: Try sharing your referral ID in your social media bios, WhatsApp status, or directly with friends. Consistent sharing brings consistent rewards!",
        "💡 **Referral Tip**: Create a compelling message explaining the benefits when sharing your referral ID. Tell people they'll get a welcome bonus too!"
    ],
    "withdrawal": [
        "💰 **Withdrawal Tips**: Remember you need at least 4 referrals and ₦1,000 to make a withdrawal. Plan your referrals to reach this threshold faster!",
        "⏱️ **Timing Withdrawals**: Some users find success by withdrawing as soon as they reach the threshold, while others prefer saving up for larger withdrawals. Choose what works best for you!"
    ],
    "daily_income": [
        "📈 **Consistent Growth**: Try to refer at least one new user daily. With a ₦200 bonus per referral, that's an extra ₦6,000 monthly!",
        "🗓️ **Income Planning**: Set weekly referral goals. Even 5 referrals a week equals ₦1,000, which meets the withdrawal threshold!",
        "🔄 **Regular Activity**: Being active in the group chat can help you connect with other users who might use your referral code."
    ],
    "strategy": [
        "🎯 **Strategic Approach**: Focus on quality over quantity. Target friends who are likely to be interested in earning through referrals themselves.",
        "🌐 **Network Expansion**: Reach out to different social circles - school friends, work colleagues, community groups. Diversifying your approach increases chances of success!",
        "📊 **Track Your Progress**: Keep note of who you've shared your code with and follow up with them. A gentle reminder can make the difference!"
    ],
    "general": [
        "✨ **Getting Started**: The easiest way to begin earning is by completing the tutorial and getting your first referral!",
        "🤝 **Community Growth**: The more active our community becomes, the more opportunities will be available for everyone.",
        "📱 **Cross-Platform Sharing**: Don't limit yourself to one platform. Share your referral code on WhatsApp, Facebook, Twitter, Instagram, and more!"
    ]
}

class AIAssistant:
    def __init__(self, system_prompt: Optional[str] = None):
        """
        Initialize the AI Assistant with optional custom system prompt.
        
        Args:
            system_prompt: Custom system prompt to guide the AI's behavior
        """
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = None
        
        # Initialize the OpenAI client if API key is available
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing OpenAI client: {e}")
                self.client = None
        
        # Set system prompt that helps the AI understand context about the KashFlow bot
        self.system_prompt = system_prompt or """
        You are KashFlow AI Assistant, an intelligent helper integrated with the KashFlow Discord bot.
        
        KashFlow is a referral rewards system where users can earn money by referring new users.
        
        Key details about KashFlow:
        - Users get a welcome bonus (₦200) when they register
        - Users earn ₦200 for each person they refer who signs up
        - Users need at least 4 referrals and ₦1,000 minimum balance to withdraw
        - Bank details are required for withdrawals
        
        Your job is to provide helpful, encouraging advice about:
        - How to maximize earnings through referrals
        - Effective strategies for sharing referral codes
        - Best practices for withdrawals
        - Ideas for consistent daily/weekly income
        
        Keep your responses concise (3-4 sentences max), friendly, and focused on helping users 
        earn more through legitimate referral practices. Never suggest dishonest methods.
        
        Always maintain a supportive, motivational tone.
        """
        
        # Load conversation history from file if it exists
        self.conversation_history = self._load_conversation_history()

    def _load_conversation_history(self) -> Dict[str, List[Dict]]:
        """Load AI conversation history from file."""
        try:
            with open('ai_conversations.json', 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_conversation_history(self) -> None:
        """Save AI conversation history to file."""
        with open('ai_conversations.json', 'w') as f:
            json.dump(self.conversation_history, f, indent=4)

    def _get_user_history(self, user_id: int) -> List[Dict]:
        """Get conversation history for a specific user."""
        user_id_str = str(user_id)
        if user_id_str not in self.conversation_history:
            self.conversation_history[user_id_str] = []
        return self.conversation_history[user_id_str]

    def _update_user_history(self, user_id: int, role: str, content: str) -> None:
        """Add a message to a user's conversation history."""
        user_id_str = str(user_id)
        if user_id_str not in self.conversation_history:
            self.conversation_history[user_id_str] = []
        
        # Add the new message
        self.conversation_history[user_id_str].append({
            "role": role,
            "content": content
        })
        
        # Keep only the last 10 messages to prevent context from getting too large
        if len(self.conversation_history[user_id_str]) > 10:
            self.conversation_history[user_id_str] = self.conversation_history[user_id_str][-10:]
        
        # Save updated history
        self._save_conversation_history()

    def _get_category_for_query(self, query: str) -> str:
        """Determine the category of a user query for selecting predefined responses."""
        query = query.lower()
        
        if any(word in query for word in ["refer", "referral", "invite", "share", "code"]):
            return "referral"
        elif any(word in query for word in ["withdraw", "payment", "cash out", "bank", "payout"]):
            return "withdrawal"
        elif any(word in query for word in ["daily", "income", "earn", "money", "naira", "day", "week"]):
            return "daily_income"
        elif any(word in query for word in ["strategy", "plan", "method", "approach", "technique"]):
            return "strategy"
        else:
            return "general"

    def _get_predefined_response(self, query: str) -> str:
        """Get a predefined response based on the query category."""
        category = self._get_category_for_query(query)
        return random.choice(PREDEFINED_RESPONSES[category])

    async def get_ai_response(self, user_id: int, query: str) -> str:
        """
        Get AI response to a user query.
        
        Args:
            user_id: Discord user ID
            query: User's question or message
            
        Returns:
            AI response text
        """
        # Update user history with their query
        self._update_user_history(user_id, "user", query)
        
        # If OpenAI client is available, use it for response
        if self.client:
            try:
                # Prepare messages for the API call
                messages = [
                    {"role": "system", "content": self.system_prompt}
                ]
                
                # Add user conversation history
                user_history = self._get_user_history(user_id)
                messages.extend(user_history)
                
                # Call the API
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Using a cost-effective model
                    messages=messages,
                    temperature=0.7,
                    max_tokens=150  # Keeping responses concise
                )
                
                # Extract and process the response
                ai_response = response.choices[0].message.content.strip()
                
                # Update user history with AI response
                self._update_user_history(user_id, "assistant", ai_response)
                
                return ai_response
                
            except Exception as e:
                logger.error(f"Error getting AI response: {e}")
                # Fallback to predefined response on error
                fallback_response = self._get_predefined_response(query)
                self._update_user_history(user_id, "assistant", fallback_response)
                return fallback_response
        else:
            # If no API key, use predefined responses
            logger.info("Using predefined response (no API key available)")
            predefined_response = self._get_predefined_response(query)
            self._update_user_history(user_id, "assistant", predefined_response)
            return predefined_response

# Create a global instance for easy importing
ai_assistant = AIAssistant()