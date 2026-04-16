import asyncio
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
from loguru import logger

from app.config import settings
from app.redis_client import redis_client


class AIService:
    """AI 服务 - 火山引擎 ARK API"""

    def _get_api_key(self) -> Optional[str]:
        return os.environ.get("ARK_CODING_PLAN_API_KEY") or settings.ARK_API_KEY

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        session_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        生成 AI 响应
        调用火山引擎 ARK API
        """
        api_key = self._get_api_key()
        if not api_key:
            logger.error("ARK_API_KEY is not configured")
            return "AI 服务未正确配置，请检查 ARK_API_KEY"

        url = f"{settings.ARK_BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.ARK_MODEL,
            "messages": messages
        }

        try:
            async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()

                ai_message = result.get("choices", [{}])[0].get("message", {})
                content = ai_message.get("content", "")

                if session_id:
                    await redis_client.set(
                        f"session:last_response:{session_id}",
                        content,
                        ttl=300
                    )

                logger.info(f"Generated response for session {session_id}")
                return content

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            return f"AI 服务请求失败: HTTP {e.response.status_code}"
        except Exception as e:
            logger.error(f"AI service error: {str(e)}")
            return f"AI 服务调用失败: {str(e)}"

    async def stream_response(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ):
        """流式响应（用于 SSE）"""
        api_key = self._get_api_key()
        if not api_key:
            yield "AI 服务未正确配置，请检查 ARK_API_KEY"
            return

        url = f"{settings.ARK_BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.ARK_MODEL,
            "messages": messages,
            "stream": True
        }

        try:
            async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            import json
                            try:
                                chunk = json.loads(data)
                                delta = chunk.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"Stream error: {str(e)}")
            yield f"流式响应失败: {str(e)}"


ai_service = AIService()
