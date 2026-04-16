from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class AIServiceException(Exception):
    """AI服务异常基类"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class SessionNotFoundException(AIServiceException):
    """会话不存在"""
    def __init__(self, session_id: str):
        super().__init__(f"Session {session_id} not found", status.HTTP_404_NOT_FOUND)


class AuthenticationException(AIServiceException):
    """认证失败"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class RateLimitException(AIServiceException):
    """请求频率限制"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status.HTTP_429_TOO_MANY_REQUESTS)


# 异常处理器
def setup_exception_handlers(app):
    """配置全局异常处理器"""
    
    @app.exception_handler(AIServiceException)
    async def ai_exception_handler(request: Request, exc: AIServiceException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"}
        )
