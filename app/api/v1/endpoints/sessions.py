from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.schemas.session import (
    SessionCreate, SessionResponse, SessionUpdate,
    Message
)
from app.schemas.user import UserResponse
from app.services.session_service import SessionService
from app.services.ai_service import ai_service
from app.api.v1.dependencies.auth import get_current_user

router = APIRouter()


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
    
    # 调用 AI 服务（过滤掉timestamp字段，只保留role和content）
    ai_messages = [{"role": msg["role"], "content": msg["content"]} for msg in session.messages]
    ai_response = await ai_service.generate_response(
        messages=ai_messages,
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
