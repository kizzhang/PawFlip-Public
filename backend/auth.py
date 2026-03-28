"""
认证模块
处理用户注册、登录、JWT 令牌管理
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from config import settings
from database import db, Tables
from base_models import UserCreate, UserResponse, TokenResponse

logger = logging.getLogger(__name__)

# ===========================================
# 密码加密配置
# ===========================================

# 直接使用 bcrypt 库来避免 passlib 兼容性问题
import bcrypt as _bcrypt

def _hash_with_bcrypt(password: str) -> str:
    """使用 bcrypt 直接哈希密码"""
    salt = _bcrypt.gensalt()
    return _bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def _verify_with_bcrypt(plain_password: str, hashed_password: str) -> bool:
    """使用 bcrypt 直接验证密码"""
    return _bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )

# ===========================================
# JWT Bearer 认证
# ===========================================

security = HTTPBearer()


# ===========================================
# 密码工具函数
# ===========================================

def hash_password(password: str) -> str:
    """
    对密码进行哈希加密
    """
    return _hash_with_bcrypt(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否正确
    """
    return _verify_with_bcrypt(plain_password, hashed_password)


# ===========================================
# JWT 令牌工具函数
# ===========================================

def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建 JWT 访问令牌
    
    Args:
        data: 要编码的数据（通常包含 user_id）
        expires_delta: 过期时间增量
        
    Returns:
        编码后的 JWT 令牌
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    解码 JWT 令牌
    
    Args:
        token: JWT 令牌字符串
        
    Returns:
        解码后的数据，如果无效则返回 None
    """
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT 解码失败: {e}")
        return None


# ===========================================
# 用户认证服务
# ===========================================

class AuthService:
    """
    认证服务类
    处理用户注册、登录等操作
    """
    
    async def register(self, user_data: UserCreate) -> TokenResponse:
        """
        用户注册
        
        Args:
            user_data: 用户注册信息
            
        Returns:
            包含令牌和用户信息的响应
            
        Raises:
            HTTPException: 如果邮箱已存在
        """
        # 检查邮箱是否已存在
        existing_user = await db.select_one(
            Tables.USERS,
            {"email": user_data.email}
        )
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被注册"
            )
        
        # 创建用户
        hashed_password = hash_password(user_data.password)
        
        new_user = await db.insert(Tables.USERS, {
            "email": user_data.email,
            "username": user_data.username or user_data.email.split("@")[0],
            "password_hash": hashed_password,
            "avatar_url": user_data.avatar_url,
            "is_pro": False
        })
        
        # 生成令牌
        access_token = create_access_token({"sub": new_user["id"]})
        
        return TokenResponse(
            access_token=access_token,
            user=UserResponse(
                id=new_user["id"],
                email=new_user["email"],
                username=new_user.get("username"),
                avatar_url=new_user.get("avatar_url"),
                created_at=new_user["created_at"],
                is_pro=new_user.get("is_pro", False)
            )
        )
    
    async def login(self, email: str, password: str) -> TokenResponse:
        """
        用户登录
        
        Args:
            email: 用户邮箱
            password: 用户密码
            
        Returns:
            包含令牌和用户信息的响应
            
        Raises:
            HTTPException: 如果凭据无效
        """
        # 查找用户
        user = await db.select_one(Tables.USERS, {"email": email})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误"
            )
        
        # 验证密码
        if not verify_password(password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误"
            )
        
        # 生成令牌
        access_token = create_access_token({"sub": user["id"]})
        
        return TokenResponse(
            access_token=access_token,
            user=UserResponse(
                id=user["id"],
                email=user["email"],
                username=user.get("username"),
                avatar_url=user.get("avatar_url"),
                created_at=user["created_at"],
                is_pro=user.get("is_pro", False)
            )
        )
    
    async def get_current_user(self, user_id: str) -> UserResponse:
        """
        获取当前用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户信息
            
        Raises:
            HTTPException: 如果用户不存在
        """
        user = await db.select_one(Tables.USERS, {"id": user_id})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return UserResponse(
            id=user["id"],
            email=user["email"],
            username=user.get("username"),
            avatar_url=user.get("avatar_url"),
            created_at=user["created_at"],
            is_pro=user.get("is_pro", False)
        )


# ===========================================
# FastAPI 依赖项
# ===========================================

async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    FastAPI 依赖项：从 JWT 令牌获取当前用户ID
    
    用法:
        @app.get("/protected")
        async def protected_route(user_id: str = Depends(get_current_user_id)):
            ...
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user_id


async def get_current_user(
    user_id: str = Depends(get_current_user_id)
) -> UserResponse:
    """
    FastAPI 依赖项：获取当前用户完整信息
    """
    auth_service = AuthService()
    return await auth_service.get_current_user(user_id)


# 导出认证服务实例
auth_service = AuthService()
