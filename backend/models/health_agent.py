"""
Health Agent 数据模型
用于对话管理、上下文构建和记忆管理
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ===========================================
# 枚举类型
# ===========================================

class ConversationStatus(str, Enum):
    """对话状态"""
    ACTIVE = "active"
    ARCHIVED = "archived"


class MessageRole(str, Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"


class KeyInfoType(str, Enum):
    """关键信息类型"""
    SYMPTOM = "symptom"      # 症状
    DIAGNOSIS = "diagnosis"  # 诊断
    ADVICE = "advice"        # 建议


# ===========================================
# 请求模型
# ===========================================

class HealthAgentChatRequest(BaseModel):
    """Health Agent 聊天请求"""
    message: str = Field(..., min_length=1, description="用户消息")
    pet_id: str = Field(..., description="宠物 ID")
    conversation_id: Optional[str] = Field(None, description="对话 ID，不传则创建新对话")


class CreateConversationRequest(BaseModel):
    """创建对话请求"""
    pet_id: str = Field(..., description="宠物 ID")
    initial_message: Optional[str] = Field(None, description="初始消息")


# ===========================================
# 响应模型
# ===========================================

class ToolAction(BaseModel):
    """工具调用动作（用于前端显示）"""
    name: str = Field(..., description="友好的工具名称")
    icon: str = Field(..., description="图标名称")
    status: str = Field(default="completed", description="状态: pending, running, completed")


class HealthAgentChatResponse(BaseModel):
    """Health Agent 聊天响应"""
    conversation_id: str
    message_id: str
    response: str
    suggestions: List[str] = Field(default_factory=list, description="推荐的后续问题")
    tool_actions: List[ToolAction] = Field(default_factory=list, description="工具调用动作")


class MessageModel(BaseModel):
    """消息模型"""
    id: str
    role: MessageRole
    content: str
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class KeyInfoModel(BaseModel):
    """关键信息模型"""
    id: str
    type: KeyInfoType
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationSummary(BaseModel):
    """对话摘要（列表用）"""
    id: str
    title: Optional[str] = None
    summary: Optional[str] = None
    pet_id: str
    pet_name: str
    updated_at: datetime
    message_count: int

    class Config:
        from_attributes = True


class ConversationDetail(BaseModel):
    """对话详情"""
    id: str
    title: Optional[str] = None
    summary: Optional[str] = None
    pet_id: str
    status: ConversationStatus
    messages: List[MessageModel]
    key_info: List[KeyInfoModel] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """对话列表响应"""
    conversations: List[ConversationSummary]
    total: int


class CreateConversationResponse(BaseModel):
    """创建对话响应"""
    conversation_id: str
    message: str = "对话创建成功"


# ===========================================
# 内部模型（服务层使用）
# ===========================================

class PetProfile(BaseModel):
    """宠物档案"""
    id: str
    name: str
    breed: Optional[str] = None
    age: Optional[str] = None
    avatar_url: Optional[str] = None


class HealthSummary(BaseModel):
    """健康数据摘要"""
    heart_rate: Optional[int] = None
    steps: Optional[int] = None
    sleep_hours: Optional[float] = None
    last_updated: Optional[datetime] = None


class LLMContext(BaseModel):
    """LLM 上下文"""
    system_prompt: str
    messages: List[Dict[str, str]]  # [{"role": "user/assistant", "content": "..."}]


class ConversationMemory(BaseModel):
    """对话记忆"""
    recent_messages: List[MessageModel]
    summary: Optional[str] = None
    key_info: List[KeyInfoModel] = Field(default_factory=list)
