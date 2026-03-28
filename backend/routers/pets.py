"""
宠物相关 API 路由
处理宠物的 CRUD 操作
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from typing import List, Optional
import tempfile
import os
import logging
from pathlib import Path

from auth import get_current_user_id
from services.pet_service import pet_service
from base_models import (
    PetCreate, PetUpdate, PetResponse,
    SuccessResponse, ErrorResponse
)

router = APIRouter(prefix="/pets", tags=["宠物管理"])
logger = logging.getLogger(__name__)


# ===========================================
# 创建宠物
# ===========================================

@router.post(
    "",
    response_model=PetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建宠物",
    description="为当前用户创建新的宠物档案"
)
async def create_pet(
    pet_data: PetCreate,
    user_id: str = Depends(get_current_user_id)
):
    """
    创建新宠物
    
    - **name**: 宠物名字（必填）
    - **breed**: 品种（必填）
    - **age**: 年龄描述，如 "2岁"（必填）
    - **avatar_url**: 头像URL（可选）
    """
    return await pet_service.create_pet(user_id, pet_data)


# ===========================================
# 创建宠物（带 3D 模型生成）
# ===========================================

@router.post(
    "/with-3d-model",
    response_model=PetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建宠物并生成 3D 模型",
    description="为当前用户创建新的宠物档案，并从照片生成 3D 数字孪生模型"
)
async def create_pet_with_3d_model(
    name: str = Form(..., description="宠物名字"),
    breed: str = Form(..., description="品种"),
    age: str = Form(..., description="年龄描述"),
    photo: UploadFile = File(..., description="宠物照片（用于生成 3D 模型）"),
    user_id: str = Depends(get_current_user_id)
):
    """
    创建新宠物并生成 3D 模型
    
    这个端点会：
    1. 创建宠物档案
    2. 使用上传的照片生成 3D 数字孪生模型
    3. 返回包含 3D 模型 URL 的宠物信息
    
    3D 模型生成可能需要 1-3 分钟，请耐心等待。
    
    - **name**: 宠物名字（必填）
    - **breed**: 品种（必填）
    - **age**: 年龄描述，如 "2岁"（必填）
    - **photo**: 宠物照片文件（必填，用于生成 3D 模型）
    """
    # 验证文件类型
    if not photo.content_type or not photo.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请上传图片文件"
        )
    
    # 保存临时文件
    suffix = Path(photo.filename).suffix if photo.filename else ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await photo.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # 创建宠物数据
        pet_data = PetCreate(
            name=name,
            breed=breed,
            age=age,
            avatar_url=None  # 将在后续设置
        )
        
        # 创建宠物并生成 3D 模型
        pet, model_result = await pet_service.create_pet_with_3d_model(
            user_id=user_id,
            pet_data=pet_data,
            image_path=tmp_path
        )
        
        # 如果 3D 模型生成失败，记录警告但仍返回宠物信息
        if model_result and not model_result.get("success"):
            logger.warning(f"3D 模型生成失败: {model_result.get('error')}")
        
        return pet
        
    finally:
        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


# ===========================================
# 获取用户的所有宠物
# ===========================================

@router.get(
    "",
    response_model=List[PetResponse],
    summary="获取宠物列表",
    description="获取当前用户的所有宠物"
)
async def get_pets(user_id: str = Depends(get_current_user_id)):
    """
    获取当前用户的所有宠物列表
    """
    return await pet_service.get_user_pets(user_id)


# ===========================================
# 获取单个宠物
# ===========================================

@router.get(
    "/{pet_id}",
    response_model=PetResponse,
    summary="获取宠物详情",
    description="获取指定宠物的详细信息"
)
async def get_pet(
    pet_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    获取指定宠物的详细信息
    
    - **pet_id**: 宠物ID
    """
    pet = await pet_service.get_pet(pet_id, user_id)
    
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="宠物不存在或无权访问"
        )
    
    return pet


# ===========================================
# 更新宠物信息
# ===========================================

@router.patch(
    "/{pet_id}",
    response_model=PetResponse,
    summary="更新宠物信息",
    description="更新指定宠物的信息"
)
async def update_pet(
    pet_id: str,
    pet_data: PetUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """
    更新宠物信息
    
    只需提供要更新的字段
    """
    pet = await pet_service.update_pet(pet_id, user_id, pet_data)
    
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="宠物不存在或无权访问"
        )
    
    return pet


# ===========================================
# 删除宠物
# ===========================================

@router.delete(
    "/{pet_id}",
    response_model=SuccessResponse,
    summary="删除宠物",
    description="删除指定的宠物档案"
)
async def delete_pet(
    pet_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    删除宠物档案
    
    注意：此操作不可恢复，相关的日记和健康数据也会被删除
    """
    success = await pet_service.delete_pet(pet_id, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="宠物不存在或无权访问"
        )
    
    return SuccessResponse(message="宠物已删除")
