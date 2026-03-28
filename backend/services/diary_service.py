"""
日记服务模块
处理宠物日记的创建、管理和 AI 生成
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import random

from database import db, Tables
from base_models import (
    DiaryEntryCreate, DiaryEntryResponse, DiaryEntryType,
    VideoProcessResult
)
from .ai_service import ai_service

logger = logging.getLogger(__name__)


class DiaryService:
    """
    日记服务类
    处理日记的 CRUD 和 AI 生成功能
    """
    
    # ===========================================
    # 日记 CRUD 操作
    # ===========================================
    
    async def create_diary_entry(
        self,
        user_id: str,
        diary_data: DiaryEntryCreate
    ) -> DiaryEntryResponse:
        """
        创建日记条目
        
        Args:
            user_id: 用户ID
            diary_data: 日记数据
            
        Returns:
            创建的日记条目
        """
        try:
            # 生成活动趋势数据（模拟）
            activity_trend = self._generate_activity_trend()
            
            new_entry = await db.insert(Tables.DIARY_ENTRIES, {
                "user_id": user_id,
                "pet_id": diary_data.pet_id,
                "title": diary_data.title,
                "content": diary_data.content,
                "type": diary_data.type.value,
                "image_url": diary_data.image_url,
                "video_url": diary_data.video_url,
                "is_video": diary_data.is_video,
                "duration": diary_data.duration,
                "activity_trend": activity_trend,
                "status": "正常"
            })
            
            logger.info(f"创建日记成功: {new_entry['id']}")
            return self._to_diary_response(new_entry)
            
        except Exception as e:
            logger.error(f"创建日记失败: {e}")
            raise
    
    async def get_diary_entry(
        self,
        entry_id: str,
        user_id: Optional[str] = None
    ) -> Optional[DiaryEntryResponse]:
        """
        获取单个日记条目
        
        Args:
            entry_id: 日记ID
            user_id: 可选，验证所有权
            
        Returns:
            日记条目，不存在则返回 None
        """
        filters = {"id": entry_id}
        if user_id:
            filters["user_id"] = user_id
        
        entry = await db.select_one(Tables.DIARY_ENTRIES, filters)
        
        if not entry:
            return None
        
        return self._to_diary_response(entry)
    
    async def get_pet_diary_entries(
        self,
        pet_id: str,
        user_id: str,
        entry_type: Optional[DiaryEntryType] = None,
        limit: int = 20
    ) -> List[DiaryEntryResponse]:
        """
        获取宠物的日记列表
        
        Args:
            pet_id: 宠物ID
            user_id: 用户ID
            entry_type: 可选，按类型过滤
            limit: 返回数量限制
            
        Returns:
            日记列表
        """
        filters = {
            "pet_id": pet_id,
            "user_id": user_id
        }
        
        if entry_type:
            filters["type"] = entry_type.value
        
        entries = await db.select(
            Tables.DIARY_ENTRIES,
            filters=filters,
            order_by="created_at.desc",
            limit=limit
        )
        
        return [self._to_diary_response(entry) for entry in entries]
    
    async def delete_diary_entry(
        self,
        entry_id: str,
        user_id: str
    ) -> bool:
        """
        删除日记条目
        
        Args:
            entry_id: 日记ID
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        # 验证所有权
        existing = await self.get_diary_entry(entry_id, user_id)
        if not existing:
            return False
        
        return await db.delete(Tables.DIARY_ENTRIES, {"id": entry_id})
    
    # ===========================================
    # AI 日记生成
    # ===========================================
    
    async def generate_diary_from_video(
        self,
        user_id: str,
        pet_id: str,
        video_result: VideoProcessResult,
        video_url: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> DiaryEntryResponse:
        """
        根据视频分析结果生成日记
        
        Args:
            user_id: 用户ID
            pet_id: 宠物ID
            video_result: 视频处理结果
            video_url: 视频URL（可选）
            image_url: 封面图URL（可选）
            
        Returns:
            生成的日记条目
        """
        if not video_result.success:
            raise ValueError("视频处理失败，无法生成日记")
        
        # 从视频分析结果提取信息
        analysis = video_result.video_analysis
        narrative = video_result.narrative
        
        # 生成标题
        title = await self._generate_diary_title(analysis)
        
        # 使用 AI 生成的故事作为内容
        content = narrative.get("story", "") if narrative else ""
        
        if not content:
            # 如果没有故事，使用摘要
            content = analysis.get("summary", "今天发生了有趣的事情！")
        
        # 确定日记类型
        activities = analysis.get("activities", []) if analysis else []
        if any(act in ["eating", "feeding", "进食"] for act in activities):
            entry_type = DiaryEntryType.FEEDING
        else:
            entry_type = DiaryEntryType.ACTIVITY
        
        # 创建日记
        diary_data = DiaryEntryCreate(
            pet_id=pet_id,
            title=title,
            content=content,
            type=entry_type,
            image_url=image_url,
            video_url=video_url,
            is_video=video_url is not None,
            duration=video_result.metadata.get("duration") if video_result.metadata else None
        )
        
        entry = await self.create_diary_entry(user_id, diary_data)
        
        # 保存 AI 分析结果
        if analysis:
            await db.update(
                Tables.DIARY_ENTRIES,
                {"id": entry.id},
                {"ai_analysis": analysis}
            )
            entry.ai_analysis = analysis
        
        return entry
    
    async def generate_ai_diary(
        self,
        user_id: str,
        pet_id: str,
        prompt: Optional[str] = None
    ) -> DiaryEntryResponse:
        """
        使用 AI 生成日记（无视频输入）
        
        Args:
            user_id: 用户ID
            pet_id: 宠物ID
            prompt: 可选的提示词
            
        Returns:
            生成的日记条目
        """
        from .pet_service import pet_service
        
        # 获取宠物信息
        pet = await pet_service.get_pet(pet_id, user_id)
        if not pet:
            raise ValueError("宠物不存在")
        
        # 构建生成提示
        if not prompt:
            prompt = f"请为{pet.name}（{pet.breed}，{pet.age}）写一篇今天的日记"
        
        system_prompt = f"""你是一个可爱的宠物日记作家。
请以{pet.name}的第一人称视角写一篇日记。
日记应该：
- 描述今天发生的有趣事情
- 体现宠物的性格特点
- 语气活泼可爱
- 长度在100-150字"""
        
        # 生成内容
        content = await ai_service.chat(
            message=prompt,
            system_prompt=system_prompt,
            pet_info={"name": pet.name, "breed": pet.breed, "age": pet.age}
        )
        
        # 生成标题
        title = await self._generate_title_from_content(content)
        
        # 创建日记
        diary_data = DiaryEntryCreate(
            pet_id=pet_id,
            title=title,
            content=content,
            type=DiaryEntryType.ACTIVITY
        )
        
        return await self.create_diary_entry(user_id, diary_data)
    
    async def get_weekly_summary(
        self,
        pet_id: str,
        user_id: str
    ) -> str:
        """
        生成本周日记总结
        
        Args:
            pet_id: 宠物ID
            user_id: 用户ID
            
        Returns:
            周总结文本
        """
        from .pet_service import pet_service
        
        # 获取宠物信息
        pet = await pet_service.get_pet(pet_id, user_id)
        if not pet:
            raise ValueError("宠物不存在")
        
        # 获取本周日记
        entries = await self.get_pet_diary_entries(pet_id, user_id, limit=7)
        
        if not entries:
            return f"{pet.name}这周还没有日记记录哦，快去记录一些精彩瞬间吧！"
        
        # 构建总结提示
        diary_summaries = "\n".join([
            f"- {entry.title}: {entry.content[:50]}..."
            for entry in entries
        ])
        
        prompt = f"""请根据以下日记内容，为{pet.name}生成一个温馨的周总结：

{diary_summaries}

请用100字左右总结这一周的精彩时刻。"""
        
        summary = await ai_service.chat(
            message=prompt,
            system_prompt="你是一个温馨的宠物日记总结助手，请用温暖的语气总结宠物的一周。"
        )
        
        return summary
    
    # ===========================================
    # 辅助方法
    # ===========================================
    
    def _to_diary_response(self, entry: Dict[str, Any]) -> DiaryEntryResponse:
        """将数据库记录转换为响应模型"""
        return DiaryEntryResponse(
            id=entry["id"],
            pet_id=entry["pet_id"],
            user_id=entry["user_id"],
            title=entry["title"],
            content=entry["content"],
            type=DiaryEntryType(entry.get("type", "activity")),
            image_url=entry.get("image_url"),
            video_url=entry.get("video_url"),
            is_video=entry.get("is_video", False),
            duration=entry.get("duration"),
            created_at=entry["created_at"],
            status=entry.get("status", "正常"),
            activity_trend=entry.get("activity_trend"),
            ai_analysis=entry.get("ai_analysis")
        )
    
    def _generate_activity_trend(self) -> List[Dict[str, int]]:
        """生成活动趋势数据"""
        return [{"v": random.randint(10, 100)} for _ in range(8)]
    
    async def _generate_diary_title(
        self,
        analysis: Optional[Dict[str, Any]]
    ) -> str:
        """根据分析结果生成日记标题"""
        if not analysis:
            return "今日记录"
        
        activities = analysis.get("activities", [])
        emotions = analysis.get("emotional_context", [])
        
        # 简单的标题生成逻辑
        if "playing" in activities or "玩耍" in activities:
            return "快乐玩耍时光"
        elif "eating" in activities or "进食" in activities:
            return "美食时刻"
        elif "sleeping" in activities or "休息" in activities:
            return "惬意午后"
        elif "exploring" in activities or "探索" in activities:
            return "探险日记"
        elif "curious" in emotions or "好奇" in emotions:
            return "好奇的一天"
        else:
            return "精彩瞬间"
    
    async def _generate_title_from_content(self, content: str) -> str:
        """从内容生成标题"""
        # 简单提取前几个字作为标题
        if len(content) > 10:
            # 尝试找到第一个句号或逗号
            for sep in ["。", "，", "！", "？", ".", ","]:
                if sep in content[:30]:
                    return content[:content.index(sep)][:15]
            return content[:15] + "..."
        return content


# 导出日记服务实例
diary_service = DiaryService()
