import uuid
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for API authentication."""
    
    def __init__(self, app, api_key_required: bool = False):
        super().__init__(app)
        self.api_key_required = api_key_required
        self.security = HTTPBearer(auto_error=False)
    
    async def dispatch(self, request: Request, call_next):
        """Process request through authentication middleware."""
        # Add unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Get client key for rate limiting
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        request.state.client_key = f"{client_ip}:{hash(user_agent) % 10000}"
        
        # Check API key if required
        if self.api_key_required and settings.API_KEY:
            await self._check_api_key(request)
        
        # Add user info to request state if present
        await self._extract_user_info(request)
        
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    async def _check_api_key(self, request: Request) -> None:
        """Check API key in request."""
        # Try to get from Authorization header
        credentials: Optional[HTTPAuthorizationCredentials] = await self.security(request)
        
        api_key = None
        if credentials:
            api_key = credentials.credentials
        else:
            # Try to get from X-API-Key header
            api_key = request.headers.get("X-API-Key")
        
        if not api_key or api_key != settings.API_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def _extract_user_info(self, request: Request) -> None:
        """Extract user information from request."""
        # Try to get user ID from headers
        user_id = request.headers.get("X-User-ID")
        session_id = request.headers.get("X-Session-ID")
        
        if user_id:
            request.state.user_id = user_id
        if session_id:
            request.state.session_id = session_id


class SessionMiddleware(BaseHTTPMiddleware):
    """Middleware for session management."""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """Process request through session middleware."""
        # Get or create session ID
        session_id = request.headers.get("X-Session-ID")
        if not session_id:
            session_id = str(uuid.uuid4())
        
        request.state.session_id = session_id
        
        response = await call_next(request)
        
        # Add session ID to response if it was newly created
        if not request.headers.get("X-Session-ID"):
            response.headers["X-Session-ID"] = session_id
        
        return response


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for security headers and protections."""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """Process request through security middleware."""
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Add CORS headers if needed
        if settings.DEBUG:
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
        
        return response


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware for multi-tenant support."""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """Process request through tenant middleware."""
        # Get tenant from header or subdomain
        tenant = request.headers.get("X-Tenant-ID")
        
        if not tenant:
            # Try to extract from subdomain
            host = request.headers.get("host", "")
            if "." in host:
                tenant = host.split(".")[0]
        
        # Default tenant if none found
        if not tenant:
            tenant = "default"
        
        request.state.tenant = tenant
        
        response = await call_next(request)
        
        return response
