"""
ADK 健康智能体服务
让 Agent 自主获取数据和调用工具
"""

import logging
import uuid
import asyncio
from typing import Optional, List
from datetime import datetime

from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

from database import db
from models.health_agent import (
    HealthAgentChatResponse,
    ToolAction,
    MessageModel,
    MessageRole,
    ConversationSummary,
    ConversationDetail,
    ConversationStatus,
    KeyInfoModel,
    KeyInfoType,
)
from agents.health_agent import create_health_agent, set_agent_context

logger = logging.getLogger(__name__)


class ADKHealthService:
    """
    基于 ADK 的宠物健康服务
    Agent 自主决定何时调用工具
    """
    
    def __init__(self):
        self.session_service = InMemorySessionService()
    
    async def chat(
        self,
        user_id: str,
        pet_id: str,
        message: str,
        conversation_id: Optional[str] = None
    ) -> HealthAgentChatResponse:
        """
        处理用户消息
        """
        try:
            # 1. 获取或创建对话
            if conversation_id:
                conv = await self._get_conversation(conversation_id, user_id)
                if not conv:
                    raise ValueError("对话不存在或无权访问")
            else:
                conversation_id = await self._create_conversation(user_id, pet_id)
            
            # 2. 设置 Agent 上下文
            set_agent_context(user_id, pet_id, conversation_id)
            
            # 3. 预先获取所有上下文数据
            pet_info = await self._get_pet_info(pet_id)
            health_data = await self._get_health_data(pet_id)
            history_info = await self._get_history_info(conversation_id)
            owner_name = await self._get_owner_name(user_id)
            
            # 4. 获取历史消息
            history = await self._get_recent_messages(conversation_id, limit=10)
            
            # 5. 创建 Agent（注入所有上下文）并运行
            agent = create_health_agent(
                pet_info=pet_info,
                health_data=health_data,
                history_info=history_info,
                owner_name=owner_name
            )
            response_text, tool_actions = await self._run_agent(agent, user_id, message, history)
            
            # 6. 保存消息
            await self._save_message(conversation_id, MessageRole.USER, message)
            msg_id = await self._save_message(conversation_id, MessageRole.ASSISTANT, response_text)
            
            # 7. 更新对话时间
            await self._update_conversation(conversation_id)
            
            return HealthAgentChatResponse(
                conversation_id=conversation_id,
                message_id=msg_id,
                response=response_text,
                suggestions=[],
                tool_actions=tool_actions
            )
            
        except Exception as e:
            logger.error(f"Health Agent 聊天失败: {e}")
            raise
    
    async def _get_pet_info(self, pet_id: str) -> dict:
        """获取宠物基本信息"""
        try:
            pet = await db.select_one("pets", {"id": pet_id}, columns="name, breed, age")
            return pet or {"name": "宠物", "breed": "未知", "age": "未知"}
        except Exception as e:
            logger.error(f"获取宠物信息失败: {e}")
            return {"name": "宠物", "breed": "未知", "age": "未知"}
    
    async def _get_owner_name(self, user_id: str) -> str:
        """获取用户昵称"""
        try:
            user = await db.select_one("users", {"id": user_id}, columns="username")
            return user.get("username") if user and user.get("username") else "主人"
        except Exception as e:
            logger.error(f"获取用户昵称失败: {e}")
            return "主人"
    
    async def _get_health_data(self, pet_id: str, days: int = 7) -> dict:
        """获取健康数据"""
        try:
            records = await db.select(
                "health_records",
                columns="heart_rate, steps, sleep_hours, created_at",
                filters={"pet_id": pet_id},
                order_by="created_at.desc",
                limit=days
            )
            if records:
                return {
                    "records": records,
                    "summary": {
                        "avg_heart_rate": round(sum(r.get("heart_rate", 0) or 0 for r in records) / len(records), 1),
                        "total_steps": sum(r.get("steps", 0) or 0 for r in records),
                        "avg_sleep": round(sum(r.get("sleep_hours", 0) or 0 for r in records) / len(records), 1),
                    }
                }
            return {}
        except Exception as e:
            logger.error(f"获取健康数据失败: {e}")
            return {}
    
    async def _get_history_info(self, conversation_id: str) -> dict:
        """获取历史记录（症状、建议）"""
        try:
            key_info = await db.select(
                "key_info",
                columns="type, content, created_at",
                filters={"conversation_id": conversation_id},
                order_by="created_at"
            )
            return {
                "symptoms": [k for k in key_info if k.get("type") == "symptom"],
                "advices": [k for k in key_info if k.get("type") == "advice"],
            }
        except Exception as e:
            logger.error(f"获取历史记录失败: {e}")
            return {}
    
    # 工具名称映射（技术名 -> 友好名）
    TOOL_NAME_MAP = {
        "get_health_records": ("查看健康记录", "monitor_heart"),
        "get_recent_diary": ("查看近期日记", "auto_stories"),
        "record_symptom": ("记录症状", "edit_note"),
        "record_advice": ("保存建议", "bookmark"),
    }
    
    async def _run_agent(
        self,
        agent: Agent,
        user_id: str,
        message: str,
        history: List[dict] = None,
        max_retries: int = 3
    ) -> tuple[str, List[ToolAction]]:
        """运行 ADK Agent，返回响应和工具调用列表，带重试机制"""
        
        for attempt in range(max_retries):
            try:
                return await self._execute_agent(agent, user_id, message, history)
            except Exception as e:
                error_str = str(e)
                # 检查是否是 429 错误
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 2  # 2, 4, 8 秒
                        logger.warning(f"API 限流，{wait_time}秒后重试 (尝试 {attempt + 1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"API 限流，已达最大重试次数")
                        return "抱歉，服务繁忙，请稍后再试。", []
                else:
                    raise
        
        return "抱歉，服务暂时不可用。", []
    
    async def _execute_agent(
        self,
        agent: Agent,
        user_id: str,
        message: str,
        history: List[dict] = None
    ) -> tuple[str, List[ToolAction]]:
        """实际执行 Agent"""
        runner = Runner(
            agent=agent,
            app_name="pet_health",
            session_service=self.session_service
        )
        
        session_id = f"session_{user_id}_{uuid.uuid4().hex[:8]}"
        session = await self.session_service.create_session(
            app_name="pet_health",
            user_id=user_id,
            session_id=session_id
        )
        
        # 添加历史消息
        if history:
            for msg in history:
                role = "user" if msg["role"] == "user" else "model"
                session.events.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })
        
        # 构建消息
        user_content = types.Content(
            role="user",
            parts=[types.Part(text=message)]
        )
        
        # 运行并收集响应和工具调用
        response_parts = []
        tool_actions = []
        
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_content
        ):
            # 捕获工具调用
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts'):
                    for part in event.content.parts:
                        # 检查是否是 function_call
                        if hasattr(part, 'function_call') and part.function_call:
                            func_name = part.function_call.name
                            if func_name in self.TOOL_NAME_MAP:
                                friendly_name, icon = self.TOOL_NAME_MAP[func_name]
                                tool_actions.append(ToolAction(
                                    name=friendly_name,
                                    icon=icon,
                                    status="completed"
                                ))
                        # 收集文本响应
                        if hasattr(part, 'text') and part.text:
                            response_parts.append(part.text)
        
        response = "".join(response_parts) if response_parts else "抱歉，我暂时无法回答。"
        return response, tool_actions
    
    # ==================== 数据库操作 ====================
    
    async def _get_conversation(self, conversation_id: str, user_id: str) -> Optional[dict]:
        return await db.select_one("conversations", {"id": conversation_id, "user_id": user_id})
    
    async def _create_conversation(self, user_id: str, pet_id: str) -> str:
        conv_id = str(uuid.uuid4())
        await db.insert("conversations", {
            "id": conv_id,
            "user_id": user_id,
            "pet_id": pet_id,
            "status": "active"
        })
        return conv_id
    
    async def _get_recent_messages(self, conversation_id: str, limit: int = 10) -> List[dict]:
        messages = await db.select(
            "messages",
            columns="role, content",
            filters={"conversation_id": conversation_id},
            order_by="created_at.desc",
            limit=limit
        )
        messages.reverse()
        return messages
    
    async def _save_message(self, conversation_id: str, role: MessageRole, content: str) -> str:
        msg_id = str(uuid.uuid4())
        await db.insert("messages", {
            "id": msg_id,
            "conversation_id": conversation_id,
            "role": role.value,
            "content": content,
            "metadata": {}
        })
        return msg_id
    
    async def _update_conversation(self, conversation_id: str):
        await db.update(
            "conversations",
            {"id": conversation_id},
            {"updated_at": datetime.utcnow().isoformat()}
        )
    
    # ==================== 对话管理 API ====================
    
    async def get_conversations(self, user_id: str, limit: int = 20) -> List[ConversationSummary]:
        """获取对话列表"""
        convs = await db.select(
            "conversations",
            columns="id, title, summary, pet_id, updated_at",
            filters={"user_id": user_id},
            order_by="updated_at.desc",
            limit=limit
        )
        
        result = []
        for conv in convs:
            msgs = await db.select("messages", columns="id", filters={"conversation_id": conv["id"]})
            pet = await db.select_one("pets", {"id": conv["pet_id"]}, columns="name")
            
            result.append(ConversationSummary(
                id=conv["id"],
                title=conv.get("title"),
                summary=conv.get("summary"),
                pet_id=conv["pet_id"],
                pet_name=pet.get("name", "未知") if pet else "未知",
                updated_at=conv["updated_at"],
                message_count=len(msgs)
            ))
        return result
    
    async def get_conversation_detail(self, conversation_id: str, user_id: str) -> ConversationDetail:
        """获取对话详情"""
        conv = await self._get_conversation(conversation_id, user_id)
        if not conv:
            raise ValueError("对话不存在或无权访问")
        
        msgs_data = await db.select(
            "messages",
            columns="id, role, content, metadata, created_at",
            filters={"conversation_id": conversation_id},
            order_by="created_at"
        )
        
        messages = [
            MessageModel(
                id=m["id"],
                role=MessageRole(m["role"]),
                content=m["content"],
                created_at=m["created_at"],
                metadata=m.get("metadata", {})
            )
            for m in msgs_data
        ]
        
        key_info_data = await db.select(
            "key_info",
            columns="id, type, content, created_at",
            filters={"conversation_id": conversation_id},
            order_by="created_at"
        )
        
        key_info = [
            KeyInfoModel(
                id=k["id"],
                type=k["type"],
                content=k["content"],
                created_at=k["created_at"]
            )
            for k in key_info_data
        ]
        
        return ConversationDetail(
            id=conv["id"],
            title=conv.get("title"),
            summary=conv.get("summary"),
            pet_id=conv["pet_id"],
            status=ConversationStatus(conv.get("status", "active")),
            messages=messages,
            key_info=key_info,
            created_at=conv["created_at"],
            updated_at=conv["updated_at"]
        )
    
    async def create_conversation(
        self,
        user_id: str,
        pet_id: str,
        initial_message: Optional[str] = None
    ) -> str:
        """创建新对话"""
        conv_id = await self._create_conversation(user_id, pet_id)
        
        if initial_message:
            await self.chat(user_id, pet_id, initial_message, conv_id)
        
        return conv_id


# 导出服务实例
adk_health_service = ADKHealthService()
