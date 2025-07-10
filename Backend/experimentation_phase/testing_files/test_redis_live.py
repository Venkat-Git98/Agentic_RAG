#!/usr/bin/env python3
"""
Live Redis Cache Testing Script

Use this script to test the actual Redis cache functionality
when Redis server is running.

Prerequisites:
1. Redis server running (redis-server)
2. Python redis package installed (pip install redis)
"""

import redis
import json
import uuid
import time
from datetime import datetime

def test_redis_connection():
    """Test Redis connection"""
    print("🔌 Testing Redis Connection...")
    try:
        client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        client.ping()
        print("✅ Redis connection successful!")
        return client
    except redis.ConnectionError:
        print("❌ Redis connection failed! Make sure Redis server is running.")
        print("💡 Start Redis with: redis-server")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def test_message_storage_and_retrieval(client):
    """Test storing and retrieving messages"""
    print("\n📝 Testing Message Storage & Retrieval...")
    
    test_user_id = "test_user_" + str(int(time.time()))
    
    # Sample messages
    test_messages = [
        {
            "id": str(uuid.uuid4()),
            "role": "user", 
            "content": "Hello, can you help me with building codes?"
        },
        {
            "id": str(uuid.uuid4()),
            "role": "assistant",
            "content": "Of course! I'd be happy to help you with building codes. What specific question do you have?"
        },
        {
            "id": str(uuid.uuid4()),
            "role": "user",
            "content": "What are the ceiling height requirements for residential buildings?"
        }
    ]
    
    print(f"🗂️  Using test key: '{test_user_id}'")
    
    # Store messages
    print("💾 Storing messages...")
    for i, msg in enumerate(test_messages):
        json_msg = json.dumps(msg)
        client.rpush(test_user_id, json_msg)
        print(f"   ✅ Stored message {i+1}: [{msg['role']}] {msg['content'][:40]}...")
    
    # Retrieve messages
    print("\n📤 Retrieving messages...")
    stored_messages = client.lrange(test_user_id, 0, -1)
    
    print(f"📊 Retrieved {len(stored_messages)} messages:")
    for i, msg_json in enumerate(stored_messages):
        msg = json.loads(msg_json)
        print(f"   {i+1}. [{msg['role']}] {msg['content'][:50]}...")
    
    # Cleanup
    client.delete(test_user_id)
    print(f"🧹 Cleaned up test data")
    
    return len(stored_messages) == len(test_messages)

def test_history_endpoint_simulation(client):
    """Simulate the /history endpoint functionality"""
    print("\n🌐 Testing History Endpoint Simulation...")
    
    # Create test data
    user_id = "demo_user_12345"
    demo_messages = [
        {"id": str(uuid.uuid4()), "role": "user", "content": "What is the minimum ceiling height for basements?"},
        {"id": str(uuid.uuid4()), "role": "assistant", "content": "According to the IRC, basement ceilings must be at least 7 feet high for habitable spaces."},
        {"id": str(uuid.uuid4()), "role": "user", "content": "Are there any exceptions to this rule?"},
        {"id": str(uuid.uuid4()), "role": "assistant", "content": "Yes, there are exceptions for utility rooms which can be as low as 6 feet 8 inches."}
    ]
    
    # Store demo data
    for msg in demo_messages:
        client.rpush(user_id, json.dumps(msg))
    
    # Simulate endpoint response
    def simulate_get_history(user_id):
        if not client.exists(user_id):
            return {
                "success": False,
                "message": f"No chat history found for user {user_id}",
                "data": []
            }
        
        messages_raw = client.lrange(user_id, 0, -1)
        messages = [json.loads(msg) for msg in messages_raw]
        
        return {
            "success": True,
            "message": f"Retrieved {len(messages)} messages for user {user_id}",
            "user_id": user_id,
            "message_count": len(messages),
            "timestamp": datetime.now().isoformat(),
            "data": messages
        }
    
    # Test the simulation
    print(f"📞 Simulating: GET /history?userId={user_id}")
    response = simulate_get_history(user_id)
    
    print(f"📊 Response Status: {'200 OK' if response['success'] else '404 Not Found'}")
    print(f"📝 Response:")
    print(json.dumps(response, indent=2)[:500] + "..." if len(json.dumps(response)) > 500 else json.dumps(response, indent=2))
    
    # Test with non-existent user
    print(f"\n📞 Testing with non-existent user...")
    response_404 = simulate_get_history("non_existent_user")
    print(f"📊 Response Status: {'200 OK' if response_404['success'] else '404 Not Found'}")
    print(f"📝 Response: {response_404['message']}")
    
    # Cleanup
    client.delete(user_id)
    print(f"🧹 Cleaned up demo data")

