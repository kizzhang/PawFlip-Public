"""
健康数据相关 API 路由
处理健康数据记录和趋势分析
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from auth import get_current_user_id
from services.pet_service import pet_service
from services.ai_service import ai_service
from base_models import (
    HealthRecordCreate, HealthRecordResponse, HealthTrendResponse,
    SuccessResponse
)

router = APIRouter(prefix="/health", tags=["健康数据"])


# ===========================================
# 记录健康数据
# ===========================================

@router.post(
    "/record/{pet_id}",
    response_model=HealthRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="记录健康数据",
    description="为宠物记录一条健康数据"
)
async def record_health_data(
    pet_id: str,
    health_data: HealthRecordCreate,
    user_id: str = Depends(get_current_user_id)
):
    """
    记录健康数据
    
    可以记录以下数据（都是可选的）：
    - **heart_rate**: 心率 (BPM)
    - **steps**: 步数
    - **sleep_hours**: 睡眠时长（小时）
    - **calories**: 消耗热量 (kcal)
    - **activity_minutes**: 活动时长（分钟）
    """
    try:
        # 确保 pet_id 一致
        health_data.pet_id = pet_id
        return await pet_service.record_health_data(pet_id, user_id, health_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ===========================================
# 获取健康趋势
# ===========================================

@router.get(
    "/trend/{pet_id}",
    response_model=HealthTrendResponse,
    summary="获取健康趋势",
    description="获取宠物的健康数据趋势"
)
async def get_health_trend(
    pet_id: str,
    period: str = Query("week", description="时间周期: week/month/year"),
    metric: str = Query("activity", description="指标类型: activity/sleep/heartRate/calories"),
    user_id: str = Depends(get_current_user_id)
):
    """
    获取健康趋势数据
    
    - **pet_id**: 宠物ID
    - **period**: 时间周期
      - week: 最近一周
      - month: 最近一月
      - year: 最近一年
    - **metric**: 指标类型
      - activity: 活动量
      - sleep: 睡眠
      - heartRate: 心率
      - calories: 热量消耗
    """
    # 验证参数
    if period not in ["week", "month", "year"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的时间周期，请使用 week/month/year"
        )
    
    if metric not in ["activity", "sleep", "heartRate", "calories"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的指标类型，请使用 activity/sleep/heartRate/calories"
        )
    
    try:
        return await pet_service.get_health_trend(pet_id, user_id, period, metric)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ===========================================
# AI 健康建议
# ===========================================

@router.get(
    "/advice/{pet_id}",
    summary="获取 AI 健康建议",
    description="根据宠物的健康数据获取 AI 生成的健康建议"
)
async def get_health_advice(
    pet_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    获取 AI 健康建议
    
    AI 会分析宠物的健康数据，提供个性化的健康建议
    """
    # 获取宠物信息
    pet = await pet_service.get_pet(pet_id, user_id)
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="宠物不存在或无权访问"
        )
    
    # 构建健康数据
    health_data = {
        "heart_rate": 72,  # 模拟数据
        "steps": pet.steps,
        "sleep_hours": 7.5,
        "calories": 350
    }
    
    pet_info = {
        "name": pet.name,
        "breed": pet.breed,
        "age": pet.age
    }
    
    try:
        advice = await ai_service.generate_health_advice(health_data, pet_info)
        return {
            "pet_id": pet_id,
            "advice": advice,
            "health_score": pet.health_score
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成健康建议失败: {str(e)}"
        )


# ===========================================
# 获取实时状态
# ===========================================

@router.get(
    "/status/{pet_id}",
    summary="获取实时状态",
    description="获取宠物的实时健康状态"
)
async def get_realtime_status(
    pet_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    获取宠物的实时状态
    
    返回当前的健康分数、步数、电量等信息
    """
    pet = await pet_service.get_pet(pet_id, user_id)
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="宠物不存在或无权访问"
        )
    
    return {
        "pet_id": pet_id,
        "name": pet.name,
        "battery": pet.battery,
        "health_score": pet.health_score,
        "steps": pet.steps,
        "next_feeding": pet.next_feeding,
        "status": "在线" if pet.battery > 0 else "离线"
    }
