"""
PetVision Narrator 配置管理模块

使用环境变量进行配置，支持 .env 文件自动加载。
"""

import os
from typing import Any, Optional
from dotenv import load_dotenv
from pathlib import Path

# 从项目根目录加载 .env 文件
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(env_path)


class Config:
    """配置管理器，从环境变量加载所有配置。"""
    
    def __init__(self, config_dict: dict = None):
        self.config = self._load_from_env()
        if config_dict:
            self.config.update(config_dict)
    
    def _load_from_env(self) -> dict:
        """从环境变量加载配置。"""
        return {
            # VLM 配置
            "vlm_mode": os.getenv("PETVISION_VLM_MODE", "local"),
            "vlm_api_provider": os.getenv("VLM_PROVIDER", "openai"),
            "vlm_model": os.getenv("VLM_MODEL", "gpt-4-vision-preview"),
            "vlm_api_key": os.getenv("VLM_API_KEY", ""),
            "vlm_api_base_url": os.getenv("VLM_BASE_URL"),
            "local_vision_model": "HuggingFaceTB/SmolVLM2-256M-Video-Instruct",
            
            # LLM 配置
            "llm_mode": os.getenv("PETVISION_LLM_MODE", "local"),
            "llm_api_provider": os.getenv("LLM_PROVIDER", "openai"),
            "llm_model": os.getenv("LLM_MODEL", "gpt-4"),
            "llm_api_key": os.getenv("LLM_API_KEY", ""),
            "llm_api_base_url": os.getenv("LLM_BASE_URL"),
            "reasoning_effort": os.getenv("REASONING_EFFORT", "medium"),
            
            # Ollama 配置
            "ollama_url": os.getenv("PETVISION_OLLAMA_URL", "http://localhost:11434"),
            "ollama_model": os.getenv("PETVISION_OLLAMA_MODEL", "gemma3"),
            
            # 处理参数
            "temperature": 0.7,
            "max_tokens": 1000000,
            "use_frame_sampling": self._get_bool("PETVISION_USE_FRAME_SAMPLING", False),
            "num_frames": 8,
            "timeout_seconds": 120,
            
            # 分析设置
            "enable_llm_analysis": self._get_bool("PETVISION_ENABLE_LLM_ANALYSIS", True),
            "analysis_llm_model": os.getenv("PETVISION_ANALYSIS_LLM_MODEL", "llama3"),
            
            # 调试设置
            "save_debug_output": self._get_bool("PETVISION_SAVE_DEBUG_OUTPUT", False),
            "debug_output_dir": os.getenv("PETVISION_DEBUG_OUTPUT_DIR", "debug_outputs"),
            
            # 内存管理
            "clear_memory_after_processing": True,
            "force_garbage_collection": True,
            "gpu_memory_fraction": 0.9
        }
    
    def _get_bool(self, key: str, default: bool) -> bool:
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes', 'on')
    
    @classmethod
    def from_file(cls, config_path: str = None) -> "Config":
        return cls()
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)
    
    def update(self, config_dict: dict):
        """更新配置。"""
        self.config.update(config_dict)
    
    def get_api_key(self, model_type: str) -> Optional[str]:
        if model_type.lower() == "vlm":
            return self.config.get("vlm_api_key")
        elif model_type.lower() == "llm":
            return self.config.get("llm_api_key")
        return self.config.get("vlm_api_key") or self.config.get("llm_api_key")
    
    @property
    def llm_mode(self) -> str:
        return self.config.get("llm_mode", "local")
    
    @property
    def vlm_mode(self) -> str:
        return self.config.get("vlm_mode", "local")
