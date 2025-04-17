import asyncio
from ai_assistant import ai_assistant

async def test_ai_response():
    """Test the AI assistant with sample queries."""
    test_user_id = 12345
    
    # Test queries
    queries = [
        "How can I make more money with referrals?",
        "What's the best way to withdraw my earnings?",
        "How do I increase my daily income?",
        "What strategy should I use for sharing my referral code?"
    ]
    
    print("Testing AI Assistant...\n")
    
    for query in queries:
        print(f"Query: {query}")
        response = await ai_assistant.get_ai_response(test_user_id, query)
        print(f"Response: {response}\n")
        
    print("Testing complete!")

if __name__ == "__main__":
    asyncio.run(test_ai_response())