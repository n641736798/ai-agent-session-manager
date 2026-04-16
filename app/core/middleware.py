from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time
import uuid
from loguru import logger

cors_origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
    "null",
    "file://",
]


class RequestIDMiddleware(BaseHTTPMiddleware):
    """请求ID中间件"""
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s"
        )
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """日志中间件"""
    async def dispatch(self, request: Request, call_next):
        logger.debug(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        logger.debug(f"Response: {response.status_code}")
        return response


def setup_middleware(app: FastAPI):
    """配置所有中间件"""
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 请求ID和日志
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(LoggingMiddleware)
