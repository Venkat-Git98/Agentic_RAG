# 🔄 Reranker Configuration Feature

## Overview

The AI Agent system now includes a configurable reranker feature that can be enabled or disabled based on performance requirements. This feature allows you to skip reranker logic when it's not performing optimally for building code documents.

## Configuration

### Environment Variable

Add the following to your `.env` file:

```bash
# Enable or disable the reranker (default: False)
USE_RERANKER=False
```

### Supported Values

The `USE_RERANKER` environment variable accepts the following values:

- **`True`**, **`true`**, **`TRUE`** - Enables the reranker
- **`False`**, **`false`**, **`FALSE`** - Disables the reranker
- **Empty string** or **any other value** - Defaults to `False` (disabled)

## How It Works

### When Reranker is Enabled (`USE_RERANKER=True`)

1. **Initialization**: The system initializes the Cohere reranker during startup
2. **Vector Search Enhancement**: After vector search results are obtained, they are reranked using semantic similarity
3. **Quality Improvement**: Results are reordered based on relevance to the specific query
4. **Fallback Protection**: If reranking fails, the system falls back to original vector search order

### When Reranker is Disabled (`USE_RERANKER=False`)

1. **Skip Initialization**: No reranker is initialized, saving memory and startup time
2. **Direct Vector Results**: Vector search results are used in their original order
3. **Faster Processing**: Eliminates reranking overhead for faster response times
4. **Simplified Pipeline**: Reduces complexity in the research pipeline

## Implementation Details

### Code Changes

#### 1. Configuration (config.py)
```python
# Controls whether to use the reranker for result optimization
USE_RERANKER = os.environ.get("USE_RERANKER", "False").lower() == "true"
```

#### 2. Research Orchestrator (agents/research_orchestrator.py)
```python
# Conditionally initialize reranker based on configuration
if USE_RERANKER:
    try:
        self.reranker = Reranker()
        self.logger.info("Reranker initialized and enabled")
    except Exception as e:
        self.logger.warning(f"Failed to initialize reranker: {e}. Continuing without reranker.")
        self.reranker = None
else:
    self.reranker = None
    self.logger.info("Reranker disabled by configuration")
```

#### 3. Parallel Research Tool (tools/parallel_research_tool.py)
```python
# Apply reranking if enabled and reranker is available
if self.use_reranker and self.reranker and primary_items:
    logging.info("Applying reranking to vector search results...")
    try:
        reranked_items = await self._rerank_documents(self.reranker, sub_query, primary_items)
        if reranked_items:
            primary_items = reranked_items
            logging.info(f"Reranking successful: reordered {len(primary_items)} items")
    except Exception as e:
        logging.warning(f"Reranking failed: {e}. Using original vector search order.")
else:
    logging.info("Reranking disabled by configuration")
```

## Usage Examples

### Disabling Reranker (Default)

```bash
# In .env file
USE_RERANKER=False
```

**Log Output:**
```
INFO - Reranker disabled by configuration
INFO - Research Orchestrator initialized with all tools
INFO - Reranking disabled by configuration
```

### Enabling Reranker

```bash
# In .env file
USE_RERANKER=True
COHERE_API_KEY=your-cohere-api-key  # Required for reranker
```

**Log Output:**
```
INFO - Reranker initialized and enabled
INFO - Research Orchestrator initialized with all tools
INFO - Applying reranking to vector search results...
INFO - Reranking successful: reordered 3 items
```

## Performance Impact

### With Reranker Disabled
- **Faster Processing**: Eliminates 200-500ms reranking overhead per query
- **Lower Memory Usage**: No reranker model loading
- **Simplified Logs**: Cleaner log output without reranking steps
- **Direct Results**: Uses vector search similarity scores directly

### With Reranker Enabled
- **Better Relevance**: Potentially improved result relevance through semantic reranking
- **Additional Latency**: 200-500ms additional processing time per sub-query
- **API Dependency**: Requires Cohere API key and network connectivity
- **Higher Complexity**: Additional failure points in the pipeline

## Troubleshooting

### Common Issues

1. **Missing Cohere API Key**
   ```
   WARNING - Failed to initialize reranker: Cohere API key not found. Continuing without reranker.
   ```
   **Solution**: Add `COHERE_API_KEY` to your `.env` file

2. **Reranker Initialization Failure**
   ```
   WARNING - Failed to initialize reranker: [error details]. Continuing without reranker.
   ```
   **Solution**: Check API key validity and network connectivity

3. **Reranking Runtime Failure**
   ```
   WARNING - Reranking failed: [error details]. Using original vector search order.
   ```
   **Solution**: System automatically falls back to original results

### Debug Information

Enable debug logging to see detailed reranker behavior:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## Migration Guide

### From Always-On Reranker
If you previously had reranker always enabled:

1. Add `USE_RERANKER=True` to your `.env` file to maintain current behavior
2. Monitor performance and consider disabling if not providing value
3. Test with `USE_RERANKER=False` to compare performance

### From No Reranker
If you want to try the reranker:

1. Add `USE_RERANKER=True` to your `.env` file
2. Add your `COHERE_API_KEY` to your `.env` file
3. Monitor logs for reranking effectiveness
4. Compare response quality with and without reranker

## Best Practices

1. **Performance Testing**: Test both configurations with your specific use cases
2. **Monitoring**: Monitor response times and quality with both settings
3. **Fallback Awareness**: System gracefully handles reranker failures
4. **Environment Specific**: Use different settings for development vs production
5. **Cost Consideration**: Reranker adds API costs - evaluate ROI

## Related Configuration

This feature works alongside other search configurations:

- **Vector Search**: Primary search method (always enabled)
- **Graph Search**: Fallback method (always enabled)
- **Keyword Search**: Secondary fallback (always enabled) 
- **Web Search**: Final fallback (always enabled)
- **Reranker**: Optional result optimization (configurable)

The reranker only affects the ordering of vector search results and does not impact the fallback chain logic. 