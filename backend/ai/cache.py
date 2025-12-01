"""Simple in-memory cache for AI responses."""

from datetime import datetime, timedelta
from functools import wraps
import hashlib
import json

# Simple in-memory cache
_cache = {}

DEFAULT_TTL = 3600  # 1 hour in seconds


def cache_key(*args, **kwargs):
    """Generate a cache key from arguments."""
    key_data = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()


def get_cached(key):
    """Get a value from cache if not expired."""
    if key in _cache:
        entry = _cache[key]
        if datetime.utcnow() < entry['expires']:
            return entry['value']
        else:
            del _cache[key]
    return None


def set_cached(key, value, ttl=DEFAULT_TTL):
    """Set a value in cache with TTL."""
    _cache[key] = {
        'value': value,
        'expires': datetime.utcnow() + timedelta(seconds=ttl),
        'created': datetime.utcnow()
    }


def clear_cache():
    """Clear all cached values."""
    global _cache
    _cache = {}


def cached(ttl=DEFAULT_TTL):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{cache_key(*args, **kwargs)}"

            # Try to get from cache
            cached_value = get_cached(key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = func(*args, **kwargs)
            set_cached(key, result, ttl)
            return result

        return wrapper
    return decorator


def get_cache_stats():
    """Get cache statistics."""
    now = datetime.utcnow()
    valid_entries = sum(1 for entry in _cache.values() if now < entry['expires'])
    return {
        'total_entries': len(_cache),
        'valid_entries': valid_entries,
        'expired_entries': len(_cache) - valid_entries
    }
