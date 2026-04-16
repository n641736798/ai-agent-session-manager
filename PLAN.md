# AI Agent 会话管理系统 - 项目计划

## 项目概述

构建一个AI Agent会话管理系统，具备用户会话管理、对话历史缓存、异步任务队列等核心能力，模拟真实AI后端服务。

## 技术栈

- **Web框架**: FastAPI 0.104.1
- **数据库**: PostgreSQL (SQLAlchemy 2.0 ORM + asyncpg)
- **缓存**: Redis 5.0.1
- **配置管理**: Pydantic Settings 2.1.0
- **容器化**: Docker + Docker Compose
- **测试**: pytest + httpx
- **异步任务**: Celery 5.3.4
- **日志**: Loguru 0.7.2

## 项目结构

```
fastapi-ai-service/
├── .env.example                 # 环境变量模板
├── .gitignore
├── docker-compose.yml           # 容器编排
├── Dockerfile                   # 应用镜像
├── requirements.txt             # Python 依赖
├── README.md
├── scripts/
│   ├── init_db.sql             # 数据库初始化脚本
│   └── entrypoint.sh           # 容器启动脚本
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理（Pydantic Settings）
│   ├── database.py             # 数据库连接（SQLAlchemy 2.0）
│   ├── redis_client.py         # Redis 连接池（单例模式）
│   ├── models/
│   │   ├── __init__.py
│   │   └── session.py          # 用户与会话ORM模型
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py             # 用户Pydantic模型
│   │   └── session.py          # 会话Pydantic模型
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py       # 路由聚合
│   │   │   ├── endpoints/
│   │   │   │   ├── users.py    # 用户相关接口
│   │   │   │   └── sessions.py # 会话相关接口
│   │   │   └── dependencies/   # 依赖注入
│   │   │       └── auth.py     # 认证逻辑
│   ├── services/
│   │   ├── __init__.py
│   │   ├── session_service.py  # 会话业务逻辑（依赖注入模式）
│   │   └── ai_service.py       # AI 调用（模拟）
│   ├── core/
│   │   ├── __init__.py
│   │   ├── exceptions.py       # 自定义异常
│   │   └── middleware.py       # 中间件（日志、CORS）
│   └── utils/
│       ├── __init__.py
│       └── logger.py           # 日志配置（Loguru）
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # pytest 配置
│   ├── test_api/
│   │   └── test_sessions.py
│   └── test_services/
│       └── test_ai_service.py
```

## 实施步骤

### 阶段一：项目基础架构

#### 1.1 依赖管理 (requirements.txt)
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
asyncpg==0.29.0
redis==5.0.1
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
alembic==1.13.0
httpx==0.25.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
celery==5.3.4
aioredis==2.0.1
loguru==0.7.2
```

#### 1.2 配置文件
- **.env.example**: 定义所有环境变量模板
  - `DATABASE_URL`: 数据库连接URL (PostgresDsn)
  - `REDIS_URL`: Redis连接URL (RedisDsn)
  - `SECRET_KEY`: JWT密钥 (min_length=32)
  - `APP_NAME`, `APP_VERSION`, `DEBUG`: 应用配置
  - `AI_MODEL`, `AI_API_KEY`, `AI_REQUEST_TIMEOUT`: AI配置

- **.gitignore**: Python项目标准忽略文件

#### 1.3 Docker配置
- **Dockerfile**: 多阶段构建
  - 使用Python 3.11 slim基础镜像
  - 安装系统依赖
  - 安装Python依赖
  - 复制应用代码
  - 设置启动命令

- **docker-compose.yml**: 服务编排
  - app: FastAPI应用服务
  - postgres: PostgreSQL 15
  - redis: Redis 7
  - celery-worker: 异步任务处理器

- **scripts/entrypoint.sh**: 容器启动脚本
  - 等待数据库就绪
  - 运行数据库迁移
  - 启动应用

- **scripts/init_db.sql**: 数据库初始化脚本

### 阶段二：应用核心模块

#### 2.1 配置管理 (app/config.py)
使用Pydantic Settings管理配置:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, RedisDsn
from typing import Optional

class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    APP_NAME: str = "AI Agent Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = Field(..., min_length=32)
    
    # 数据库配置
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/ai_agent"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis 配置
    REDIS_URL: RedisDsn = Field(
        default="redis://localhost:6379/0"
    )
    REDIS_MAX_CONNECTIONS: int = 10
    
    # 会话配置
    SESSION_TTL: int = 3600  # 会话过期时间（秒）
    
    # AI 服务配置
    AI_MODEL: str = "gpt-3.5-turbo"
    AI_API_KEY: Optional[str] = None
    AI_REQUEST_TIMEOUT: int = 30
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

settings = Settings()
```

