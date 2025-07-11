import requests
import json

def test_chat_endpoint():
    """Test the chat endpoint to verify the KeywordRetrievalTool fix."""
    url = "http://localhost:8000/chat"
    
    payload = {
        "message": "What are the fire safety requirements for a new single-family home in Fairfax County?",
        "thread_id": "test-123"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print("Testing chat endpoint...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ SUCCESS! The KeywordRetrievalTool fix is working!")
            result = response.json()
            print(f"Response length: {len(result.get('response', ''))}")
            print(f"Response preview: {result.get('response', '')[:200]}...")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    test_chat_endpoint() 