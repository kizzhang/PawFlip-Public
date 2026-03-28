"""
AI 服务模块
提供多种 AI 提供商的统一接口
支持 Google Gemini、OpenAI 等
"""

import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import aiohttp

from config import settings

logger = logging.getLogger(__name__)


# ===========================================
# AI 提供商抽象基类
# ===========================================

class AIProvider(ABC):
    """AI 提供商抽象基类"""
    
    @abstractmethod
    async def chat(
        self,
        message: str,
        history: List[Dict[str, str]] = None,
        system_prompt: str = None
    ) -> str:
        """
        发送聊天消息并获取响应
        
        Args:
            message: 用户消息
            history: 对话历史
            system_prompt: 系统提示词
            
        Returns:
            AI 响应文本
        """
        pass
    
    @abstractmethod
    async def generate_story(
        self,
        video_analysis: Dict[str, Any]
    ) -> str:
        """
        根据视频分析结果生成故事
        
        Args:
            video_analysis: 视频分析结果
            
        Returns:
            生成的故事文本
        """
        pass


# ===========================================
# Google Gemini 实现
# ===========================================

class GeminiProvider(AIProvider):
    """Google Gemini AI 提供商"""
    
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.model = settings.GEMINI_MODEL
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        
        if not self.api_key:
            logger.warning("Google API Key 未配置")
    
    async def chat(
        self,
        message: str,
        history: List[Dict[str, str]] = None,
        system_prompt: str = None
    ) -> str:
        """使用 Gemini 进行对话"""
        
        if not self.api_key:
            raise ValueError("Google API Key 未配置")
        
        # 构建消息内容
        contents = []
        
        # 添加历史消息
        if history:
            for msg in history:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })
        
        # 添加当前消息
        contents.append({
            "role": "user",
            "parts": [{"text": message}]
        })
        
        # 构建请求
        url = f"{self.base_url}/models/{self.model}:generateContent"
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1024
            }
        }
        
        # 添加系统指令
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{url}?key={self.api_key}",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Gemini API 错误: {error_text}")
                        raise Exception(f"Gemini API 返回错误: {response.status}")
                    
                    result = await response.json()
                    
                    # 提取响应文本
                    candidates = result.get("candidates", [])
                    if candidates:
                        content = candidates[0].get("content", {})
                        parts = content.get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                    
                    return "抱歉，我暂时无法回答。"
                    
        except Exception as e:
            logger.error(f"Gemini 请求失败: {e}")
            raise
    
    async def generate_story(
        self,
        video_analysis: Dict[str, Any]
    ) -> str:
        """使用 Gemini 生成宠物故事"""
        
        # 构建故事生成提示
        prompt = self._build_story_prompt(video_analysis)
        
        system_prompt = """你是一个专业的宠物故事作家。
你需要根据视频分析结果，以宠物的第一人称视角写一个有趣、温馨的故事。
故事应该：
- 使用第一人称（"我"）
- 体现宠物的性格特点
- 包含感官描写（看到、闻到、感受到）
- 语气活泼可爱
- 长度在150-200字左右
"""
        
        return await self.chat(prompt, system_prompt=system_prompt)
    
    def _build_story_prompt(self, analysis: Dict[str, Any]) -> str:
        """构建故事生成提示"""
        
        summary = analysis.get("summary", "")
        objects = ", ".join(analysis.get("detected_objects", []))
        activities = ", ".join(analysis.get("activities", []))
        emotions = ", ".join(analysis.get("emotional_context", []))
        
        prompt = f"""请根据以下视频分析结果，以宠物的第一人称视角写一个故事：

视频摘要：{summary}
看到的物体：{objects}
进行的活动：{activities}
情绪状态：{emotions}

请写一个150-200字的第一人称故事："""
        
        return prompt


# ===========================================
# OpenAI 实现
# ===========================================

class OpenAIProvider(AIProvider):
    """OpenAI GPT 提供商"""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.base_url = "https://api.openai.com/v1"
        
        if not self.api_key:
            logger.warning("OpenAI API Key 未配置")
    
    async def chat(
        self,
        message: str,
        history: List[Dict[str, str]] = None,
        system_prompt: str = None
    ) -> str:
        """使用 OpenAI 进行对话"""
        
        if not self.api_key:
            raise ValueError("OpenAI API Key 未配置")
        
        # 构建消息列表
        messages = []
        
        # 添加系统提示
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # 添加历史消息
        if history:
            for msg in history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # 添加当前消息
        messages.append({
            "role": "user",
            "content": message
        })
        
        # 发送请求
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OpenAI API 错误: {error_text}")
                        raise Exception(f"OpenAI API 返回错误: {response.status}")
                    
                    result = await response.json()
                    
                    choices = result.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "")
                    
                    return "抱歉，我暂时无法回答。"
                    
        except Exception as e:
            logger.error(f"OpenAI 请求失败: {e}")
            raise
    
    async def generate_story(
        self,
        video_analysis: Dict[str, Any]
    ) -> str:
        """使用 OpenAI 生成宠物故事"""
        
        prompt = self._build_story_prompt(video_analysis)
        
        system_prompt = """你是一个专业的宠物故事作家。
你需要根据视频分析结果，以宠物的第一人称视角写一个有趣、温馨的故事。
故事应该使用第一人称，体现宠物的性格特点，包含感官描写，语气活泼可爱。"""
        
        return await self.chat(prompt, system_prompt=system_prompt)
    
    def _build_story_prompt(self, analysis: Dict[str, Any]) -> str:
        """构建故事生成提示"""
        summary = analysis.get("summary", "")
        objects = ", ".join(analysis.get("detected_objects", []))
        activities = ", ".join(analysis.get("activities", []))
        emotions = ", ".join(analysis.get("emotional_context", []))
        
        return f"""请根据以下视频分析结果，以宠物的第一人称视角写一个150-200字的故事：

视频摘要：{summary}
看到的物体：{objects}
进行的活动：{activities}
情绪状态：{emotions}"""


