from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    APP_NAME: str = "AI Agent Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = Field(..., min_length=32)
    
    # 数据库配置
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/ai_agent"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis 配置
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0"
    )
    REDIS_MAX_CONNECTIONS: int = 10
    USE_REDIS: bool = True
    
    # 会话配置
    SESSION_TTL: int = 3600  # 会话过期时间（秒）
    
    # AI 服务配置
    AI_MODEL: str = "gpt-3.5-turbo"
    AI_API_KEY: Optional[str] = None
    AI_REQUEST_TIMEOUT: int = 30

    # 火山引擎 ARK API 配置
    ARK_API_KEY: Optional[str] = Field(default=None)
    ARK_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/coding/v3"
    ARK_MODEL: str = "ark-code-latest"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.ARK_API_KEY is None:
            import os
            self.ARK_API_KEY = os.environ.get("ARK_CODING_PLAN_API_KEY")


settings = Settings()
