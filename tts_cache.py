"""
TTS Cache - Instantly serve pre-generated phrases
"""
import os
import hashlib

CACHE_DIR = os.path.join(os.path.dirname(__file__), "output", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cached_audio(text: str) -> str | None:
    """
    Check if audio for this text is already generated.
    Returns path if cached, None otherwise.
    """
    # Create hash of text for filename
    text_hash = hashlib.md5(text.encode()).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"cached_{text_hash}.wav")

    if os.path.exists(cache_path):
        return cache_path

    return None

def cache_audio(text: str, audio_path: str) -> str:
    """
    Copy generated audio to cache for future instant use.
    Returns cached path.
    """
    import shutil

    text_hash = hashlib.md5(text.encode()).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"cached_{text_hash}.wav")

    shutil.copy(audio_path, cache_path)
    return cache_path
