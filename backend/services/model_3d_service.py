"""
3D 模型生成服务
支持从宠物照片生成 3D 模型
统一的本地/云端接口
"""

import logging
import asyncio
import aiohttp
import base64
import json as json_module
from typing import Dict, Any, Optional
from pathlib import Path
import time

from config import settings

logger = logging.getLogger(__name__)


# ===========================================
# 3D 模型生成统一接口
# ===========================================

class Model3DService:
    """
    3D 模型生成服务
    支持本地和云端两种模式
    """

    def __init__(self):
        raw_provider = settings.MODEL_3D_PROVIDER.lower()
        self.provider = raw_provider
        self.mode = "cloud" if raw_provider in {"hunyuan", "meshy", "tripo", "cloud"} else "local"

        # 兼容旧配置: cloud 模式按 key 自动选择提供商
        if raw_provider == "cloud":
            if settings.HUNYUAN_API_KEY:
                self.provider = "hunyuan"
            elif settings.MESHY_API_KEY:
                self.provider = "meshy"
            elif settings.TRIPO_API_KEY:
                self.provider = "tripo"
            else:
                self.provider = "local"
                self.mode = "local"

        self.cloud_api_key = self._resolve_api_key(self.provider)
        self.cloud_api_url = self._resolve_api_url(self.provider)

        if self.mode == "cloud" and not self.cloud_api_key:
            logger.warning(f"{self.provider} 模式未配置 API Key，将使用本地模拟模式")
            self.mode = "local"
            self.provider = "local"

        logger.info(f"3D 模型服务初始化: {self.mode} 模式, provider={self.provider}")

    async def generate_pet_model(
        self,
        image_path: str,
        pet_name: str,
        pet_breed: str
    ) -> Dict[str, Any]:
        """为宠物生成 3D 模型"""

        logger.info(f"开始为 {pet_name}（{pet_breed}）生成 3D 模型...")
        logger.info(f"使用模式: {self.mode}")

        try:
            if self.mode == "cloud":
                result = await self._generate_cloud(image_path, pet_name, pet_breed)
            else:
                result = await self._generate_local(image_path, pet_name, pet_breed)

            if result.get("success"):
                logger.info("✓ 3D 模型生成成功")
                await self._save_model_info(result, pet_name)
            else:
                logger.error(f"✗ 3D 模型生成失败: {result.get('error')}")

            return result

        except Exception as e:
            logger.error(f"3D 模型生成异常: {e}")
            return {"success": False, "error": str(e), "mode": self.mode}

    # ===========================================
    # 云端生成实现
    # ===========================================

    async def _generate_cloud(
        self, image_path: str, pet_name: str, pet_breed: str
    ) -> Dict[str, Any]:
        """使用云端 API 生成 3D 模型"""

        if self.provider == "hunyuan":
            return await self._generate_hunyuan(image_path, pet_name, pet_breed)

        if self.provider == "tripo":
            return {
                "success": False,
                "error": "当前版本暂未实现 Tripo 接口，请切换到 hunyuan 或 meshy",
                "mode": "cloud",
                "provider": "tripo",
            }

        return await self._generate_meshy(image_path, pet_name, pet_breed)

    async def _generate_hunyuan(
        self, image_path: str, pet_name: str, pet_breed: str
    ) -> Dict[str, Any]:
        """
        使用混元生3D（专业版）OpenAI 兼容接口生成模型。
        提交: POST https://api.ai3d.cloud.tencent.com/v1/ai3d/submit
        查询: POST https://api.ai3d.cloud.tencent.com/v1/ai3d/query
        """

        try:
            logger.info("  → 准备图片数据...")
            with open(image_path, "rb") as f:
                image_data = f.read()
                image_base64 = base64.b64encode(image_data).decode()

            # data URL 格式: data:image/jpeg;base64,xxxxxxx
            image_data_url = f"data:image/jpeg;base64,{image_base64}"

            headers = {
                "Authorization": self.cloud_api_key,
                "Content-Type": "application/json",
            }

            # OpenAI 兼容接口 (映射到 SubmitHunyuanTo3DProJob)
            # 尝试使用 ImageBase64 (纯 base64，不含 data URL 前缀)
            payload: Dict[str, Any] = {
                "ImageBase64": image_base64,
            }
            if settings.HUNYUAN_MODEL:
                payload["Model"] = settings.HUNYUAN_MODEL

            logger.info(f"  → payload keys: {list(payload.keys())}, ImageBase64 length: {len(image_base64)}")
            logger.info(f"  → Model: {payload.get('Model')}")

            submit_url = f"{self.cloud_api_url}/v1/ai3d/submit"
            logger.info(f"  → 提交混元 3D 任务: {submit_url}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    submit_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    resp_text = await response.text()
                    if response.status not in (200, 201, 202):
                        raise Exception(
                            f"混元任务提交失败 ({response.status}): {resp_text}"
                        )
                    try:
                        create_result = json_module.loads(resp_text)
                    except Exception:
                        raise Exception(f"混元返回非 JSON: {resp_text}")

            # 响应: {"Response": {"JobId": "...", "RequestId": "..."}}
            response_data = create_result.get("Response", create_result)

            # 检查错误
            error = response_data.get("Error")
            if error:
                raise Exception(
                    f"混元任务提交失败: [{error.get('Code')}] {error.get('Message')}"
                )

            job_id = response_data.get("JobId")
            if not job_id:
                raise Exception(f"混元返回中未找到 JobId，响应: {create_result}")

            logger.info(f"  → 混元任务已创建: {job_id}")
            result = await self._wait_for_completion_hunyuan(job_id)

            return {
                "success": True,
                "model_url": result.get("model_url"),
                "preview_url": result.get("preview_url"),
                "task_id": job_id,
                "mode": "cloud",
                "provider": "hunyuan",
                "metadata": result,
            }

        except Exception as e:
            logger.error(f"混元生成失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "mode": "cloud",
                "provider": "hunyuan",
            }

    async def _wait_for_completion_hunyuan(
        self, job_id: str, max_wait_seconds: int = 600
    ) -> Dict[str, Any]:
        """轮询混元任务状态 (POST /v1/ai3d/query)，每次请求用新连接避免被服务器断开"""

        headers = {
            "Authorization": self.cloud_api_key,
            "Content-Type": "application/json",
        }
        query_url = f"{self.cloud_api_url}/v1/ai3d/query"
        start_time = time.time()
        consecutive_errors = 0

        while True:
            if time.time() - start_time > max_wait_seconds:
                raise TimeoutError("混元 3D 任务超时")

            # 每次轮询用新的 session，避免长连接被服务器 RST
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        query_url,
                        headers=headers,
                        json={"JobId": job_id},
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as response:
                        body_text = await response.text()
                        if response.status != 200:
                            raise Exception(
                                f"混元状态查询失败 ({response.status}): {body_text}"
                            )
                        try:
                            body = json_module.loads(body_text)
                        except Exception:
                            body = {"raw": body_text}

                consecutive_errors = 0  # 请求成功，重置计数

            except (OSError, aiohttp.ClientError, ConnectionError) as e:
                consecutive_errors += 1
                logger.warning(f"     轮询连接异常 ({consecutive_errors}/5): {e}")
                if consecutive_errors >= 5:
                    raise Exception(f"混元轮询连续失败 {consecutive_errors} 次: {e}")
                await asyncio.sleep(3)
                continue

            response_data = body.get("Response", body)

            # 检查 API 错误
            error = response_data.get("Error")
            if error:
                raise Exception(
                    f"混元查询失败: [{error.get('Code')}] {error.get('Message')}"
                )

            status = str(response_data.get("Status", "")).upper()
            logger.info(f"     混元任务状态: {status or 'UNKNOWN'}")

            if status in {"SUCCEEDED", "SUCCESS", "COMPLETED", "DONE", "FINISHED"}:
                model_url = self._extract_hunyuan_model_url(response_data)
                preview_url = self._extract_hunyuan_preview_url(response_data)

                if not model_url:
                    raise Exception(
                        f"混元任务已完成但未返回模型地址，响应: {response_data}"
                    )

                return {
                    "model_url": model_url,
                    "preview_url": preview_url,
                    "status": status,
                    "raw": response_data,
                }

            if status in {"FAILED", "ERROR", "CANCELLED", "CANCELED", "EXPIRED"}:
                error_msg = (
                    response_data.get("ErrorMsg")
                    or response_data.get("Message")
                    or "未知错误"
                )
                raise Exception(f"混元任务失败: {error_msg}")

            await asyncio.sleep(8)

    def _extract_hunyuan_model_url(self, data: Dict[str, Any]) -> Optional[str]:
        """从混元查询响应中提取模型下载 URL"""
        # ResultFile3Ds: [{"Type": "OBJ", "Url": "...", "PreviewImageUrl": "..."}, {"Type": "GLB", ...}]
        file3ds = data.get("ResultFile3Ds")
        if isinstance(file3ds, list) and file3ds:
            # 优先 GLB
            for item in file3ds:
                if isinstance(item, dict) and item.get("Type", "").upper() == "GLB":
                    url = item.get("Url")
                    if url:
                        return url
            # 其次取第一个有 Url 的
            for item in file3ds:
                if isinstance(item, dict) and item.get("Url"):
                    return item["Url"]

        # 兜底: 直接字段
        for key in ["ResultUrl", "DownloadUrl", "model_url", "modelUrl", "url"]:
            val = data.get(key)
            if isinstance(val, str) and val:
                return val

        return None

    def _extract_hunyuan_preview_url(self, data: Dict[str, Any]) -> Optional[str]:
        """从混元查询响应中提取预览图 URL"""
        file3ds = data.get("ResultFile3Ds")
        if isinstance(file3ds, list) and file3ds:
            for item in file3ds:
                if isinstance(item, dict) and item.get("PreviewImageUrl"):
                    return item["PreviewImageUrl"]

        for key in ["PreviewUrl", "ThumbnailUrl", "preview_url", "PreviewImageUrl"]:
            val = data.get(key)
            if isinstance(val, str) and val:
                return val

        return None

    async def _generate_meshy(
        self, image_path: str, pet_name: str, pet_breed: str
    ) -> Dict[str, Any]:
        """使用 Meshy API 生成 3D 模型"""

        try:
            logger.info("  → 准备图片数据...")
            image_data = await self._upload_image_base64(image_path)

            logger.info("  → 创建 3D 生成任务...")
            task_id = await self._create_task_cloud(image_data, pet_name, pet_breed)
            logger.info(f"  → 任务已创建: {task_id}")

            logger.info("  → 等待模型生成（这可能需要 1-3 分钟）...")
            result = await self._wait_for_completion_cloud(task_id)

            return {
                "success": True,
                "model_url": result.get("model_url"),
                "preview_url": result.get("preview_url"),
                "task_id": task_id,
                "mode": "cloud",
                "provider": "meshy",
                "metadata": result,
            }

        except Exception as e:
            logger.error(f"云端生成失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "mode": "cloud",
                "provider": "meshy",
            }

    async def _upload_image_base64(self, image_path: str) -> str:
        """读取图片并返回 data URL base64"""
        with open(image_path, "rb") as f:
            image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode()
        return f"data:image/jpeg;base64,{image_base64}"

    async def _create_task_cloud(
        self, image_data: str, pet_name: str, pet_breed: str
    ) -> str:
        """创建云端 3D 生成任务（Meshy API）"""

        headers = {
            "Authorization": f"Bearer {self.cloud_api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "image_url": image_data,
            "ai_model": "latest",
            "topology": "triangle",
            "target_polycount": 30000,
            "enable_pbr": True,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.cloud_api_url}/image-to-3d",
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as response:
                response_text = await response.text()

                if response.status not in (200, 202):
                    raise Exception(f"任务创建失败 ({response.status}): {response_text}")

                try:
                    result = await response.json()
                except Exception:
                    result = {"result": response_text}

                return result.get("result") or result.get("id") or result.get("task_id")

    async def _wait_for_completion_cloud(
        self, task_id: str, max_wait_seconds: int = 300
    ) -> Dict[str, Any]:
        """等待云端任务完成（Meshy API）"""

        headers = {"Authorization": f"Bearer {self.cloud_api_key}"}
        start_time = time.time()
        task_started = False

        async with aiohttp.ClientSession() as session:
            while True:
                if not task_started and (time.time() - start_time > max_wait_seconds):
                    raise TimeoutError("3D 模型生成超时（任务未开始）")

                try:
                    async with session.get(
                        f"{self.cloud_api_url}/image-to-3d/{task_id}",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as response:
                        if response.status != 200:
                            error = await response.text()
                            raise Exception(f"状态查询失败: {error}")

                        result = await response.json()
                        status = result.get("status", "").upper()

                        if status in ["IN_PROGRESS", "PROCESSING", "RUNNING"]:
                            task_started = True

                        logger.info(f"     任务状态: {status}")

                        if status in ["SUCCEEDED", "COMPLETED", "DONE"]:
                            logger.info(f"     任务完成，完整响应: {result}")
                            model_urls = result.get("model_urls", {})
                            model_url = (
                                model_urls.get("glb")
                                or model_urls.get("obj")
                                or model_urls.get("fbx")
                                or result.get("model_url")
                            )
                            texture_urls = result.get("texture_urls", {})
                            preview_url = (
                                result.get("thumbnail_url")
                                or result.get("preview_url")
                                or texture_urls.get("base_color")
                                or result.get("image_url")
                            )
                            logger.info(f"     模型 URL: {model_url}")
                            logger.info(f"     预览图 URL: {preview_url}")
                            return {
                                "model_url": model_url,
                                "preview_url": preview_url,
                                "status": status,
                                "progress": 100,
                            }
                        elif status in ["FAILED", "ERROR", "EXPIRED"]:
                            task_error = result.get("task_error", {})
                            error_msg = task_error.get("message", "未知错误")
                            raise Exception(f"生成失败: {error_msg}")
                        else:
                            progress = result.get("progress", 0)
                            logger.info(f"     进度: {progress}%")
                            await asyncio.sleep(10)

                except asyncio.TimeoutError:
                    logger.warning("状态查询超时，重试...")
                    await asyncio.sleep(5)

    def _resolve_api_key(self, provider: str) -> Optional[str]:
        if provider == "hunyuan":
            return settings.HUNYUAN_API_KEY
        if provider == "meshy":
            return settings.MESHY_API_KEY
        if provider == "tripo":
            return settings.TRIPO_API_KEY
        return None

    def _resolve_api_url(self, provider: str) -> str:
        if provider == "hunyuan":
            return settings.HUNYUAN_API_URL.rstrip("/")
        if provider == "meshy":
            return settings.MESHY_API_URL.rstrip("/")
        if provider == "tripo":
            return settings.TRIPO_API_URL.rstrip("/")
        return ""

    # ===========================================
    # 本地生成实现
    # ===========================================

    async def _generate_local(
        self, image_path: str, pet_name: str, pet_breed: str
    ) -> Dict[str, Any]:
        """本地模拟 3D 生成，用于开发测试或离线环境"""

        logger.info("  → 使用本地模拟生成 3D 模型...")
        await asyncio.sleep(2)

        return {
            "success": True,
            "model_url": "https://example.com/models/pet_model.glb",
            "preview_url": image_path,
            "mode": "local",
            "provider": "local_simulator",
            "metadata": {
                "note": "这是本地模拟生成的 3D 模型",
                "pet_name": pet_name,
                "pet_breed": pet_breed,
            },
        }

    # ===========================================
    # 辅助方法
    # ===========================================

    async def _save_model_info(self, result: Dict[str, Any], pet_name: str):
        """保存模型信息到本地"""

        try:
            model_dir = Path(settings.MODEL_3D_DIR)
            model_dir.mkdir(exist_ok=True)

            import json
            from datetime import datetime

            metadata = {
                **result,
                "generated_at": datetime.now().isoformat(),
                "pet_name": pet_name,
            }

            metadata_path = model_dir / f"{pet_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            logger.debug(f"模型信息已保存: {metadata_path}")

        except Exception as e:
            logger.warning(f"保存模型信息失败: {e}")


# 导出服务实例
model_3d_service = Model3DService()
