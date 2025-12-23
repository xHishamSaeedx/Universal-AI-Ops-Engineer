"""
Rate limiting module for target server.
Provides configurable rate limiting with in-memory storage.
"""
import time
from collections import defaultdict, deque
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

# Global rate limit configuration (can be updated dynamically)
_rate_limit_config = {
    "enabled": True,
    "max_requests": 100,
    "window_seconds": 60,
}

# In-memory storage: IP -> deque of request timestamps
_rate_limit_storage: Dict[str, deque] = defaultdict(lambda: deque())

# Statistics
_rate_limit_stats = {
    "total_requests": 0,
    "rate_limited_requests": 0,
    "current_rate": 0.0,  # requests per second
}


def get_rate_limit_config() -> dict:
    """Get current rate limit configuration."""
    return _rate_limit_config.copy()


def update_rate_limit_config(enabled: bool = None, max_requests: int = None, window_seconds: int = None):
    """Update rate limit configuration dynamically."""
    if enabled is not None:
        _rate_limit_config["enabled"] = enabled
    if max_requests is not None:
        _rate_limit_config["max_requests"] = max_requests
    if window_seconds is not None:
        _rate_limit_config["window_seconds"] = window_seconds
    logger.info(f"Rate limit config updated: {_rate_limit_config}")


def get_rate_limit_stats() -> dict:
    """Get rate limiting statistics."""
    return {
        "config": _rate_limit_config.copy(),
        "stats": _rate_limit_stats.copy(),
    }


def _get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    # Check for forwarded IP (from proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client
    if request.client:
        return request.client.host
    
    return "unknown"


def _clean_old_requests(ip: str, window_seconds: int):
    """Remove request timestamps outside the time window."""
    current_time = time.time()
    cutoff_time = current_time - window_seconds
    
    request_times = _rate_limit_storage[ip]
    # Remove timestamps older than the window
    while request_times and request_times[0] < cutoff_time:
        request_times.popleft()


async def check_rate_limit(request: Request) -> Tuple[bool, dict]:
    """
    Check if request should be rate limited.
    Returns: (is_allowed, rate_limit_info)
    """
    if not _rate_limit_config["enabled"]:
        return True, {}
    
    ip = _get_client_ip(request)
    max_requests = _rate_limit_config["max_requests"]
    window_seconds = _rate_limit_config["window_seconds"]
    
    current_time = time.time()
    
    # Clean old requests outside the window
    _clean_old_requests(ip, window_seconds)
    
    # Get current request count for this IP
    request_times = _rate_limit_storage[ip]
    current_count = len(request_times)
    
    # Update statistics
    _rate_limit_stats["total_requests"] += 1
    
    # Check if limit exceeded
    if current_count >= max_requests:
        _rate_limit_stats["rate_limited_requests"] += 1
        
        # Log the rate limit violation
        logger.warning(
            f"Rate limit exceeded for {request.url.path} - "
            f"IP: {ip} - Count: {current_count + 1}/{max_requests} - "
            f"Window: {window_seconds}s"
        )
        
        # Calculate reset time (oldest request + window)
        reset_time = int(request_times[0] + window_seconds) if request_times else int(current_time + window_seconds)
        retry_after = max(0, reset_time - int(current_time))
        
        return False, {
            "limit": max_requests,
            "remaining": 0,
            "reset": reset_time,
            "retry_after": retry_after,
        }
    
    # Allow request - add current timestamp
    request_times.append(current_time)
    
    # Calculate remaining requests
    remaining = max(0, max_requests - (current_count + 1))
    reset_time = int(current_time + window_seconds)
    
    return True, {
        "limit": max_requests,
        "remaining": remaining,
        "reset": reset_time,
        "retry_after": 0,
    }


async def rate_limit_middleware(request: Request, call_next):
    """FastAPI middleware for rate limiting."""
    # Skip rate limiting for health checks
    if request.url.path in ["/healthz", "/"]:
        return await call_next(request)
    
    # Check rate limit
    is_allowed, rate_limit_info = await check_rate_limit(request)
    
    if not is_allowed:
        # Return 429 Too Many Requests
        response = JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Limit: {rate_limit_info['limit']} per {_rate_limit_config['window_seconds']} seconds",
                "retry_after": rate_limit_info["retry_after"],
            }
        )
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(rate_limit_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_limit_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_limit_info["reset"])
        response.headers["Retry-After"] = str(rate_limit_info["retry_after"])
        return response
    
    # Proceed with request
    response = await call_next(request)
    
    # Add rate limit headers to successful responses
    response.headers["X-RateLimit-Limit"] = str(rate_limit_info["limit"])
    response.headers["X-RateLimit-Remaining"] = str(rate_limit_info["remaining"])
    response.headers["X-RateLimit-Reset"] = str(rate_limit_info["reset"])
    
    return response

