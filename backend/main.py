"""
PawFlip Backend - 主应用入口
FastAPI 应用配置和启动
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from config import settings
from routers import (
    auth_router,
    pets_router,
    diary_router,
    health_router,
    video_router,
    ai_router,
    social_router,
    proxy_router,
    health_agent_router
)

# ===========================================
# 日志配置
# ===========================================

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ===========================================
# 应用生命周期管理
# ===========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时初始化资源，关闭时清理资源
    """
    # 启动时
    logger.info("="*60)
    logger.info(f"🚀 启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"📍 API 地址: http://{settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"📚 API 文档: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    logger.info(f"🤖 AI 提供商: {settings.AI_PROVIDER}")
    logger.info("="*60)
    
    yield
    
    # 关闭时
    logger.info("👋 应用正在关闭...")


# ===========================================
# 创建 FastAPI 应用
# ===========================================

app = FastAPI(
    title=settings.APP_NAME,
    description="""
# PawFlip Backend API

智能宠物管家后端服务，提供以下功能：

## 🔐 认证
- 用户注册、登录
- JWT 令牌认证

## 🐾 宠物管理
- 宠物档案 CRUD
- 多宠物支持

## 📔 日记功能
- 手动创建日记
- AI 自动生成日记
- 视频转日记

## 💊 健康监测
- 健康数据记录
- 趋势分析
- AI 健康建议

## 🎬 视频处理
- 视频上传分析
- pet-vision-narrator 集成
- 异步处理支持

## 🤖 AI 助手
- 智能对话
- 健康问诊
- 故事生成

## 👥 社交功能
- 发布动态
- 点赞互动
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# ===========================================
# CORS 中间件配置
# ===========================================

# 解析允许的源
cors_origins = [
    origin.strip() 
    for origin in settings.CORS_ORIGINS.split(",")
    if origin.strip()
]

# 在开发模式下允许所有源
if settings.DEBUG:
    logger.info("DEBUG 模式: 允许所有 CORS 源")
    cors_origins = ["*"]
    allow_credentials = False
else:
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,  # 预检请求缓存时间
)


# ===========================================
# 全局异常处理
# ===========================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
):
    """
    请求验证错误处理
    返回更友好的错误信息
    """
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "请求参数验证失败",
            "details": errors
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理
    捕获未处理的异常
    """
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "服务器内部错误",
            "message": str(exc) if settings.DEBUG else "请稍后重试"
        }
    )


# ===========================================
# 注册路由
# ===========================================

# API v1 路由前缀
API_V1_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_V1_PREFIX)
app.include_router(pets_router, prefix=API_V1_PREFIX)
app.include_router(diary_router, prefix=API_V1_PREFIX)
app.include_router(health_router, prefix=API_V1_PREFIX)
app.include_router(video_router, prefix=API_V1_PREFIX)
app.include_router(ai_router, prefix=API_V1_PREFIX)
app.include_router(social_router, prefix=API_V1_PREFIX)
app.include_router(proxy_router, prefix=API_V1_PREFIX)
app.include_router(health_agent_router, prefix=API_V1_PREFIX)


# ===========================================
# 根路由
# ===========================================

@app.get("/", tags=["根"])
async def root():
    """
    API 根路由
    返回服务基本信息
    """
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "api_prefix": API_V1_PREFIX,
        "endpoints": {
            "auth": f"{API_V1_PREFIX}/auth",
            "pets": f"{API_V1_PREFIX}/pets",
            "diary": f"{API_V1_PREFIX}/diary",
            "health": f"{API_V1_PREFIX}/health",
            "video": f"{API_V1_PREFIX}/video",
            "ai": f"{API_V1_PREFIX}/ai",
            "social": f"{API_V1_PREFIX}/social",
            "health_agent": f"{API_V1_PREFIX}/health-agent"
        }
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    """
    健康检查端点
    用于监控服务状态
    """
    from datetime import datetime
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.APP_VERSION,
        "ai_provider": settings.AI_PROVIDER
    }


# ===========================================
# 启动入口
# ===========================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )
