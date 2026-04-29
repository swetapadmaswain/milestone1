import time
import logging
from typing import Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import json

from app.core.config import settings


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = self._setup_logger()
    
    async def dispatch(self, request: Request, call_next):
        """Process request through logging middleware."""
        start_time = time.time()
        
        # Log request
        request_data = await self._get_request_data(request)
        self.logger.info(f"Request started: {request.method} {request.url}", extra=request_data)
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        process_time = time.time() - start_time
        
        # Log response
        response_data = await self._get_response_data(response, process_time)
        self.logger.info(f"Request completed: {request.method} {request.url}", extra=response_data)
        
        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    async def _get_request_data(self, request: Request) -> Dict[str, Any]:
        """Extract request data for logging."""
        data = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_host": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "request_id": getattr(request.state, "request_id", None),
            "tenant": getattr(request.state, "tenant", "default"),
        }
        
        # Add user info if available
        if hasattr(request.state, "user_id"):
            data["user_id"] = request.state.user_id
        if hasattr(request.state, "session_id"):
            data["session_id"] = request.state.session_id
        
        # Add content length if available
        content_length = request.headers.get("content-length")
        if content_length:
            data["content_length"] = int(content_length)
        
        return data
    
    async def _get_response_data(self, response: Response, process_time: float) -> Dict[str, Any]:
        """Extract response data for logging."""
        data = {
            "status_code": response.status_code,
            "process_time": process_time,
            "content_type": response.headers.get("content-type", "unknown"),
            "content_length": response.headers.get("content-length"),
        }
        
        # Add response size if available
        if hasattr(response, "body") and response.body:
            data["response_size"] = len(response.body)
        
        return data
    
    def _setup_logger(self) -> logging.Logger:
        """Setup structured logger."""
        logger = logging.getLogger("restaurant_api")
        
        if not logger.handlers:
            # Create console handler
            handler = logging.StreamHandler()
            handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
            
            # Create formatter
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            
            # Add handler to logger
            logger.addHandler(handler)
            logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        
        return logger


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured JSON logging."""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = self._setup_structured_logger()
    
    async def dispatch(self, request: Request, call_next):
        """Process request with structured logging."""
        start_time = time.time()
        
        # Generate correlation ID
        correlation_id = getattr(request.state, "request_id", f"req_{int(time.time() * 1000)}")
        
        # Log request
        log_entry = {
            "timestamp": time.time(),
            "level": "INFO",
            "message": "API request started",
            "correlation_id": correlation_id,
            "request": {
                "method": request.method,
                "path": request.url.path,
                "query": dict(request.query_params),
                "user_agent": request.headers.get("user-agent"),
                "client_ip": request.client.host if request.client else "unknown",
            }
        }
        
        # Add user context if available
        if hasattr(request.state, "user_id"):
            log_entry["user_id"] = request.state.user_id
        if hasattr(request.state, "session_id"):
            log_entry["session_id"] = request.state.session_id
        
        self._log_structured(log_entry)
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        log_entry = {
            "timestamp": time.time(),
            "level": "INFO" if response.status_code < 400 else "ERROR",
            "message": "API request completed",
            "correlation_id": correlation_id,
            "duration_ms": duration * 1000,
            "response": {
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type"),
                "content_length": response.headers.get("content-length"),
            }
        }
        
        self._log_structured(log_entry)
        
        return response
    
    def _setup_structured_logger(self) -> logging.Logger:
        """Setup structured logger."""
        logger = logging.getLogger("structured_api")
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
            
            # Custom formatter for JSON
            class StructuredFormatter(logging.Formatter):
                def format(self, record):
                    log_entry = record.msg
                    if isinstance(log_entry, dict):
                        return json.dumps(log_entry, default=str)
                    return super().format(record)
            
            handler.setFormatter(StructuredFormatter())
            logger.addHandler(handler)
            logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
            logger.propagate = False
        
        return logger
    
    def _log_structured(self, log_entry: Dict[str, Any]) -> None:
        """Log structured entry."""
        self.logger.info(log_entry)


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for audit logging of sensitive operations."""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = self._setup_audit_logger()
        self.sensitive_endpoints = {
            "/recommend",  # Personal data processing
            "/feedback",   # User feedback
            "/profile",    # User profile access
            "/admin",      # Administrative operations
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request with audit logging."""
        # Check if this is a sensitive endpoint
        is_sensitive = any(request.url.path.startswith(endpoint) for endpoint in self.sensitive_endpoints)
        
        if is_sensitive:
            # Log audit entry
            audit_entry = {
                "timestamp": time.time(),
                "event_type": "api_access",
                "endpoint": request.url.path,
                "method": request.method,
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent"),
                "request_id": getattr(request.state, "request_id", None),
            }
            
            # Add user context if available
            if hasattr(request.state, "user_id"):
                audit_entry["user_id"] = request.state.user_id
            if hasattr(request.state, "session_id"):
                audit_entry["session_id"] = request.state.session_id
            
            # Log request body for sensitive operations (be careful with PII)
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.body()
                    if body:
                        # Parse and sanitize body for audit
                        body_str = body.decode("utf-8", errors="ignore")
                        audit_entry["request_body"] = self._sanitize_body_for_audit(body_str)
                except Exception:
                    pass
            
            self._log_audit(audit_entry)
        
        response = await call_next(request)
        
        # Log audit response for sensitive operations
        if is_sensitive:
            audit_entry["response_status"] = response.status_code
            self._log_audit(audit_entry)
        
        return response
    
    def _sanitize_body_for_audit(self, body: str) -> str:
        """Sanitize request body for audit logging."""
        try:
            # Try to parse as JSON
            data = json.loads(body)
            
            # Remove or mask sensitive fields
            sensitive_fields = ["password", "token", "api_key", "secret", "credit_card"]
            
            def sanitize(obj):
                if isinstance(obj, dict):
                    return {
                        k: "***MASKED***" if any(field in k.lower() for field in sensitive_fields)
                        else sanitize(v)
                        for k, v in obj.items()
                    }
                elif isinstance(obj, list):
                    return [sanitize(item) for item in obj]
                else:
                    return obj
            
            sanitized = sanitize(data)
            return json.dumps(sanitized, default=str)
            
        except Exception:
            # If parsing fails, return truncated body
            return body[:500] + "..." if len(body) > 500 else body
    
    def _setup_audit_logger(self) -> logging.Logger:
        """Setup audit logger."""
        logger = logging.getLogger("audit")
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            
            formatter = logging.Formatter(
                "%(asctime)s - AUDIT - %(message)s"
            )
            handler.setFormatter(formatter)
            
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            logger.propagate = False
        
        return logger
    
    def _log_audit(self, audit_entry: Dict[str, Any]) -> None:
        """Log audit entry."""
        self.logger.info(json.dumps(audit_entry, default=str, sort_keys=True))
