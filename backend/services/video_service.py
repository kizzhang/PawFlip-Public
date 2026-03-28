"""
视频处理服务模块
通过 HTTP API 调用 pet-vision-narrator 服务
"""

import logging
import asyncio
import uuid
import os
import aiohttp
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from config import settings
from database import db, Tables
from base_models import VideoJobStatus, VideoProcessResult

logger = logging.getLogger(__name__)


# ===========================================
# 配置
# ===========================================

# pet-vision-narrator API 服务地址
NARRATOR_API_URL = os.getenv("NARRATOR_API_URL", "http://localhost:8002")

# API 超时设置（秒）
API_TIMEOUT = int(os.getenv("NARRATOR_API_TIMEOUT", "300"))  # 5分钟

# 视频处理任务存储（内存）
_video_jobs: Dict[str, Dict[str, Any]] = {}


# ===========================================
# 视频处理服务
# ===========================================

class VideoService:
    """
    视频处理服务
    通过 HTTP API 调用 pet-vision-narrator
    """
    
    def __init__(self):
        self.api_url = NARRATOR_API_URL
        self.api_timeout = API_TIMEOUT
        logger.info(f"VideoService 初始化 - API地址: {self.api_url}")

    async def _process_with_simulator(self, video_path: str) -> "VideoProcessResult":
        """当 narrator 服务不可用时，用 OpenRouter 视频模型分析并生成故事"""
        import base64
        import json as json_module
        from config import settings

        api_key = settings.OPENROUTER_API_KEY
        model = settings.OPENROUTER_VIDEO_MODEL or "google/gemini-2.0-flash-001"

        if not api_key:
            # 没有 OpenRouter key，尝试 Gemini
            api_key_gemini = settings.GOOGLE_API_KEY
            if not api_key_gemini:
                logger.warning("OpenRouter 和 Gemini API Key 均未配置，使用模拟器")
                from services.narrator_simulator import video_processor_simulator, story_generator_simulator
                analysis_result = video_processor_simulator.analyze_video(video_path)
                if not analysis_result.get("success"):
                    return VideoProcessResult(success=False, error=analysis_result.get("error", "模拟分析失败"))
                analysis = analysis_result.get("analysis", {})
                story_result = story_generator_simulator.generate_story(analysis)
                return VideoProcessResult(
                    success=True,
                    video_analysis=analysis,
                    narrative=story_result.get("story") if story_result.get("success") else None,
                    metadata={"mode": "simulator"},
                )

        try:
            logger.info(f"使用 OpenRouter ({model}) 分析视频...")

            # 读取视频并 base64 编码
            with open(video_path, "rb") as f:
                video_b64 = base64.b64encode(f.read()).decode("utf-8")
            logger.info(f"  → 视频已编码 ({len(video_b64) / 1024 / 1024:.1f} MB base64)")

            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            # 第一步：分析视频内容
            analysis_prompt = '请分析这个宠物视频，以JSON格式返回。只返回JSON，不要其他文字：\n{"summary":"视频内容简要描述","scenes":[{"description":"场景描述","timestamp":"时间段","confidence":"0.9"}],"detected_objects":["物体"],"activities":["活动"],"emotional_context":["情绪"]}'

            payload = {
                "model": model,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "video_url", "video_url": {"url": f"data:video/mp4;base64,{video_b64}"}},
                        {"type": "text", "text": analysis_prompt},
                    ]
                }],
                "max_tokens": 1024,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"OpenRouter 分析失败 ({resp.status}): {error_text[:300]}")
                    data = await resp.json()

            analysis_text = data["choices"][0]["message"]["content"].strip()

            # 去掉 markdown 代码块
            if analysis_text.startswith("```"):
                analysis_text = analysis_text.split("\n", 1)[1]
                if analysis_text.endswith("```"):
                    analysis_text = analysis_text[:-3]
                analysis_text = analysis_text.strip()

            try:
                analysis = json_module.loads(analysis_text)
                for scene in analysis.get("scenes", []):
                    for k, v in list(scene.items()):
                        scene[k] = str(v)
            except json_module.JSONDecodeError:
                analysis = {
                    "summary": analysis_text[:200],
                    "scenes": [],
                    "detected_objects": [],
                    "activities": [],
                    "emotional_context": [],
                }

            logger.info(f"  → 视频分析完成: {analysis.get('summary', '')[:80]}...")

            # 第二步：基于分析结果生成第一人称故事
            story_prompt = f"""基于以下视频分析结果，以宠物的第一人称视角写一段有趣的日记故事（中文，150-300字）。
    要求：语气可爱、活泼，像宠物在讲述自己的一天。

    视频分析：
    {json_module.dumps(analysis, ensure_ascii=False, indent=2)}

    请直接输出故事文字，不要加标题或其他格式。"""

            story_payload = {
                "model": model,
                "messages": [{"role": "user", "content": story_prompt}],
                "max_tokens": 1024,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=story_payload, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"OpenRouter 故事生成失败 ({resp.status}): {error_text[:300]}")
                    story_data = await resp.json()

            story_text = story_data["choices"][0]["message"]["content"].strip()
            logger.info(f"  → 故事生成完成 ({len(story_text)} 字)")

            return VideoProcessResult(
                success=True,
                video_analysis=analysis,
                narrative={"story": story_text, "style": "first-person pet POV", "tone": "playful"},
                metadata={"mode": "openrouter", "vision_model": model},
            )

        except Exception as e:
            logger.error(f"OpenRouter 视频分析失败: {e}", exc_info=True)
            return VideoProcessResult(success=False, error=f"视频分析失败: {str(e)}")
    
    async def check_narrator_health(self) -> bool:
        """
        检查 pet-vision-narrator 服务是否可用
        
        Returns:
            服务是否健康
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Narrator 服务健康: {data}")
                        return True
                    return False
        except Exception as e:
            logger.error(f"检查 Narrator 服务健康失败: {e}")
            return False
    
    async def process_video_sync(
        self,
        video_path: str,
        mode: str = "local",
        pet_id: Optional[str] = None,
        user_id: Optional[str] = None,
        use_frame_sampling: Optional[bool] = None,
        enable_llm_analysis: Optional[bool] = None,
        request: Optional[Any] = None  # FastAPI Request 对象，用于检测断开
    ) -> VideoProcessResult:
        """
        同步处理视频（等待完成）
        调用 pet-vision-narrator 的同步 API
        
        Args:
            video_path: 视频文件路径
            mode: 处理模式 (local/api)
            pet_id: 关联的宠物ID
            user_id: 用户ID
            use_frame_sampling: 是否使用帧采样
            enable_llm_analysis: 是否启用LLM分析
            request: FastAPI Request 对象，用于检测客户端断开
            
        Returns:
            视频处理结果
        """
        try:
            logger.info(f"开始同步处理视频: {video_path}")
            
            # 检查客户端是否已断开
            if request and await request.is_disconnected():
                logger.info("客户端已断开连接，取消视频处理")
                return VideoProcessResult(
                    success=False,
                    error="客户端取消请求"
                )
            
            # 检查文件是否存在
            if not os.path.exists(video_path):
                return VideoProcessResult(
                    success=False,
                    error=f"视频文件不存在: {video_path}"
                )
            
            # 准备表单数据
            form_data = aiohttp.FormData()
            
            # 添加视频文件
            with open(video_path, 'rb') as f:
                form_data.add_field(
                    'file',
                    f,
                    filename=os.path.basename(video_path),
                    content_type='video/mp4'
                )
                
                # 添加其他参数
                form_data.add_field('mode', mode)
                if use_frame_sampling is not None:
                    form_data.add_field('use_frame_sampling', str(use_frame_sampling).lower())
                if enable_llm_analysis is not None:
                    form_data.add_field('enable_llm_analysis', str(enable_llm_analysis).lower())
                
                # 再次检查客户端连接
                if request and await request.is_disconnected():
                    logger.info("客户端已断开连接，取消视频处理")
                    return VideoProcessResult(
                        success=False,
                        error="客户端取消请求"
                    )
                
                # 调用 API
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.api_url}/api/v1/process",
                        data=form_data,
                        timeout=aiohttp.ClientTimeout(total=self.api_timeout)
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info("视频处理成功")
                            
                            return VideoProcessResult(
                                success=result.get("success", True),
                                video_analysis=result.get("video_analysis"),
                                narrative=result.get("narrative"),
                                metadata=result.get("metadata")
                            )
                        else:
                            error_text = await response.text()
                            logger.error(f"API 返回错误: {response.status} - {error_text}")
                            return VideoProcessResult(
                                success=False,
                                error=f"API 错误 ({response.status}): {error_text}"
                            )
                            
        except asyncio.TimeoutError:
            logger.error("视频处理超时")
            return VideoProcessResult(
                success=False,
                error=f"处理超时（超过 {self.api_timeout} 秒）"
            )
        except Exception as e:
            # 检查是否是客户端断开导致的
            if request and await request.is_disconnected():
                logger.info("客户端已断开连接")
                return VideoProcessResult(
                    success=False,
                    error="客户端取消请求"
                )
            
            logger.error(f"视频处理失败: {e}", exc_info=True)
            
            # 如果是连接错误（narrator 服务不可用），fallback 到模拟器
            if isinstance(e, (aiohttp.ClientConnectorError, ConnectionRefusedError, OSError)):
                logger.warning("Narrator 服务连接失败，自动切换到模拟器模式")
                return await self._process_with_simulator(video_path)
            
            return VideoProcessResult(
                success=False,
                error=str(e)
            )
    
    async def process_video_async(
        self,
        video_path: str,
        mode: str = "local",
        pet_id: Optional[str] = None,
        user_id: Optional[str] = None,
        use_frame_sampling: Optional[bool] = None,
        enable_llm_analysis: Optional[bool] = None
    ) -> str:
        """
        异步处理视频（返回任务ID）
        调用 pet-vision-narrator 的异步 API
        
        Args:
            video_path: 视频文件路径
            mode: 处理模式
            pet_id: 关联的宠物ID
            user_id: 用户ID
            use_frame_sampling: 是否使用帧采样
            enable_llm_analysis: 是否启用LLM分析
            
        Returns:
            任务ID
        """
        try:
            logger.info(f"开始异步处理视频: {video_path}")
            
            # 检查文件是否存在
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"视频文件不存在: {video_path}")
            
            # 准备表单数据
            form_data = aiohttp.FormData()
            
            # 添加视频文件
            with open(video_path, 'rb') as f:
                form_data.add_field(
                    'file',
                    f,
                    filename=os.path.basename(video_path),
                    content_type='video/mp4'
                )
                
                # 添加其他参数
                form_data.add_field('mode', mode)
                if use_frame_sampling is not None:
                    form_data.add_field('use_frame_sampling', str(use_frame_sampling).lower())
                if enable_llm_analysis is not None:
                    form_data.add_field('enable_llm_analysis', str(enable_llm_analysis).lower())
                
                # 调用异步 API
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.api_url}/api/v1/process/async",
                        data=form_data,
                        timeout=aiohttp.ClientTimeout(total=60)  # 上传超时60秒
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            narrator_job_id = result.get("job_id")
                            
                            # 创建本地任务记录
                            local_job_id = str(uuid.uuid4())
                            _video_jobs[local_job_id] = {
                                "job_id": local_job_id,
                                "narrator_job_id": narrator_job_id,
                                "status": VideoJobStatus.PENDING,
                                "progress": "任务已提交到 Narrator 服务",
                                "video_path": video_path,
                                "mode": mode,
                                "pet_id": pet_id,
                                "user_id": user_id,
                                "created_at": datetime.now().isoformat(),
                                "completed_at": None,
                                "result": None,
                                "error": None
                            }
                            
                            # 如果配置了数据库，保存到数据库
                            if user_id:
                                try:
                                    await db.insert(Tables.VIDEO_JOBS, {
                                        "id": local_job_id,
                                        "user_id": user_id,
                                        "pet_id": pet_id,
                                        "status": VideoJobStatus.PENDING.value,
                                        "video_path": video_path
                                    })
                                except Exception as e:
                                    logger.warning(f"保存任务到数据库失败: {e}")
                            
                            # 启动后台轮询任务
                            asyncio.create_task(
                                self._poll_narrator_job(local_job_id, narrator_job_id)
                            )
                            
                            logger.info(f"创建异步任务: {local_job_id} (Narrator: {narrator_job_id})")
                            return local_job_id
                        else:
                            error_text = await response.text()
                            raise Exception(f"API 错误 ({response.status}): {error_text}")
                            
        except Exception as e:
            logger.error(f"创建异步任务失败: {e}", exc_info=True)
            raise
    
    async def _poll_narrator_job(self, local_job_id: str, narrator_job_id: str):
        """
        轮询 pet-vision-narrator 的任务状态
        
        Args:
            local_job_id: 本地任务ID
            narrator_job_id: Narrator 服务的任务ID
        """
        job = _video_jobs.get(local_job_id)
        if not job:
            return
        
        try:
            # 更新状态为处理中
            job["status"] = VideoJobStatus.PROCESSING
            job["progress"] = "正在处理视频..."
            
            # 轮询 Narrator 服务
            async with aiohttp.ClientSession() as session:
                while True:
                    # 检查本地任务是否已被取消
                    if job["status"] == VideoJobStatus.FAILED and job.get("error") == "用户取消":
                        logger.info(f"任务 {local_job_id} 已被取消，停止轮询")
                        break
                    
                    try:
                        async with session.get(
                            f"{self.api_url}/api/v1/jobs/{narrator_job_id}",
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            if response.status == 200:
                                status_data = await response.json()
                                narrator_status = status_data.get("status")
                                
                                # 更新进度
                                job["progress"] = status_data.get("progress", "处理中...")
                                
                                if narrator_status == "completed":
                                    # 处理完成
                                    result = status_data.get("result")
                                    job["status"] = VideoJobStatus.COMPLETED
                                    job["progress"] = "处理完成"
                                    job["result"] = result
                                    job["completed_at"] = datetime.now().isoformat()
                                    
                                    # 更新数据库
                                    if job.get("user_id"):
                                        try:
                                            await db.update(
                                                Tables.VIDEO_JOBS,
                                                {"id": local_job_id},
                                                {
                                                    "status": VideoJobStatus.COMPLETED.value,
                                                    "result": result,
                                                    "completed_at": job["completed_at"]
                                                }
                                            )
                                        except Exception as e:
                                            logger.warning(f"更新数据库失败: {e}")
                                    
                                    logger.info(f"任务 {local_job_id} 处理完成")
                                    break
                                    
                                elif narrator_status in ["failed", "cancelled"]:
                                    # 处理失败或被取消
                                    error = status_data.get("error", "未知错误")
                                    job["status"] = VideoJobStatus.FAILED
                                    job["error"] = error
                                    job["completed_at"] = datetime.now().isoformat()
                                    
                                    logger.error(f"任务 {local_job_id} 处理失败: {error}")
                                    break
                                    
                                # 继续轮询
                                await asyncio.sleep(2)
                                
                            elif response.status == 404:
                                # 任务不存在
                                job["status"] = VideoJobStatus.FAILED
                                job["error"] = "Narrator 服务中找不到任务"
                                job["completed_at"] = datetime.now().isoformat()
                                break
                            else:
                                # 其他错误，继续重试
                                await asyncio.sleep(2)
                                
                    except asyncio.TimeoutError:
                        # 超时，继续重试
                        await asyncio.sleep(2)
                        
        except Exception as e:
            logger.error(f"轮询任务状态失败: {e}", exc_info=True)
            job["status"] = VideoJobStatus.FAILED
            job["error"] = f"轮询失败: {str(e)}"
            job["completed_at"] = datetime.now().isoformat()
        
        finally:
            # 清理临时文件
            try:
                if os.path.exists(job["video_path"]):
                    os.unlink(job["video_path"])
                    logger.info(f"已清理临时文件: {job['video_path']}")
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            job_id: 任务ID
            
        Returns:
            任务状态信息
        """
        job = _video_jobs.get(job_id)
        if not job:
            return None
        
        return {
            "job_id": job["job_id"],
            "status": job["status"].value if isinstance(job["status"], VideoJobStatus) else job["status"],
            "progress": job["progress"],
            "result": job["result"],
            "error": job["error"],
            "created_at": job["created_at"],
            "completed_at": job["completed_at"]
        }
    
    def list_jobs(self, user_id: Optional[str] = None) -> list:
        """
        列出所有任务
        
        Args:
            user_id: 可选，按用户过滤
            
        Returns:
            任务列表
        """
        jobs = []
        for job in _video_jobs.values():
            if user_id and job.get("user_id") != user_id:
                continue
            jobs.append({
                "job_id": job["job_id"],
                "status": job["status"].value if isinstance(job["status"], VideoJobStatus) else job["status"],
                "created_at": job["created_at"]
            })
        return jobs
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        取消任务
        
        Args:
            job_id: 任务ID
            
        Returns:
            是否取消成功
        """
        job = _video_jobs.get(job_id)
        if not job:
            logger.warning(f"任务 {job_id} 不存在")
            return False
        
        # 只能取消 pending 或 processing 状态的任务
        if job["status"] not in [VideoJobStatus.PENDING, VideoJobStatus.PROCESSING]:
            logger.warning(f"任务 {job_id} 状态为 {job['status']}，无法取消")
            return False
        
        try:
            # 调用 narrator 服务取消任务
            narrator_job_id = job.get("narrator_job_id")
            if narrator_job_id:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.delete(
                            f"{self.api_url}/api/v1/jobs/{narrator_job_id}",
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            if response.status == 200:
                                logger.info(f"已取消 Narrator 任务: {narrator_job_id}")
                            else:
                                logger.warning(f"取消 Narrator 任务失败: {response.status}")
                except Exception as e:
                    logger.warning(f"调用 Narrator 取消 API 失败: {e}")
            
            # 更新本地任务状态
            job["status"] = VideoJobStatus.FAILED
            job["error"] = "用户取消"
            job["completed_at"] = datetime.now().isoformat()
            
            # 清理临时文件
            try:
                if os.path.exists(job["video_path"]):
                    os.unlink(job["video_path"])
                    logger.info(f"已清理临时文件: {job['video_path']}")
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")
            
            # 更新数据库
            if job.get("user_id"):
                try:
                    await db.update(
                        Tables.VIDEO_JOBS,
                        {"id": job_id},
                        {
                            "status": VideoJobStatus.FAILED.value,
                            "error": "用户取消",
                            "completed_at": job["completed_at"]
                        }
                    )
                except Exception as e:
                    logger.warning(f"更新数据库失败: {e}")
            
            logger.info(f"任务 {job_id} 已取消")
            return True
            
        except Exception as e:
            logger.error(f"取消任务失败: {e}", exc_info=True)
            return False
    
    def delete_job(self, job_id: str) -> bool:
        """
        删除任务
        
        Args:
            job_id: 任务ID
            
        Returns:
            是否删除成功
        """
        if job_id in _video_jobs:
            del _video_jobs[job_id]
            return True
        return False


# 导出视频服务实例
video_service = VideoService()
