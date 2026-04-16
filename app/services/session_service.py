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
            metadata=session_data.meta_data,
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
        msg_dict = message.model_dump()
        msg_dict['timestamp'] = msg_dict['timestamp'].isoformat() if msg_dict.get('timestamp') else None
        messages.append(msg_dict)
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
