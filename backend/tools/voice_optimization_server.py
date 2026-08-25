"""Voice Optimization Server - Makes Jarvis voice faster and more responsive."""
import time
import asyncio
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("voice-optimization")

# Cache for frequently spoken phrases
_response_cache = {}
_cache_timestamps = {}

@mcp.tool()
def get_cached_response(text: str) -> str:
    """Check if a response is cached for faster delivery."""
    # Simple hash-based cache key
    cache_key = text[:100].lower().strip()
    
    if cache_key in _response_cache:
        age = time.time() - _cache_timestamps.get(cache_key, 0)
        if age < 300:  # 5 minute cache
            return _response_cache[cache_key]
    
    return ""

@mcp.tool()
def cache_response(text: str, response: str) -> str:
    """Cache a response for faster future delivery."""
    cache_key = text[:100].lower().strip()
    _response_cache[cache_key] = response
    _cache_timestamps[cache_key] = time.time()
    
    # Keep cache size manageable
    if len(_response_cache) > 100:
        oldest_key = min(_cache_timestamps, key=_cache_timestamps.get)
        del _response_cache[oldest_key]
        del _cache_timestamps[oldest_key]
    
    return "cached"

@mcp.tool()
def get_voice_stats() -> dict:
    """Get voice system performance statistics."""
    return {
        "cache_size": len(_response_cache),
        "cache_hit_rate": "optimizing",
        "stt_model": "preloaded",
        "tts_engine": "elevenlabs",
        "latency_target": "< 500ms"
    }

@mcp.tool()
def preload_common_phrases() -> str:
    """Preload common phrases for faster response."""
    common_phrases = [
        "Good morning Mr. Owen",
        "How can I help you today?",
        "Let me check that for you",
        "I've completed the task",
        "Here's what I found",
        "Processing your request",
        "Task completed successfully",
        "I'll handle that right away",
        "Analyzing the data now",
        "Report ready for your review"
    ]
    
    for phrase in common_phrases:
        _response_cache[phrase.lower()] = phrase
        _cache_timestamps[phrase.lower()] = time.time()
    
    return f"Preloaded {len(common_phrases)} common phrases"

if __name__ == "__main__":
    mcp.run()
