import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# ... existing code ...

app = FastAPI(
    title="LangGraph Agentic AI",
    version="1.0.0",
    lifespan=lifespan
)

# --- CORS Configuration ---
# This is necessary to allow the frontend (running on a different port)
# to communicate with the backend.
origins = [
    "http://localhost:5173",  # React default dev port
    "http://127.0.0.1:5173",
    # You can add other origins here, like your production frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods, including OPTIONS for preflight
    allow_headers=["*"],  # Allows all headers
)

# --- Streaming Logic ---

async def stream_logs_and_query(user_query: str, thread_id: str) -> AsyncGenerator[str, None]:
    # ... existing code ...