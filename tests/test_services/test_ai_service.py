import pytest
from app.services.ai_service import ai_service


@pytest.mark.asyncio
async def test_ai_generate_response():
    """测试AI生成响应"""
    messages = [{"role": "user", "content": "你好"}]
    response = await ai_service.generate_response(messages, session_id="test-123")
    assert isinstance(response, str)
    assert len(response) > 0
    print(f"AI Response: {response}")


@pytest.mark.asyncio
async def test_ai_generate_response_hello():
    """测试AI对问候语的响应"""
    messages = [{"role": "user", "content": "你好"}]
    response = await ai_service.generate_response(messages)
    assert "你好" in response or "Hello" in response


@pytest.mark.asyncio
async def test_ai_generate_response_weather():
    """测试AI对天气查询的响应"""
    messages = [{"role": "user", "content": "今天天气怎么样？"}]
    response = await ai_service.generate_response(messages)
    assert "天气" in response or "抱歉" in response


@pytest.mark.asyncio
async def test_ai_stream_response():
    """测试AI流式响应"""
    messages = [{"role": "user", "content": "你好"}]
    chunks = []
    async for chunk in ai_service.stream_response(messages):
        chunks.append(chunk)
    
    assert len(chunks) > 0
    full_response = "".join(chunks).strip()
    assert len(full_response) > 0
    print(f"Streamed Response: {full_response}")


@pytest.mark.asyncio
async def test_ai_with_history():
    """测试带历史上下文的AI响应"""
    messages = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什么可以帮你的？"},
        {"role": "user", "content": "谢谢"}
    ]
    response = await ai_service.generate_response(messages, session_id="test-history")
    assert isinstance(response, str)
    assert len(response) > 0
