"""
日记相关 API 路由
处理日记的 CRUD 和 AI 生成
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional

from auth import get_current_user_id
from services.diary_service import diary_service
from base_models import (
    DiaryEntryCreate, DiaryEntryResponse, DiaryEntryType,
    SuccessResponse
)

router = APIRouter(prefix="/diary", tags=["宠物日记"])


# ===========================================
# 创建日记条目
# ===========================================

@router.post(
    "",
    response_model=DiaryEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建日记",
    description="手动创建一条日记记录"
)
async def create_diary_entry(
    diary_data: DiaryEntryCreate,
    user_id: str = Depends(get_current_user_id)
):
    """
    创建日记条目
    
    - **pet_id**: 宠物ID（必填）
    - **title**: 标题（必填）
    - **content**: 内容（必填）
    - **type**: 类型 (activity/feeding/health/social)
    - **image_url**: 图片URL（可选）
    - **video_url**: 视频URL（可选）
    """
    return await diary_service.create_diary_entry(user_id, diary_data)


# ===========================================
# 获取宠物的日记列表
# ===========================================

@router.get(
    "/pet/{pet_id}",
    response_model=List[DiaryEntryResponse],
    summary="获取日记列表",
    description="获取指定宠物的日记列表"
)
async def get_pet_diary_entries(
    pet_id: str,
    entry_type: Optional[DiaryEntryType] = Query(None, description="按类型过滤"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    user_id: str = Depends(get_current_user_id)
):
    """
    获取宠物的日记列表
    
    - **pet_id**: 宠物ID
    - **entry_type**: 可选，按类型过滤 (activity/feeding/health/social)
    - **limit**: 返回数量，默认20，最大100
    """
    return await diary_service.get_pet_diary_entries(
        pet_id, user_id, entry_type, limit
    )


# ===========================================
# 获取单条日记
# ===========================================

@router.get(
    "/{entry_id}",
    response_model=DiaryEntryResponse,
    summary="获取日记详情",
    description="获取单条日记的详细信息"
)
async def get_diary_entry(
    entry_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    获取单条日记详情
    """
    entry = await diary_service.get_diary_entry(entry_id, user_id)
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="日记不存在或无权访问"
        )
    
    return entry


# ===========================================
# 删除日记
# ===========================================

@router.delete(
    "/{entry_id}",
    response_model=SuccessResponse,
    summary="删除日记",
    description="删除指定的日记条目"
)
async def delete_diary_entry(
    entry_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    删除日记条目
    """
    success = await diary_service.delete_diary_entry(entry_id, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="日记不存在或无权访问"
        )
    
    return SuccessResponse(message="日记已删除")


# ===========================================
# AI 生成日记
# ===========================================

@router.post(
    "/generate/{pet_id}",
    response_model=DiaryEntryResponse,
    summary="AI 生成日记",
    description="使用 AI 为宠物生成一篇日记"
)
async def generate_ai_diary(
    pet_id: str,
    prompt: Optional[str] = Query(None, description="可选的生成提示"),
    user_id: str = Depends(get_current_user_id)
):
    """
    使用 AI 生成日记
    
    - **pet_id**: 宠物ID
    - **prompt**: 可选的提示词，用于引导 AI 生成特定内容
    """
    try:
        return await diary_service.generate_ai_diary(user_id, pet_id, prompt)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ===========================================
# 获取周总结
# ===========================================

@router.get(
    "/summary/{pet_id}",
    summary="获取周总结",
    description="获取宠物本周的日记总结"
)
async def get_weekly_summary(
    pet_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    获取本周日记总结
    
    使用 AI 分析本周的日记，生成温馨的总结
    """
    try:
        summary = await diary_service.get_weekly_summary(pet_id, user_id)
        return {"summary": summary}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
