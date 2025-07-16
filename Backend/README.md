# 🤖 LangGraph Agentic AI Backend

A sophisticated multi-agent AI system built on LangGraph that orchestrates specialized agents to provide intelligent, context-aware responses through advanced reasoning and knowledge retrieval capabilities.

## 🌟 Overview

This backend implements a state-of-the-art agentic AI architecture where multiple specialized agents collaborate through a carefully orchestrated workflow. Each agent has a specific role in the cognitive pipeline, from initial query triage to complex research orchestration and response synthesis.

The system is designed to handle complex queries that require:
- **Multi-step reasoning** and research planning
- **Context-aware retrieval** from knowledge graphs and vector stores
- **Mathematical calculations** and formula extraction
- **Conversation memory** and contextual follow-ups
- **Parallel research execution** for efficiency
- **High-performance caching** for instant responses

## 🏗️ Architecture

### Core Components

1. **LangGraph Workflow Engine**: Manages state transitions and agent orchestration
2. **Specialized Agents**: Each handles specific cognitive tasks
3. **Knowledge Infrastructure**: Neo4j graph database + Redis caching
4. **Thinking Engine**: Provides transparent reasoning visibility
5. **API Layer**: FastAPI-based streaming server

### Agent Ecosystem

- **🔍 Triage Agent**: Classifies queries and routes to appropriate workflows
- **💭 Contextual Answering Agent**: Handles follow-up questions using conversation context
- **📋 Planning Agent**: Breaks complex queries into research sub-tasks
- **🔮 Hyde Agent**: Generates hypothetical answers for better retrieval
- **🔬 Research Orchestrator**: Executes parallel research operations
- **✨ Synthesis Agent**: Combines research into coherent responses
- **🧠 Memory Agent**: Updates conversation and structured memory
- **⚠️ Error Handler**: Manages failures and provides fallback strategies

### Data Infrastructure

- **Neo4j**: Knowledge graph for structured document storage
- **Redis**: High-performance caching and session management
- **Vector Search**: Semantic similarity retrieval
- **Web Search**: Real-time information gathering via Tavily

## 🚀 Features

### Advanced Capabilities

- **🔄 Stateful Conversations**: Maintains context across multiple interactions
- **🧮 Mathematical Processing**: Extracts and executes formulas from documents
- **📊 Parallel Research**: Executes multiple research queries simultaneously
- **🎯 Precision Retrieval**: Combines vector, graph, and keyword search strategies
- **🔍 Transparent Reasoning**: Optional thinking mode reveals agent decision-making
- **⚡ Stream Processing**: Real-time response streaming for better UX
- **📈 Quality Metrics**: Tracks retrieval relevance and synthesis quality

### Intelligent Query Handling

- Natural language understanding with intent classification
- Complex multi-document research and synthesis
- Mathematical calculations with step-by-step explanations
- Contextual follow-ups without repeating information
- Fallback strategies for challenging queries

## 📦 Installation

### Prerequisites

- Python 3.11+
- Redis server
- Neo4j database
- API keys for: Google Gemini, Cohere, Tavily

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Backend
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Configure environment**
   Create a `.env` file:
   ```env
   GOOGLE_API_KEY=your_google_api_key
   COHERE_API_KEY=your_cohere_api_key
   TAVILY_API_KEY=your_tavily_api_key
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_password
   REDIS_URL=redis://localhost:6379
   LANGCHAIN_API_KEY=your_langsmith_key  # Optional
   ```

4. **Initialize the database**
   ```bash
   python manage_neo4j_indexes.py
   ```

5. **Run the server**
   ```bash
   poetry run uvicorn server:app --reload
   ```

## 🔧 Configuration

Key configuration options in `config.py`:

- **Model Tiers**: Configure primary (tier_1) and secondary (tier_2) LLMs
- **Cache Settings**: Redis connection and TTL configurations
- **Search Parameters**: Retrieval limits and reranking thresholds
- **Debug Mode**: Enable detailed logging and thinking visibility

## 📡 API Usage

### Basic Query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "What are the load requirements for residential buildings?",
    "thread_id": "unique-session-id"
  }'
```

### Streaming Response

The API returns Server-Sent Events (SSE) for real-time updates:

```javascript
const eventSource = new EventSource('/query');
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'final_response') {
    console.log('Answer:', data.content);
  }
};
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
python comprehensive_test_suite.py
```

Test categories include:
- Simple queries
- Complex research scenarios
- Mathematical calculations
- Contextual follow-ups
- Error handling

## 📊 Monitoring & Debugging

### LangSmith Integration

Enable tracing by setting:
```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_key
```

### Thinking Mode

Enable detailed reasoning visibility:
```python
ai_system = LangGraphAgenticAI(
    thinking_detail_mode=ThinkingMode.DETAILED
)
```

### Logs

- Application logs: `logs/agent_run.log`
- Test results: `test_output.log`
- Evaluation metrics: `evaluation_log.jsonl`

## 🗂️ Project Structure

```
Backend/
├── agents/              # Specialized agent implementations
├── core/               # Core workflow and state management
├── tools/              # Utility tools (search, retrieval, etc.)
├── thinking_agents/    # Enhanced reasoning capabilities
├── knowledge_graph/    # Graph database integration
├── data/              # Static data and configurations
├── server.py          # FastAPI application
├── main.py            # CLI entry point
├── config.py          # Configuration management
└── prompts.py         # Centralized prompt templates
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software. All rights reserved.

## 🙏 Acknowledgments

Built with:
- [LangGraph](https://github.com/langchain-ai/langgraph) for workflow orchestration
- [LangChain](https://github.com/langchain-ai/langchain) for LLM integration
- [FastAPI](https://fastapi.tiangolo.com/) for the API layer
- [Neo4j](https://neo4j.com/) for knowledge graph storage
- [Redis](https://redis.io/) for caching 