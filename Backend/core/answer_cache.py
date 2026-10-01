"""Keys and switches for the cross-user answer cache (Redis)."""
import contextvars
import hashlib

# Part of every cache key. Bump it when retrieval or the prompts change, so
# answers produced by the old pipeline are not served by the new one.
CACHE_VERSION = "v2"

# Set per request (evals turn the cache off so they always measure the live pipeline).
cache_disabled = contextvars.ContextVar("cache_disabled", default=False)


def cache_key(query: str) -> str:
    digest = hashlib.sha256(query.lower().strip().encode()).hexdigest()
    return f"query_cache:{CACHE_VERSION}:{digest}"
