#!/usr/bin/env python3
"""
Test script to check if history includes assistant answers
"""

import requests
import json

def test_history_answers():
    """Test if history includes assistant answers"""
    print("🔍 Testing History for Assistant Answers...")
    
    # Test user ID
    user_id = "ff87a48e-bb33-4b87-8e68-fa3e5c5a6577"
    
    try:
        # Make request to history endpoint
        response = requests.get(f"http://localhost:8000/history?userId={user_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data.get('success')}")
            print(f"📊 Total Messages: {data.get('message_count')}")
            
            # Analyze message types
            messages = data.get('data', [])
            user_messages = [msg for msg in messages if msg.get('role') == 'user']
            assistant_messages = [msg for msg in messages if msg.get('role') == 'assistant']
            
            print(f"\n📋 Message Analysis:")
            print(f"  👤 User messages: {len(user_messages)}")
            print(f"  🤖 Assistant messages: {len(assistant_messages)}")
            
            # Show all messages
            print(f"\n📝 All Messages:")
            for i, msg in enumerate(messages):
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:100]
                print(f"  {i+1}. [{role.upper()}] {content}{'...' if len(msg.get('content', '')) > 100 else ''}")
            
            # Answer the specific question
            print(f"\n❓ **ANSWER TO YOUR QUESTION:**")
            if assistant_messages:
                print(f"✅ YES - The history endpoint DOES provide assistant answers!")
                print(f"   Found {len(assistant_messages)} assistant responses")
            else:
                print(f"❌ NO - Currently no assistant answers in history")
                print(f"   This might be because:")
                print(f"   - The assistant response wasn't saved properly")
                print(f"   - The conversation is incomplete")
                print(f"   - There was an issue with the MemoryAgent")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error testing history: {e}")

if __name__ == "__main__":
    test_history_answers() 