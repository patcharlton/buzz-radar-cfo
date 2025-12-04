"""Persistent cache for AI and dashboard responses.

Cache hierarchy (fastest to slowest):
1. Redis (if REDIS_URL configured) - shared across workers, fast
2. Postgres (AICache table) - persistent, survives restarts
3. In-memory (fallback) - per-worker, lost on restart
"""

from datetime import datetime, timedelta
from functools import wraps
import hashlib
import json
import os

# Default TTL: 4 hours for AI responses
DEFAULT_TTL = int(os.getenv('AI_CACHE_TTL', 14400))

# In-memory fallback cache
_memory_cache = {}

# Redis client (lazy initialized)
_redis_client = None


def _get_redis():
    """Get Redis client, initializing if needed."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    redis_url = os.getenv('REDIS_URL')
    if not redis_url:
        return None

    try:
        import redis
        _redis_client = redis.from_url(redis_url, decode_responses=True)
        # Test connection
        _redis_client.ping()
        return _redis_client
    except Exception as e:
        print(f"Redis connection failed: {e}")
        _redis_client = None
        return None


def cache_key(*args, **kwargs):
    """Generate a cache key from arguments."""
    key_data = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()


def get_cached(key, cache_type='general'):
    """Get a value from cache if not expired.

    Tries Redis first, then Postgres, then in-memory fallback.
    """
    # Try Redis first (fastest for shared cache)
    redis_client = _get_redis()
    if redis_client:
        try:
            redis_key = f"cache:{cache_type}:{key}"
            cached = redis_client.get(redis_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            print(f"Redis read failed: {e}")

    # Try Postgres
    try:
        from database.models import AICache
        from database.db import db

        entry = AICache.query.filter_by(cache_key=key).first()
        if entry and not entry.is_expired():
            value = json.loads(entry.value)
            # Populate Redis for next time if available
            if redis_client:
                try:
                    remaining_ttl = int((entry.expires_at - datetime.utcnow()).total_seconds())
                    if remaining_ttl > 0:
                        redis_key = f"cache:{cache_type}:{key}"
                        redis_client.setex(redis_key, remaining_ttl, entry.value)
                except Exception:
                    pass
            return value
        elif entry and entry.is_expired():
            # Clean up expired entry
            db.session.delete(entry)
            db.session.commit()
    except Exception as e:
        print(f"Cache read from Postgres failed: {e}")

    # Fallback to in-memory cache
    if key in _memory_cache:
        entry = _memory_cache[key]
        if datetime.utcnow() < entry['expires']:
            return entry['value']
        else:
            del _memory_cache[key]

    return None


def set_cached(key, value, ttl=DEFAULT_TTL, cache_type='general'):
    """Set a value in cache with TTL.

    Writes to Redis (if available), Postgres, and in-memory.
    """
    expires_at = datetime.utcnow() + timedelta(seconds=ttl)
    value_json = json.dumps(value, default=str)

    # Write to Redis first (fastest)
    redis_client = _get_redis()
    if redis_client:
        try:
            redis_key = f"cache:{cache_type}:{key}"
            redis_client.setex(redis_key, ttl, value_json)
        except Exception as e:
            print(f"Redis write failed: {e}")

    # Write to Postgres for persistence
    try:
        from database.models import AICache
        from database.db import db

        # Upsert: update if exists, insert if not
        entry = AICache.query.filter_by(cache_key=key).first()
        if entry:
            entry.value = value_json
            entry.expires_at = expires_at
            entry.cache_type = cache_type
            entry.created_at = datetime.utcnow()
        else:
            entry = AICache(
                cache_key=key,
                cache_type=cache_type,
                value=value_json,
                expires_at=expires_at
            )
            db.session.add(entry)

        db.session.commit()
    except Exception as e:
        print(f"Cache write to Postgres failed: {e}")

    # Always also cache in memory for fast access within same worker
    _memory_cache[key] = {
        'value': value,
        'expires': expires_at,
        'created': datetime.utcnow()
    }


def clear_cache(cache_type=None):
    """Clear cached values. If cache_type specified, only clear that type."""
    global _memory_cache

    # Clear Redis
    redis_client = _get_redis()
    if redis_client:
        try:
            if cache_type:
                # Delete keys matching pattern
                pattern = f"cache:{cache_type}:*"
                keys = redis_client.keys(pattern)
                if keys:
                    redis_client.delete(*keys)
            else:
                # Clear all cache keys
                keys = redis_client.keys("cache:*")
                if keys:
                    redis_client.delete(*keys)
        except Exception as e:
            print(f"Redis clear failed: {e}")

    # Clear Postgres
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
    """Get cache statistics from Redis, Postgres and memory."""
    now = datetime.utcnow()

    stats = {
        'memory_total': len(_memory_cache),
        'memory_valid': sum(1 for entry in _memory_cache.values() if now < entry['expires']),
        'redis_available': False,
        'redis_keys': 0,
        'postgres_total': 0,
        'postgres_valid': 0,
        'postgres_by_type': {}
    }

    # Redis stats
    redis_client = _get_redis()
    if redis_client:
        try:
            stats['redis_available'] = True
            stats['redis_keys'] = len(redis_client.keys("cache:*"))
        except Exception as e:
            stats['redis_error'] = str(e)

    # Postgres stats
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
    """Remove expired entries from Postgres cache.

    Redis handles TTL automatically, so no cleanup needed there.
    """
    try:
        from database.models import AICache
        from database.db import db

        deleted = AICache.query.filter(AICache.expires_at < datetime.utcnow()).delete()
        db.session.commit()
        return deleted
    except Exception as e:
        print(f"Cache cleanup failed: {e}")
        return 0
