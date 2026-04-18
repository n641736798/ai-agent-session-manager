from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.config import settings
from app.api.v1.router import api_router
from app.core.middleware import setup_middleware
from app.core.exceptions import setup_exception_handlers
from app.database import init_db
from app.redis_client import redis_client
from app.utils.logger import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    setup_logging()
    try:
        await redis_client.connect()
    except Exception as e:
        print(f"Redis connection failed: {e}")
        print("Continuing without Redis...")
    await init_db()
    
    yield
    
    # 关闭时
    try:
        await redis_client.disconnect()
    except:
        pass


app = FastAPI(
    title=settings.APP_NAME,
    description="AI Agent Session Management System",
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# 注册中间件
setup_middleware(app)

# 注册异常处理器
setup_exception_handlers(app)

# 注册路由
app.include_router(api_router, prefix="/api/v1")


# 健康检查
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "service": settings.APP_NAME
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
