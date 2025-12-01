"""Simple file-based cache for Notion data."""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Any


# Cache directory relative to backend
CACHE_DIR = Path(__file__).parent.parent / 'cache'
CACHE_TTL_MINUTES = 60  # Cache expires after 60 minutes


def _ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_path(key: str) -> Path:
    """Get path for a cache key."""
    return CACHE_DIR / f"{key}.json"


def get_cached(key: str) -> Optional[dict]:
    """
    Get cached data if it exists and is valid.

    Args:
        key: Cache key

    Returns:
        dict or None: Cached data if valid, None otherwise
    """
    cache_file = _cache_path(key)

    if not cache_file.exists():
        return None

    try:
        with open(cache_file, 'r') as f:
            data = json.load(f)

        # Check if cache is still valid
        cached_at = data.get('_cached_at')
        if cached_at:
            cached_time = datetime.fromisoformat(cached_at)
            if datetime.utcnow() - cached_time < timedelta(minutes=CACHE_TTL_MINUTES):
                return data

        return None  # Cache expired
    except (json.JSONDecodeError, IOError):
        return None


def set_cached(key: str, data: Any) -> None:
    """
    Save data to cache.

    Args:
        key: Cache key
        data: Data to cache (must be JSON serializable)
    """
    _ensure_cache_dir()
    cache_file = _cache_path(key)

    # Add timestamp
    cache_data = {
        **data,
        '_cached_at': datetime.utcnow().isoformat(),
    }

    with open(cache_file, 'w') as f:
        json.dump(cache_data, f, indent=2, default=str)


def is_cache_valid(key: str) -> bool:
    """
    Check if cache exists and is not expired.

    Args:
        key: Cache key

    Returns:
        bool: True if cache is valid
    """
    return get_cached(key) is not None


def clear_cache(key: str) -> None:
    """
    Clear a specific cache entry.

    Args:
        key: Cache key to clear
    """
    cache_file = _cache_path(key)
    if cache_file.exists():
        cache_file.unlink()


def clear_all_cache() -> None:
    """Clear all cache files."""
    if CACHE_DIR.exists():
        for cache_file in CACHE_DIR.glob('*.json'):
            cache_file.unlink()


def get_cache_age(key: str) -> Optional[float]:
    """
    Get age of cache in minutes.

    Args:
        key: Cache key

    Returns:
        float or None: Age in minutes, or None if no cache
    """
    cache_file = _cache_path(key)

    if not cache_file.exists():
        return None

    try:
        with open(cache_file, 'r') as f:
            data = json.load(f)

        cached_at = data.get('_cached_at')
        if cached_at:
            cached_time = datetime.fromisoformat(cached_at)
            age = datetime.utcnow() - cached_time
            return age.total_seconds() / 60

        return None
    except (json.JSONDecodeError, IOError):
        return None
