#!/usr/bin/env python3
"""
Query Cache Testing Script

This script tests the new cross-user query caching functionality.
"""

import asyncio
import json
import requests
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"  # Change to your Railway URL for production testing
TEST_THREAD_ID = "test_cache_user_1"

def test_api_endpoint(endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
    """
    Test an API endpoint and return the response.
    
    Args:
        endpoint: API endpoint path
        method: HTTP method (GET, POST, DELETE)
        data: Request data for POST requests
        
    Returns:
        Dictionary containing response data
    """
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": getattr(response, 'status_code', None)}

def test_query_processing(query: str, thread_id: str) -> Dict[str, Any]:
    """
    Send a query to the chat endpoint and measure response time.
    
    Args:
        query: User query to test
        thread_id: Thread ID for the conversation
        
    Returns:
        Dictionary containing timing and response data
    """
    start_time = time.time()
    
    response = test_api_endpoint("/chat", "POST", {
        "message": query,
        "thread_id": thread_id
    })
    
    end_time = time.time()
    response_time = end_time - start_time
    
    return {
        "query": query,
        "response_time": response_time,
        "response": response,
        "timestamp": time.time()
    }

def main():
    """
    Main testing function that demonstrates query caching behavior.
    """
    print("🧪 QUERY CACHE TESTING SCRIPT")
    print("=" * 50)
    
    # Test queries to demonstrate caching
    test_queries = [
        "What is Section 1607 about?",
        "What are the live load requirements for residential buildings?",
        "What is the definition of occupancy classification?",
        "What is Section 1607 about?"  # Repeat first query to test cache hit
    ]
    
    print("\n📊 1. INITIAL CACHE STATISTICS")
    print("-" * 30)
    
    cache_stats = test_api_endpoint("/query-cache/stats")
    if "error" not in cache_stats:
        stats = cache_stats.get("statistics", {})
        print(f"Cached Queries: {stats.get('total_queries_cached', 0)}")
        print(f"Cache Hits: {stats.get('total_cache_hits', 0)}")
        print(f"Hit Rate: {stats.get('cache_hit_rate', 'N/A')}")
    else:
        print(f"❌ Error getting cache stats: {cache_stats.get('error')}")
    
    print(f"\n🚀 2. PROCESSING TEST QUERIES")
    print("-" * 30)
    
    results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔹 Query {i}: '{query[:50]}{'...' if len(query) > 50 else ''}'")
        
        result = test_query_processing(query, f"{TEST_THREAD_ID}_{i}")
        results.append(result)
        
        if "error" not in result["response"]:
            print(f"✅ Response time: {result['response_time']:.2f}s")
            
            # Check if this was a cache hit (if response contains cache indicators)
            response_text = result["response"].get("response", "")
            if "cached" in response_text.lower() or result["response_time"] < 2.0:
                print("🎯 Possible cache hit detected (fast response)")
            else:
                print("🔍 Fresh processing (normal response time)")
        else:
            print(f"❌ Error: {result['response'].get('error')}")
        
        # Brief pause between queries
        time.sleep(1)
    
    print(f"\n📈 3. UPDATED CACHE STATISTICS")
    print("-" * 30)
    
    cache_stats_after = test_api_endpoint("/query-cache/stats")
    if "error" not in cache_stats_after:
        stats = cache_stats_after.get("statistics", {})
        print(f"Cached Queries: {stats.get('total_queries_cached', 0)}")
        print(f"Cache Hits: {stats.get('total_cache_hits', 0)}")
        print(f"Hit Rate: {stats.get('cache_hit_rate', 'N/A')}")
        print(f"Average Confidence: {stats.get('average_confidence', 0):.2f}")
        
        # Show sample cached entries
        samples = cache_stats_after.get("sample_entries", [])
        if samples:
            print(f"\n📋 Sample Cached Entries:")
            for entry in samples[:3]:
                print(f"   • Query: {entry.get('query', '')[:60]}...")
                print(f"     Confidence: {entry.get('confidence_score', 0):.2f}, Uses: {entry.get('usage_count', 0)}")
    
    print(f"\n🔍 4. CACHE SEARCH TEST")
    print("-" * 30)
    
    search_results = test_api_endpoint("/query-cache/search?query=section&limit=5")
    if "error" not in search_results:
        results_data = search_results.get("results", [])
        print(f"Found {len(results_data)} cached entries containing 'section'")
        
        for result in results_data[:2]:  # Show first 2 results
            print(f"   • {result.get('query', '')[:80]}...")
            print(f"     Uses: {result.get('usage_count', 0)}, Confidence: {result.get('confidence_score', 0):.2f}")
    
    print(f"\n⏱️  5. PERFORMANCE ANALYSIS")
    print("-" * 30)
    
    # Analyze response times
    response_times = [r["response_time"] for r in results if "error" not in r["response"]]
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        
        print(f"Average Response Time: {avg_time:.2f}s")
        print(f"Fastest Response: {min_time:.2f}s")
        print(f"Slowest Response: {max_time:.2f}s")
        
        # Identify potential cache hits (very fast responses)
        fast_responses = [t for t in response_times if t < 3.0]
        if fast_responses:
            print(f"Potential Cache Hits: {len(fast_responses)}/{len(response_times)} queries")
    
    print(f"\n✅ 6. TESTING COMPLETE")
    print("-" * 30)
    print("🎯 Key Points to Verify:")
    print("   • Repeated queries should be faster (cache hits)")
    print("   • Cache statistics should show increased usage")
    print("   • High-confidence answers should be stored")
    print("   • Search functionality should find relevant queries")
    
    print(f"\n📡 API Endpoints for Manual Testing:")
    print(f"   Cache Stats: GET {BASE_URL}/query-cache/stats")
    print(f"   Search Cache: GET {BASE_URL}/query-cache/search?query=section")
    print(f"   Clear Cache: DELETE {BASE_URL}/query-cache/clear?confirm=true")

if __name__ == "__main__":
    main() 