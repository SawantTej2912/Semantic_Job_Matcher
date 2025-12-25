"""
Redis caching module - symlink/wrapper for connection.py
"""
from services.redis.connection import cache_job, get_cached_job, get_recent_jobs, get_redis_client

__all__ = ['cache_job', 'get_cached_job', 'get_recent_jobs', 'get_redis_client']
