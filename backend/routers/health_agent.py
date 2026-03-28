"""
Health Agent API 路由
处理宠物健康 AI 助手的对话管理
基于 Google ADK 构建
"""

import uuid
import random
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from auth import get_current_user_id
from database import db, Tables
from services.adk_health_service import adk_health_service
from models.health_agent import (
    HealthAgentChatRequest,
    HealthAgentChatResponse,
    CreateConversationRequest,
    CreateConversationResponse,
    ConversationListResponse,
    ConversationDetail,
)

router = APIRouter(prefix="/health-agent", tags=["Health Agent"])


# ===========================================
# 获取健康趋势数据
# ===========================================

@router.get(
    "/trends/{pet_id}",
    summary="获取健康趋势数据",
    description="获取宠物的健康趋势数据用于图表展示"
)
async def get_health_trends(
    pet_id: str,
    range: str = "week",  # week, month, year
    user_id: str = Depends(get_current_user_id)
):
    """
    获取健康趋势数据
    
    - **pet_id**: 宠物 ID
    - **range**: 时间范围 (week/month/year)
    """
    try:
        # 验证宠物归属
        pet = await db.select_one("pets", {"id": pet_id, "user_id": user_id})
        if not pet:
            raise HTTPException(status_code=404, detail="宠物不存在")
        
        # 根据范围确定天数
        days_map = {"week": 7, "month": 30, "year": 365}
        days = days_map.get(range, 7)
        
        # 获取健康记录
        records = await db.select(
            Tables.HEALTH_RECORDS,
            columns="heart_rate, steps, sleep_hours, calories, activity_minutes, created_at",
            filters={"pet_id": pet_id},
            order_by="created_at.desc",
            limit=days
        )
        
        # 反转顺序（从旧到新）
        records.reverse()
        
        if not records:
            return {
                "activity": [],
                "sleep": [],
                "heartRate": [],
                "calories": [],
                "summary": None
            }
        
        # 格式化数据
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        
        def format_label(date_str: str, range_type: str) -> str:
            from datetime import datetime as dt_class
            date_obj = dt_class.fromisoformat(date_str.replace("Z", "+00:00"))
            if range_type == "week":
                return weekdays[date_obj.weekday()]
            elif range_type == "month":
                return f"{date_obj.day}日"
            else:
                return f"{date_obj.month}月"
        
        # 对于年视图，按月聚合数据
        if range == "year":
            from collections import defaultdict
            monthly_data = defaultdict(lambda: {"activity": [], "sleep": [], "heart_rate": [], "calories": []})
            
            for r in records:
                from datetime import datetime as dt_class
                date_obj = dt_class.fromisoformat(r["created_at"].replace("Z", "+00:00"))
                month_key = f"{date_obj.month}月"
                monthly_data[month_key]["activity"].append(r.get("activity_minutes") or 0)
                monthly_data[month_key]["sleep"].append(r.get("sleep_hours") or 0)
                monthly_data[month_key]["heart_rate"].append(r.get("heart_rate") or 0)
                monthly_data[month_key]["calories"].append(r.get("calories") or 0)
            
            # 按月份排序
            months_order = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]
            sorted_months = [m for m in months_order if m in monthly_data]
            
            activity_data = [{"name": m, "value": round(sum(monthly_data[m]["activity"]) / len(monthly_data[m]["activity"]))} for m in sorted_months]
            sleep_data = [{"name": m, "value": round(sum(monthly_data[m]["sleep"]) / len(monthly_data[m]["sleep"]), 1)} for m in sorted_months]
            heart_rate_data = [{"name": m, "value": round(sum(monthly_data[m]["heart_rate"]) / len(monthly_data[m]["heart_rate"]))} for m in sorted_months]
            calories_data = [{"name": m, "value": round(sum(monthly_data[m]["calories"]) / len(monthly_data[m]["calories"]))} for m in sorted_months]
        else:
            activity_data = []
            sleep_data = []
            heart_rate_data = []
            calories_data = []
            
            for r in records:
                label = format_label(r["created_at"], range)
                activity_data.append({"name": label, "value": r.get("activity_minutes") or 0})
                sleep_data.append({"name": label, "value": r.get("sleep_hours") or 0})
                heart_rate_data.append({"name": label, "value": r.get("heart_rate") or 0})
                calories_data.append({"name": label, "value": r.get("calories") or 0})
        
        # 计算摘要
        total_records = len(records)
        summary = {
            "avgActivity": round(sum(r.get("activity_minutes") or 0 for r in records) / total_records, 1),
            "avgSleep": round(sum(r.get("sleep_hours") or 0 for r in records) / total_records, 1),
            "avgHeartRate": round(sum(r.get("heart_rate") or 0 for r in records) / total_records, 1),
            "totalCalories": sum(r.get("calories") or 0 for r in records),
            "totalSteps": sum(r.get("steps") or 0 for r in records),
        }
        
        return {
            "activity": activity_data,
            "sleep": sleep_data,
            "heartRate": heart_rate_data,
            "calories": calories_data,
            "summary": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取趋势数据失败: {str(e)}"
        )


