"""
配置管理模块
集中管理所有环境变量和配置项
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv

# 获取 backend 目录的绝对路径
BACKEND_DIR = Path(__file__).parent
ENV_FILE = BACKEND_DIR / ".env"

# 加载 .env 文件
load_dotenv(dotenv_path=ENV_FILE)


class Settings(BaseSettings):
    """
    应用配置类
    从环境变量或 .env 文件加载配置
    """
    
    # ===========================================
    # 应用基础配置
    # ===========================================
    APP_NAME: str = "PawFlip Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API 服务配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    
    # CORS 配置 (允许的前端域名，逗号分隔)
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    # ===========================================
    # Supabase 数据库配置
    # ===========================================
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""  # anon/public key
    SUPABASE_SERVICE_KEY: Optional[str] = None  # service role key (可选)
    
    # ===========================================
    # JWT 认证配置
    # ===========================================
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    
    # ===========================================
    # AI 服务配置
    # ===========================================
    # Google Gemini API
    GOOGLE_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"
    
    # OpenAI API (备选)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    
    # OpenRouter API (视频分析等)
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_VIDEO_MODEL: str = "google/gemini-2.0-flash-001"
    
    # AI 服务选择: "gemini" | "openai" | "local"
    AI_PROVIDER: str = "gemini"
    
    # ===========================================
    # Pet Vision Narrator 配置
    # ===========================================
    # Narrator API 服务地址
    NARRATOR_API_URL: str = "http://localhost:8002"
    NARRATOR_API_TIMEOUT: int = 300
    
    # 视频处理模式: "local" | "api"
    PETVISION_MODE: str = "api"
    
    # 本地模型配置 (如果使用 local 模式)
    PETVISION_LOCAL_MODEL: str = "HuggingFaceTB/SmolVLM2-256M-Video-Instruct"
    
    # Ollama 配置 (本地 LLM)
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    
    # 视频处理选项
    PETVISION_USE_FRAME_SAMPLING: bool = False
    PETVISION_ENABLE_LLM_ANALYSIS: bool = True
    PETVISION_SAVE_DEBUG_OUTPUT: bool = True
    
    # ===========================================
    # 3D 模型生成配置
    # ===========================================
    # 3D 生成服务提供商: "hunyuan" | "meshy" | "tripo" | "cloud" | "local"
    MODEL_3D_PROVIDER: str = "hunyuan"

    # 混元生3D（专业版）OpenAI 兼容接口
    # API Key: 从控制台 API Key 页面创建
    HUNYUAN_API_KEY: Optional[str] = None
    HUNYUAN_API_URL: str = "https://api.ai3d.cloud.tencent.com"
    # 模型版本: "3.0" 或 "3.1"
    HUNYUAN_MODEL: str = "3.0"
    
    # Meshy AI API
    MESHY_API_KEY: Optional[str] = None
    MESHY_API_URL: str = "https://api.meshy.ai/openapi/v1"
    
    # Tripo AI API (备选)
    TRIPO_API_KEY: Optional[str] = None
    TRIPO_API_URL: str = "https://api.tripo3d.ai/v2/openapi"
    
    # ===========================================
    # 文件存储配置
    # ===========================================
    # 上传文件临时目录
    UPLOAD_DIR: str = "uploads"
    # 最大上传文件大小 (MB)
    MAX_UPLOAD_SIZE_MB: int = 100
    # 3D 模型存储目录
    MODEL_3D_DIR: str = "models_3d"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    获取配置单例
    使用 lru_cache 确保只创建一次实例
    """
    return Settings()


# 导出配置实例
settings = get_settings()
