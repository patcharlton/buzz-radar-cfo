"""Persistent cache for AI responses using Postgres with in-memory fallback."""

from datetime import datetime, timedelta
from functools import wraps
import hashlib
import json
import os

# Default TTL: 4 hours for AI responses
DEFAULT_TTL = int(os.getenv('AI_CACHE_TTL', 14400))

# In-memory fallback cache
_memory_cache = {}


def cache_key(*args, **kwargs):
    """Generate a cache key from arguments."""
    key_data = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()


def get_cached(key, cache_type='general'):
    """Get a value from cache if not expired. Uses Postgres with in-memory fallback."""
    try:
        # Try Postgres first
        from database.models import AICache
        from database.db import db

        entry = AICache.query.filter_by(cache_key=key).first()
        if entry and not entry.is_expired():
            return json.loads(entry.value)
        elif entry and entry.is_expired():
            # Clean up expired entry
            db.session.delete(entry)
            db.session.commit()
    except Exception as e:
        # Postgres unavailable, fall back to memory
        print(f"Cache read from Postgres failed, using memory: {e}")

    # Fallback to in-memory cache
    if key in _memory_cache:
        entry = _memory_cache[key]
        if datetime.utcnow() < entry['expires']:
            return entry['value']
        else:
            del _memory_cache[key]

    return None


def set_cached(key, value, ttl=DEFAULT_TTL, cache_type='general'):
    """Set a value in cache with TTL. Uses Postgres with in-memory fallback."""
    expires_at = datetime.utcnow() + timedelta(seconds=ttl)

    try:
        # Try Postgres first
        from database.models import AICache
        from database.db import db

        # Upsert: update if exists, insert if not
        entry = AICache.query.filter_by(cache_key=key).first()
        if entry:
            entry.value = json.dumps(value, default=str)
            entry.expires_at = expires_at
            entry.cache_type = cache_type
            entry.created_at = datetime.utcnow()
        else:
            entry = AICache(
                cache_key=key,
                cache_type=cache_type,
                value=json.dumps(value, default=str),
                expires_at=expires_at
            )
            db.session.add(entry)

        db.session.commit()
    except Exception as e:
        # Postgres unavailable, fall back to memory
        print(f"Cache write to Postgres failed, using memory: {e}")

    # Always also cache in memory for fast access
    _memory_cache[key] = {
        'value': value,
        'expires': expires_at,
        'created': datetime.utcnow()
    }


def clear_cache(cache_type=None):
    """Clear cached values. If cache_type specified, only clear that type."""
    global _memory_cache

    try:
        from database.models import AICache
        from database.db import db

        if cache_type:
            AICache.query.filter_by(cache_type=cache_type).delete()
        else:
            AICache.query.delete()
        db.session.commit()
    except Exception as e:
        print(f"Cache clear from Postgres failed: {e}")

    # Also clear memory cache
    if cache_type:
        # Can't easily filter memory cache by type, so clear all
        _memory_cache = {}
    else:
        _memory_cache = {}


def cached(ttl=DEFAULT_TTL, cache_type='general'):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{cache_key(*args, **kwargs)}"

            # Try to get from cache
            cached_value = get_cached(key, cache_type)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = func(*args, **kwargs)
            set_cached(key, result, ttl, cache_type)
            return result

        return wrapper
    return decorator


def get_cache_stats():
    """Get cache statistics from both Postgres and memory."""
    now = datetime.utcnow()

    stats = {
        'memory_total': len(_memory_cache),
        'memory_valid': sum(1 for entry in _memory_cache.values() if now < entry['expires']),
        'postgres_total': 0,
        'postgres_valid': 0,
        'postgres_by_type': {}
    }

    try:
        from database.models import AICache

        all_entries = AICache.query.all()
        stats['postgres_total'] = len(all_entries)
        stats['postgres_valid'] = sum(1 for e in all_entries if not e.is_expired())

        # Group by type
        for entry in all_entries:
            if entry.cache_type not in stats['postgres_by_type']:
                stats['postgres_by_type'][entry.cache_type] = {'total': 0, 'valid': 0}
            stats['postgres_by_type'][entry.cache_type]['total'] += 1
            if not entry.is_expired():
                stats['postgres_by_type'][entry.cache_type]['valid'] += 1

    except Exception as e:
        stats['postgres_error'] = str(e)

    return stats


def cleanup_expired():
    """Remove expired entries from Postgres cache."""
    try:
        from database.models import AICache
        from database.db import db

        deleted = AICache.query.filter(AICache.expires_at < datetime.utcnow()).delete()
        db.session.commit()
        return deleted
    except Exception as e:
        print(f"Cache cleanup failed: {e}")
        return 0