# ===========================================
# 发送消息
# ===========================================

@router.post(
    "/chat",
    response_model=HealthAgentChatResponse,
    summary="发送消息",
    description="向 AI 健康助手发送消息"
)
async def chat(
    request: HealthAgentChatRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    发送消息到 AI 健康助手
    
    - **message**: 用户消息（必填）
    - **pet_id**: 宠物 ID（必填）
    - **conversation_id**: 对话 ID（可选，不传则创建新对话）
    
    返回:
    - **conversation_id**: 对话 ID
    - **message_id**: 消息 ID
    - **response**: AI 响应
    - **suggestions**: 推荐的后续问题
    """
    try:
        response = await adk_health_service.chat(
            user_id=user_id,
            pet_id=request.pet_id,
            message=request.message,
            conversation_id=request.conversation_id
        )
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务错误: {str(e)}"
        )


# ===========================================
# 获取对话列表
# ===========================================

@router.get(
    "/conversations",
    response_model=ConversationListResponse,
    summary="获取对话列表",
    description="获取当前用户的所有对话"
)
async def get_conversations(
    limit: int = 20,
    user_id: str = Depends(get_current_user_id)
):
    """
    获取用户的对话列表
    
    - **limit**: 返回数量限制（默认 20）
    
    返回对话列表，按更新时间倒序排列
    """
    try:
        conversations = await adk_health_service.get_conversations(
            user_id=user_id,
            limit=limit
        )
        return ConversationListResponse(
            conversations=conversations,
            total=len(conversations)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取对话列表失败: {str(e)}"
        )


# ===========================================
# 获取对话详情
# ===========================================

@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetail,
    summary="获取对话详情",
    description="获取指定对话的详细信息和所有消息"
)
async def get_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    获取对话详情
    
    - **conversation_id**: 对话 ID
    
    返回对话的完整信息，包括所有消息和关键信息
    """
    try:
        detail = await adk_health_service.get_conversation_detail(
            conversation_id=conversation_id,
            user_id=user_id
        )
        return detail
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取对话详情失败: {str(e)}"
        )


# ===========================================
# 创建新对话
# ===========================================

