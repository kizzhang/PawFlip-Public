"""
宠物服务模块
处理宠物相关的业务逻辑
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import random

from database import db, Tables
from base_models import (
    PetCreate, PetUpdate, PetResponse,
    HealthRecordCreate, HealthRecordResponse, HealthTrendResponse
)

logger = logging.getLogger(__name__)


class PetService:
    """
    宠物服务类
    处理宠物的 CRUD 和健康数据管理
    """
    
    # ===========================================
    # 宠物 CRUD 操作
    # ===========================================
    
    async def create_pet(
        self,
        user_id: str,
        pet_data: PetCreate
    ) -> PetResponse:
        """
        创建新宠物
        
        Args:
            user_id: 用户ID
            pet_data: 宠物信息
            
        Returns:
            创建的宠物信息
        """
        try:
            new_pet = await db.insert(Tables.PETS, {
                "user_id": user_id,
                "name": pet_data.name,
                "breed": pet_data.breed,
                "age": pet_data.age,
                "avatar_url": pet_data.avatar_url,
                "battery": 100,
                "health_score": 100,
                "steps": 0,
                "next_feeding": "18:00"
            })
            
            logger.info(f"创建宠物成功: {new_pet['id']}")
            return self._to_pet_response(new_pet)
            
        except Exception as e:
            logger.error(f"创建宠物失败: {e}")
            raise
    
    async def create_pet_with_3d_model(
        self,
        user_id: str,
        pet_data: PetCreate,
        image_path: Optional[str] = None
    ) -> tuple[PetResponse, Optional[Dict[str, Any]]]:
        """
        创建新宠物并生成 3D 模型
        
        Args:
            user_id: 用户ID
            pet_data: 宠物信息
            image_path: 宠物照片路径（用于生成 3D 模型）
            
        Returns:
            (宠物信息, 3D 模型结果)
        """
        from .model_3d_service import model_3d_service
        
        try:
            # 1. 创建宠物记录
            new_pet = await db.insert(Tables.PETS, {
                "user_id": user_id,
                "name": pet_data.name,
                "breed": pet_data.breed,
                "age": pet_data.age,
                "avatar_url": pet_data.avatar_url,
                "battery": 100,
                "health_score": 100,
                "steps": 0,
                "next_feeding": "18:00"
            })
            
            logger.info(f"创建宠物成功: {new_pet['id']}")
            
            # 2. 如果提供了照片，生成 3D 模型
            model_result = None
            if image_path:
                logger.info(f"开始为 {pet_data.name} 生成 3D 模型...")
                
                model_result = await model_3d_service.generate_pet_model(
                    image_path=image_path,
                    pet_name=pet_data.name,
                    pet_breed=pet_data.breed
                )
                
                # 如果生成成功，更新宠物记录
                if model_result.get("success"):
                    await db.update(
                        Tables.PETS,
                        {"id": new_pet["id"]},
                        {
                            "model_3d_url": model_result.get("model_url"),
                            "model_3d_preview": model_result.get("preview_url")
                        }
                    )
                    
                    # 更新返回的宠物数据
                    new_pet["model_3d_url"] = model_result.get("model_url")
                    new_pet["model_3d_preview"] = model_result.get("preview_url")
            
            return self._to_pet_response(new_pet), model_result
            
        except Exception as e:
            logger.error(f"创建宠物失败: {e}")
            raise
    
    async def get_pet(
        self,
        pet_id: str,
        user_id: Optional[str] = None
    ) -> Optional[PetResponse]:
        """
        获取宠物信息
        
        Args:
            pet_id: 宠物ID
            user_id: 可选，验证所有权
            
        Returns:
            宠物信息，不存在则返回 None
        """
        filters = {"id": pet_id}
        if user_id:
            filters["user_id"] = user_id
        
        pet = await db.select_one(Tables.PETS, filters)
        
        if not pet:
            return None
        
        return self._to_pet_response(pet)
    
    async def get_user_pets(self, user_id: str) -> List[PetResponse]:
        """
        获取用户的所有宠物
        
        Args:
            user_id: 用户ID
            
        Returns:
            宠物列表
        """
        pets = await db.select(
            Tables.PETS,
            filters={"user_id": user_id},
            order_by="created_at.desc"
        )
        
        return [self._to_pet_response(pet) for pet in pets]
    
    async def update_pet(
        self,
        pet_id: str,
        user_id: str,
        pet_data: PetUpdate
    ) -> Optional[PetResponse]:
        """
        更新宠物信息
        
        Args:
            pet_id: 宠物ID
            user_id: 用户ID（验证所有权）
            pet_data: 更新数据
            
        Returns:
            更新后的宠物信息
        """
        # 验证所有权
        existing = await self.get_pet(pet_id, user_id)
        if not existing:
            return None
        
        # 构建更新数据
        update_data = {}
        if pet_data.name is not None:
            update_data["name"] = pet_data.name
        if pet_data.breed is not None:
            update_data["breed"] = pet_data.breed
        if pet_data.age is not None:
            update_data["age"] = pet_data.age
        if pet_data.avatar_url is not None:
            update_data["avatar_url"] = pet_data.avatar_url
        
        if not update_data:
            return existing
        
        updated = await db.update(
            Tables.PETS,
            {"id": pet_id},
            update_data
        )
        
        return self._to_pet_response(updated)
    
    async def delete_pet(
        self,
        pet_id: str,
        user_id: str
    ) -> bool:
        """
        删除宠物
        
        Args:
            pet_id: 宠物ID
            user_id: 用户ID（验证所有权）
            
        Returns:
            是否删除成功
        """
        # 验证所有权
        existing = await self.get_pet(pet_id, user_id)
        if not existing:
            return False
        
        return await db.delete(Tables.PETS, {"id": pet_id})
    
    # ===========================================
    # 健康数据管理
    # ===========================================
    
    async def record_health_data(
        self,
        pet_id: str,
        user_id: str,
        health_data: HealthRecordCreate
    ) -> HealthRecordResponse:
        """
        记录健康数据
        
        Args:
            pet_id: 宠物ID
            user_id: 用户ID
            health_data: 健康数据
            
        Returns:
            记录的健康数据
        """
        # 验证宠物所有权
        pet = await self.get_pet(pet_id, user_id)
        if not pet:
            raise ValueError("宠物不存在或无权访问")
        
        record = await db.insert(Tables.HEALTH_RECORDS, {
            "pet_id": pet_id,
            "heart_rate": health_data.heart_rate,
            "steps": health_data.steps,
            "sleep_hours": health_data.sleep_hours,
            "calories": health_data.calories,
            "activity_minutes": health_data.activity_minutes
        })
        
        # 更新宠物的实时状态
        update_data = {}
        if health_data.steps is not None:
            update_data["steps"] = health_data.steps
        if health_data.heart_rate is not None:
            # 根据心率计算健康分数（简化逻辑）
            health_score = self._calculate_health_score(health_data)
            update_data["health_score"] = health_score
        
        if update_data:
            await db.update(Tables.PETS, {"id": pet_id}, update_data)
        
        return HealthRecordResponse(
            id=record["id"],
            pet_id=record["pet_id"],
            heart_rate=record.get("heart_rate"),
            steps=record.get("steps"),
            sleep_hours=record.get("sleep_hours"),
            calories=record.get("calories"),
            activity_minutes=record.get("activity_minutes"),
            recorded_at=record["created_at"]
        )
    
    async def get_health_trend(
        self,
        pet_id: str,
        user_id: str,
        period: str = "week",
        metric: str = "activity"
    ) -> HealthTrendResponse:
        """
        获取健康趋势数据
        
        Args:
            pet_id: 宠物ID
            user_id: 用户ID
            period: 时间周期 (week/month/year)
            metric: 指标类型 (activity/sleep/heartRate/calories)
            
        Returns:
            健康趋势数据
        """
        # 验证宠物所有权
        pet = await self.get_pet(pet_id, user_id)
        if not pet:
            raise ValueError("宠物不存在或无权访问")
        
        # 计算时间范围
        now = datetime.now()
        if period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            start_date = now - timedelta(days=30)
        else:  # year
            start_date = now - timedelta(days=365)
        
        # 查询健康记录
        # 注意：这里简化处理，实际应该使用日期过滤
        records = await db.select(
            Tables.HEALTH_RECORDS,
            filters={"pet_id": pet_id},
            order_by="created_at.asc",
            limit=100
        )
        
        # 如果没有真实数据，生成模拟数据
        if not records:
            data = self._generate_mock_trend_data(period, metric)
        else:
            data = self._process_health_records(records, period, metric)
        
        # 计算摘要
        summary = self._calculate_trend_summary(data, metric)
        
        return HealthTrendResponse(
            period=period,
            data=data,
            summary=summary
        )
    
    # ===========================================
    # 辅助方法
    # ===========================================
    
    def _to_pet_response(self, pet: Dict[str, Any]) -> PetResponse:
        """将数据库记录转换为响应模型"""
        return PetResponse(
            id=pet["id"],
            user_id=pet["user_id"],
            name=pet["name"],
            breed=pet["breed"],
            age=pet["age"],
            avatar_url=pet.get("avatar_url"),
            created_at=pet["created_at"],
            battery=pet.get("battery", 100),
            health_score=pet.get("health_score", 100),
            steps=pet.get("steps", 0),
            next_feeding=pet.get("next_feeding"),
            model_3d_url=pet.get("model_3d_url"),
            model_3d_preview=pet.get("model_3d_preview")
        )
    
    def _calculate_health_score(self, health_data: HealthRecordCreate) -> int:
        """
        计算健康分数
        简化的计算逻辑
        """
        score = 100
        
        # 根据心率调整
        if health_data.heart_rate:
            if health_data.heart_rate < 60 or health_data.heart_rate > 120:
                score -= 10
        
        # 根据活动量调整
        if health_data.activity_minutes:
            if health_data.activity_minutes < 30:
                score -= 5
            elif health_data.activity_minutes > 60:
                score += 5
        
        # 根据睡眠调整
        if health_data.sleep_hours:
            if health_data.sleep_hours < 6 or health_data.sleep_hours > 10:
                score -= 5
        
        return max(0, min(100, score))
    
    def _generate_mock_trend_data(
        self,
        period: str,
        metric: str
    ) -> List[Dict[str, Any]]:
        """
        生成模拟趋势数据
        用于演示目的
        """
        data = []
        
        if period == "week":
            labels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        elif period == "month":
            labels = [f"{i+1}日" for i in range(30)]
        else:
            labels = ["1月", "2月", "3月", "4月", "5月", "6月", 
                     "7月", "8月", "9月", "10月", "11月", "12月"]
        
        # 根据指标类型生成不同范围的数据
        ranges = {
            "activity": (30, 70),
            "sleep": (6.0, 9.0),
            "heartRate": (65, 85),
            "calories": (250, 450)
        }
        
        min_val, max_val = ranges.get(metric, (0, 100))
        
        for label in labels:
            if metric == "sleep":
                value = round(random.uniform(min_val, max_val), 1)
            else:
                value = random.randint(int(min_val), int(max_val))
            
            data.append({
                "name": label,
                "value": value
            })
        
        return data
    
    def _process_health_records(
        self,
        records: List[Dict[str, Any]],
        period: str,
        metric: str
    ) -> List[Dict[str, Any]]:
        """
        处理健康记录为趋势数据
        """
        # 简化处理：直接返回最近的记录
        metric_map = {
            "activity": "activity_minutes",
            "sleep": "sleep_hours",
            "heartRate": "heart_rate",
            "calories": "calories"
        }
        
        field = metric_map.get(metric, "activity_minutes")
        
        data = []
        for i, record in enumerate(records[-7:]):  # 最近7条
            data.append({
                "name": f"Day {i+1}",
                "value": record.get(field, 0) or 0
            })
        
        return data
    
    def _calculate_trend_summary(
        self,
        data: List[Dict[str, Any]],
        metric: str
    ) -> Dict[str, Any]:
        """
        计算趋势摘要
        """
        if not data:
            return {"average": 0, "trend": "stable", "change": "0%"}
        
        values = [d["value"] for d in data]
        avg = sum(values) / len(values)
        
        # 计算趋势
        if len(values) >= 2:
            first_half = sum(values[:len(values)//2]) / (len(values)//2)
            second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
            
            if second_half > first_half * 1.05:
                trend = "up"
                change = f"+{((second_half - first_half) / first_half * 100):.1f}%"
            elif second_half < first_half * 0.95:
                trend = "down"
                change = f"{((second_half - first_half) / first_half * 100):.1f}%"
            else:
                trend = "stable"
                change = "0%"
        else:
            trend = "stable"
            change = "0%"
        
        return {
            "average": round(avg, 1),
            "trend": trend,
            "change": change
        }


# 导出宠物服务实例
pet_service = PetService()
