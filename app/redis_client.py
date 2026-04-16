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
            cls._instance.disabled = not settings.USE_REDIS
        return cls._instance

    async def connect(self) -> None:
        """建立连接池"""
        if self.disabled:
            logger.info("Redis is disabled, skipping connection")
            return
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
        if self.disabled or not self.client:
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
        if self.disabled or not self.client:
            return False
        if not isinstance(value, str):
            value = json.dumps(value, ensure_ascii=False)

        if ttl:
            return await self.client.setex(key, ttl, value)
        return await self.client.set(key, value)

    async def delete(self, key: str) -> int:
        """删除键"""
        if self.disabled or not self.client:
            return 0
        return await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if self.disabled or not self.client:
            return False
        return await self.client.exists(key) > 0


# 全局Redis客户端实例
redis_client = RedisClient()
