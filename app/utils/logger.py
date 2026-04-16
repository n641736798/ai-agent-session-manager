from loguru import logger
import sys
from app.config import settings


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
