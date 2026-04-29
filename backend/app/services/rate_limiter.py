import time
from collections import defaultdict, deque
from threading import Lock
from typing import Dict, Any

from app.core.config import settings


class RateLimiter:
    """Rate limiter using sliding window algorithm."""
    
    def __init__(self):
        self._clients: Dict[str, deque] = defaultdict(lambda: deque(maxlen=settings.RATE_LIMIT_PER_MIN * 2))
        self._lock = Lock()
        self.window_size = 60  # 1 minute window
    
    def allow(self, client_key: str) -> bool:
        """Check if client is allowed to make a request."""
        with self._lock:
            current_time = time.time()
            client_requests = self._clients[client_key]
            
            # Remove old requests outside the window
            while client_requests and client_requests[0] < current_time - self.window_size:
                client_requests.popleft()
            
            # Check if under rate limit
            if len(client_requests) < settings.RATE_LIMIT_PER_MIN:
                client_requests.append(current_time)
                return True
            
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        with self._lock:
            current_time = time.time()
            stats = {
                "active_clients": len(self._clients),
                "rate_limit_per_min": settings.RATE_LIMIT_PER_MIN,
                "window_size_seconds": self.window_size,
                "client_request_counts": {},
            }
            
            # Count requests per client in current window
            for client_key, requests in self._clients.items():
                recent_requests = sum(1 for req_time in requests if req_time >= current_time - self.window_size)
                stats["client_request_counts"][client_key] = recent_requests
            
            return stats
    
    def reset_client(self, client_key: str) -> None:
        """Reset rate limit for a specific client."""
        with self._lock:
            if client_key in self._clients:
                del self._clients[client_key]
    
    def reset_all(self) -> None:
        """Reset all rate limits."""
        with self._lock:
            self._clients.clear()


class TokenBucketRateLimiter:
    """Token bucket rate limiter for more sophisticated rate limiting."""
    
    def __init__(self, refill_rate: float = None, bucket_size: int = None):
        self.refill_rate = refill_rate or settings.RATE_LIMIT_PER_MIN / 60.0  # tokens per second
        self.bucket_size = bucket_size or settings.RATE_LIMIT_PER_MIN
        self._buckets: Dict[str, Dict[str, float]] = {}
        self._lock = Lock()
    
    def allow(self, client_key: str) -> bool:
        """Check if client is allowed to make a request using token bucket."""
        with self._lock:
            current_time = time.time()
            
            # Get or create bucket
            if client_key not in self._buckets:
                self._buckets[client_key] = {
                    "tokens": float(self.bucket_size),
                    "last_refill": current_time,
                }
            
            bucket = self._buckets[client_key]
            
            # Refill tokens based on time elapsed
            time_elapsed = current_time - bucket["last_refill"]
            tokens_to_add = time_elapsed * self.refill_rate
            bucket["tokens"] = min(bucket["tokens"] + tokens_to_add, self.bucket_size)
            bucket["last_refill"] = current_time
            
            # Check if there's a token available
            if bucket["tokens"] >= 1.0:
                bucket["tokens"] -= 1.0
                return True
            
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get token bucket statistics."""
        with self._lock:
            stats = {
                "active_clients": len(self._buckets),
                "refill_rate": self.refill_rate,
                "bucket_size": self.bucket_size,
                "client_token_counts": {},
            }
            
            for client_key, bucket in self._buckets.items():
                stats["client_token_counts"][client_key] = bucket["tokens"]
            
            return stats
    
    def reset_client(self, client_key: str) -> None:
        """Reset token bucket for a specific client."""
        with self._lock:
            if client_key in self._buckets:
                del self._buckets[client_key]


class SlidingWindowRateLimiter:
    """Advanced sliding window rate limiter with memory efficiency."""
    
    def __init__(self, window_size: int = 60, max_requests: int = None):
        self.window_size = window_size
        self.max_requests = max_requests or settings.RATE_LIMIT_PER_MIN
        self._clients: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
    
    def allow(self, client_key: str) -> bool:
        """Check if client is allowed to make a request."""
        with self._lock:
            current_time = time.time()
            
            # Get or create client data
            if client_key not in self._clients:
                self._clients[client_key] = {
                    "requests": deque(),
                    "count": 0,
                }
            
            client = self._clients[client_key]
            requests = client["requests"]
            
            # Remove old requests outside the window
            while requests and requests[0] <= current_time - self.window_size:
                requests.popleft()
                client["count"] -= 1
            
            # Check if under rate limit
            if client["count"] < self.max_requests:
                requests.append(current_time)
                client["count"] += 1
                return True
            
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get sliding window statistics."""
        with self._lock:
            current_time = time.time()
            stats = {
                "active_clients": len(self._clients),
                "window_size_seconds": self.window_size,
                "max_requests_per_window": self.max_requests,
                "client_request_counts": {},
            }
            
            for client_key, client in self._clients.items():
                # Count requests in current window
                recent_count = sum(
                    1 for req_time in client["requests"]
                    if req_time > current_time - self.window_size
                )
                stats["client_request_counts"][client_key] = recent_count
            
            return stats
