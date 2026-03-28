"""
认证相关 API 路由
处理用户注册、登录、信息获取
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from pydantic import BaseModel
from typing import Optional
import base64
import uuid
from pathlib import Path

from auth import auth_service, get_current_user, get_current_user_id
from database import db
from config import settings
from base_models import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    SuccessResponse, ErrorResponse
)

router = APIRouter(prefix="/auth", tags=["认证"])

# 头像存储目录
AVATAR_DIR = Path(settings.UPLOAD_DIR) / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

# 允许的图片格式
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB


class UpdateProfileRequest(BaseModel):
    """更新用户资料请求"""
    username: Optional[str] = None
    avatar_url: Optional[str] = None


# ===========================================
# 用户注册
# ===========================================

@router.post(
    "/register",
    response_model=TokenResponse,
    summary="用户注册",
    description="创建新用户账户并返回访问令牌"
)
async def register(user_data: UserCreate):
    """
    用户注册接口
    
    - **email**: 用户邮箱（必填，唯一）
    - **password**: 密码（必填，至少6位）
    - **username**: 用户名（可选）
    - **avatar_url**: 头像URL（可选）
    """
    return await auth_service.register(user_data)


# ===========================================
# 用户登录
# ===========================================

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="用户登录",
    description="验证用户凭据并返回访问令牌"
)
async def login(credentials: UserLogin):
    """
    用户登录接口
    
    - **email**: 用户邮箱
    - **password**: 密码
    """
    return await auth_service.login(credentials.email, credentials.password)


# ===========================================
# 获取当前用户信息
# ===========================================

@router.get(
    "/me",
    response_model=UserResponse,
    summary="获取当前用户信息",
    description="获取已登录用户的详细信息"
)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """
    获取当前登录用户的信息
    
    需要在请求头中携带 Bearer Token
    """
    return current_user


# ===========================================
# 验证令牌
# ===========================================

@router.get(
    "/verify",
    response_model=SuccessResponse,
    summary="验证令牌",
    description="验证当前令牌是否有效"
)
async def verify_token(user_id: str = Depends(get_current_user_id)):
    """
    验证访问令牌是否有效
    
    如果令牌有效，返回成功响应
    如果令牌无效或过期，返回 401 错误
    """
    return SuccessResponse(message="令牌有效")


# ===========================================
# 更新用户资料
# ===========================================

@router.put(
    "/profile",
    response_model=UserResponse,
    summary="更新用户资料",
    description="更新当前用户的昵称或头像"
)
async def update_profile(
    request: UpdateProfileRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    更新用户资料
    
    - **username**: 用户昵称（可选）
    - **avatar_url**: 头像URL（可选）
    """
    try:
        update_data = {}
        if request.username is not None:
            update_data["username"] = request.username
        if request.avatar_url is not None:
            update_data["avatar_url"] = request.avatar_url
        
        if not update_data:
            raise HTTPException(status_code=400, detail="没有要更新的内容")
        
        await db.update("users", {"id": user_id}, update_data)
        
        # 重新获取完整用户数据（包含 created_at）
        user = await db.select_one("users", {"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return UserResponse(
            id=user_id,
            email=user.get("email", ""),
            username=user.get("username"),
            avatar_url=user.get("avatar_url"),
            is_pro=user.get("is_pro", False),
            created_at=user.get("created_at")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


# ===========================================
# 上传头像
# ===========================================

@router.post(
    "/avatar",
    response_model=UserResponse,
    summary="上传头像",
    description="上传用户头像图片"
)
async def upload_avatar(
    file: UploadFile = File(..., description="头像图片 (jpg, png, gif, webp)"),
    user_id: str = Depends(get_current_user_id)
):
    """
    上传用户头像
    
    - 支持格式: jpg, png, gif, webp
    - 最大大小: 5MB
    """
    # 验证文件类型
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的图片格式，请上传 jpg/png/gif/webp"
        )
    
    # 读取文件内容
    content = await file.read()
    
    # 验证文件大小
    if len(content) > MAX_AVATAR_SIZE:
        raise HTTPException(
            status_code=400,
            detail="图片过大，最大允许 5MB"
        )
    
    try:
        # 生成唯一文件名
        ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "jpg"
        filename = f"{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
        file_path = AVATAR_DIR / filename
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 生成访问 URL (相对路径，前端通过 API 访问)
        avatar_url = f"/api/v1/auth/avatar/{filename}"
        
        # 更新数据库
        await db.update("users", {"id": user_id}, {"avatar_url": avatar_url})
        
        # 返回更新后的用户信息
        user = await db.select_one("users", {"id": user_id})
        
        return UserResponse(
            id=user_id,
            email=user.get("email", ""),
            username=user.get("username"),
            avatar_url=avatar_url,
            is_pro=user.get("is_pro", False),
            created_at=user.get("created_at")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")



# ===========================================
# 获取头像文件
# ===========================================

from fastapi.responses import FileResponse

@router.get(
    "/avatar/{filename}",
    summary="获取头像",
    description="获取用户头像图片文件"
)
async def get_avatar(filename: str):
    """获取头像图片"""
    file_path = AVATAR_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="头像不存在")
    
    # 安全检查：确保文件在 AVATAR_DIR 内
    if not file_path.resolve().is_relative_to(AVATAR_DIR.resolve()):
        raise HTTPException(status_code=403, detail="禁止访问")
    
    return FileResponse(file_path)
