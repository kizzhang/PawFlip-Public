"""
AI 聊天相关 API 路由
处理 AI 对话和智能助手功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from auth import get_current_user_id
from services.ai_service import ai_service
from services.pet_service import pet_service
from base_models import ChatRequest, ChatResponse

router = APIRouter(prefix="/ai", tags=["AI 助手"])


# ===========================================
# AI 聊天
# ===========================================

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="AI 聊天",
    description="与 AI 助手进行对话"
)
async def chat(
    request: ChatRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    AI 聊天接口
    
    支持多种上下文类型：
    - **health**: 健康咨询模式，AI 会以宠物健康顾问的身份回答
    - **diary**: 日记助手模式，帮助记录和理解宠物日常
    - **general**: 通用模式，回答各种宠物相关问题
    
    参数：
    - **message**: 用户消息（必填）
    - **history**: 对话历史（可选）
    - **pet_id**: 关联的宠物ID（可选，用于个性化响应）
    - **context_type**: 上下文类型（可选）
    """
    # 获取宠物信息（如果提供了 pet_id）
    pet_info = None
    if request.pet_id:
        pet = await pet_service.get_pet(request.pet_id, user_id)
        if pet:
            pet_info = {
                "name": pet.name,
                "breed": pet.breed,
                "age": pet.age
            }
    
    # 转换历史消息格式
    history = None
    if request.history:
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.history
        ]
    
    try:
        # 调用 AI 服务
        response = await ai_service.chat(
            message=request.message,
            history=history,
            context_type=request.context_type,
            pet_info=pet_info
        )
        
        # 生成建议问题
        suggestions = _generate_suggestions(request.context_type)
        
        return ChatResponse(
            message=response,
            suggestions=suggestions
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 服务错误: {str(e)}"
        )


# ===========================================
# 健康问诊
# ===========================================

@router.post(
    "/health-consult",
    response_model=ChatResponse,
    summary="健康问诊",
    description="专门的健康问诊 AI 助手"
)
async def health_consult(
    request: ChatRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    健康问诊接口
    
    专门用于宠物健康咨询的 AI 助手。
    会根据宠物的健康数据提供专业建议。
    """
    # 强制使用健康上下文
    request.context_type = "health"
    
    # 获取宠物信息
    pet_info = None
    if request.pet_id:
        pet = await pet_service.get_pet(request.pet_id, user_id)
        if pet:
            pet_info = {
                "name": pet.name,
                "breed": pet.breed,
                "age": pet.age,
                "health_score": pet.health_score,
                "steps": pet.steps
            }
    
    # 转换历史消息
    history = None
    if request.history:
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.history
        ]
    
    try:
        response = await ai_service.chat(
            message=request.message,
            history=history,
            context_type="health",
            pet_info=pet_info
        )
        
        return ChatResponse(
            message=response,
            suggestions=[
                "分析睡眠异常",
                "查看年度活跃对比",
                "附近兽医推荐"
            ]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 服务错误: {str(e)}"
        )


# ===========================================
# 生成故事
# ===========================================

@router.post(
    "/generate-story",
    summary="生成故事",
    description="根据视频分析结果生成宠物故事"
)
async def generate_story(
    analysis: dict,
    user_id: str = Depends(get_current_user_id)
):
    """
    生成宠物故事
    
    根据视频分析结果，以宠物的第一人称视角生成故事。
    
    参数 analysis 应包含：
    - summary: 视频摘要
    - detected_objects: 检测到的物体列表
    - activities: 活动列表
    - emotional_context: 情绪状态列表
    """
    try:
        story = await ai_service.generate_story(analysis)
        return {"story": story}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"故事生成失败: {str(e)}"
        )


# ===========================================
# 获取 AI 配置
# ===========================================

@router.get(
    "/config",
    summary="获取 AI 配置",
    description="获取当前 AI 服务的配置信息"
)
async def get_ai_config(user_id: str = Depends(get_current_user_id)):
    """
    获取 AI 配置信息
    
    返回当前使用的 AI 提供商和模型信息
    """
    from config import settings
    
    return {
        "provider": settings.AI_PROVIDER,
        "model": settings.GEMINI_MODEL if settings.AI_PROVIDER == "gemini" else settings.OPENAI_MODEL,
        "features": {
            "chat": True,
            "health_consult": True,
            "story_generation": True,
            "video_analysis": True
        }
    }


# ===========================================
# 辅助函数
# ===========================================

def _generate_suggestions(context_type: Optional[str]) -> list:
    """根据上下文类型生成建议问题"""
    
    suggestions_map = {
        "health": [
            "分析睡眠异常",
            "查看年度活跃对比",
            "附近兽医推荐"
        ],
        "diary": [
            "生成今日日记",
            "总结本周活动",
            "分析行为变化"
        ],
        "general": [
            "如何训练宠物",
            "推荐宠物食品",
            "日常护理建议"
        ]
    }
    
    return suggestions_map.get(context_type, suggestions_map["general"])