# ===========================================
# AI 服务工厂
# ===========================================

class AIService:
    """
    AI 服务统一接口
    根据配置自动选择合适的 AI 提供商
    """
    
    def __init__(self):
        self.provider = self._get_provider()
    
    def _get_provider(self) -> AIProvider:
        """根据配置获取 AI 提供商"""
        
        provider_name = settings.AI_PROVIDER.lower()
        
        if provider_name == "gemini":
            return GeminiProvider()
        elif provider_name == "openai":
            return OpenAIProvider()
        else:
            # 默认使用 Gemini
            logger.warning(f"未知的 AI 提供商: {provider_name}，使用 Gemini")
            return GeminiProvider()
    
    async def chat(
        self,
        message: str,
        history: List[Dict[str, str]] = None,
        system_prompt: str = None,
        context_type: str = None,
        pet_info: Dict[str, Any] = None
    ) -> str:
        """
        AI 聊天接口
        
        Args:
            message: 用户消息
            history: 对话历史
            system_prompt: 自定义系统提示（可选）
            context_type: 上下文类型 (health, diary, general)
            pet_info: 宠物信息（用于个性化响应）
            
        Returns:
            AI 响应文本
        """
        
        # 如果没有自定义系统提示，根据上下文类型生成
        if not system_prompt:
            system_prompt = self._get_system_prompt(context_type, pet_info)
        
        return await self.provider.chat(message, history, system_prompt)
    
    async def generate_story(
        self,
        video_analysis: Dict[str, Any]
    ) -> str:
        """
        生成宠物故事
        
        Args:
            video_analysis: 视频分析结果
            
        Returns:
            生成的故事文本
        """
        return await self.provider.generate_story(video_analysis)
    
    async def generate_health_advice(
        self,
        health_data: Dict[str, Any],
        pet_info: Dict[str, Any]
    ) -> str:
        """
        生成健康建议
        
        Args:
            health_data: 健康数据
            pet_info: 宠物信息
            
        Returns:
            健康建议文本
        """
        
        prompt = f"""请根据以下宠物健康数据提供专业建议：

宠物信息：
- 名字：{pet_info.get('name', '未知')}
- 品种：{pet_info.get('breed', '未知')}
- 年龄：{pet_info.get('age', '未知')}

健康数据：
- 心率：{health_data.get('heart_rate', '未记录')} BPM
- 今日步数：{health_data.get('steps', '未记录')}
- 睡眠时长：{health_data.get('sleep_hours', '未记录')} 小时
- 消耗热量：{health_data.get('calories', '未记录')} kcal

请提供简洁的健康评估和建议（100字以内）："""
        
        system_prompt = """你是一个专业的宠物健康顾问。
请根据提供的数据给出简洁、专业的健康建议。
如果数据异常，请提醒主人注意并建议就医。"""
        
        return await self.provider.chat(prompt, system_prompt=system_prompt)
    
    def _get_system_prompt(
        self,
        context_type: str = None,
        pet_info: Dict[str, Any] = None
    ) -> str:
        """根据上下文类型生成系统提示"""
        
        pet_name = pet_info.get("name", "宠物") if pet_info else "宠物"
        
        prompts = {
            "health": f"""你是一个专业的宠物健康顾问，名字叫'AI 问诊助手'。
你需要根据用户提供的宠物（{pet_name}）的监测数据（心率、步数、行为）提供健康建议。
语气要亲切、专业。如果用户询问症状，给出初步分析并建议是否需要看兽医。
回答要简短精炼。""",
            
            "diary": f"""你是一个有趣的宠物日记助手。
你帮助用户记录和理解{pet_name}的日常生活。
你可以根据视频或图片描述宠物的活动，并以宠物的视角写有趣的日记。
语气要活泼可爱。""",
            
            "general": f"""你是 PawFlip 智能助手，专门帮助用户照顾他们的宠物。
当前用户的宠物叫{pet_name}。
你可以回答关于宠物护理、健康、训练等方面的问题。
语气要友好、专业。"""
        }
        
        return prompts.get(context_type, prompts["general"])


# 导出 AI 服务实例
ai_service = AIService()
