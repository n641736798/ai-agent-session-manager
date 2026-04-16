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
