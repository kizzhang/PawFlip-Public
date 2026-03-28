"""
API 路由模块
"""

from .auth import router as auth_router
from .pets import router as pets_router
from .diary import router as diary_router
from .health import router as health_router
from .video import router as video_router
from .ai import router as ai_router
from .social import router as social_router
from .proxy import router as proxy_router
from .health_agent import router as health_agent_router

__all__ = [
    "auth_router",
    "pets_router",
    "diary_router",
    "health_router",
    "video_router",
    "ai_router",
    "social_router",
    "proxy_router",
    "health_agent_router"
]
