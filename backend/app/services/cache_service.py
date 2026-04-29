import hashlib
import json
import time
from typing import Any, Dict, Optional
from threading import Lock

from app.core.config import settings


class CacheService:
    """In-memory caching service with TTL support."""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0,
        }
        self._lock = Lock()
    
    def make_key(self, data: Dict[str, Any]) -> str:
        """Generate a cache key from request data."""
        # Create a deterministic key from the request data
        key_data = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None
            
            entry = self._cache[key]
            current_time = time.time()
            
            # Check if expired
            if current_time - entry["timestamp"] > settings.CACHE_TTL_SECONDS:
                del self._cache[key]
                self._stats["evictions"] += 1
                self._stats["misses"] += 1
                return None
            
            self._stats["hits"] += 1
            return entry["value"]
    
    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Set value in cache."""
        with self._lock:
            # Check cache size limit
            if len(self._cache) >= settings.CACHE_MAX_SIZE:
                self._evict_oldest()
            
            self._cache[key] = {
                "value": value,
                "timestamp": time.time(),
            }
            self._stats["sets"] += 1
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "entries": len(self._cache),
                "max_entries": settings.CACHE_TTL_SECONDS,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "sets": self._stats["sets"],
                "evictions": self._stats["evictions"],
                "hit_rate_percent": round(hit_rate, 2),
                "ttl_seconds": settings.CACHE_TTL_SECONDS,
            }
    
    def _evict_oldest(self) -> None:
        """Evict the oldest entry from cache."""
        if not self._cache:
            return
        
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k]["timestamp"]
        )
        del self._cache[oldest_key]
        self._stats["evictions"] += 1
    
    def get_expired_keys(self) -> list[str]:
        """Get list of expired keys (for cleanup)."""
        current_time = time.time()
        expired_keys = []
        
        with self._lock:
            for key, entry in self._cache.items():
                if current_time - entry["timestamp"] > settings.CACHE_TTL_SECONDS:
                    expired_keys.append(key)
        
        return expired_keys
    
    def cleanup_expired(self) -> int:
        """Clean up expired entries and return count of removed entries."""
        expired_keys = self.get_expired_keys()
        
        with self._lock:
            for key in expired_keys:
                del self._cache[key]
                self._stats["evictions"] += 1
        
        return len(expired_keys)


class RedisCacheService:
    """Redis-based cache service for distributed deployments."""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or "redis://localhost:6379"
        self._redis = None
        self._connected = False
    
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            import aioredis
            self._redis = await aioredis.from_url(self.redis_url)
            self._connected = True
        except Exception as exc:
            raise ConnectionError(f"Failed to connect to Redis: {exc}") from exc
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self._connected = False
    
    def make_key(self, data: Dict[str, Any]) -> str:
        """Generate a cache key from request data."""
        key_data = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from Redis cache."""
        if not self._connected:
            await self.connect()
        
        try:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as exc:
            raise RuntimeError(f"Failed to get from cache: {exc}") from exc
    
    async def set(self, key: str, value: Dict[str, Any], ttl: int = None) -> None:
        """Set value in Redis cache."""
        if not self._connected:
            await self.connect()
        
        ttl = ttl or settings.CACHE_TTL_SECONDS
        
        try:
            await self._redis.setex(
                key,
                ttl,
                json.dumps(value, separators=(",", ":"))
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to set cache: {exc}") from exc
    
    async def delete(self, key: str) -> bool:
        """Delete value from Redis cache."""
        if not self._connected:
            await self.connect()
        
        try:
            result = await self._redis.delete(key)
            return result > 0
        except Exception as exc:
            raise RuntimeError(f"Failed to delete from cache: {exc}") from exc
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        if not self._connected:
            await self.connect()
        
        try:
            await self._redis.flushdb()
        except Exception as exc:
            raise RuntimeError(f"Failed to clear cache: {exc}") from exc
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics."""
        if not self._connected:
            await self.connect()
        
        try:
            info = await self._redis.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate_percent": self._calculate_hit_rate(info),
            }
        except Exception as exc:
            raise RuntimeError(f"Failed to get cache stats: {exc}") from exc
    
    def _calculate_hit_rate(self, info: Dict[str, Any]) -> float:
        """Calculate hit rate from Redis info."""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return round((hits / total) * 100, 2)


# Factory function to create appropriate cache service
def create_cache_service(use_redis: bool = False, redis_url: str = None) -> CacheService:
    """Create appropriate cache service based on configuration."""
    if use_redis:
        return RedisCacheService(redis_url)
    else:
        return CacheService()
