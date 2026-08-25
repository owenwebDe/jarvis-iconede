"""ElevenLabs high-fidelity real-time TTS provider.

Implements :class:`services.tts.TTSProvider` using direct ElevenLabs REST & Streaming APIs:
* ``stream_audio`` — yields MP3 audio chunks streamed in real-time.
* ``stream_pcm`` — yields raw 24kHz int16 mono PCM for ultra-low latency WebSocket streaming.
* ``generate_audio`` — generates full MP3 bytes with instant fallback to EdgeTTS on quota exhaust.
"""
from __future__ import annotations

import asyncio
import io
import json
import logging
import os
from typing import Any, AsyncIterator, Optional

import httpx
from services.tts import TTSProvider, EdgeTTSProvider

logger = logging.getLogger(__name__)

DEFAULT_ELEVENLABS_VOICE_ID = "onwK4e9ZLuTAKqWW03F9"  # Daniel / Deep British Broadcaster
DEFAULT_ELEVENLABS_MODEL_ID = "eleven_flash_v2"       # Low latency & high quality


class ElevenLabsTTSProvider(TTSProvider):
    """Native ElevenLabs TTS Provider with streaming and failover."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
        stability: float = 0.5,
        similarity_boost: float = 0.8,
    ) -> None:
        self._api_key = api_key or os.getenv("ELEVENLABS_API_KEY", "")
        self.voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID") or DEFAULT_ELEVENLABS_VOICE_ID
        self.model_id = model_id or os.getenv("ELEVENLABS_MODEL_ID") or DEFAULT_ELEVENLABS_MODEL_ID
        self.stability = float(stability)
        self.similarity_boost = float(similarity_boost)
        self._fallback_provider = EdgeTTSProvider()

    async def generate_audio(self, text: str) -> Optional[bytes]:
        """Generate full MP3 audio for given text."""
        if not text or not text.strip():
            return None

        if not self._api_key:
            logger.warning("[ElevenLabs] No API key provided, falling back to EdgeTTS")
            return await self._fallback_provider.generate_audio(text)

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
            "User-Agent": "JarvisAI/2.0",
        }
        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": self.stability,
                "similarity_boost": self.similarity_boost,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    return resp.content
                elif resp.status_code in (401, 402, 429):
                    logger.warning("[ElevenLabs] HTTP %d (quota/key issue) -> falling back to EdgeTTS", resp.status_code)
                    return await self._fallback_provider.generate_audio(text)
                else:
                    logger.error("[ElevenLabs] Generation error %d: %s", resp.status_code, resp.text[:150])
                    return await self._fallback_provider.generate_audio(text)
        except Exception as e:
            logger.error("[ElevenLabs] generate_audio exception: %s -> falling back to EdgeTTS", e)
            return await self._fallback_provider.generate_audio(text)

    async def stream_audio(self, text: str) -> AsyncIterator[bytes]:
        """Stream MP3 chunks directly from ElevenLabs."""
        if not text or not text.strip():
            return

        if not self._api_key:
            async for chunk in self._fallback_provider.stream_audio(text):
                yield chunk
            return

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream?output_format=mp3_44100_128"
        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
            "User-Agent": "JarvisAI/2.0",
        }
        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": self.stability,
                "similarity_boost": self.similarity_boost,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as resp:
                    if resp.status_code == 200:
                        async for chunk in resp.aiter_bytes(chunk_size=4096):
                            if chunk:
                                yield chunk
                        return
                    else:
                        logger.warning("[ElevenLabs] stream_audio status %d -> falling back", resp.status_code)
        except Exception as e:
            logger.warning("[ElevenLabs] stream_audio failed (%s) -> fallback", e)

        # Fallback to EdgeTTS
        async for chunk in self._fallback_provider.stream_audio(text):
            yield chunk

    async def stream_pcm(self, text: str, sample_rate: int = 24000) -> AsyncIterator[bytes]:
        """Stream raw int16 mono PCM at sample_rate (24kHz default)."""
        if not text or not text.strip():
            return

        if not self._api_key:
            async for chunk in self._fallback_provider.stream_pcm(text, sample_rate=sample_rate):
                yield chunk
            return

        fmt = f"pcm_{sample_rate}" if sample_rate in (16000, 22050, 24000, 44100) else "pcm_24000"
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream?output_format={fmt}"
        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
            "User-Agent": "JarvisAI/2.0",
        }
        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": self.stability,
                "similarity_boost": self.similarity_boost,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as resp:
                    if resp.status_code == 200:
                        async for chunk in resp.aiter_bytes(chunk_size=4096):
                            if chunk:
                                yield chunk
                        return
                    else:
                        logger.warning("[ElevenLabs] stream_pcm status %d -> falling back", resp.status_code)
        except Exception as e:
            logger.warning("[ElevenLabs] stream_pcm failed (%s) -> fallback", e)

        # Fallback to EdgeTTS
        async for chunk in self._fallback_provider.stream_pcm(text, sample_rate=sample_rate):
            yield chunk


def build_provider(params: dict[str, Any], secrets: dict[str, str]) -> ElevenLabsTTSProvider:
    """Factory called by services.tts_realtime.build_chat_provider."""
    api_key = (secrets or {}).get("api_key") or os.getenv("ELEVENLABS_API_KEY", "")
    voice_id = (params or {}).get("voice") or os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_ELEVENLABS_VOICE_ID)
    model_id = (params or {}).get("model") or DEFAULT_ELEVENLABS_MODEL_ID
    stability = (params or {}).get("stability", 0.5)
    similarity_boost = (params or {}).get("similarity_boost", 0.8)

    return ElevenLabsTTSProvider(
        api_key=api_key,
        voice_id=voice_id,
        model_id=model_id,
        stability=stability,
        similarity_boost=similarity_boost,
    )
