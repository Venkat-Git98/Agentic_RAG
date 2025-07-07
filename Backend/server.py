"""
FastAPI Backend Server for the LangGraph Agentic AI System.

This server exposes the agentic AI workflow via a streaming API,
allowing for real-time interaction and log streaming to a frontend.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, AsyncGenerator
from datetime import datetime
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# --- Local Imports ---
# Import the main AI class
from main import LangGraphAgenticAI
from knowledge_graph import get_knowledge_graph_service

# --- Pydantic Models for API ---

class QueryRequest(BaseModel):
    """Request model for a user query."""
    user_query: str
    thread_id: str

class LogMessage(BaseModel):
    """Structured log message for streaming."""
    level: str
    message: str
    timestamp: str

# --- Custom Logging Handler ---

class QueueHandler(logging.Handler):
    """A custom logging handler that puts log records into an asyncio.Queue."""
    def __init__(self, queue: asyncio.Queue):
        super().__init__()
        self.queue = queue

    def emit(self, record: logging.LogRecord):
        """Puts the log record into the queue."""
        self.queue.put_nowait(record)

# --- AI System Singleton ---
# This dictionary will hold the AI system instance.
# It's a simple way to manage the singleton instance.
ai_system_instance: Dict[str, LangGraphAgenticAI] = {}

# --- FastAPI Application Setup ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the FastAPI application.
    This is where the AI system is initialized.
    """
    print("Server starting up...")
    # Initialize the AI system on startup and store it in the singleton
    ai_system_instance["instance"] = LangGraphAgenticAI(debug=True, detailed_thinking=True)
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
# This is necessary to allow the frontend (running on a different port)
# to communicate with the backend.
origins = ["*"]

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
    Runs the AI query and streams logs in real-time as Server-Sent Events.
    """
    log_queue = asyncio.Queue()
    queue_handler = QueueHandler(log_queue)
    
    # Add the handler to the root logger to capture all logs.
    root_logger = logging.getLogger()
    root_logger.addHandler(queue_handler)
    
    ai_system = ai_system_instance.get("instance")
    if not ai_system:
        error_message = LogMessage(
            level="ERROR", 
            message="AI system not initialized.",
            timestamp=datetime.now().isoformat()
        ).json()
        yield f"event: log\ndata: {error_message}\n\n"
        return

    try:
        # Run the AI query in a background task.
        query_task = asyncio.create_task(
            ai_system.query(user_query=user_query, thread_id=thread_id)
        )
        
        # Concurrently stream logs and wait for the final result.
        while not query_task.done():
            try:
                # Wait for a log message to appear in the queue.
                log_record: logging.LogRecord = await asyncio.wait_for(log_queue.get(), timeout=0.1)
                
                log_msg = LogMessage(
                    timestamp=datetime.fromtimestamp(log_record.created).isoformat(),
                    level=log_record.levelname,
                    message=log_record.getMessage()
                )
                
                yield f"event: log\ndata: {log_msg.json()}\n\n"
            except asyncio.TimeoutError:
                # No log message, just continue to check if the task is done.
                continue
        
        # Once the query is done, get the result.
        final_answer = await query_task
        
        # Send the final answer as a 'result' event.
        result_data = {"result": final_answer}
        yield f"event: result\ndata: {json.dumps(result_data)}\n\n"

    except Exception as e:
        error_message = LogMessage(
            level="ERROR", 
            message=f"An unexpected error occurred during processing: {str(e)}",
            timestamp=datetime.now().isoformat()
        )
        yield f"event: log\ndata: {error_message.json()}\n\n"
    finally:
        # CRITICAL: Remove the handler to prevent log duplication in subsequent requests.
        root_logger.removeHandler(queue_handler)

# --- API Endpoints ---

@app.get("/", summary="Health Check")
async def read_root():
    """Health check endpoint to ensure the server is running."""
    return {"status": "ok", "message": "Welcome to the Agentic AI Server!"}

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)