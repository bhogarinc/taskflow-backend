"""
Error Handler Middleware.

Centralized error handling with structured responses and logging.
"""

import logging
import time
import traceback
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling and logging errors."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle errors."""
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Log successful requests
            duration = time.time() - start_time
            logger.info(
                f"{request.method} {request.url.path} "
                f"- {response.status_code} - {duration:.3f}s"
            )
            
            return response
            
        except Exception as exc:
            duration = time.time() - start_time
            
            # Log the error
            logger.error(
                f"Error processing {request.method} {request.url.path}: {str(exc)}"
            )
            logger.debug(traceback.format_exc())
            
            # Create error response
            error_detail = str(exc) if settings.DEBUG else "Internal server error"
            status_code = getattr(exc, "status_code", 500)
            
            return JSONResponse(
                status_code=status_code if isinstance(status_code, int) else 500,
                content={
                    "error": "Internal server error",
                    "detail": error_detail,
                    "path": request.url.path,
                    "method": request.method,
                },
            )