#### 2.2 数据库连接 (app/database.py)
使用SQLAlchemy 2.0异步模式:
```python
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
from loguru import logger

from app.config import settings

# 创建异步引擎
engine: AsyncEngine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # 连接前检查
)

# 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# ORM 基类
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """依赖注入：获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db() -> None:
    """初始化数据库（生产环境请使用 Alembic 迁移）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")
```

#### 2.3 Redis客户端 (app/redis_client.py)
使用单例模式，全局共享Redis客户端实例:
```python
import redis.asyncio as redis
from typing import Optional, Any
import json
from loguru import logger

from app.config import settings

class RedisClient:
    """Redis 客户端封装（单例模式）"""
    
    _instance: Optional["RedisClient"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client: Optional[redis.Redis] = None
        return cls._instance
    
    async def connect(self) -> None:
        """建立连接池"""
        if self.client is None:
            self.client = redis.from_url(
                str(settings.REDIS_URL),
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                decode_responses=True,
            )
            await self.client.ping()
            logger.info("Redis connected")
    
    async def disconnect(self) -> None:
        """关闭连接"""
        if self.client:
            await self.client.close()
            self.client = None
            logger.info("Redis disconnected")
    
    async def get(self, key: str) -> Optional[Any]:
        """获取值"""
        if not self.client:
            return None
        value = await self.client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """设置值"""
        if not self.client:
            return False
        if not isinstance(value, str):
            value = json.dumps(value, ensure_ascii=False)
        
        if ttl:
            return await self.client.setex(key, ttl, value)
        return await self.client.set(key, value)
    
    async def delete(self, key: str) -> int:
        """删除键"""
        if not self.client:
            return 0
        return await self.client.delete(key)
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self.client:
            return False
        return await self.client.exists(key) > 0

# 全局Redis客户端实例
redis_client = RedisClient()
```

#### 2.4 日志配置 (app/utils/logger.py)
使用Loguru替代标准logging:
```python
from loguru import logger
import sys
from app.config import settings

# 配置 Loguru
def setup_logging():
    """配置日志"""
    # 移除默认处理器
    logger.remove()
    
    # 添加控制台处理器
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        level="DEBUG" if settings.DEBUG else "INFO",
        colorize=True
    )
    
    # 添加文件处理器（生产环境）
    if not settings.DEBUG:
        logger.add(
            "logs/app.log",
            rotation="10 MB",
            retention="30 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            level="INFO"
        )
```

### 阶段三：数据模型层

#### 3.1 ORM 模型 (app/models/session.py)
使用SQLAlchemy 2.0声明式API:
```python
from sqlalchemy import (
    Column, Integer, String, Text, DateTime,
    ForeignKey, JSON, Index
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200))
    messages = Column(JSON, default=list)  # 存储对话历史
    metadata = Column(JSON, default=dict)  # 扩展元数据
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="sessions")
    
    # 复合索引
    __table_args__ = (
        Index("ix_sessions_user_updated", "user_id", "updated_at"),
    )
```

#### 3.2 Pydantic Schemas

**app/schemas/session.py**:
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

class Message(BaseModel):
    """对话消息"""
    role: str  # user / assistant / system
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class SessionBase(BaseModel):
    title: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SessionCreate(SessionBase):
    pass

class SessionUpdate(SessionBase):
    messages: Optional[List[Message]] = None

class SessionResponse(SessionBase):
    id: int
    session_id: str
    user_id: int
    messages: List[Message]
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}
```

**app/schemas/user.py**:
```python
from pydantic import BaseModel, Field
from datetime import datetime

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6)

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    
    model_config = {"from_attributes": True}
