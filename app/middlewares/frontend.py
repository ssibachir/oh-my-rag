from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import FileResponse
import os

class FrontendMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        if response.status_code == 404 and not request.url.path.startswith("/api"):
            return FileResponse("static/index.html")
            
        return response
