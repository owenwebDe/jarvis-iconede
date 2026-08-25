"""TTS routes: cancel, stream/serve audio."""
import os
import re
import uuid
import asyncio
import logging

import aiofiles
from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel

from core.auth import verify_api_key, verify_optional_api_key
from helpers.text_processing import clean_text_for_tts
from helpers.audio_cache import get_audio_cache_path
from services.shared_state import (
    tts_cache, library_manager, generation_tasks,
)
import services.shared_state as _state

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tts", tags=["tts"])


def ensure_tts_generation(request_id: str, text: str, is_notification: bool = True):
    """Pre-warm or start background TTS generation immediately when text is ready."""
    if not text or not text.strip():
        return
    cache_path = get_audio_cache_path(text)
    mp3_exists = os.path.exists(cache_path)
    lock_path = cache_path + ".lock"
    meta_path = cache_path + ".part.json"

    if mp3_exists or request_id in generation_tasks:
        return

    provider = (
        _state.tts_chat_provider if is_notification else _state.tts_stories_provider
    )

    async def generate_worker():
        task_id = request_id
        generation_tasks[task_id] = asyncio.current_task()
        try:
            with open(lock_path, 'w') as lf: lf.write("locked")
        except: pass

        try:
            async with aiofiles.open(cache_path, "wb") as f:
                async for chunk in provider.stream_audio(text):
                    if chunk:
                        await f.write(chunk)
                        await f.flush()
            logger.debug(f"[TTS] Generation Complete for {cache_path}")
            if os.path.exists(lock_path): os.remove(lock_path)
            if os.path.exists(meta_path): os.remove(meta_path)
        except asyncio.CancelledError:
            logger.debug(f"[TTS] Generation task {task_id} cancelled.")
        except Exception as e:
            logger.error(f"[TTS] Generation task {task_id} failed: {e}")
            if os.path.exists(cache_path):
                try: os.remove(cache_path)
                except: pass
        finally:
            if task_id in generation_tasks: del generation_tasks[task_id]
            if os.path.exists(lock_path):
                try: os.remove(lock_path)
                except: pass

    asyncio.create_task(generate_worker())


class TTSPrepareRequest(BaseModel):
    text: str


@router.post("/prepare")
async def prepare_tts(body: TTSPrepareRequest, _=Depends(verify_api_key)):
    """Register arbitrary text in TTS cache and return a streamable request_id."""
    if not body.text or not body.text.strip():
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=400, content={"detail": "text must not be empty"})

    cleaned = clean_text_for_tts(body.text.strip())
    request_id = str(uuid.uuid4())
    tts_cache.save_tts_text(request_id, cleaned)
    ensure_tts_generation(request_id, cleaned, is_notification=True)
    audio_url = f"/api/tts/{request_id}"
    logger.info(f"[TTS] /prepare request_id={request_id} text_len={len(cleaned)}")
    return {"request_id": request_id, "audio_url": audio_url}


@router.post("/cancel/{request_id}")
async def cancel_tts(request_id: str, _=Depends(verify_api_key)):
    """Cancel an ongoing TTS generation task."""
    task = generation_tasks.get(request_id)
    if task:
        task.cancel()
        logger.debug(f"User requested cancellation for task {request_id}")
        return {"status": "cancelled", "message": f"Task {request_id} cancelled."}
    return {"status": "not_found", "message": "No active task found."}


