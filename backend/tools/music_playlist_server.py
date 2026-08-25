"""Music & Playlist Management MCP Server.

Playlist creation, music search, playback control, and recommendations.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Dict, List, Any, Optional

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("music_playlist")
mcp = FastMCP("MusicPlaylist")


# Music storage
_playlists: Dict[str, Dict[str, Any]] = {}
_queue: List[Dict[str, Any]] = []
_history: List[Dict[str, Any]] = []
_current_track: Optional[Dict[str, Any]] = None


@mcp.tool()
def create_playlist(
    name: str,
    description: str = "",
    tracks: str = "",
) -> str:
    """Create a new playlist.

    Args:
        name: Playlist name
        description: Playlist description
        tracks: JSON array of track objects (optional)

    Returns:
        JSON with playlist details
    """
    playlist_id = f"playlist-{int(time.time())}"

    track_list = []
    if tracks:
        try:
            track_list = json.loads(tracks)
        except json.JSONDecodeError:
            pass

    _playlists[playlist_id] = {
        "id": playlist_id,
        "name": name,
        "description": description,
        "tracks": track_list,
        "created_at": time.time(),
        "play_count": 0,
    }

    return json.dumps({
        "status": "created",
        "playlist_id": playlist_id,
        "name": name,
        "tracks_count": len(track_list),
    })


@mcp.tool()
def add_to_playlist(playlist_id: str, track: str) -> str:
    """Add a track to a playlist.

    Args:
        playlist_id: Playlist ID
        track: Track JSON (title, artist, url)

    Returns:
        JSON confirmation
    """
    playlist = _playlists.get(playlist_id)
    if not playlist:
        return json.dumps({"status": "error", "message": "Playlist not found"})

    try:
        track_data = json.loads(track)
    except json.JSONDecodeError:
        track_data = {"title": track, "artist": "Unknown"}

    playlist["tracks"].append(track_data)

    return json.dumps({
        "status": "added",
        "playlist": playlist["name"],
        "tracks_count": len(playlist["tracks"]),
    })


@mcp.tool()
def list_playlists() -> str:
    """List all playlists.

    Returns:
        JSON with playlist list
    """
    playlists = []
    for pid, p in _playlists.items():
        playlists.append({
            "id": pid,
            "name": p["name"],
            "tracks_count": len(p["tracks"]),
            "play_count": p["play_count"],
        })

    return json.dumps({
        "status": "success",
        "playlists": playlists,
        "total": len(playlists),
    })


@mcp.tool()
def get_playlist(playlist_id: str) -> str:
    """Get playlist details with tracks.

    Args:
        playlist_id: Playlist ID

    Returns:
        JSON with playlist details
    """
    playlist = _playlists.get(playlist_id)
    if not playlist:
        return json.dumps({"status": "error", "message": "Playlist not found"})

    return json.dumps({
        "status": "success",
        "playlist": playlist,
    })


@mcp.tool()
def play_track(track: str, playlist_id: str = "") -> str:
    """Start playing a track.

    Args:
        track: Track JSON (title, artist, url)
        playlist_id: Optional playlist context

    Returns:
        JSON confirmation
    """
    global _current_track

    try:
        track_data = json.loads(track)
    except json.JSONDecodeError:
        track_data = {"title": track, "artist": "Unknown"}

    _current_track = {
        **track_data,
        "started_at": time.time(),
        "playlist_id": playlist_id,
    }

    return json.dumps({
        "status": "playing",
        "track": _current_track,
    })


@mcp.tool()
def get_current_track() -> str:
    """Get currently playing track.

    Returns:
        JSON with current track
    """
    if not _current_track:
        return json.dumps({"status": "success", "playing": False})

    elapsed = time.time() - _current_track["started_at"]

    return json.dumps({
        "status": "success",
        "playing": True,
        "track": _current_track,
        "elapsed_seconds": round(elapsed, 1),
    })


@mcp.tool()
def queue_track(track: str) -> str:
    """Add a track to the play queue.

    Args:
        track: Track JSON (title, artist, url)

    Returns:
        JSON confirmation
    """
    try:
        track_data = json.loads(track)
    except json.JSONDecodeError:
        track_data = {"title": track, "artist": "Unknown"}

    _queue.append({
        **track_data,
        "queued_at": time.time(),
    })

    return json.dumps({
        "status": "queued",
        "queue_length": len(_queue),
    })


@mcp.tool()
def get_queue() -> str:
    """Get the play queue.

    Returns:
        JSON with queue
    """
    return json.dumps({
        "status": "success",
        "queue": _queue,
        "length": len(_queue),
    })


@mcp.tool()
def search_music(query: str, source: str = "library") -> str:
    """Search for music.

    Args:
        query: Search query (title, artist, genre)
        source: Search source ('library', 'spotify', 'youtube')

    Returns:
        JSON with search results
    """
    # In production, integrate with music APIs
    # For now, return mock results
    results = [
        {
            "title": f"Result for '{query}' (1)",
            "artist": "Artist Name",
            "duration": "3:45",
            "source": source,
        },
        {
            "title": f"Result for '{query}' (2)",
            "artist": "Another Artist",
            "duration": "4:12",
            "source": source,
        },
    ]

    return json.dumps({
        "status": "success",
        "query": query,
        "results": results,
        "total": len(results),
    })


@mcp.tool()
def get_playback_history(limit: int = 20) -> str:
    """Get playback history.

    Args:
        limit: Max tracks to return

    Returns:
        JSON with history
    """
    return json.dumps({
        "status": "success",
        "history": _history[-limit:],
        "total": len(_history),
    })


if __name__ == "__main__":
    mcp.run()
