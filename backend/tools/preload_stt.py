"""Pre-load STT model at startup for faster voice response."""
import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

# Global flag to track if STT is preloaded
_stt_preloaded = False

async def preload_stt_model() -> bool:
    """Pre-load the faster-whisper STT model at startup."""
    global _stt_preloaded
    
    if _stt_preloaded:
        return True
    
    try:
        logger.info("[PRELOAD] Starting STT model pre-loading...")
        start_time = asyncio.get_event_loop().time()
        
        # Import the STT builder
        from services.stt_realtime import build_stt_service
        from services import voice_config as _vc
        from services.runtime_config import _get_config_service
        
        # Get the current STT config
        config = _vc.get_stt_config(_get_config_service())
        
        # Build the service (this loads the model)
        await asyncio.to_thread(build_stt_service, config)
        
        elapsed = asyncio.get_event_loop().time() - start_time
        logger.info(f"[PRELOAD] STT model loaded in {elapsed:.2f}s")
        
        _stt_preloaded = True
        return True
        
    except Exception as e:
        logger.error(f"[PRELOAD] Failed to preload STT model: {e}")
        return False

def is_stt_preloaded() -> bool:
    """Check if STT model is preloaded."""
    return _stt_preloaded

# Fast response cache for common phrases
_response_cache = {}
_cache_timestamps = {}

def cache_response(text: str, response: str) -> None:
    """Cache a response for faster future delivery."""
    cache_key = text[:100].lower().strip()
    _response_cache[cache_key] = response
    _cache_timestamps[cache_key] = asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0
    
    # Keep cache size manageable
    if len(_response_cache) > 100:
        oldest_key = min(_cache_timestamps, key=_cache_timestamps.get)
        del _response_cache[oldest_key]
        del _cache_timestamps[oldest_key]

def get_cached_response(text: str) -> Optional[str]:
    """Check if a response is cached for faster delivery."""
    cache_key = text[:100].lower().strip()
    
    if cache_key in _response_cache:
        import time
        age = time.time() - _cache_timestamps.get(cache_key, 0)
        if age < 300:  # 5 minute cache
            return _response_cache[cache_key]
    
    return None

def preload_common_phrases() -> int:
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
        "Report ready for your review",
        "Lead found and qualified",
        "Campaign metrics updated",
        "WhatsApp message sent",
        "Research completed",
        "All agents operational"
    ]
    
    import time
    now = time.time()
    for phrase in common_phrases:
        _response_cache[phrase.lower()] = phrase
        _cache_timestamps[phrase.lower()] = now
    
    return len(common_phrases)