```

### 阶段四：API层

#### 4.1 认证依赖 (app/api/v1/dependencies/auth.py)
- JWT Token验证
- 当前用户获取
- 权限检查

#### 4.2 用户接口 (app/api/v1/endpoints/users.py)
- `POST /users` - 创建用户
- `GET /users/me` - 获取当前用户信息
- `PUT /users/me` - 更新用户信息
- `POST /users/login` - 用户登录（返回JWT）

#### 4.3 会话接口 (app/api/v1/endpoints/sessions.py)
完整的会话API实现:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.schemas.session import (
    SessionCreate, SessionResponse, SessionUpdate,
    Message, UserResponse
)
from app.services.session_service import SessionService
from app.services.ai_service import ai_service
from app.api.v1.dependencies.auth import get_current_user

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建新会话"""
    service = SessionService(db)
    session = await service.create_session(current_user.id, session_data)
    return session

@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    limit: int = 50,
    offset: int = 0,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户会话列表"""
    service = SessionService(db)
    sessions = await service.list_user_sessions(current_user.id, limit, offset)
    return sessions

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取会话详情"""
    service = SessionService(db)
    session = await service.get_session(session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.post("/{session_id}/messages")
async def send_message(
    session_id: str,
    message: Message,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """发送消息并获取 AI 响应"""
    # 添加用户消息
    service = SessionService(db)
    session = await service.add_message(session_id, current_user.id, message)
    
    # 调用 AI 服务
    ai_response = await ai_service.generate_response(
        messages=session.messages,
        session_id=session_id
    )
    
    # 添加 AI 响应消息
    ai_message = Message(role="assistant", content=ai_response)
    session = await service.add_message(session_id, current_user.id, ai_message)
    
    return {
        "response": ai_response,
        "session": session
    }

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除会话"""
    service = SessionService(db)
    deleted = await service.delete_session(session_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
```

#### 4.4 路由聚合 (app/api/v1/router.py)
整合所有端点路由:
```python
from fastapi import APIRouter
from app.api.v1.endpoints import users, sessions

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
```

### 阶段五：业务服务层

#### 5.1 会话服务 (app/services/session_service.py)
使用依赖注入模式，通过构造函数接收db实例:
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Optional, List
import uuid
from loguru import logger

from app.models.session import Session, User
from app.schemas.session import SessionCreate, SessionUpdate, Message
from app.redis_client import redis_client
from app.config import settings

class SessionService:
    """会话业务逻辑"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_session(
        self,
        user_id: int,
        session_data: SessionCreate
    ) -> Session:
        """创建新会话"""
        session = Session(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            title=session_data.title or "新对话",
            metadata=session_data.metadata,
            messages=[]
        )
        self.db.add(session)
        await self.db.flush()
        
        # 缓存会话元数据到 Redis
        cache_key = f"session:meta:{session.session_id}"
        await redis_client.set(
            cache_key,
            {"title": session.title, "user_id": user_id},
            ttl=settings.SESSION_TTL
        )
        
        return session
    
    async def get_session(
        self,
        session_id: str,
        user_id: int
    ) -> Optional[Session]:
        """获取会话（带缓存）"""
        # 先从 Redis 检查是否有完整缓存
        cache_key = f"session:full:{session_id}"
        cached = await redis_client.get(cache_key)
        
        if cached:
            # 从缓存重建对象（简化处理）
            logger.info(f"Session {session_id} from cache")
            # 实际应该反序列化为 Session 对象
        
        # 从数据库查询
        stmt = select(Session).where(
            Session.session_id == session_id,
            Session.user_id == user_id
        )
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if session:
            # 更新缓存
            await redis_client.set(
                cache_key,
                {
                    "id": session.id,
                    "session_id": session.session_id,
                    "title": session.title,
                    "messages": session.messages,
                },
                ttl=settings.SESSION_TTL
            )
        
        return session
    
    async def add_message(
        self,
        session_id: str,
        user_id: int,
        message: Message
    ) -> Session:
        """添加消息到会话"""
        session = await self.get_session(session_id, user_id)
        if not session:
            raise ValueError("Session not found")
        
        # 更新消息列表
        messages = session.messages or []
        messages.append(message.model_dump())
        session.messages = messages
        
        await self.db.commit()
        await self.db.refresh(session)
        
        # 使缓存失效
        cache_key = f"session:full:{session_id}"
        await redis_client.delete(cache_key)
        
        return session
    
    async def list_user_sessions(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Session]:
        """获取用户会话列表"""
        stmt = select(Session).where(
            Session.user_id == user_id
        ).order_by(
            Session.updated_at.desc()
        ).limit(limit).offset(offset)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def delete_session(
        self,
        session_id: str,
        user_id: int
    ) -> bool:
        """删除会话"""
        stmt = delete(Session).where(
            Session.session_id == session_id,
            Session.user_id == user_id
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        if result.rowcount > 0:
            # 清理缓存
            await redis_client.delete(f"session:full:{session_id}")
            await redis_client.delete(f"session:meta:{session_id}")
            return True
        return False
```

#### 5.2 AI服务 (app/services/ai_service.py)
AI服务模拟（支持全局单例实例）:
```python
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from app.config import settings
from app.redis_client import redis_client

class AIService:
    """AI 服务（模拟真实 LLM 调用）"""
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        session_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        生成 AI 响应
        实际应调用 OpenAI/Anthropic/Qwen 等 API
        """
        # 模拟 API 延迟
        await asyncio.sleep(1.5)
        
        # 获取最后一条用户消息
        last_user_msg = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break
        
        # 简单的响应生成
        if "你好" in last_user_msg or "hello" in last_user_msg.lower():
            response = "你好！我是 AI 助手，有什么可以帮你的吗？"
        elif "天气" in last_user_msg:
            response = "抱歉，我暂时无法查询实时天气。不过我可以帮你分析其他问题。"
        else:
            response = f"收到你的问题：{last_user_msg[:50]}... 这是一个模拟响应，实际应该调用真实的 AI 模型。"
        
        # 如果有会话 ID，记录到 Redis
        if session_id:
            await redis_client.set(
                f"session:last_response:{session_id}",
                response,
                ttl=300  # 5分钟
            )
        
        logger.info(f"Generated response for session {session_id}")
        return response
    
    async def stream_response(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ):
        """流式响应（用于 SSE）"""
        # 模拟流式输出
        response = await self.generate_response(messages)
        words = response.split()
        
        for word in words:
            yield word + " "
            await asyncio.sleep(0.1)

