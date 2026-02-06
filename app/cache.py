"""
Caching utilities for Strava API responses
"""
import hashlib
import json
from flask_caching import Cache

# Initialize cache instance (will be configured in app factory)
cache = Cache()


def generate_cache_key(prefix, athlete_id, **kwargs):
    """
    Generate a consistent cache key from parameters

    Args:
        prefix: Cache key prefix (e.g., 'activities', 'stats')
        athlete_id: Strava athlete ID
        **kwargs: Additional parameters to include in cache key
    """
    # Sort kwargs for consistent key generation
    params_str = json.dumps(sorted(kwargs.items()), sort_keys=True)
    params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]

    return f"strava:{athlete_id}:{prefix}:{params_hash}"


def get_activities_cache_key(athlete_id, **params):
    """Generate cache key for activities list"""
    return generate_cache_key("activities", athlete_id, **params)


def get_activity_cache_key(athlete_id, activity_id):
    """Generate cache key for single activity"""
    return generate_cache_key("activity", athlete_id, activity_id=activity_id)


def get_stats_cache_key(athlete_id):
    """Generate cache key for athlete stats"""
    return generate_cache_key("stats", athlete_id)


def clear_athlete_cache(athlete_id):
    """
    Clear all cached data for an athlete

    Args:
        athlete_id: Strava athlete ID
    """
    # This will clear cache entries matching the pattern
    # Note: FileSystemCache doesn't support pattern-based deletion
    # So we'll just clear the entire cache for simplicity
    cache.clear()