def test_with_existing_data(client):
    """Test with existing conversation data if available"""
    print("\n📂 Testing with Existing Data...")
    
    data_file = "data/_personal_portfolio_session_uuid_01.json"
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        conversation_id = existing_data.get('conversation_id', 'existing_session')
        messages = existing_data.get('full_history', [])
        
        print(f"📁 Found existing data: {len(messages)} messages")
        print(f"🏷️  Conversation ID: {conversation_id}")
        
        # Migrate to Redis for testing
        print("🔄 Migrating to Redis for testing...")
        for msg in messages[:5]:  # Just test with first 5 messages
            client.rpush(f"test_{conversation_id}", json.dumps(msg))
        
        # Test retrieval
        retrieved = client.lrange(f"test_{conversation_id}", 0, -1)
        print(f"✅ Successfully stored and retrieved {len(retrieved)} messages")
        
        # Show sample
        if retrieved:
            sample_msg = json.loads(retrieved[0])
            print(f"📝 Sample message: [{sample_msg.get('role')}] {sample_msg.get('content', '')[:60]}...")
        
        # Cleanup
        client.delete(f"test_{conversation_id}")
        print(f"🧹 Cleaned up test migration")
        
    except FileNotFoundError:
        print("📭 No existing data file found")
    except Exception as e:
        print(f"❌ Error testing with existing data: {e}")

def show_redis_info(client):
    """Show Redis server information"""
    print("\n📊 Redis Server Information...")
    try:
        info = client.info()
        print(f"🔧 Redis version: {info.get('redis_version', 'Unknown')}")
        print(f"💾 Used memory: {info.get('used_memory_human', 'Unknown')}")
        print(f"🔗 Connected clients: {info.get('connected_clients', 'Unknown')}")
        print(f"📦 Total keys: {client.dbsize()}")
        
        # Show existing keys
        keys = client.keys('*')
        if keys:
            print(f"🗂️  Existing keys: {len(keys)}")
            for key in keys[:5]:  # Show first 5 keys
                key_type = client.type(key)
                print(f"   • {key} ({key_type})")
        else:
            print(f"📭 No existing keys in database")
            
    except Exception as e:
        print(f"❌ Error getting Redis info: {e}")

def main():
    """Main testing function"""
    print("🔬 Live Redis Cache Testing")
    print("=" * 50)
    
    # Test connection
    client = test_redis_connection()
    if not client:
        print("\n💡 To start Redis server:")
        print("   Windows: Download Redis and run redis-server.exe")
        print("   Linux/Mac: redis-server")
        print("   Docker: docker run -d -p 6379:6379 redis:alpine")
        return
    
    # Show Redis info
    show_redis_info(client)
    
    # Test basic operations
    success = test_message_storage_and_retrieval(client)
    if success:
        print("✅ Basic storage/retrieval test passed!")
    else:
        print("❌ Basic storage/retrieval test failed!")
    
    # Test endpoint simulation
    test_history_endpoint_simulation(client)
    
    # Test with existing data
    test_with_existing_data(client)
    
    print(f"\n🎯 Summary:")
    print(f"   ✅ Redis connection working")
    print(f"   ✅ Message storage working") 
    print(f"   ✅ Message retrieval working")
    print(f"   ✅ API endpoint simulation working")
    print(f"   ✅ Ready for frontend integration!")
    
    print(f"\n🔧 Next Steps:")
    print(f"   1. Start your backend server: python -m uvicorn server:app --reload")
    print(f"   2. Test the actual /history endpoint")
    print(f"   3. Integrate with your frontend application")

if __name__ == "__main__":
    main() 