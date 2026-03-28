"""
代理路由 - 用于解决 CORS 问题
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import httpx
import logging

router = APIRouter(prefix="/proxy", tags=["代理"])
logger = logging.getLogger(__name__)

# 允许代理的域名模式（子串匹配）
ALLOWED_DOMAINS = [
    "assets.meshy.ai",
    "hunyuan",
    "tencentcos.cn",
    "myqcloud.com",
    ".cos.",
]

# 禁止代理的内网地址
BLOCKED_PREFIXES = [
    "http://localhost",
    "http://127.",
    "http://10.",
    "http://192.168.",
    "http://172.",
]


def _validate_proxy_url(url: str):
    """验证代理 URL 安全性"""
    for blocked in BLOCKED_PREFIXES:
        if url.startswith(blocked):
            raise HTTPException(status_code=400, detail="不允许代理内网资源")
    if not url.startswith("https://"):
        raise HTTPException(status_code=400, detail="只允许代理 HTTPS 资源")
    # 检查是否在允许的域名列表中
    if not any(domain in url for domain in ALLOWED_DOMAINS):
        raise HTTPException(status_code=400, detail="不允许代理该域名的资源")


@router.get("/3d-model")
async def proxy_3d_model(url: str):
    """代理 3D 模型文件请求，解决 CORS 问题"""
    try:
        logger.info(f"代理 3D 模型请求: {url}")
        _validate_proxy_url(url)

        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()

            # 根据 URL 后缀或响应头判断 content-type
            content_type = response.headers.get("content-type", "")
            if not content_type or "octet-stream" in content_type:
                if url.lower().endswith(".glb"):
                    content_type = "model/gltf-binary"
                elif url.lower().endswith(".obj"):
                    content_type = "text/plain"
                else:
                    content_type = "model/gltf-binary"

            return StreamingResponse(
                iter([response.content]),
                media_type=content_type,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                    "Cache-Control": "public, max-age=86400",
                },
            )

    except httpx.HTTPError as e:
        logger.error(f"代理请求失败: {e}")
        raise HTTPException(status_code=502, detail=f"无法获取 3D 模型文件: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"代理请求异常: {e}")
        raise HTTPException(status_code=500, detail=f"代理请求失败: {str(e)}")


@router.get("/3d-preview")
async def proxy_3d_preview(url: str):
    """代理 3D 模型预览图请求，解决 CORS 问题"""
    try:
        logger.info(f"代理预览图请求: {url}")
        _validate_proxy_url(url)

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()

            # 自动检测图片类型
            content_type = response.headers.get("content-type", "image/png")

            return StreamingResponse(
                iter([response.content]),
                media_type=content_type,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                    "Cache-Control": "public, max-age=86400",
                },
            )

    except httpx.HTTPError as e:
        logger.error(f"代理请求失败: {e}")
        raise HTTPException(status_code=502, detail=f"无法获取预览图: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"代理请求异常: {e}")
        raise HTTPException(status_code=500, detail=f"代理请求失败: {str(e)}")


@router.get("/3d-job/{job_id}")
async def proxy_3d_job_query(job_id: str):
    """代理混元3D任务查询，解决浏览器 CORS 问题"""
    from config import settings

    api_key = settings.HUNYUAN_API_KEY
    api_url = settings.HUNYUAN_API_URL.rstrip("/")

    if not api_key:
        raise HTTPException(status_code=500, detail="未配置混元 API Key")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{api_url}/v1/ai3d/query",
                headers={
                    "Authorization": api_key,
                    "Content-Type": "application/json",
                },
                json={"JobId": job_id},
            )
            return response.json()
    except Exception as e:
        logger.error(f"查询混元任务失败: {e}")
        raise HTTPException(status_code=502, detail=str(e))
