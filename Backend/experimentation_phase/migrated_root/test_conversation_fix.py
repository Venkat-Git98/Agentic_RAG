#!/usr/bin/env python3
"""
Test script to verify conversation manager integration fix
"""

import asyncio
import json
from main import LangGraphAgenticAI

async def test_conversation_manager():
    """Test the conversation manager integration"""
    print("🧪 Testing Conversation Manager Integration...")
    
    # Test user ID
    user_id = "ff87a48e-bb33-4b87-8e68-fa3e5c5a6577"
    test_query = "What is the minimum ceiling height for basements?"
    
    print(f"📝 User ID: {user_id}")
    print(f"📝 Query: {test_query}")
    
    # Create AI system
    ai = LangGraphAgenticAI()
    
    # Get response
    print("\n🔄 Processing query...")
    final_answer = ""
    
    async for chunk in ai.get_response_stream(test_query, user_id):
        if "final_answer" in chunk:
            final_answer = chunk["final_answer"]
            print(f"✅ Got final answer: {len(final_answer)} characters")
        elif "cognitive_message" in chunk:
            print(f"🤔 {chunk['cognitive_message'][:100]}...")
    
    print(f"\n📄 Final Answer Preview: {final_answer[:200]}...")
    
    # Test history retrieval
    print("\n🔍 Testing history retrieval...")
    import requests
    
    try:
        response = requests.get(f"http://localhost:8000/history?userId={user_id}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("data"):
                print(f"✅ History found: {len(data['data'])} messages")
                for i, msg in enumerate(data['data']):
                    print(f"  {i+1}. {msg['role']}: {msg['content'][:100]}...")
            else:
                print(f"❌ No history found: {data.get('message', 'Unknown error')}")
        else:
            print(f"❌ History endpoint error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing history: {e}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_conversation_manager()) 