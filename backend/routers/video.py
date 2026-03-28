"""
视频处理相关 API 路由
处理视频上传、分析和日记生成
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, BackgroundTasks
from typing import Optional
import tempfile
import os
from pathlib import Path

from auth import get_current_user_id
from services.video_service import video_service
from services.diary_service import diary_service
from config import settings
from base_models import (
    VideoJobResponse, VideoProcessResult,
    DiaryEntryResponse, SuccessResponse
)

router = APIRouter(prefix="/video", tags=["视频处理"])


# ===========================================
# 同步处理视频
# ===========================================

@router.post(
    "/process",
    response_model=VideoProcessResult,
    summary="处理视频（同步）",
    description="上传并处理视频，等待处理完成后返回结果"
)
async def process_video_sync(
    file: UploadFile = File(..., description="视频文件 (mp4, avi, mov)"),
    mode: str = Form(default="api", description="处理模式: local 或 api"),
    pet_id: Optional[str] = Form(default=None, description="关联的宠物ID"),
    user_id: str = Depends(get_current_user_id)
):
    """
    同步处理视频
    
    上传视频文件，等待处理完成后返回分析结果和生成的故事。
    适用于较短的视频（< 30秒）。
    
    对于较长的视频，建议使用异步处理接口 `/video/process/async`
    """
    # 验证文件类型
    if not file.content_type or not file.content_type.startswith('video/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的文件类型: {file.content_type}，请上传视频文件"
        )
    
    # 检查文件大小
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件过大，最大允许 {settings.MAX_UPLOAD_SIZE_MB}MB"
        )
    
    # 保存临时文件
    suffix = Path(file.filename).suffix if file.filename else ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # 处理视频
        result = await video_service.process_video_sync(
            video_path=tmp_path,
            mode=mode,
            pet_id=pet_id,
            user_id=user_id
        )
        
        return result
        
    finally:
        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


# ===========================================
# 异步处理视频
# ===========================================

@router.post(
    "/process/async",
    summary="处理视频（异步）",
    description="上传视频并创建异步处理任务，立即返回任务ID"
)
async def process_video_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="视频文件"),
    mode: str = Form(default="api", description="处理模式"),
    pet_id: Optional[str] = Form(default=None, description="关联的宠物ID"),
    user_id: str = Depends(get_current_user_id)
):
    """
    异步处理视频
    
    上传视频后立即返回任务ID，可通过 `/video/jobs/{job_id}` 查询处理状态。
    适用于较长的视频或需要后台处理的场景。
    """
    # 验证文件类型
    if not file.content_type or not file.content_type.startswith('video/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请上传视频文件"
        )
    
    # 确保上传目录存在
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(exist_ok=True)
    
    # 保存上传的文件
    import uuid
    file_id = str(uuid.uuid4())
    suffix = Path(file.filename).suffix if file.filename else ".mp4"
    file_path = upload_dir / f"{file_id}{suffix}"
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 创建异步任务
    job_id = await video_service.process_video_async(
        video_path=str(file_path),
        mode=mode,
        pet_id=pet_id,
        user_id=user_id
    )
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "视频处理任务已创建",
        "check_status_url": f"/api/v1/video/jobs/{job_id}"
    }


# ===========================================
# 查询任务状态
# ===========================================

@router.get(
    "/jobs/{job_id}",
    summary="查询任务状态",
    description="查询异步视频处理任务的状态和结果"
)
async def get_job_status(
    job_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    查询视频处理任务状态
    
    返回任务的当前状态、进度和结果（如果已完成）
    """
    job = video_service.get_job_status(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    return job


# ===========================================
# 列出所有任务
# ===========================================

@router.get(
    "/jobs",
    summary="列出所有任务",
    description="列出当前用户的所有视频处理任务"
)
async def list_jobs(user_id: str = Depends(get_current_user_id)):
    """
    列出所有视频处理任务
    """
    jobs = video_service.list_jobs(user_id)
    return {
        "total": len(jobs),
        "jobs": jobs
    }


# ===========================================
# 取消任务
# ===========================================

@router.post(
    "/jobs/{job_id}/cancel",
    response_model=SuccessResponse,
    summary="取消任务",
    description="取消正在处理的视频任务"
)
async def cancel_job(
    job_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    取消视频处理任务
    
    只能取消 pending 或 processing 状态的任务
    """
    success = await video_service.cancel_job(job_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法取消任务（任务不存在或已完成）"
        )
    
    return SuccessResponse(message="任务已取消")


# ===========================================
# 删除任务
# ===========================================

@router.delete(
    "/jobs/{job_id}",
    response_model=SuccessResponse,
    summary="删除任务",
    description="删除指定的视频处理任务"
)
async def delete_job(
    job_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    删除视频处理任务
    """
    success = video_service.delete_job(job_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    return SuccessResponse(message="任务已删除")


# ===========================================
# 从视频生成日记
# ===========================================

@router.post(
    "/to-diary",
    response_model=DiaryEntryResponse,
    summary="视频转日记",
    description="上传视频，分析后自动生成宠物日记"
)
async def video_to_diary(
    file: UploadFile = File(..., description="视频文件"),
    pet_id: str = Form(..., description="宠物ID"),
    mode: str = Form(default="api", description="处理模式"),
    user_id: str = Depends(get_current_user_id)
):
    """
    视频转日记
    
    上传宠物视频，AI 会分析视频内容并自动生成一篇日记。
    这是 pet-vision-narrator 的核心功能。
    
    流程：
    1. 上传视频
    2. AI 分析视频内容（检测活动、物体、情绪等）
    3. 生成第一人称叙事故事
    4. 创建日记条目
    """
    # 验证文件
    if not file.content_type or not file.content_type.startswith('video/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请上传视频文件"
        )
    
    # 保存临时文件
    suffix = Path(file.filename).suffix if file.filename else ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # 处理视频
        result = await video_service.process_video_sync(
            video_path=tmp_path,
            mode=mode,
            pet_id=pet_id,
            user_id=user_id
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"视频处理失败: {result.error}"
            )
        
        # 生成日记
        diary_entry = await diary_service.generate_diary_from_video(
            user_id=user_id,
            pet_id=pet_id,
            video_result=result
        )
        
        return diary_entry
        
    finally:
        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
