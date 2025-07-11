import requests

def test_root_endpoint():
    """Test the root endpoint to verify server is running."""
    try:
        print("Testing root endpoint...")
        response = requests.get("http://localhost:8000/", timeout=5)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ Server is running!")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_chat_quick():
    """Quick test with a simple query."""
    if not test_root_endpoint():
        return
        
    payload = {
        "message": "hello",
        "thread_id": "test-simple"
    }
    
    try:
        print("\nTesting chat endpoint with simple message...")
        response = requests.post("http://localhost:8000/chat", json=payload, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ SUCCESS! The KeywordRetrievalTool fix is working!")
            result = response.json()
            print(f"Success: {result.get('success')}")
            print(f"Response length: {len(result.get('response', ''))}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_chat_quick() 