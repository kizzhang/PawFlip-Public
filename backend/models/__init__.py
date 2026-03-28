"""
数据模型包
"""

# 从 base_models.py 导入基础模型
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from base_models import (
    UserCreate,
    UserResponse,
    TokenResponse,
    UserLogin,
    PetCreate,
    PetUpdate,
    PetResponse,
    DiaryEntryCreate,
    DiaryEntryResponse,
    HealthRecordCreate,
    HealthRecordResponse,
    ChatRequest,
    ChatResponse,
)

# 从 health_agent 导入健康智能体模型
from .health_agent import (
    # 枚举
    ConversationStatus,
    MessageRole,
    KeyInfoType,
    # 请求模型
    HealthAgentChatRequest,
    CreateConversationRequest,
    # 响应模型
    HealthAgentChatResponse,
    MessageModel,
    KeyInfoModel,
    ConversationSummary,
    ConversationDetail,
    ConversationListResponse,
    CreateConversationResponse,
    # 内部模型
    PetProfile,
    HealthSummary,
    LLMContext,
    ConversationMemory,
)

__all__ = [
    # 基础模型
    "UserCreate",
    "UserResponse",
    "TokenResponse",
    "UserLogin",
    "PetCreate",
    "PetUpdate",
    "PetResponse",
    "DiaryEntryCreate",
    "DiaryEntryResponse",
    "HealthRecordCreate",
    "HealthRecordResponse",
    "ChatRequest",
    "ChatResponse",
    # 健康智能体模型
    "ConversationStatus",
    "MessageRole",
    "KeyInfoType",
    "HealthAgentChatRequest",
    "CreateConversationRequest",
    "HealthAgentChatResponse",
    "MessageModel",
    "KeyInfoModel",
    "ConversationSummary",
    "ConversationDetail",
    "ConversationListResponse",
    "CreateConversationResponse",
    "PetProfile",
    "HealthSummary",
    "LLMContext",
    "ConversationMemory",
]
