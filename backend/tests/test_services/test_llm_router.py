import time
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from services.llm_router import MultiModelRouter, ProviderKey


@pytest.mark.asyncio
async def test_router_key_registration_and_rotation():
    router = MultiModelRouter(cascade_order=["groq", "deepseek"], load_env=False)
    
    # Register 2 keys for groq
    router.add_key("groq", "key_1", owner="Owen")
    router.add_key("groq", "key_2", owner="Friend_1")
    
    # Check round robin
    k1 = router.get_next_available_key("groq")
    assert k1 is not None
    assert k1.api_key == "key_1"
    
    k2 = router.get_next_available_key("groq")
    assert k2 is not None
    assert k2.api_key == "key_2"
    
    k3 = router.get_next_available_key("groq")
    assert k3 is not None
    assert k3.api_key == "key_1"


@pytest.mark.asyncio
async def test_router_rate_limit_cooldown_and_fallback():
    router = MultiModelRouter(cascade_order=["groq", "deepseek"], load_env=False)
    
    router.add_key("groq", "groq_key_1", owner="Owen")
    router.add_key("groq", "groq_key_2", owner="Friend_1")
    router.add_key("deepseek", "deepseek_key_1", owner="Friend_2")
    
    k1 = router.get_next_available_key("groq")
    assert k1.api_key == "groq_key_1"
    
    # Mark k1 as rate-limited (429)
    router.mark_rate_limited(k1, cooldown_seconds=30.0)
    assert not k1.is_available
    
    # Next available key for groq should be k2
    k2 = router.get_next_available_key("groq")
    assert k2.api_key == "groq_key_2"
    
    # Mark k2 as rate-limited as well
    router.mark_rate_limited(k2, cooldown_seconds=30.0)
    assert not k2.is_available
    
    # Groq has no more available keys
    assert router.get_next_available_key("groq") is None
    
    # DeepSeek key is available
    ds_key = router.get_next_available_key("deepseek")
    assert ds_key is not None
    assert ds_key.api_key == "deepseek_key_1"


@pytest.mark.asyncio
async def test_router_chat_completion_cascade():
    router = MultiModelRouter(cascade_order=["groq", "cerebras", "deepseek"], load_env=False)
    router.add_key("groq", "groq_key", owner="Owen")
    router.add_key("cerebras", "cerebras_key", owner="Friend_1")
    router.add_key("deepseek", "deepseek_key", owner="Friend_2")
    
    mock_client = AsyncMock()
    
    # First call (groq) returns 429 Rate Limit
    # Second call (cerebras) succeeds with 200 OK
    resp_429 = MagicMock(status_code=429, text="Rate limit exceeded")
    resp_200 = MagicMock(
        status_code=200,
        json=lambda: {
            "id": "chatcmpl-test",
            "choices": [{"message": {"role": "assistant", "content": "Hello from Cerebras!"}}],
            "usage": {"total_tokens": 42},
        }
    )
    
    mock_client.post.side_effect = [resp_429, resp_200]
    
    with patch.object(router, "_get_client", return_value=mock_client):
        result = await router.chat_completion(messages=[{"role": "user", "content": "Hi"}])
        
        assert result["choices"][0]["message"]["content"] == "Hello from Cerebras!"
        assert mock_client.post.call_count == 2


def test_router_pool_status():
    router = MultiModelRouter(cascade_order=["groq", "deepseek"], load_env=False)
    router.add_key("groq", "key_a", owner="Owen")
    router.add_key("groq", "key_b", owner="Friend_1")
    
    status = router.get_pool_status()
    assert "groq" in status
    assert status["groq"]["total_keys"] == 2
    assert status["groq"]["available_keys"] == 2
    assert len(status["groq"]["keys"]) == 2
