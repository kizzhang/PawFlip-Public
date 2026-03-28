"""
统一 API 客户端工厂

支持多个 LLM 提供商，通过 OpenAI SDK 统一调用。
"""

import logging
from typing import Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# 提供商配置
PROVIDERS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "requires_api_key": True
    },
    "google": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "requires_api_key": True
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1",
        "requires_api_key": True
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "requires_api_key": True
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "requires_api_key": True
    },
    "together": {
        "base_url": "https://api.together.xyz/v1",
        "requires_api_key": True
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "requires_api_key": True
    },
    "custom": {
        "base_url": None,
        "requires_api_key": False
    }
}


class APIClientFactory:
    """API 客户端工厂类。"""
    
    @classmethod
    def create_client(
        cls,
        provider: str = "openai",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ) -> AsyncOpenAI:
        """创建 OpenAI 兼容的异步客户端。"""
        provider = provider.lower()
        
        if provider not in PROVIDERS:
            logger.warning(f"未知提供商 '{provider}'，使用 custom")
            provider = "custom"
        
        config = PROVIDERS[provider]
        final_base_url = base_url or config["base_url"]
        
        if not final_base_url:
            raise ValueError(f"提供商 '{provider}' 需要指定 base_url")
        
        if config["requires_api_key"] and not api_key:
            logger.warning(f"提供商 '{provider}' 通常需要 API 密钥")
        
        logger.info(f"创建 API 客户端: {provider}")
        
        return AsyncOpenAI(
            api_key=api_key or "dummy-key",
            base_url=final_base_url,
            **kwargs
        )
    
    @classmethod
    def list_providers(cls) -> list:
        return list(PROVIDERS.keys())
    
    @classmethod
    def get_provider_info(cls, provider: str) -> dict:
        return PROVIDERS.get(provider.lower(), {"error": "未知提供商"})


def create_openai_client(api_key: str, **kwargs) -> AsyncOpenAI:
    return APIClientFactory.create_client("openai", api_key=api_key, **kwargs)


def create_google_client(api_key: str, **kwargs) -> AsyncOpenAI:
    return APIClientFactory.create_client("google", api_key=api_key, **kwargs)


def create_custom_client(base_url: str, api_key: Optional[str] = None, **kwargs) -> AsyncOpenAI:
    return APIClientFactory.create_client("custom", base_url=base_url, api_key=api_key, **kwargs)
