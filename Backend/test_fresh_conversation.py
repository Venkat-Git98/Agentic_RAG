#!/usr/bin/env python3
"""
Test script to test a fresh conversation and see if assistant responses are saved
"""

import requests
import json
import time

def test_fresh_conversation():
    """Test a fresh conversation to see if assistant responses are saved"""
    print("🧪 Testing Fresh Conversation...")
    
    # Generate a new user ID
    import uuid
    new_user_id = str(uuid.uuid4())
    test_query = "What is the minimum ceiling height for residential buildings?"
    
    print(f"👤 New User ID: {new_user_id}")
    print(f"📝 Test Query: {test_query}")
    
    try:
        # Step 1: Send a query
        print(f"\n📤 Step 1: Sending query...")
        query_response = requests.post("http://localhost:8000/query", json={
            "user_query": test_query,
            "thread_id": new_user_id
        })
        
        if query_response.status_code == 200:
            print(f"✅ Query sent successfully")
            
            # Step 2: Wait a moment for processing
            print(f"⏳ Step 2: Waiting for processing...")
            time.sleep(5)
            
            # Step 3: Check history
            print(f"📋 Step 3: Checking history...")
            history_response = requests.get(f"http://localhost:8000/history?userId={new_user_id}")
            
            if history_response.status_code == 200:
                history_data = history_response.json()
                messages = history_data.get('data', [])
                user_messages = [msg for msg in messages if msg.get('role') == 'user']
                assistant_messages = [msg for msg in messages if msg.get('role') == 'assistant']
                
                print(f"\n📊 History Results:")
                print(f"  📝 Total messages: {len(messages)}")
                print(f"  👤 User messages: {len(user_messages)}")
                print(f"  🤖 Assistant messages: {len(assistant_messages)}")
                
                # Show all messages
                print(f"\n📋 All Messages:")
                for i, msg in enumerate(messages):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')[:100]
                    print(f"  {i+1}. [{role.upper()}] {content}{'...' if len(msg.get('content', '')) > 100 else ''}")
                
                # Final answer
                print(f"\n❓ **FINAL ANSWER:**")
                if assistant_messages:
                    print(f"✅ YES - Assistant answers ARE being saved!")
                    print(f"   Found {len(assistant_messages)} assistant responses")
                else:
                    print(f"❌ NO - Assistant answers are NOT being saved")
                    print(f"   This indicates an issue with the MemoryAgent or conversation flow")
                    
            else:
                print(f"❌ History check failed: {history_response.status_code}")
                
        else:
            print(f"❌ Query failed: {query_response.status_code}")
            print(query_response.text)
            
    except Exception as e:
        print(f"❌ Error in test: {e}")

if __name__ == "__main__":
    test_fresh_conversation() 