"""
PetVision Narrator - 猫咪 POV 视频分析和叙事生成工具

兼容 Google ADK 框架。
"""

from .tool_definition import PetVisionNarrator, register_tool, get_tool_schema
from .config import Config

__version__ = "1.0.0"
__all__ = ["PetVisionNarrator", "register_tool", "get_tool_schema", "Config"]
