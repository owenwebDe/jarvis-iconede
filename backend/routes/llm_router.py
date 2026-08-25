"""FastAPI routes for Multi-Model LLM Router monitoring and key management.

Also exposes an OpenAI-compatible /v1/chat/completions proxy so fast-agent
(or any OpenAI SDK consumer) can route through the MultiModelRouter cascade
without any client-side changes.  Point the provider base_url at
http://localhost:8000 and every chat/completions call cascades automatically:
  Groq -> Cerebras -> SambaNova -> Google -> OpenRouter -> DeepSeek
"""
from __future__ import annotations

import time
import uuid as _uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from fastapi.responses import StreamingResponse
from core.auth import verify_api_key
from services.llm_router import get_router

import logging
logger = logging.getLogger("llm_router.proxy")

router = APIRouter(prefix="/api/llm-router", tags=["LLM Router"])

# Separate router WITHOUT prefix for the OpenAI-compatible proxy.
# fast-agent sends to {base_url}/chat/completions, so the path must be
# exactly /v1/chat/completions — not nested under /api/llm-router/.
_openai_proxy_router = APIRouter(tags=["LLM Router Proxy"])


def _to_sse_stream(result: dict) -> StreamingResponse:
    """Convert a non-streaming OpenAI response to SSE streaming format.

    Fast-agent's OpenAI provider expects streaming chunks when `stream=True`.
    This converts a single completion result into the SSE chunk format that
    the OpenAI SDK/client expects.
    """
    import json as _json

    chunk_id = result.get("id", f"chatcmpl-{_uuid.uuid4().hex[:12]}")
    model = result.get("model", "routed")
    choices = result.get("choices", [])
    usage = result.get("usage")

    def generate():
        for choice in choices:
            delta = choice.get("delta", choice.get("message", {}))
            finish = choice.get("finish_reason")

            # Emit the content delta
            if delta.get("content"):
                chunk = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": result.get("created", int(time.time())),
                    "model": model,
                    "choices": [{
                        "index": choice.get("index", 0),
                        "delta": {"content": delta["content"]},
                        "finish_reason": None,
                    }],
                }
                yield f"data: {_json.dumps(chunk)}\n\n"

            # Emit tool calls if present
            if delta.get("tool_calls"):
                for tc in delta["tool_calls"]:
                    chunk = {
                        "id": chunk_id,
                        "object": "chat.completion.chunk",
                        "created": result.get("created", int(time.time())),
                        "model": model,
                        "choices": [{
                            "index": choice.get("index", 0),
                            "delta": {"tool_calls": [tc]},
                            "finish_reason": None,
                        }],
                    }
                    yield f"data: {_json.dumps(chunk)}\n\n"

            # Emit finish reason
            if finish:
                chunk = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": result.get("created", int(time.time())),
                    "model": model,
                    "choices": [{
                        "index": choice.get("index", 0),
                        "delta": {},
                        "finish_reason": finish,
                    }],
                }
                if usage:
                    chunk["usage"] = usage
                yield f"data: {_json.dumps(chunk)}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


class AddKeyRequest(BaseModel):
    provider: str
    api_key: str
    owner: str = "primary"
    base_url: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    messages: List[Dict[str, Any]]
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None


@router.get("/status")
async def get_router_status(_auth=Depends(verify_api_key)):
    """Return live status of the multi-model key pool and cascade tiers."""
    llm_router = get_router()
    return {
        "cascade_order": llm_router.cascade_order,
        "telemetry": llm_router.get_pool_telemetry(),
    }


@router.post("/reload")
async def reload_keys_from_env(_auth=Depends(verify_api_key)):
    """Dynamically re-scan .env for newly added keys without restarting."""
    llm_router = get_router()
    counts = llm_router.reload_keys_from_env()
    return {"status": "ok", "message": "Keys reloaded from .env", "key_counts": counts}


@router.post("/prune")
async def prune_dead_keys(_auth=Depends(verify_api_key)):
    """Manually trigger dead key purging."""
    llm_router = get_router()
    pruned = llm_router.prune_dead_keys()
    return {"status": "ok", "pruned_dead_keys": pruned}


@router.post("/keys")
async def add_provider_key(req: AddKeyRequest, _auth=Depends(verify_api_key)):
    """Add or register a new API key into the live provider pool."""
    llm_router = get_router()
    if req.provider.lower() not in llm_router.cascade_order:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider '{req.provider}'. Allowed: {llm_router.cascade_order}",
        )
    llm_router.add_key(
        provider=req.provider,
        api_key=req.api_key,
        owner=req.owner,
        base_url=req.base_url,
    )
    return {"status": "ok", "provider": req.provider, "owner": req.owner}


@router.post("/complete")
async def execute_routed_completion(req: ChatCompletionRequest, _auth=Depends(verify_api_key)):
    """Execute a completion via the multi-model cascade engine."""
    llm_router = get_router()
    try:
        result = await llm_router.chat_completion(
            messages=req.messages,
            model=req.model,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


# ── OpenAI-compatible proxy (fast-agent integration) ────────────────────────
# This endpoint lets fast-agent (or any OpenAI SDK consumer) route through
# the MultiModelRouter cascade by simply setting base_url to localhost:8000.
# No auth — local-only, never exposed to the internet.

@_openai_proxy_router.post("/v1/chat/completions")
async def openai_completions_proxy(request: Request):
    """OpenAI-compatible /v1/chat/completions that routes through the cascade.

    Accepts the full OpenAI chat completion schema (messages, model, tools,
    temperature, max_tokens, response_format, stream, etc.) and returns an
    OpenAI-compatible response.  On429/rate-limit the router automatically
    cascades to the next provider — the caller sees no difference.
    """
    body = await request.json()
    llm_router = get_router()

    messages = body.get("messages", [])
    model = body.get("model")
    temperature = body.get("temperature", 0.7)
    max_tokens = body.get("max_tokens")
    tools = body.get("tools")
    response_format = body.get("response_format")
    stream = body.get("stream", False)

    t0 = time.time()
    try:
        result = await llm_router.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            response_format=response_format,
        )
        elapsed = time.time() - t0

        # Ensure OpenAI-compatible envelope
        result.setdefault("id", f"chatcmpl-{_uuid.uuid4().hex[:12]}")
        result.setdefault("object", "chat.completion")
        result.setdefault("created", int(time.time()))
        result.setdefault("model", model or "routed")

        # Log which provider actually served the request
        choices = result.get("choices", [])
        if choices:
            finish = choices[0].get("finish_reason", "unknown")
            provider = result.get("_routed_provider", "unknown")
            logger.info(
                "[ROUTER-PROXY] Completed via %s in %.1fs (finish=%s)",
                provider, elapsed, finish,
            )

        # If client requested streaming, convert to SSE format
        if stream:
            return _to_sse_stream(result)

        return JSONResponse(content=result)

    except RuntimeError as exc:
        # All providers exhausted
        logger.error("[ROUTER-PROXY] All providers exhausted: %s", exc)
        return JSONResponse(
            status_code=502,
            content={
                "error": {
                    "message": str(exc),
                    "type": "server_error",
                    "code": "provider_exhausted",
                }
            },
        )
    except Exception as exc:
        logger.error("[ROUTER-PROXY] Unexpected error: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "message": str(exc),
                    "type": "server_error",
                    "code": "internal_error",
                }
            },
        )
