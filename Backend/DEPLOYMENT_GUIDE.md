# Deployment Guide: Railway Backend + Netlify Frontend

## Backend Deployment (Railway)

### 1. **Environment Variables Required**
Set these in your Railway project dashboard:

```bash
# API Keys
GOOGLE_API_KEY=your_google_api_key
COHERE_API_KEY=your_cohere_api_key
TAVILY_API_KEY=your_tavily_api_key

# Database
NEO4J_URI=your_neo4j_uri
NEO4J_USERNAME=your_neo4j_username
NEO4J_PASSWORD=your_neo4j_password
REDIS_URL=your_redis_url

# Model Configuration
TIER_1_MODEL_NAME=gemini-1.5-pro-latest
TIER_2_MODEL_NAME=gemini-1.5-flash-latest
TIER_3_MODEL_NAME=gemini-1.5-flash-latest
MEMORY_ANALYSIS_MODEL=gemini-1.5-flash-latest

# Research Configuration
USE_RERANKER=False
USE_PARALLEL_EXECUTION=True
USE_DOCKER=False

# Railway will automatically set these:
PORT=8000
RAILWAY_ENVIRONMENT=production
```

### 2. **Files Updated for Deployment**
- ✅ `server.py` - Fixed Pydantic deprecation warnings
- ✅ `server.py` - Updated CORS configuration for production
- ✅ `server.py` - Added Railway PORT environment variable support
- ✅ `tools/keyword_retrieval_tool.py` - Fixed deprecated pydantic imports
- ✅ `Procfile` - Already configured for Railway
- ✅ `requirements.txt` - Should contain all dependencies

### 3. **CORS Configuration**
Update the specific Netlify URL in `server.py`:

```python
origins = [
    "https://your-app-name.netlify.app",  # Replace with your actual Netlify URL
    "https://*.netlify.app",  # Netlify deployments
    # Remove "*" for production security
]
```

### 4. **Railway Deployment Steps**
1. Connect your GitHub repository to Railway
2. Set all environment variables in Railway dashboard
3. Deploy using the Procfile configuration
4. Monitor logs for any startup issues

## Frontend Configuration (Netlify)

### 1. **API Endpoint Configuration**
Update your frontend to use the Railway backend URL:

```javascript
// In your frontend config
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://your-railway-app.railway.app'
  : 'http://localhost:8000';
```

### 2. **Environment Variables for Frontend**
Set in Netlify dashboard:

```bash
REACT_APP_API_URL=https://your-railway-app.railway.app
REACT_APP_ENVIRONMENT=production
```

## Testing Deployment

### 1. **Health Check**
```bash
curl https://your-railway-app.railway.app/
```

### 2. **API Endpoints**
- `GET /` - Health check
- `POST /chat` - Chat endpoint (JSON response)
- `POST /query` - Streaming endpoint (SSE)
- `GET /history?userId=test` - History endpoint

### 3. **CORS Testing**
Test from your Netlify frontend to ensure CORS is working correctly.

## Common Issues & Solutions

### 1. **Port Issues**
- Railway automatically sets the PORT environment variable
- Make sure your server listens on `0.0.0.0:$PORT`

### 2. **CORS Issues**
- Add your specific Netlify URL to the origins list
- Remove "*" from origins in production

### 3. **Environment Variables**
- Double-check all API keys are set correctly
- Ensure Redis and Neo4j URLs are accessible from Railway

### 4. **Pydantic Warnings**
- All deprecation warnings have been fixed
- Use `model_dump_json()` instead of `json()`

## Performance Considerations

### 1. **Parallel Execution**
- `USE_PARALLEL_EXECUTION=True` for 4-6x performance improvement
- Monitor Railway's CPU/memory usage

### 2. **Model Tiering**
- Tier-1: Gemini Pro for critical tasks
- Tier-2: Gemini Flash for general tasks
- Optimized for cost and performance

### 3. **Caching**
- Redis caching is enabled for conversation history
- Monitor Redis usage and limits

## Security Notes

### 1. **API Keys**
- Never commit API keys to version control
- Use Railway's environment variables

### 2. **CORS**
- Restrict origins to your specific domains
- Remove wildcard "*" in production

### 3. **Rate Limiting**
- Consider implementing rate limiting for production
- Monitor API usage and costs

## Monitoring & Logging

### 1. **Railway Logs**
- Monitor deployment logs for errors
- Check startup sequence completion

### 2. **Application Logs**
- Structured logging is configured
- Monitor for API errors and performance issues

### 3. **Health Monitoring**
- Set up uptime monitoring for your Railway app
- Monitor API response times 