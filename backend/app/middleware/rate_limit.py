from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.rate_limiter import RateLimiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests."""
    
    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter
    
    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiting middleware."""
        # Get client key from request state (set by auth middleware)
        client_key = getattr(request.state, "client_key", f"{request.client.host if request.client else 'unknown'}")
        
        # Check rate limit
        if not self.rate_limiter.allow(client_key):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.rate_limiter.max_requests if hasattr(self.rate_limiter, 'max_requests') else 120),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(__import__('time').time()) + 60),
                }
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        stats = self.rate_limiter.get_stats()
        client_stats = stats.get("client_request_counts", {})
        current_requests = client_stats.get(client_key, 0)
        limit = stats.get("rate_limit_per_min", 120)
        remaining = max(0, limit - current_requests)
        
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(__import__('time').time()) + 60)
        
        return response


class AdvancedRateLimitMiddleware(BaseHTTPMiddleware):
    """Advanced rate limiting with different limits per endpoint."""
    
    def __init__(self, app):
        super().__init__(app)
        self.rate_limiters = {}
        self.endpoint_limits = {
            "/recommend": 30,      # Stricter limit for expensive LLM calls
            "/feedback": 60,       # Medium limit for feedback
            "/profile": 120,       # Standard limit for profile access
            "/health": 300,        # Lenient limit for health checks
            "/metrics": 60,        # Medium limit for metrics
            "/ingest": 10,         # Very strict limit for data ingestion
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request with endpoint-specific rate limiting."""
        path = request.url.path
        client_key = getattr(request.state, "client_key", f"{request.client.host if request.client else 'unknown'}")
        
        # Get rate limit for this endpoint
        limit = self.endpoint_limits.get(path, 120)  # Default limit
        
        # Get or create rate limiter for this endpoint
        limiter_key = f"{path}:{limit}"
        if limiter_key not in self.rate_limiters:
            from app.services.rate_limiter import RateLimiter
            # Create a custom rate limiter for this endpoint
            class CustomRateLimiter(RateLimiter):
                def __init__(self, custom_limit):
                    from app.core.config import settings
                    self.max_requests = custom_limit
                    super().__init__()
            
            self.rate_limiters[limiter_key] = CustomRateLimiter(limit)
        
        rate_limiter = self.rate_limiters[limiter_key]
        
        # Check rate limit
        if not rate_limiter.allow(client_key):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for {path}. Limit: {limit} requests per minute.",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(__import__('time').time()) + 60),
                    "X-RateLimit-Scope": path,
                }
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        stats = rate_limiter.get_stats()
        client_stats = stats.get("client_request_counts", {})
        current_requests = client_stats.get(client_key, 0)
        remaining = max(0, limit - current_requests)
        
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(__import__('time').time()) + 60)
        response.headers["X-RateLimit-Scope"] = path
        
        return response
