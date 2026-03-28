"""
社交功能相关 API 路由
处理社交帖子的发布、浏览和互动
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Form, Request
from typing import List, Optional
import tempfile
import os
import logging
from pathlib import Path

from auth import get_current_user_id
from database import db, Tables
from services.pet_service import pet_service
from services.video_service import video_service
from services.diary_service import diary_service
from base_models import (
    SocialPostCreate, SocialPostResponse,
    SuccessResponse, DiaryEntryCreate, DiaryEntryType
)

router = APIRouter(prefix="/social", tags=["社交功能"])
logger = logging.getLogger(__name__)


# ===========================================
# 发布帖子
# ===========================================

@router.post(
    "/posts",
    response_model=SocialPostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="发布帖子",
    description="发布一条社交动态"
)
async def create_post(
    post_data: SocialPostCreate,
    user_id: str = Depends(get_current_user_id)
):
    """
    发布社交帖子
    
    - **pet_id**: 宠物ID（必填）
    - **content**: 帖子内容（必填）
    - **image_url**: 图片URL（可选）
    - **is_ai_story**: 是否为 AI 生成的故事
    - **diary_entry_id**: 关联的日记ID（可选）
    """
    # 验证宠物所有权
    pet = await pet_service.get_pet(post_data.pet_id, user_id)
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="宠物不存在或无权访问"
        )
    
    # 创建帖子
    new_post = await db.insert(Tables.SOCIAL_POSTS, {
        "user_id": user_id,
        "pet_id": post_data.pet_id,
        "content": post_data.content,
        "image_url": post_data.image_url,
        "is_ai_story": post_data.is_ai_story,
        "diary_entry_id": post_data.diary_entry_id,
        "likes": 0,
        "comments": 0
    })
    
    return SocialPostResponse(
        id=new_post["id"],
        pet_id=new_post["pet_id"],
        user_id=new_post["user_id"],
        content=new_post["content"],
        image_url=new_post.get("image_url"),
        is_ai_story=new_post.get("is_ai_story", False),
        created_at=new_post["created_at"],
        likes=0,
        comments=0,
        pet_name=pet.name,
        pet_breed=pet.breed,
        pet_avatar=pet.avatar_url
    )


# ===========================================
# 发布视频帖子（调用 pet-vision-narrator）
# ===========================================

@router.post(
    "/posts/video",
    response_model=SocialPostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="发布视频帖子",
    description="上传视频并使用 AI 生成故事，然后发布为社交帖子"
)
async def create_video_post(
    request: Request,
    pet_id: str = Form(...),
    video: UploadFile = File(...),
    mode: str = Form("api"),
    user_id: str = Depends(get_current_user_id)
):
    """
    发布视频帖子
    
    - **pet_id**: 宠物ID（必填）
    - **video**: 视频文件（必填）
    - **mode**: 处理模式，local 或 api（默认 api）
    
    流程：
    1. 验证宠物所有权
    2. 保存视频文件
    3. 调用 pet-vision-narrator 分析视频
    4. 生成 AI 故事
    5. 创建日记条目
    6. 发布社交帖子
    
    支持取消：客户端断开连接时会自动停止处理
    """
    # 验证宠物所有权
    pet = await pet_service.get_pet(pet_id, user_id)
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="宠物 ID 不存在，请先完成注册流程"
        )
    
    # 验证视频文件
    if not video.content_type or not video.content_type.startswith('video/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请上传有效的视频文件"
        )
    
    video_path = None
    try:
        # 检查客户端是否已断开
        if await request.is_disconnected():
            logger.info("客户端已断开连接，取消处理")
            raise HTTPException(status_code=499, detail="客户端取消请求")
        
        # 保存临时视频文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            content = await video.read()
            tmp_file.write(content)
            video_path = tmp_file.name
        
        # 再次检查客户端连接
        if await request.is_disconnected():
            logger.info("客户端已断开连接，取消处理")
            raise HTTPException(status_code=499, detail="客户端取消请求")
        
        # 调用视频服务处理视频（传入 request 用于检测断开）
        result = await video_service.process_video_sync(
            video_path=video_path,
            mode=mode,
            pet_id=pet_id,
            user_id=user_id,
            request=request  # 传入 request 对象
        )
        
        # 检查是否被取消
        if await request.is_disconnected():
            logger.info("客户端已断开连接，取消后续处理")
            raise HTTPException(status_code=499, detail="客户端取消请求")
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"视频处理失败: {result.error}"
            )
        
        # 生成故事内容
        narrative = result.narrative
        if narrative:
            story_content = narrative.story
        else:
            story_content = '今天又是充满探索的一天！'
        
        # 创建日记条目
        diary_data = DiaryEntryCreate(
            pet_id=pet_id,
            title=f"{pet.name}的视频日记",
            content=story_content,
            type=DiaryEntryType.ACTIVITY,
            is_video=True
        )
        
        try:
            diary_entry = await diary_service.create_diary_entry(user_id, diary_data)
            logger.info(f"日记创建成功: {diary_entry.id}")
        except Exception as e:
            logger.error(f"日记创建失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"日记创建失败: {str(e)}"
            )
        
        # 保存 AI 分析结果和元数据
        if result.video_analysis or result.metadata:
            try:
                update_data = {}
                if result.video_analysis:
                    update_data["ai_analysis"] = result.video_analysis.model_dump() if hasattr(result.video_analysis, 'model_dump') else result.video_analysis
                if result.metadata:
                    if "ai_analysis" in update_data:
                        update_data["ai_analysis"]["metadata"] = result.metadata
                    else:
                        update_data["ai_analysis"] = {"metadata": result.metadata}
                
                await db.update(
                    Tables.DIARY_ENTRIES,
                    {"id": diary_entry.id},
                    update_data
                )
                logger.info(f"AI 分析数据保存成功: {diary_entry.id}")
            except Exception as e:
                logger.error(f"AI 分析数据保存失败: {e}")
                # 不抛出异常，因为日记已经创建成功
        
        # 创建社交帖子
        try:
            new_post = await db.insert(Tables.SOCIAL_POSTS, {
                "user_id": user_id,
                "pet_id": pet_id,
                "content": story_content,
                "image_url": None,  # 视频帖子暂时不设置图片
                "is_ai_story": True,
                "diary_entry_id": diary_entry.id,
                "likes": 0,
                "comments": 0
            })
            logger.info(f"社交帖子创建成功: {new_post['id']}")
        except Exception as e:
            logger.error(f"社交帖子创建失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"社交帖子创建失败: {str(e)}"
            )
        
        return SocialPostResponse(
            id=new_post["id"],
            pet_id=new_post["pet_id"],
            user_id=new_post["user_id"],
            content=new_post["content"],
            image_url=new_post.get("image_url"),
            is_ai_story=True,
            created_at=new_post["created_at"],
            likes=0,
            comments=0,
            pet_name=pet.name,
            pet_breed=pet.breed,
            pet_avatar=pet.avatar_url,
            diary_entry_id=diary_entry.id
        )
        
    except HTTPException:
        # 重新抛出 HTTP 异常（包括 499 客户端取消）
        raise
    except Exception as e:
        logger.error(f"处理视频时发生错误: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理视频时发生错误: {str(e)}"
        )
    finally:
        # 清理临时文件
        if video_path and os.path.exists(video_path):
            try:
                os.unlink(video_path)
                logger.info(f"已清理临时文件: {video_path}")
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")


# ===========================================
# 获取帖子列表（关注）
# ===========================================

@router.get(
    "/posts/following",
    response_model=List[SocialPostResponse],
    summary="获取关注动态",
    description="获取关注用户的帖子列表"
)
async def get_following_posts(
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id)
):
    """
    获取关注的动态
    
    返回关注用户发布的帖子（目前返回所有帖子作为演示）
    """
    posts = await db.select(
        Tables.SOCIAL_POSTS,
        order_by="created_at.desc",
        limit=limit
    )
    
    result = []
    for post in posts:
        # 获取宠物信息
        pet = await pet_service.get_pet(post["pet_id"])
        
        result.append(SocialPostResponse(
            id=post["id"],
            pet_id=post["pet_id"],
            user_id=post["user_id"],
            content=post["content"],
            image_url=post.get("image_url"),
            is_ai_story=post.get("is_ai_story", False),
            created_at=post["created_at"],
            likes=post.get("likes", 0),
            comments=post.get("comments", 0),
            pet_name=pet.name if pet else "未知",
            pet_breed=pet.breed if pet else "未知",
            pet_avatar=pet.avatar_url if pet else None
        ))
    
    return result


# ===========================================
# 获取发现页帖子
# ===========================================

@router.get(
    "/posts/discovery",
    response_model=List[SocialPostResponse],
    summary="获取发现页动态",
    description="获取推荐的热门帖子"
)
async def get_discovery_posts(
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id)
):
    """
    获取发现页动态
    
    返回热门推荐的帖子
    """
    # 按点赞数排序获取热门帖子
    posts = await db.select(
        Tables.SOCIAL_POSTS,
        order_by="likes.desc",
        limit=limit
    )
    
    result = []
    for post in posts:
        pet = await pet_service.get_pet(post["pet_id"])
        
        result.append(SocialPostResponse(
            id=post["id"],
            pet_id=post["pet_id"],
            user_id=post["user_id"],
            content=post["content"],
            image_url=post.get("image_url"),
            is_ai_story=post.get("is_ai_story", False),
            created_at=post["created_at"],
            likes=post.get("likes", 0),
            comments=post.get("comments", 0),
            pet_name=pet.name if pet else "未知",
            pet_breed=pet.breed if pet else "未知",
            pet_avatar=pet.avatar_url if pet else None
        ))
    
    return result


# ===========================================
# 获取用户的帖子
# ===========================================

@router.get(
    "/posts/user/{target_user_id}",
    response_model=List[SocialPostResponse],
    summary="获取用户帖子",
    description="获取指定用户的所有帖子"
)
async def get_user_posts(
    target_user_id: str,
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id)
):
    """
    获取指定用户的帖子
    """
    posts = await db.select(
        Tables.SOCIAL_POSTS,
        filters={"user_id": target_user_id},
        order_by="created_at.desc",
        limit=limit
    )
    
    result = []
    for post in posts:
        pet = await pet_service.get_pet(post["pet_id"])
        
        result.append(SocialPostResponse(
            id=post["id"],
            pet_id=post["pet_id"],
            user_id=post["user_id"],
            content=post["content"],
            image_url=post.get("image_url"),
            is_ai_story=post.get("is_ai_story", False),
            created_at=post["created_at"],
            likes=post.get("likes", 0),
            comments=post.get("comments", 0),
            pet_name=pet.name if pet else "未知",
            pet_breed=pet.breed if pet else "未知",
            pet_avatar=pet.avatar_url if pet else None
        ))
    
    return result


# ===========================================
# 点赞帖子
# ===========================================

@router.post(
    "/posts/{post_id}/like",
    response_model=SuccessResponse,
    summary="点赞帖子",
    description="为帖子点赞"
)
async def like_post(
    post_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    点赞帖子
    """
    # 获取帖子
    post = await db.select_one(Tables.SOCIAL_POSTS, {"id": post_id})
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"
        )
    
    # 增加点赞数
    await db.update(
        Tables.SOCIAL_POSTS,
        {"id": post_id},
        {"likes": post.get("likes", 0) + 1}
    )
    
    return SuccessResponse(message="点赞成功")


# ===========================================
# 取消点赞
# ===========================================

@router.delete(
    "/posts/{post_id}/like",
    response_model=SuccessResponse,
    summary="取消点赞",
    description="取消帖子点赞"
)
async def unlike_post(
    post_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    取消点赞
    """
    post = await db.select_one(Tables.SOCIAL_POSTS, {"id": post_id})
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"
        )
    
    # 减少点赞数
    new_likes = max(0, post.get("likes", 0) - 1)
    await db.update(
        Tables.SOCIAL_POSTS,
        {"id": post_id},
        {"likes": new_likes}
    )
    
    return SuccessResponse(message="已取消点赞")


# ===========================================
# 删除帖子
# ===========================================

@router.delete(
    "/posts/{post_id}",
    response_model=SuccessResponse,
    summary="删除帖子",
    description="删除自己发布的帖子"
)
async def delete_post(
    post_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    删除帖子
    
    只能删除自己发布的帖子
    """
    # 验证所有权
    post = await db.select_one(
        Tables.SOCIAL_POSTS,
        {"id": post_id, "user_id": user_id}
    )
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在或无权删除"
        )
    
    await db.delete(Tables.SOCIAL_POSTS, {"id": post_id})
    
    return SuccessResponse(message="帖子已删除")
