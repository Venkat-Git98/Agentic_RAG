"""
FastAPI Backend Server for the LangGraph Agentic AI System.

This server exposes the agentic AI workflow via a streaming API,
allowing for real-time interaction and log streaming to a frontend.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any, AsyncGenerator
from datetime import datetime
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import redis

# --- Local Imports ---
# Import the main AI class
from main import LangGraphAgenticAI
from knowledge_graph import get_knowledge_graph_service
from config import REDIS_URL
from main import ThinkingMode

# --- Pydantic Models for API ---

class QueryRequest(BaseModel):
    """Request model for a user query."""
    user_query: str
    thread_id: str

# --- AI System Singleton ---
# This dictionary will hold the AI system instance.
# It's a simple way to manage the singleton instance.
ai_system_instance: Dict[str, LangGraphAgenticAI] = {}

# --- FastAPI Application Setup ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the FastAPI application.
    This is where the AI system and other resources are initialized.
    """
    print("Server starting up...")
    
    # Initialize the AI system on startup. It will use the global redis_client from config.
    ai_system_instance["instance"] = LangGraphAgenticAI(
        debug=True,
        thinking_detail_mode=ThinkingMode.DETAILED
    )
    print("AI System Initialized.")
    yield
    # Placeholder for cleanup
    print("Server shutting down...")
    ai_system_instance.clear()
    print("AI System shut down.")
    
app = FastAPI(
    title="LangGraph Agentic AI Server",
    description="A backend server for the multi-agent AI system.",
    version="1.0.0",
    lifespan=lifespan
)