@router.post(
    "/conversations",
    response_model=CreateConversationResponse,
    summary="创建新对话",
    description="创建一个新的对话"
)
async def create_conversation(
    request: CreateConversationRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    创建新对话
    
    - **pet_id**: 宠物 ID（必填）
    - **initial_message**: 初始消息（可选）
    
    返回新创建的对话 ID
    """
    try:
        conversation_id = await adk_health_service.create_conversation(
            user_id=user_id,
            pet_id=request.pet_id,
            initial_message=request.initial_message
        )
        return CreateConversationResponse(
            conversation_id=conversation_id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建对话失败: {str(e)}"
        )


# ===========================================
# 生成 Mock 健康数据
# ===========================================

@router.post(
    "/mock-data/{pet_id}",
    summary="生成 Mock 健康数据",
    description="为指定宠物生成模拟健康数据和日记"
)
async def generate_mock_data(
    pet_id: str,
    days: int = 365,  # 默认生成一年数据
    user_id: str = Depends(get_current_user_id)
):
    """
    生成模拟数据用于测试
    
    - **days**: 生成天数（默认 365 天）
    - 健康记录（心率、步数、睡眠、卡路里）
    - 日记记录
    """
    try:
        # 验证宠物归属
        pet = await db.select_one("pets", {"id": pet_id, "user_id": user_id})
        if not pet:
            raise HTTPException(status_code=404, detail="宠物不存在")
        
        # 删除旧的 mock 数据
        db.client.table(Tables.HEALTH_RECORDS).delete().eq("pet_id", pet_id).execute()
        db.client.table(Tables.DIARY_ENTRIES).delete().eq("pet_id", pet_id).execute()
        
        # 生成健康数据
        health_records = []
        now = datetime.utcnow()
        
        for i in range(days):
            day = now - timedelta(days=days-1-i)
            # 模拟真实的波动
            base_hr = 72
            base_steps = 8000
            base_sleep = 8.0
            base_calories = 320
            
            # 周末活动量更高
            is_weekend = day.weekday() >= 5
            activity_boost = 1.3 if is_weekend else 1.0
            
            # 季节性变化（夏天活动更多）
            month = day.month
            season_boost = 1.2 if month in [5, 6, 7, 8] else 1.0
            
            record = {
                "id": str(uuid.uuid4()),
                "pet_id": pet_id,
                "heart_rate": base_hr + random.randint(-8, 12),
                "steps": int((base_steps + random.randint(-2000, 3000)) * activity_boost * season_boost),
                "sleep_hours": round(base_sleep + random.uniform(-1.5, 1.0), 1),
                "calories": int((base_calories + random.randint(-50, 80)) * activity_boost * season_boost),
                "activity_minutes": int((45 + random.randint(-15, 30)) * activity_boost * season_boost),
                "created_at": day.isoformat()
            }
            health_records.append(record)
        
        # 批量插入健康数据（分批避免超时）
        batch_size = 100
        for i in range(0, len(health_records), batch_size):
            batch = health_records[i:i+batch_size]
            db.client.table(Tables.HEALTH_RECORDS).insert(batch).execute()
        
        # 生成日记记录（每周 2-3 条）
        diary_templates = [
            {"title": "公园散步", "content": f"{pet['name']}今天在公园玩得很开心，追了好多蝴蝶！", "type": "activity"},
            {"title": "食欲很好", "content": f"{pet['name']}今天把饭都吃光了，还想要更多零食。", "type": "feeding"},
            {"title": "睡眠充足", "content": f"{pet['name']}昨晚睡得很香，早上精神特别好。", "type": "health"},
            {"title": "遇到新朋友", "content": f"{pet['name']}在小区遇到了一只金毛，玩了好久。", "type": "social"},
            {"title": "定期检查", "content": f"带{pet['name']}去做了常规检查，一切正常！", "type": "health"},
            {"title": "洗澡日", "content": f"{pet['name']}今天洗了澡，毛发特别蓬松柔软。", "type": "activity"},
            {"title": "学会新技能", "content": f"{pet['name']}学会了握手，太聪明了！", "type": "activity"},
        ]
        
        diary_entries = []
        for i in range(min(days // 3, 100)):  # 大约每 3 天一条，最多 100 条
            day = now - timedelta(days=i*3 + random.randint(0, 2))
            template = random.choice(diary_templates)
            entry = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "pet_id": pet_id,
                "title": template["title"],
                "content": template["content"],
                "type": template["type"],
                "status": "正常",
                "created_at": day.isoformat()
            }
            diary_entries.append(entry)
        
        if diary_entries:
            db.client.table(Tables.DIARY_ENTRIES).insert(diary_entries).execute()
        
        return {
            "message": "Mock 数据生成成功",
            "health_records": len(health_records),
            "diary_entries": len(diary_entries)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成数据失败: {str(e)}"
        )
