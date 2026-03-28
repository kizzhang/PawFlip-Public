"""
PetVision Narrator - Google ADK 工具定义

分析猫咪 POV 视频并生成第一人称叙事故事。
"""

import logging
import time
import gc
from typing import Dict, Any, Optional
from pathlib import Path

from .video_processor import VideoProcessor
from .video_analyzer import VideoAnalyzer
from .story_generator import StoryGenerator
from .config import Config

logger = logging.getLogger(__name__)


class PetVisionNarrator:
    """ADK 兼容的猫咪视频处理工具。"""
    
    TOOL_NAME = "pet_vision_narrator"
    TOOL_DESCRIPTION = "分析猫咪 POV 视频，生成第一人称叙事故事。"
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.video_processor = VideoProcessor(self.config)
        self.video_analyzer = VideoAnalyzer(self.config)
        self.story_generator = StoryGenerator(self.config)
        
        if self.config.get("save_debug_output", True):
            self._setup_debug_logging()
        
        logger.info(f"PetVision Narrator 初始化 - VLM: {self.config.get('vlm_mode')}, LLM: {self.config.get('llm_mode')}")
    
    def _setup_debug_logging(self):
        debug_dir = Path(self.config.get("debug_output_dir", "debug_outputs"))
        debug_dir.mkdir(exist_ok=True)
        
        log_file = debug_dir / "latest_session.log"
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        logging.getLogger().addHandler(file_handler)
    
    def _finalize_debug_logging(self):
        try:
            import shutil
            
            debug_dir = Path(self.config.get("debug_output_dir", "debug_outputs"))
            log_file = debug_dir / "latest_session.log"
            
            if not log_file.exists():
                return
            
            session_id = getattr(self.video_processor, 'debug_session_id', None)
            if session_id:
                session_dir = debug_dir / session_id
                session_dir.mkdir(exist_ok=True)
                shutil.copy2(log_file, session_dir / "session.log")
        except:
            pass
    
    @classmethod
    def get_tool_definition(cls) -> Dict[str, Any]:
        """返回 ADK 工具定义。"""
        return {
            "name": cls.TOOL_NAME,
            "description": cls.TOOL_DESCRIPTION,
            "parameters": {
                "type": "object",
                "properties": {
                    "video_path": {"type": "string", "description": "视频文件路径"},
                    "video_bytes": {"type": "string", "description": "Base64 编码的视频"},
                    "vlm_mode": {"type": "string", "enum": ["local", "api"]},
                    "llm_mode": {"type": "string", "enum": ["local", "api"]}
                },
                "oneOf": [
                    {"required": ["video_path"]},
                    {"required": ["video_bytes"]}
                ]
            }
        }
    
    async def process_pet_video(
        self,
        video_path: Optional[str] = None,
        video_bytes: Optional[bytes] = None,
        vlm_mode: Optional[str] = None,
        llm_mode: Optional[str] = None,
        model_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """处理猫咪 POV 视频的主函数。"""
        try:
            start_time = time.time()
            
            logger.info("=" * 50)
            logger.info("开始视频处理流水线")
            logger.info("=" * 50)
            
            if not video_path and not video_bytes:
                raise ValueError("必须提供 video_path 或 video_bytes")
            
            if model_config:
                self.config.config.update(model_config)
            
            vlm_mode = vlm_mode or self.config.get("vlm_mode", "local")
            llm_mode = llm_mode or self.config.get("llm_mode", "local")
            
            logger.info(f"VLM: {vlm_mode}, LLM: {llm_mode}")
            
            # 步骤 1: VLM 分析视频
            logger.info(f"步骤 1/3: VLM 分析视频...")
            video_result = await self.video_processor.analyze_video(
                video_path=video_path,
                video_bytes=video_bytes,
                vlm_mode=vlm_mode
            )
            
            # 步骤 2: LLM 提取结构化信息
            logger.info(f"步骤 2/3: LLM 提取结构化信息...")
            analysis = await self.video_analyzer.analyze_description(
                vlm_description=video_result.get('description', ''),
                llm_mode=llm_mode,
                debug_session_id=getattr(self.video_processor, 'debug_session_id', None)
            )
            
            video_analysis = {
                "description": video_result.get('description', ''),
                "summary": analysis.get('raw_description', ''),
                "scenes": analysis.get('scenes', []),
                "objects": analysis.get('objects', []),
                "activities": analysis.get('activities', []),
                "emotions": analysis.get('emotions', []),
                "model_used": video_result.get('model_used', ''),
                "confidence": video_result.get('confidence', 0.0),
                "processing_mode": video_result.get('processing_mode', 'unknown')
            }
            
            # 步骤 3: 生成叙事故事
            logger.info(f"步骤 3/3: 生成猫咪叙事...")
            narrative = await self.story_generator.generate_story(
                video_analysis=video_analysis,
                llm_mode=llm_mode,
                debug_session_id=getattr(self.video_processor, 'debug_session_id', None)
            )
            
            processing_time = time.time() - start_time
            logger.info(f"✓ 流水线完成，耗时 {processing_time:.2f}s")
            
            if self.config.get("save_debug_output", True):
                self._finalize_debug_logging()
            
            return {
                "success": True,
                "video_analysis": {
                    "summary": video_analysis.get("summary", ""),
                    "scenes": video_analysis.get("scenes", []),
                    "detected_objects": video_analysis.get("objects", []),
                    "activities": video_analysis.get("activities", []),
                    "emotional_context": video_analysis.get("emotions", [])
                },
                "narrative": {
                    "story": narrative.get("story", ""),
                    "style": "first-person cat POV",
                    "tone": narrative.get("tone", "playful")
                },
                "metadata": {
                    "processing_time_seconds": round(processing_time, 2),
                    "vlm_mode": vlm_mode,
                    "llm_mode": llm_mode,
                    "vision_model": video_analysis.get("model_used", ""),
                    "llm_model": narrative.get("model_used", ""),
                    "confidence_score": video_analysis.get("confidence", 0.0)
                }
            }
            
        except Exception as e:
            logger.error(f"处理视频错误: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
        finally:
            try:
                if self.config.get("clear_memory_after_processing", True):
                    if hasattr(self, 'video_processor') and self.video_processor:
                        self.video_processor.clear_model_memory()
                    
                    if self.config.get("force_garbage_collection", True):
                        gc.collect()
            except:
                pass
    
    def __call__(self, **kwargs) -> Dict[str, Any]:
        import asyncio
        return asyncio.run(self.process_pet_video(**kwargs))


def register_tool():
    """注册工具到 Google ADK。"""
    return PetVisionNarrator()


def get_tool_schema():
    """获取工具 schema。"""
    return PetVisionNarrator.get_tool_definition()