# 全局实例
ai_service = AIService()
```

#### 5.3 Celery任务 (app/tasks/ai_tasks.py)
```python
from celery import Celery
from app.config import settings

# 创建Celery应用
celery_app = Celery(
    "ai_service",
    broker=str(settings.REDIS_URL),
    backend=str(settings.REDIS_URL),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5分钟超时
)

@celery_app.task(bind=True, max_retries=3)
def process_ai_inference(self, session_id: str, message: str, history: list):
    """
    异步AI推理任务
    - 模拟AI处理延迟
    - 支持重试机制
    - 更新任务状态到Redis
    """
    try:
        import time
        time.sleep(2)  # 模拟处理时间
        
        # 生成响应
        response = f"AI处理结果：'{message}' 已处理完成"
        
        return {
            "status": "success",
            "session_id": session_id,
            "response": response,
        }
    except Exception as exc:
        # 重试机制
        if self.request.retries < 3:
            raise self.retry(exc=exc, countdown=5)
        raise
```

### 阶段六：核心组件

#### 6.1 自定义异常 (app/core/exceptions.py)
```python
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
```

#### 6.2 中间件 (app/core/middleware.py)
```python
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
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 请求ID和日志
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(LoggingMiddleware)
```

### 阶段七：FastAPI入口 (app/main.py)

```python
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
    await redis_client.connect()
    await init_db()
    
    yield
    
    # 关闭时
    await redis_client.disconnect()

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
```

### 阶段八：测试

#### 8.1 测试配置 (tests/conftest.py)
```python
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.config import settings

# 测试数据库
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/test_ai_agent"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
        
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
```

#### 8.2 API测试 (tests/test_api/test_sessions.py)
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_session(client: AsyncClient):
    response = await client.post("/api/v1/sessions", json={"title": "Test Session"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Session"
    assert "session_id" in data
```

#### 8.3 服务测试 (tests/test_services/test_ai_service.py)
```python
import pytest
from app.services.ai_service import ai_service

@pytest.mark.asyncio
async def test_ai_generate_response():
    messages = [{"role": "user", "content": "你好"}]
    response = await ai_service.generate_response(messages, session_id="test-123")
    assert isinstance(response, str)
    assert len(response) > 0
```

### 阶段九：文档和部署

