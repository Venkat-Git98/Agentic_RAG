# 🚀 Agentic AI Backend Repository

A cutting-edge multi-agent AI system powered by LangGraph, designed to orchestrate specialized AI agents for complex reasoning, research, and intelligent response generation.

## 🎯 Project Overview

This repository contains a sophisticated backend system that implements an agentic AI architecture. Multiple specialized agents collaborate through a carefully orchestrated workflow to handle complex queries requiring multi-step reasoning, parallel research execution, and context-aware responses.

### Key Highlights

- **🤖 Multi-Agent Architecture**: Specialized agents for different cognitive tasks
- **🔄 LangGraph Workflow**: State-based orchestration with conditional routing
- **🧠 Transparent Reasoning**: Optional thinking mode reveals decision-making
- **⚡ High Performance**: Parallel execution, Redis caching, optimized retrieval
- **💾 Dual Storage**: Neo4j knowledge graph + Redis for session management
- **🌐 Real-time Streaming**: Server-Sent Events for responsive UX

## 📁 Repository Structure

```
.
├── Backend/                    # Main backend implementation
│   ├── agents/                # Specialized agent implementations
│   ├── core/                  # Core workflow and state management
│   ├── tools/                 # Reusable utility tools
│   ├── thinking_agents/       # Enhanced reasoning capabilities
│   ├── knowledge_graph/       # Graph database integration
│   ├── technical_specification/ # Detailed technical docs
│   ├── server.py              # FastAPI application
│   ├── main.py                # CLI entry point
│   └── README.md              # Backend-specific documentation
│
├── evaluation_log.jsonl       # System evaluation metrics
└── README.md                  # This file
```

## 🏗️ System Architecture

### High-Level Flow

```
User Query → API Gateway → LangGraph Workflow → Multi-Agent Pipeline → Response
                                    ↓
                            State Management
                                    ↓
                        [Knowledge Base | Cache | Memory]
```

### Agent Pipeline

1. **Triage Agent**: Classifies queries and determines routing
2. **Planning Agent**: Decomposes complex queries into sub-tasks
3. **Research Orchestrator**: Executes parallel information retrieval
4. **Synthesis Agent**: Combines findings into coherent responses
5. **Memory Agent**: Updates conversation context and extracts facts

### Data Infrastructure

- **Neo4j**: Stores structured knowledge as a graph
- **Redis**: Handles caching and session management
- **Vector DB**: Enables semantic similarity search
- **Web Search**: Real-time information via Tavily API

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker (for Redis and Neo4j)
- API Keys: Google Gemini, Cohere, Tavily

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd agentic-ai-backend
   ```

2. **Set up the backend**
   ```bash
   cd Backend
   poetry install
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and database credentials
   ```

4. **Start services**
   ```bash
   docker-compose up -d  # Starts Redis and Neo4j
   python manage_neo4j_indexes.py  # Initialize database
   ```

5. **Run the server**
   ```bash
   poetry run uvicorn server:app --reload
   ```

## 💡 Usage Examples

### Basic Query
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "Explain the emergency exit requirements",
    "thread_id": "session-123"
  }'
```

### Python Client
```python
import asyncio
from Backend.main import LangGraphAgenticAI

async def main():
    ai = LangGraphAgenticAI(debug=True)
    response = await ai.get_response_stream(
        "What are the load calculations for residential buildings?",
        thread_id="session-456"
    )
    
    async for chunk in response:
        if chunk["type"] == "final_response":
            print(chunk["content"])

asyncio.run(main())
```

## 🔬 Key Features

### 1. Intelligent Query Routing
- Automatic classification of query complexity
- Optimal agent selection for efficiency
- Fallback strategies for edge cases

### 2. Advanced Research Capabilities
- **Vector Search**: Semantic similarity matching
- **Graph Traversal**: Relationship-based retrieval
- **Keyword Search**: Exact term matching
- **Web Search**: Real-time information gathering

### 3. Context-Aware Conversations
- Maintains conversation history
- Extracts and stores key facts
- Enables natural follow-up questions

### 4. Mathematical Processing
- Formula extraction from documents
- Variable identification and mapping
- Step-by-step calculation execution

### 5. Quality Assurance
- Retrieval relevance scoring
- Answer completeness validation
- Source verification and citations

## 📊 Performance & Monitoring

### Metrics Tracked
- Agent execution times
- Cache hit rates
- Token usage per query
- Error rates and types
- Response quality scores

### Monitoring Tools
- **LangSmith**: Detailed execution traces
- **Custom Logs**: Structured logging to files
- **Real-time Metrics**: Available via `/metrics` endpoint

## 🧪 Testing

Run the comprehensive test suite:
```bash
cd Backend
python comprehensive_test_suite.py
```

Test categories:
- Unit tests for individual agents
- Integration tests for workflows
- Performance benchmarks
- Error handling scenarios

## 📚 Documentation

### For Developers
- [Backend Architecture](Backend/README.md)
- [Technical Specifications](Backend/technical_specification/README.md)
- [Agent Documentation](Backend/agents/README.md)
- [Tools Reference](Backend/tools/README.md)
- [Core Components](Backend/core/README.md)


## 🛠️ Development

### Adding New Agents

1. Create agent class inheriting from `BaseLangGraphAgent`
2. Implement the `execute()` method
3. Add to workflow in `thinking_workflow.py`
4. Define routing logic

### Extending Tools

1. Create tool class in `tools/` directory
2. Implement core functionality
3. Add error handling and logging
4. Write comprehensive tests

## 🔒 Security Considerations

- API keys stored in environment variables
- Redis password protection enabled
- Neo4j authentication required
- Rate limiting on API endpoints
- Input validation and sanitization

## 📞 Support

- 📧 Email: svenkatesh.js@gmail.com
