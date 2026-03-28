"""
视频处理模块 - 分析猫咪 POV 视频

支持本地模型 (SmolVLM2) 和云端 API。
"""

import logging
import json
import gc
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

import cv2
import numpy as np

from .api_client import APIClientFactory

logger = logging.getLogger(__name__)


class VideoProcessor:
    """使用视觉模型处理和分析视频。"""
    
    def __init__(self, config):
        self.config = config
        self.local_model = None
        self.local_processor = None
        self.api_client = None
        self.debug_session_id = None
        
        if self.config.get("save_debug_output", True):
            self.debug_dir = Path(self.config.get("debug_output_dir", "debug_outputs"))
            self.debug_dir.mkdir(exist_ok=True)
        else:
            self.debug_dir = None
    
    async def analyze_video(
        self,
        video_path: Optional[str] = None,
        video_bytes: Optional[bytes] = None,
        vlm_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """分析视频内容。"""
        mode = vlm_mode or self.config.get("vlm_mode", "local")
        
        self.debug_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        if video_path:
            self.debug_session_id = f"{Path(video_path).stem}_{self.debug_session_id}"
        
        use_frame_sampling = self.config.get("use_frame_sampling", False)
        
        if use_frame_sampling or mode == "api":
            logger.info("→ 提取视频关键帧...")
            frames = self._extract_key_frames(video_path, video_bytes)
            logger.info(f"  ✓ 提取了 {len(frames)} 帧")
        else:
            logger.info("→ 处理完整视频...")
            frames = None
        
        if mode == "local":
            logger.info("→ 使用本地 SmolVLM2 模型分析...")
            return await self._analyze_local(video_path, video_bytes, frames)
        else:
            provider = self.config.get("vlm_api_provider", "openai")
            logger.info(f"→ 使用 {provider} API 分析...")
            return await self._analyze_api(frames)
    
    def _extract_key_frames(
        self,
        video_path: Optional[str],
        video_bytes: Optional[bytes],
        num_frames: int = 8
    ) -> List[np.ndarray]:
        """从视频中提取关键帧。"""
        cap = None
        tmp_path = None
        frames = []
        
        try:
            if video_path:
                cap = cv2.VideoCapture(video_path)
            else:
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
                    tmp.write(video_bytes)
                    tmp_path = tmp.name
                cap = cv2.VideoCapture(tmp_path)
            
            if not cap.isOpened():
                raise ValueError("无法打开视频文件")
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames == 0:
                raise ValueError("视频没有帧")
            
            frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
            
            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if ret:
                    frames.append(frame.copy())
                    del frame
            
            return frames
            
        finally:
            if cap is not None:
                cap.release()
                cv2.destroyAllWindows()
            
            if tmp_path and Path(tmp_path).exists():
                try:
                    Path(tmp_path).unlink()
                except:
                    pass
            
            gc.collect()
    
    async def _analyze_local(
        self, 
        video_path: Optional[str],
        video_bytes: Optional[bytes],
        frames: Optional[List[np.ndarray]]
    ) -> Dict[str, Any]:
        """使用 SmolVLM2 分析视频。"""
        from transformers import AutoProcessor, AutoModelForImageTextToText
        import torch
        
        try:
            if not self.local_model:
                model_name = self.config.get(
                    "local_vision_model", 
                    "HuggingFaceTB/SmolVLM2-256M-Video-Instruct"
                )
                logger.info(f"  → 加载视觉模型: {model_name}")
                
                self.local_processor = AutoProcessor.from_pretrained(model_name)
                
                if torch.cuda.is_available():
                    gpu_fraction = self.config.get("gpu_memory_fraction", 0.9)
                    if gpu_fraction < 1.0:
                        torch.cuda.set_per_process_memory_fraction(gpu_fraction)
                    
                    self.local_model = AutoModelForImageTextToText.from_pretrained(
                        model_name,
                        torch_dtype=torch.bfloat16,
                        _attn_implementation="sdpa"
                    ).to("cuda")
                    logger.info("  ✓ 模型加载到 GPU")
                else:
                    self.local_model = AutoModelForImageTextToText.from_pretrained(
                        model_name,
                        torch_dtype=torch.float32,
                        _attn_implementation="eager"
                    )
                    self.local_model.eval()
                    logger.info("  ✓ 模型加载到 CPU")
            
            logger.info("  → 生成视频描述...")
            description = await self._query_video_local(
                video_path, video_bytes, frames,
                "Describe this cat's first-person POV video in detail."
            )
            
            logger.info(f"  ✓ 描述生成完成 ({len(description)} 字符)")
            self._save_debug_output("vlm_description.txt", description)
            
            result = {
                "description": description,
                "model_used": "SmolVLM2-256M-Video-Instruct",
                "processing_mode": "whole_video" if frames is None else "frame_sampling",
                "confidence": 0.88
            }
            
            self._save_debug_output("VideoProcessorOutput.json", result)
            return result
            
        finally:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            self._clear_opencv_memory()
    
    async def _query_video_local(
        self,
        video_path: Optional[str],
        video_bytes: Optional[bytes],
        frames: Optional[List[np.ndarray]],
        question: str
    ) -> str:
        """向视频模型提问。"""
        import torch
        from PIL import Image
        
        inputs = None
        generated_ids = None
        pil_frames = None
        
        try:
            if frames is not None:
                pil_frames = [
                    Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)) 
                    for frame in frames[:8]
                ]
                
                messages = [{
                    "role": "user",
                    "content": [{"type": "text", "text": question}] + 
                              [{"type": "image", "image": img} for img in pil_frames]
                }]
            else:
                if not video_path:
                    raise ValueError("完整视频处理需要 video_path")
                
                messages = [{
                    "role": "user",
                    "content": [
                        {"type": "video", "path": video_path},
                        {"type": "text", "text": question}
                    ]
                }]
            
            inputs = self.local_processor.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
            )
            
            if next(self.local_model.parameters()).is_cuda:
                inputs = inputs.to("cuda", dtype=torch.bfloat16)
            else:
                inputs = inputs.to("cpu", dtype=torch.float32)
            
            with torch.no_grad():
                generated_ids = self.local_model.generate(
                    **inputs, 
                    do_sample=False,
                    max_new_tokens=512,
                    repetition_penalty=1.2,
                    no_repeat_ngram_size=3
                )
            
            generated_texts = self.local_processor.batch_decode(
                generated_ids,
                skip_special_tokens=True,
            )

            response = generated_texts[0]
            
            if "Assistant:" in response:
                response = response.split("Assistant:")[-1].strip()
            elif "assistant" in response.lower():
                idx = response.lower().rfind("assistant")
                response = response[idx + len("assistant"):].strip()
                if response.startswith(":"):
                    response = response[1:].strip()
            
            return response
            
        finally:
            del inputs, generated_ids
            if pil_frames:
                for img in pil_frames:
                    img.close()
                del pil_frames
            
            gc.collect()
            
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    
    async def _analyze_api(self, frames: List[np.ndarray]) -> Dict[str, Any]:
        """使用云端视觉 API 分析帧。"""
        import base64
        
        try:
            provider = self.config.get("vlm_api_provider", "openai")
            api_key = self.config.get_api_key("vlm")
            base_url = self.config.get("vlm_api_base_url")
            model = self.config.get("vlm_model", "gpt-4-vision-preview")
            
            if not self.api_client:
                self.api_client = APIClientFactory.create_client(
                    provider=provider,
                    api_key=api_key,
                    base_url=base_url
                )
            
            encoded_frames = []
            for frame in frames[:4]:
                _, buffer = cv2.imencode('.jpg', frame)
                encoded = base64.b64encode(buffer).decode('utf-8')
                encoded_frames.append(encoded)
            
            messages = [{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyze these frames from a cat's first-person POV video. Describe what the cat sees and does."
                    }
                ] + [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}}
                    for img in encoded_frames
                ]
            }]
            
            api_params = self._get_vlm_api_params(model)
            
            response = await self.api_client.chat.completions.create(
                model=model,
                messages=messages,
                **api_params
            )
            
            description = response.choices[0].message.content
            
            result = {
                "description": description,
                "model_used": f"{provider}/{model}",
                "processing_mode": "frame_sampling",
                "confidence": 0.92
            }
            
            self._save_debug_output("vlm_description.txt", description)
            self._save_debug_output("VideoProcessorOutput.json", result)
            
            logger.info(f"  ✓ 描述生成完成 ({len(description)} 字符)")
            return result
            
        except Exception as e:
            logger.error(f"API 错误: {e}")
            raise
    
    def _get_vlm_api_params(self, model: str) -> dict:
        params = {
            "max_tokens": 500,
            "reasoning_effort": self.config.get("reasoning_effort", "medium")
        }
        
        model_lower = model.lower()
        if not any(x in model_lower for x in ["o1", "deepseek-r1", "qwq"]):
            params["temperature"] = self.config.get("temperature", 0.7)
        
        return params
    
    def clear_model_memory(self):
        """清理模型内存。"""
        import torch
        
        logger.info("清理模型内存...")
        
        if self.local_model is not None:
            if next(self.local_model.parameters()).is_cuda:
                self.local_model.cpu()
            
            del self.local_model
            self.local_model = None
            
            if self.local_processor is not None:
                del self.local_processor
                self.local_processor = None
        
        self._clear_opencv_memory()
        gc.collect()
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        
        logger.info("✓ 内存已清理")
    
    def _clear_opencv_memory(self):
        try:
            cv2.destroyAllWindows()
            cv2.waitKey(1)
            gc.collect()
        except:
            pass
    
    def _save_debug_output(self, filename: str, content: Any):
        if not self.debug_dir or not self.debug_session_id:
            return
        
        try:
            session_dir = self.debug_dir / self.debug_session_id
            session_dir.mkdir(exist_ok=True)
            output_path = session_dir / filename
            
            if isinstance(content, (dict, list)):
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(content, f, indent=2, ensure_ascii=False)
            else:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(str(content))
        except:
            pass