#### 9.1 README.md
- 项目介绍
- 快速开始指南
- API文档链接
- 部署说明

#### 9.2 部署配置优化
- 生产环境Docker配置
- 环境变量说明
- 监控和日志配置

## 数据流设计

### 用户创建会话流程
```
1. 用户调用 POST /sessions
2. 认证中间件验证JWT (get_current_user)
3. SessionService.create_session() 写入PostgreSQL
   - 生成UUID作为session_id
   - 初始化空messages列表
4. 同时缓存会话元数据到Redis (TTL: SESSION_TTL)
5. 返回SessionResponse
```

### 用户发送消息流程
```
1. 用户调用 POST /sessions/{session_id}/messages
2. 认证中间件验证JWT
3. SessionService.add_message() 保存用户消息
   - 先调用get_session()获取会话（带缓存）
   - 更新messages JSON字段
   - 使Redis缓存失效
4. ai_service.generate_response() 生成AI响应
   - 分析messages历史
   - 模拟1.5s延迟
   - 缓存最后响应到Redis (5分钟)
5. SessionService.add_message() 保存AI响应
6. 返回{response, session}
```

### 数据模型设计特点
- **User**: 用户基础信息，关联sessions
- **Session**: 
  - 使用 `session_id` (UUID) 作为业务主键
  - `messages` 存储为JSON数组，简化消息查询
  - `metadata` 支持扩展字段
  - 复合索引优化用户会话列表查询

### 缓存策略
- **会话元数据**: 创建时缓存，TTL=SESSION_TTL
  - Key: `session:meta:{session_id}`
- **会话完整数据**: 读取时缓存，更新时失效
  - Key: `session:full:{session_id}`
- **AI最后响应**: 5分钟缓存
  - Key: `session:last_response:{session_id}`

## 架构设计特点

### 1. 依赖注入模式
- `SessionService` 通过构造函数接收 `db: AsyncSession`
- FastAPI的`Depends(get_db)`自动注入数据库会话
- 便于测试时注入Mock对象

### 2. 单例模式服务实例
- `redis_client` - 全局Redis客户端单例
- `ai_service` - 全局AI服务单例
- 避免重复创建连接池，统一管理资源

### 3. 分层架构
```
API Layer (endpoints/)
    ↓ 调用
Service Layer (services/)
    ↓ 调用
Data Layer (models/)
    ↓ 使用
Redis Cache (redis_client/)
```

### 4. 缓存失效策略
- **写入后失效**: add_message后删除缓存
- **读取时加载**: get_session时更新缓存
- **保证一致性**: 数据库为唯一数据源

## API端点汇总

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | /api/v1/sessions | 创建会话 | 是 |
| GET | /api/v1/sessions | 获取会话列表 | 是 |
| GET | /api/v1/sessions/{id} | 获取会话详情 | 是 |
| POST | /api/v1/sessions/{id}/messages | 发送消息 | 是 |
| DELETE | /api/v1/sessions/{id} | 删除会话 | 是 |

## 安全考虑

1. **认证**: JWT Token，过期时间24小时
2. **密码**: bcrypt哈希存储
3. **CORS**: 限制可访问域名
4. **速率限制**: 每分钟最多30次请求
5. **SQL注入**: 使用SQLAlchemy ORM参数化查询
6. **输入验证**: Pydantic模型严格验证
7. **密钥安全**: SECRET_KEY最小32位字符
8. **级联删除**: 用户删除时自动删除关联会话

## 扩展性考虑

1. **数据库**: 支持读写分离配置（通过DATABASE_URL配置）
2. **缓存**: Redis Cluster支持
3. **任务队列**: Celery支持多Worker横向扩展
4. **API**: 版本化设计（/api/v1/）
5. **模型**: 预留多模型切换接口（AI_MODEL配置）
6. **连接池**: 可配置的数据库和Redis连接池大小
7. **消息存储**: JSON格式便于后续迁移到独立表结构

## 实施优先级

1. **P0** - 核心功能
   - 项目基础架构
   - 用户认证
   - 会话CRUD
   - AI消息交互

2. **P1** - 重要功能
   - Redis缓存
   - 异步任务队列
   - 日志和监控
   - 基础测试

3. **P2** - 增强功能
   - 流式响应
   - 高级缓存策略
   - 完整测试覆盖
   - 性能优化
