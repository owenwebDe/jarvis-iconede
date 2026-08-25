"""Voice profiles for Jarvis and other agents."""

# Best ElevenLabs voice IDs for a strong, authoritative British male voice
VOICE_PROFILES = {
    "jarvis": {
        "name": "Daniel",
        "label": "Deep British Male",
        "description": "Strong, authoritative British male voice with cinematic quality",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Daniel - best British male
        "model": "eleven_multilingual_v2",
        "stability": 0.55,
        "similarity_boost": 0.78,
        "style": 0.35,
        "speed": 1.05,
        "fallback": "en-GB-ThomasNeural",  # Edge TTS fallback
    },
    "narrator": {
        "name": "Arnold",
        "label": "Deep Cinematic",
        "description": "Dramatic, movie-trailer style voice",
        "voice_id": "VR6AewLTigWG4xSOukaG",  # Arnold
        "model": "eleven_multilingual_v2",
        "stability": 0.60,
        "similarity_boost": 0.80,
        "style": 0.40,
        "speed": 1.00,
        "fallback": "en-GB-RyanNeural",
    },
    "female_assistant": {
        "name": "Rachel",
        "label": "Professional Female",
        "description": "Clear, professional American female voice",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "model": "eleven_multilingual_v2",
        "stability": 0.55,
        "similarity_boost": 0.75,
        "style": 0.30,
        "speed": 1.00,
        "fallback": "en-US-AriaNeural",
    },
}

# Default settings for ElevenLabs TTS
DEFAULT_ELEVENLABS_SETTINGS = {
    "voice": "Daniel",
    "model": "eleven_multilingual_v2",
    "stability": 0.55,
    "similarity_boost": 0.78,
    "style": 0.35,
    "speed": 1.05,
}

# Pre-optimized voice settings by use case
VOICE_PRESETS = {
    "sales_pitch": {
        "stability": 0.45,
        "similarity_boost": 0.82,
        "style": 0.50,  # More expressive for persuasion
        "speed": 1.10,
    },
    "formal_report": {
        "stability": 0.70,
        "similarity_boost": 0.80,
        "style": 0.20,  # Less expressive for formality
        "speed": 0.95,
    },
    "storytelling": {
        "stability": 0.50,
        "similarity_boost": 0.75,
        "style": 0.65,  # Very expressive
        "speed": 0.90,
    },
    "quick_update": {
        "stability": 0.55,
        "similarity_boost": 0.78,
        "style": 0.30,
        "speed": 1.20,  # Faster for quick updates
    },
}
