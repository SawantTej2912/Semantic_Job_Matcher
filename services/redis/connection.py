"""
Redis connection and caching module.
"""
import os
import json
import redis

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

def get_redis_client():
    """
    Get Redis client connection.
    
    Returns:
        redis.Redis: Redis client instance.
    """
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
        # Check connection
        r.ping()
        print(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        return r
    except Exception as e:
        print(f"Error connecting to Redis: {e}")
        return None


def cache_job(job_dict, ttl=3600):
    """
    Cache a job in Redis with TTL.
    
    Args:
        job_dict: Job dictionary to cache.
        ttl: Time to live in seconds (default 1 hour).
    """
    client = get_redis_client()
    if not client:
        return
    
    try:
        job_id = job_dict.get('id', '')
        if not job_id:
            return
        
        # Store full job data
        key = f"job:{job_id}"
        client.setex(key, ttl, json.dumps(job_dict))
        
        # Add to recent jobs list (keep last 100)
        client.lpush("recent_jobs", job_id)
        client.ltrim("recent_jobs", 0, 99)
        
        # Cache job summary for quick access
        summary_key = f"job_summary:{job_id}"
        summary = {
            'id': job_id,
            'company': job_dict.get('company', ''),
            'position': job_dict.get('position', ''),
            'seniority': job_dict.get('seniority', ''),
            'skills': job_dict.get('skills', [])
        }
        client.setex(summary_key, ttl, json.dumps(summary))
        
    except Exception as e:
        print(f"Error caching job: {e}")


def get_cached_job(job_id):
    """
    Retrieve a cached job from Redis.
    
    Args:
        job_id: Job ID to retrieve.
        
    Returns:
        dict: Job dictionary or None if not found.
    """
    client = get_redis_client()
    if not client:
        return None
    
    try:
        key = f"job:{job_id}"
        data = client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        print(f"Error retrieving cached job: {e}")
        return None


def get_recent_jobs(limit=10):
    """
    Get list of recent job IDs from Redis.
    
    Args:
        limit: Maximum number of job IDs to return.
        
    Returns:
        list: List of recent job IDs.
    """
    client = get_redis_client()
    if not client:
        return []
    
    try:
        return client.lrange("recent_jobs", 0, limit - 1)
    except Exception as e:
        print(f"Error retrieving recent jobs: {e}")
        return []


if __name__ == "__main__":
    # Test Redis connection
    client = get_redis_client()
    if client:
        # Basic Set
        client.set("test_key", "Hello from Redis!")
        print("Set 'test_key' to 'Hello from Redis!'")
        
        # Basic Get
        value = client.get("test_key")
        print(f"Got 'test_key': {value}")