# --- CORS Configuration ---
# This is necessary to allow the frontend (running on a different domain)
# to communicate with the backend.
origins = [
    "http://localhost:3000",  # Local development
    "http://localhost:5173",  # Vite dev server
    "https://phenomenal-puffpuff-a9bba5.netlify.app",  # Your specific Netlify URL
    "https://*.netlify.app",  # Netlify deployments
    "https://netlify.app", 
    "https://vabuildingcode.netlify.app/",
          # Netlify domains
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- Streaming Logic ---

async def stream_logs_and_query(user_query: str, thread_id: str) -> AsyncGenerator[str, None]:
    """
    Runs the AI query and streams thinking logs and the final result in real-time 
    as Server-Sent Events.
    """
    ai_system = ai_system_instance.get("instance")
    if not ai_system:
        error_message = {
            "level": "ERROR", 
            "message": "AI system not initialized.",
            "timestamp": datetime.now().isoformat()
        }
        yield f"event: log\ndata: {json.dumps(error_message)}\n\n"
        return

    try:
        async for event in ai_system.get_response_stream(user_query, thread_id):
            if "cognitive_message" in event:
                log_msg = {
                    "level": "INFO",
                    "message": event["cognitive_message"],
                    "timestamp": datetime.now().isoformat()
                }
                yield f"event: log\ndata: {json.dumps(log_msg)}\n\n"
            elif "final_answer" in event:
                result_data = {"result": event["final_answer"]}
                yield f"event: result\ndata: {json.dumps(result_data)}\n\n"
                
    except Exception as e:
        error_message = {
            "level": "ERROR", 
            "message": f"An unexpected error occurred during processing: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        yield f"event: log\ndata: {json.dumps(error_message)}\n\n"

# --- API Endpoints ---

@app.get("/", summary="Health Check")
async def read_root():
    """Health check endpoint to ensure the server is running."""
    return {"status": "ok", "message": "Welcome to the Agentic AI Server!"}

class ChatRequest(BaseModel):
    """Request model for a chat message."""
    message: str
    thread_id: str

@app.post("/query", summary="Process a query and stream logs")
async def query_endpoint(request: QueryRequest):
    """
    Accepts a user query and a thread_id, then streams logs and the final
    response back to the client using Server-Sent Events (SSE).
    
    - **log**: An event that streams structured log messages as they are generated.
    - **result**: The final event containing the AI's response.
    """
    return StreamingResponse(
        stream_logs_and_query(request.user_query, request.thread_id),
        media_type="text/event-stream"
    )

@app.post("/chat", summary="Process a chat message")
async def chat_endpoint(request: ChatRequest):
    """
    Accepts a chat message and thread_id, processes it through the AI system,
    and returns the response directly (non-streaming version).
    """
    ai_system = ai_system_instance.get("instance")
    if not ai_system:
        raise HTTPException(status_code=503, detail="AI system not initialized.")
    
    try:
        # Process the chat message
        response = await ai_system.query(user_query=request.message, thread_id=request.thread_id)
        
        return {
            "success": True,
            "message": "Message processed successfully",
            "thread_id": request.thread_id,
            "response": response
        }
        
    except Exception as e:
        logging.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.get("/api/knowledge-graph", summary="Get knowledge graph data")
async def get_knowledge_graph_endpoint(query: str):
    """
    Accepts a user query and returns the corresponding knowledge graph data.
    """
    try:
        graph_data = get_knowledge_graph_service(query)
        if not graph_data["nodes"]:
            raise HTTPException(status_code=404, detail="No data found for the specified query.")
        return graph_data
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Error getting knowledge graph: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/history", summary="Get chat history for a user")
async def get_history(userId: str):
    """
    Retrieves the chat history for a specific user from Redis.
    Falls back to file-based storage if Redis is unavailable.
    The `userId` corresponds to the `thread_id` used in the query endpoint.
    """
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    
    # Try Redis first if available
    if redis_client:
        try:
            # The history is stored as a Redis list. LRANGE fetches all items.
            history_json = redis_client.lrange(userId, 0, -1)
            
            if history_json:
                # The items stored in Redis are JSON strings, so they must be parsed.
                history = [json.loads(item) for item in history_json]
                return {
                    "success": True,
                    "message": f"Retrieved {len(history)} messages from Redis",
                    "user_id": userId,
                    "message_count": len(history),
                    "data": history
                }
            
        except Exception as e:
            logging.error(f"Error fetching history from Redis for userId '{userId}': {e}")
    
    # If Redis fails or no data found, try file system fallback
    try:
        file_path = f"data/{userId}.json"
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            history = data.get('full_history', [])
            return {
                "success": True,
                "message": f"Retrieved {len(history)} messages from file system",
                "user_id": userId,
                "message_count": len(history),
                "data": history
            }
    except Exception as e:
        logging.error(f"Error fetching history from file for userId '{userId}': {e}")
    
    # If both methods fail
    return {
        "success": False,
        "message": "No history found for this user",
        "user_id": userId,
        "message_count": 0,
        "data": []
    }

@app.get("/query-cache/stats", summary="Get query cache statistics")
async def get_query_cache_stats():
    """
    Get statistics about the query cache system.
    
    Returns:
        Dictionary containing cache statistics and metrics
    """
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        
        if not redis_client:
            raise HTTPException(status_code=503, detail="Redis not available")
        
        # Get basic cache statistics
        total_stored = redis_client.get("query_cache:total_stored") or 0
        
        # Get all cache keys
        cache_keys = redis_client.keys("query_cache:*")
        active_cache_keys = [key for key in cache_keys if not key.endswith(":usage") and not key.endswith(":last_used")]
        
        # Get sample of cache entries for analysis
        sample_entries = []
        for key in active_cache_keys[:10]:  # Sample first 10
            try:
                cache_data = redis_client.get(key)
                if cache_data:
                    entry = json.loads(cache_data)
                    usage_count = redis_client.get(f"{key}:usage") or 0
                    sample_entries.append({
                        "query": entry.get("query", "")[:100] + "..." if len(entry.get("query", "")) > 100 else entry.get("query", ""),
                        "cached_at": entry.get("cached_at"),
                        "confidence_score": entry.get("confidence_score"),
                        "usage_count": int(usage_count),
                        "answer_length": len(entry.get("answer", ""))
                    })
            except Exception as e:
                logging.error(f"Error processing cache entry {key}: {e}")
                continue
        
        # Calculate usage statistics
        total_usage = sum(int(redis_client.get(f"{key}:usage") or 0) for key in active_cache_keys)
        
        return {
            "success": True,
            "statistics": {
                "total_queries_cached": len(active_cache_keys),
                "total_cache_hits": total_usage,
                "total_stored_lifetime": int(total_stored),
                "cache_hit_rate": f"{(total_usage / int(total_stored) * 100):.1f}%" if int(total_stored) > 0 else "N/A",
                "average_confidence": sum(entry["confidence_score"] for entry in sample_entries) / len(sample_entries) if sample_entries else 0,
                "sample_size": len(sample_entries)
            },
            "sample_entries": sample_entries,
            "cache_health": {
                "redis_connected": True,
                "total_cache_keys": len(cache_keys),
                "active_queries": len(active_cache_keys)
            }
        }
        
    except Exception as e:
        logging.error(f"Error getting query cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving cache statistics: {str(e)}")

@app.get("/query-cache/search", summary="Search query cache")
async def search_query_cache(query: str = "", limit: int = 20):
    """
    Search for cached queries and their answers.
    
    Args:
        query: Search term to filter cached queries (optional)
        limit: Maximum number of results to return
        
    Returns:
        List of matching cached query-answer pairs
    """
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        
        if not redis_client:
            raise HTTPException(status_code=503, detail="Redis not available")
        
        # Get all cache keys
        cache_keys = redis_client.keys("query_cache:*")
        active_cache_keys = [key for key in cache_keys if not key.endswith(":usage") and not key.endswith(":last_used")]
        
        results = []
        for key in active_cache_keys[:limit]:  # Limit results
            try:
                cache_data = redis_client.get(key)
                if cache_data:
                    entry = json.loads(cache_data)
                    cached_query = entry.get("query", "").lower()
                    
                    # Filter by search query if provided
                    if query and query.lower() not in cached_query:
                        continue
                    
                    usage_count = redis_client.get(f"{key}:usage") or 0
                    results.append({
                        "cache_key": key.replace("query_cache:", ""),
                        "query": entry.get("query", ""),
                        "answer": entry.get("answer", "")[:500] + "..." if len(entry.get("answer", "")) > 500 else entry.get("answer", ""),
                        "confidence_score": entry.get("confidence_score"),
                        "sources": entry.get("sources", []),
                        "cached_at": entry.get("cached_at"),
                        "usage_count": int(usage_count),
                        "last_validated": entry.get("last_validated")
                    })
            except Exception as e:
                logging.error(f"Error processing cache entry {key}: {e}")
                continue
        
        # Sort by usage count descending
        results.sort(key=lambda x: x["usage_count"], reverse=True)
        
        return {
            "success": True,
            "message": f"Found {len(results)} cached queries",
            "search_query": query,
            "results": results[:limit]
        }
        
    except Exception as e:
        logging.error(f"Error searching query cache: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching cache: {str(e)}")

@app.delete("/query-cache/clear", summary="Clear query cache")
async def clear_query_cache(confirm: bool = False):
    """
    Clear all cached queries from Redis.
    
    Args:
        confirm: Must be True to actually clear the cache (safety measure)
        
    Returns:
        Confirmation of cache clearing
    """
    if not confirm:
        raise HTTPException(status_code=400, detail="Must set confirm=true to clear cache")
    
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        
        if not redis_client:
            raise HTTPException(status_code=503, detail="Redis not available")
        
        # Get all cache keys
        cache_keys = redis_client.keys("query_cache:*")
        
        if cache_keys:
            redis_client.delete(*cache_keys)
            logging.info(f"Cleared {len(cache_keys)} query cache entries")
        
        return {
            "success": True,
            "message": f"Cleared {len(cache_keys)} query cache entries",
            "cleared_keys": len(cache_keys)
        }
        
    except Exception as e:
        logging.error(f"Error clearing query cache: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Use Railway's PORT environment variable, default to 8000 for local development
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(app, host="0.0.0.0", port=port)