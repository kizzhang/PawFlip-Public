"""
Pydantic 数据模型定义
用于请求/响应数据验证和序列化
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ===========================================
# 枚举类型定义
# ===========================================

class AIProvider(str, Enum):
    """AI 服务提供商"""
    GEMINI = "gemini"
    OPENAI = "openai"
    LOCAL = "local"


class VideoJobStatus(str, Enum):
    """视频处理任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DiaryEntryType(str, Enum):
    """日记条目类型"""
    ACTIVITY = "activity"
    FEEDING = "feeding"
    HEALTH = "health"
    SOCIAL = "social"


# ===========================================
# 用户相关模型
# ===========================================

class UserBase(BaseModel):
    """用户基础信息"""
    email: EmailStr
    username: Optional[str] = None
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    """用户注册请求"""
    password: str = Field(..., min_length=6, description="密码至少6位")


class UserLogin(BaseModel):
    """用户登录请求"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """用户响应模型"""
    id: str
    created_at: datetime
    is_pro: bool = False
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """登录令牌响应"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ===========================================
# 宠物相关模型
# ===========================================

class PetBase(BaseModel):
    """宠物基础信息"""
    name: str = Field(..., min_length=1, max_length=50)
    breed: str = Field(..., description="品种")
    age: str = Field(..., description="年龄描述，如 '2岁'")
    avatar_url: Optional[str] = None


class PetCreate(PetBase):
    """创建宠物请求"""
    pass


class PetUpdate(BaseModel):
    """更新宠物请求"""
    name: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[str] = None
    avatar_url: Optional[str] = None


class PetResponse(PetBase):
    """宠物响应模型"""
    id: str
    user_id: str
    created_at: datetime
    
    # 实时状态数据
    battery: int = Field(default=100, ge=0, le=100)
    health_score: int = Field(default=100, ge=0, le=100)
    steps: int = Field(default=0, ge=0)
    next_feeding: Optional[str] = None
    
    # 3D 模型数据
    model_3d_url: Optional[str] = Field(default=None, description="3D 模型文件 URL (GLB 格式)")
    model_3d_preview: Optional[str] = Field(default=None, description="3D 模型预览图 URL")
    
    class Config:
        from_attributes = True


# ===========================================
# 日记相关模型
# ===========================================

class DiaryEntryBase(BaseModel):
    """日记条目基础信息"""
    title: str
    content: str
    type: DiaryEntryType = DiaryEntryType.ACTIVITY
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    is_video: bool = False
    duration: Optional[str] = None


class DiaryEntryCreate(DiaryEntryBase):
    """创建日记条目请求"""
    pet_id: str


class DiaryEntryResponse(DiaryEntryBase):
    """日记条目响应"""
    id: str
    pet_id: str
    user_id: str
    created_at: datetime
    status: str = "正常"
    
    # AI 生成的活动趋势数据
    activity_trend: Optional[List[Dict[str, int]]] = None
    
    # AI 分析结果
    ai_analysis: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


# ===========================================
# 健康数据模型
# ===========================================

class HealthRecordBase(BaseModel):
    """健康记录基础信息"""
    heart_rate: Optional[int] = Field(None, ge=0, le=300)
    steps: Optional[int] = Field(None, ge=0)
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    calories: Optional[int] = Field(None, ge=0)
    activity_minutes: Optional[int] = Field(None, ge=0)


class HealthRecordCreate(HealthRecordBase):
    """创建健康记录请求"""
    pet_id: str


class HealthRecordResponse(HealthRecordBase):
    """健康记录响应"""
    id: str
    pet_id: str
    recorded_at: datetime
    
    class Config:
        from_attributes = True


class HealthTrendResponse(BaseModel):
    """健康趋势响应"""
    period: str  # week, month, year
    data: List[Dict[str, Any]]
    summary: Dict[str, Any]


# ===========================================
# 社交相关模型
# ===========================================

class SocialPostBase(BaseModel):
    """社交帖子基础信息"""
    content: str
    image_url: Optional[str] = None
    is_ai_story: bool = False


class SocialPostCreate(SocialPostBase):
    """创建社交帖子请求"""
    pet_id: str
    diary_entry_id: Optional[str] = None  # 可选关联日记


class SocialPostResponse(SocialPostBase):
    """社交帖子响应"""
    id: str
    pet_id: str
    user_id: str
    created_at: datetime
    likes: int = 0
    comments: int = 0
    
    # 关联的宠物信息
    pet_name: Optional[str] = None
    pet_breed: Optional[str] = None
    pet_avatar: Optional[str] = None
    
    # 关联的日记ID
    diary_entry_id: Optional[str] = None
    
    class Config:
        from_attributes = True


# ===========================================
# 视频处理相关模型
# ===========================================

class VideoProcessRequest(BaseModel):
    """视频处理请求"""
    mode: str = Field(default="api", description="处理模式: local 或 api")
    use_frame_sampling: Optional[bool] = None
    enable_llm_analysis: Optional[bool] = None
    pet_id: Optional[str] = None  # 关联的宠物ID


class VideoJobResponse(BaseModel):
    """视频处理任务响应"""
    job_id: str
    status: VideoJobStatus
    progress: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class VideoAnalysisResult(BaseModel):
    """视频分析结果"""
    summary: str
    scenes: List[Dict[str, str]]
    detected_objects: List[str]
    activities: List[str]
    emotional_context: List[str]


class NarrativeResult(BaseModel):
    """叙事生成结果"""
    story: str
    style: str = "first-person cat POV"
    tone: str = "playful"


class VideoProcessResult(BaseModel):
    """完整的视频处理结果"""
    success: bool
    video_analysis: Optional[VideoAnalysisResult] = None
    narrative: Optional[NarrativeResult] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ===========================================
# AI 聊天相关模型
# ===========================================

class ChatMessage(BaseModel):
    """聊天消息"""
    role: str = Field(..., description="角色: user 或 assistant")
    content: str


class ChatRequest(BaseModel):
    """AI 聊天请求"""
    message: str
    history: Optional[List[ChatMessage]] = []
    pet_id: Optional[str] = None  # 可选关联宠物，用于上下文
    context_type: Optional[str] = None  # health, diary, general


class ChatResponse(BaseModel):
    """AI 聊天响应"""
    message: str
    suggestions: Optional[List[str]] = None


# ===========================================
# 通知相关模型
# ===========================================

class NotificationResponse(BaseModel):
    """通知响应"""
    id: str
    user_id: str
    title: str
    description: str
    icon: str
    color: str
    created_at: datetime
    is_read: bool = False
    
    class Config:
        from_attributes = True


# ===========================================
# 设备相关模型
# ===========================================

class DeviceBase(BaseModel):
    """设备基础信息"""
    name: str
    device_type: str = "collar"  # collar, camera, etc.
    firmware_version: Optional[str] = None


class DeviceCreate(DeviceBase):
    """创建设备请求"""
    pet_id: str


class DeviceResponse(DeviceBase):
    """设备响应"""
    id: str
    pet_id: str
    user_id: str
    is_connected: bool = False
    battery_level: int = 100
    last_sync: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ===========================================
# 通用响应模型
# ===========================================

class SuccessResponse(BaseModel):
    """通用成功响应"""
    success: bool = True
    message: str = "操作成功"


class ErrorResponse(BaseModel):
    """通用错误响应"""
    success: bool = False
    error: str
    error_code: Optional[str] = None
