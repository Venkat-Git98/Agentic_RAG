#!/usr/bin/env python3
"""
Endpoint Testing Script

Tests the server endpoints without requiring Redis to be running.
This allows us to verify the basic functionality works.
"""

import requests
import json
import time
from typing import Dict, Any

def test_server_health():
    """Test if the server is running"""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        print(f"✅ Server is running - Status: {response.status_code}")
        return True
    except requests.ConnectionError:
        print("❌ Server is not running")
        print("💡 Start the server with: python -m uvicorn server:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False

def test_chat_endpoint():
    """Test the main chat endpoint"""
    print("\n🗣️  Testing Chat Endpoint...")
    
    test_payload = {
        "message": "What are the minimum ceiling height requirements for residential buildings?",
        "thread_id": "test_thread_123"
    }
    
    try:
        print(f"📤 Sending: {test_payload}")
        response = requests.post(
            "http://localhost:8000/chat",
            json=test_payload,
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat endpoint working!")
            print(f"📝 Response preview: {str(data)[:100]}...")
            return True
        else:
            print(f"❌ Chat endpoint failed")
            print(f"📝 Error: {response.text}")
            return False
            
    except requests.Timeout:
        print("⏰ Request timed out (30s)")
        return False
    except Exception as e:
        print(f"❌ Error testing chat endpoint: {e}")
        return False

def test_history_endpoint():
    """Test the history endpoint"""
    print("\n📚 Testing History Endpoint...")
    
    # Test with existing conversation ID from the data file
    test_user_id = "_personal_portfolio_session_uuid_01"
    
    try:
        print(f"📤 Requesting history for user: {test_user_id}")
        response = requests.get(
            f"http://localhost:8000/history?userId={test_user_id}",
            timeout=10
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ History endpoint working!")
            print(f"📊 Response structure:")
            for key, value in data.items():
                if key == 'data' and isinstance(value, list):
                    print(f"   {key}: List with {len(value)} items")
                else:
                    print(f"   {key}: {type(value).__name__}")
            
            # Show sample data if available
            if 'data' in data and data['data']:
                print(f"📝 Sample message: {data['data'][0] if data['data'] else 'No messages'}")
            
            return True
        else:
            print(f"❌ History endpoint failed")
            print(f"📝 Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing history endpoint: {e}")
        return False

def test_history_endpoint_nonexistent():
    """Test history endpoint with non-existent user"""
    print("\n🔍 Testing History Endpoint with Non-existent User...")
    
    test_user_id = "nonexistent_user_12345"
    
    try:
        response = requests.get(
            f"http://localhost:8000/history?userId={test_user_id}",
            timeout=10
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code in [200, 404]:
            data = response.json()
            print(f"✅ Proper handling of non-existent user")
            print(f"📝 Response: {data.get('message', 'No message')}")
            return True
        else:
            print(f"❌ Unexpected response for non-existent user")
            return False
            
    except Exception as e:
        print(f"❌ Error testing with non-existent user: {e}")
        return False

def test_knowledge_graph_endpoint():
    """Test the knowledge graph endpoint"""
    print("\n🕸️  Testing Knowledge Graph Endpoint...")
    
    try:
        response = requests.get(
            "http://localhost:8000/api/knowledge-graph?query=ceiling",
            timeout=15
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Knowledge graph endpoint working!")
            print(f"📊 Nodes: {len(data.get('nodes', []))}")
            print(f"📊 Edges: {len(data.get('edges', []))}")
            return True
        else:
            print(f"❌ Knowledge graph endpoint failed")
            print(f"📝 Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing knowledge graph endpoint: {e}")
        return False

def main():
    """Main testing function"""
    print("🧪 Endpoint Testing Suite")
    print("=" * 50)
    
    # Check server health first
    if not test_server_health():
        return
    
    # Test various endpoints
    results = {
        "chat": test_chat_endpoint(),
        "history": test_history_endpoint(),
        "history_404": test_history_endpoint_nonexistent(),
        "knowledge_graph": test_knowledge_graph_endpoint()
    }
    
    # Summary
    print(f"\n📊 Test Results Summary:")
    print("=" * 30)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name:<15}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All endpoints are working correctly!")
    else:
        print("⚠️  Some endpoints need attention")
    
    print(f"\n💡 Notes:")
    print(f"   - This test runs without Redis requirement")
    print(f"   - History endpoint may work with file-based fallback")
    print(f"   - For full Redis testing, use: python test_redis_live.py")

if __name__ == "__main__":
    main() 