@router.api_route("/{request_id}", methods=["GET", "HEAD"])
async def tts_endpoint(request_id: str, request: Request, _auth=Depends(verify_optional_api_key)):
    if _state.bg_scheduler:
        _state.bg_scheduler.notify_tts_activity()
    
    book = library_manager.get_book(request_id)
    text = None
    cache_path = None
    is_notification = not book and not request_id.startswith('story_')
    
    if book:
        logger.debug(f"Streaming from Library: {book.title}")
        text = tts_cache.get_tts_text(request_id)
        if text:
            cache_path = get_audio_cache_path(text)
            if book.file_path != cache_path:
                library_manager.update_file_path(request_id, cache_path)
        else:
            cache_path = book.file_path
        
        if not text and not os.path.exists(cache_path) and not os.path.exists(cache_path + ".part"):
            return {"error": "Book source missing and text not available."}
    else:
        text = tts_cache.get_tts_text(request_id)
        if not text:
            return {"error": "Text not found or expired"}
        cache_path = get_audio_cache_path(text)

    mp3_exists = os.path.exists(cache_path)
    part_path = cache_path + ".part"
    part_exists = os.path.exists(part_path)
    
    if not text and not mp3_exists and not part_exists:
         return {"error": "Text missing for generation"}

    if request.method == "HEAD":
        file_size = 0
        if mp3_exists:
             file_size = os.path.getsize(cache_path)
        headers = {"Accept-Ranges": "bytes", "Content-Type": "audio/mpeg"}
        if file_size > 0:
            headers["Content-Length"] = str(file_size)
        if os.path.exists(cache_path + ".lock"):
            headers["X-TTS-Generating"] = "1"
        return Response(status_code=200, headers=headers)

    lock_path = cache_path + ".lock"
    
    if mp3_exists:
        if book and book.status != "ready":
            try:
                from mutagen.mp3 import MP3
                audio = MP3(cache_path)
                duration = int(audio.info.length)
                library_manager.set_status(book.id, "ready", duration=duration)
            except Exception:
                library_manager.set_status(book.id, "ready")
    else:
        # Cache miss: Stream directly from provider to browser with zero delay
        provider = _state.tts_chat_provider if is_notification else _state.tts_stories_provider
        
        async def live_tts_generator():
            try:
                async with aiofiles.open(cache_path, "wb") as f:
                    async for chunk in provider.stream_audio(text):
                        if chunk:
                            await f.write(chunk)
                            yield chunk
                if os.path.exists(lock_path):
                    try: os.remove(lock_path)
                    except: pass
                if book:
                    library_manager.set_status(book.id, "ready")
            except Exception as e:
                logger.error(f"[TTS] Live stream error: {e}")
                if os.path.exists(cache_path):
                    try: os.remove(cache_path)
                    except: pass
            finally:
                if request_id in generation_tasks:
                    del generation_tasks[request_id]

        headers = {
            "Accept-Ranges": "none",
            "Content-Type": "audio/mpeg",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "X-TTS-Streaming": "1",
        }
        return StreamingResponse(
            live_tts_generator(),
            status_code=200,
            headers=headers,
            media_type="audio/mpeg"
        )

    target_file = cache_path
    file_size = os.path.getsize(cache_path)
    status_code = 200
    is_live_mode = False
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Type": "audio/mpeg",
        "Cache-Control": "public, max-age=86400",
    }

    start_byte = 0
    end_byte = None
    length_to_serve = None
    
    range_header = request.headers.get('Range')
    if range_header:
        if not is_live_mode:
            status_code = 206
            try:
                logger.debug(f"Received Range Header: {range_header}")
                range_match = re.search(r'bytes=(\d+)-(\d*)', range_header, re.IGNORECASE)
                if not range_match:
                     raise ValueError("Invalid Range Format")
                
                start_byte = int(range_match.group(1))
                end_byte = int(range_match.group(2)) if range_match.group(2) else None
                
                if start_byte >= file_size:
                    logger.warning(f"Range Request Out of Bounds: {start_byte} >= {file_size}")
                    return Response(status_code=416, headers={"Content-Range": f"bytes */{file_size}"})

                actual_end = end_byte if end_byte is not None else file_size - 1
                if actual_end >= file_size: actual_end = file_size - 1
                
                length_to_serve = actual_end - start_byte + 1
                
                headers["Content-Range"] = f"bytes {start_byte}-{actual_end}/{file_size}"
                headers["Content-Length"] = str(length_to_serve)
                logger.debug(f"Handling Range Request: {headers['Content-Range']} (Size: {length_to_serve})")
            except Exception as e:
                logger.error(f"Failed to parse range header '{range_header}': {e}")
                status_code = 200
                pass 
        else:
             status_code = 200
             logger.debug("Ignoring Range header for Active Stream (Live Mode)")
    else:
        if not is_live_mode:
            headers["Content-Length"] = str(file_size)
            logger.debug("Serving Full MP3 (200 OK)")

    async def file_reader(offset=0):
        async with aiofiles.open(target_file, "rb") as f:
            if offset > 0:
                await f.seek(offset)
            while True:
                chunk = await f.read(65536)
                if not chunk:
                    break
                yield chunk

    async def limited_stream():
        count = 0
        async for chunk in file_reader(start_byte):
            if length_to_serve:
                if count + len(chunk) > length_to_serve:
                    yield chunk[:length_to_serve - count]
                    break
            yield chunk
            count += len(chunk)
            if length_to_serve and count >= length_to_serve:
                break
    
    return StreamingResponse(
        limited_stream(),
        status_code=status_code,
        headers=headers,
        media_type="audio/mpeg"
    )
