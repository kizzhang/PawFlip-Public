"""
故事生成模块 - 从视频分析生成猫咪第一人称叙事
"""

import logging
import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .api_client import APIClientFactory

logger = logging.getLogger(__name__)


class StoryGenerator:
    """从视频分析生成猫咪叙事故事。"""
    
    def __init__(self, config):
        self.config = config
        self.api_client = None
        self.debug_session_id = None
        
        if self.config.get("save_debug_output", True):
            self.debug_dir = Path(self.config.get("debug_output_dir", "debug_outputs"))
            self.debug_dir.mkdir(exist_ok=True)
        else:
            self.debug_dir = None
    
    async def generate_story(
        self,
        video_analysis: Dict[str, Any],
        llm_mode: Optional[str] = None,
        debug_session_id: str = None
    ) -> Dict[str, Any]:
        """从视频分析生成猫咪第一人称叙事。"""
        self.debug_session_id = debug_session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        
        logger.info("  → 创建叙事提示词...")
        prompt = self._create_narrative_prompt(video_analysis)
        self._save_debug_output("story_prompt.txt", prompt)
        
        mode = llm_mode or self.config.get("llm_mode", "local")
        
        if mode == "local":
            logger.info("  → 使用 Ollama 生成故事...")
            return await self._generate_local(prompt)
        else:
            provider = self.config.get("llm_api_provider", "openai")
            logger.info(f"  → 使用 {provider} API 生成故事...")
            return await self._generate_api(prompt)
    
    def _create_narrative_prompt(self, analysis: Dict[str, Any]) -> str:
        """创建故事生成提示词。"""
        has_structured = (
            analysis.get("objects") or 
            analysis.get("activities") or 
            analysis.get("emotions")
        )
        
        base_instructions = """请用猫的第一人称写一段 150-200 字的叙事文字，并包含：
- 感官描写（我看到什么、闻到什么、触感如何）
- 猫咪式的观察与内心吐槽/思考
- 顽皮、好奇、有探索欲的性格
- 符合猫的自然行为与本能

直接开始叙述，不要包含任何标题或标签："""
        
        if has_structured:
            summary = analysis.get("summary", "")
            objects = ", ".join(analysis.get("objects", []))
            activities = ", ".join(analysis.get("activities", []))
            emotions = ", ".join(analysis.get("emotions", []))
            
            return f"""你是一只猫，请用第一人称叙述你的一天。

视频摘要：{summary}
我看到的物体：{objects}
我做了什么：{activities}
我的情绪感受：{emotions}

{base_instructions}"""
        else:
            description = analysis.get("description", "")
            
            return f"""你是一只猫，请用第一人称叙述你的一天。

视频描述：{description}

{base_instructions}"""
    
    async def _generate_local(self, prompt: str) -> Dict[str, Any]:
        """使用本地 Ollama 生成故事。"""
        import aiohttp
        
        try:
            ollama_url = self.config.get("ollama_url", "http://localhost:11434")
            model = self.config.get("ollama_model", "gemma3")
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.config.get("temperature", 0.7),
                        "num_predict": self.config.get("max_tokens", 250)
                    }
                }
                
                async with session.post(f"{ollama_url}/api/generate", json=payload) as response:
                    if response.status != 200:
                        raise Exception(f"Ollama 返回 {response.status}")
                    
                    result = await response.json()
                    story = result.get("response", "").strip()
                    
                    if not story:
                        raise Exception("Ollama 返回空响应")
                    
                    logger.info(f"  ✓ 故事生成完成 ({len(story)} 字符)")
                    
                    result_data = {
                        "story": story,
                        "model_used": model,
                        "tone": "playful"
                    }
                    
                    self._save_debug_output("story_output.json", result_data)
                    self._save_debug_output("story_output.txt", story)
                    
                    return result_data
                    
        except Exception as e:
            logger.error(f"  ✗ Ollama 错误: {e}")
            return self._generate_fallback_story()
    
    async def _generate_api(self, prompt: str) -> Dict[str, Any]:
        """使用云端 LLM API 生成故事。"""
        try:
            provider = self.config.get("llm_api_provider", "openai")
            api_key = self.config.get_api_key("llm")
            base_url = self.config.get("llm_api_base_url")
            model = self.config.get("llm_model", "gpt-4")
            
            if not self.api_client:
                self.api_client = APIClientFactory.create_client(
                    provider=provider,
                    api_key=api_key,
                    base_url=base_url
                )
            
            api_params = self._get_api_params(model)
            
            response = await self.api_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a creative writer."},
                    {"role": "user", "content": prompt}
                ],
                **api_params
            )
            
            story = response.choices[0].message.content.strip()
            
            result = {
                "story": story,
                "model_used": f"{provider}/{model}",
                "tone": "playful"
            }
            
            self._save_debug_output("story_output.json", result)
            self._save_debug_output("story_output.txt", story)
            
            logger.info(f"  ✓ 故事生成完成 ({len(story)} 字符)")
            return result
            
        except Exception as e:
            logger.error(f"  ✗ API 错误: {e}")
            return self._generate_fallback_story()
    
    def _get_api_params(self, model: str) -> dict:
        params = {
            "max_tokens": self.config.get("max_tokens", 300),
            "reasoning_effort": self.config.get("reasoning_effort", "medium")
        }
        
        model_lower = model.lower()
        if not any(x in model_lower for x in ["o1", "deepseek-r1", "qwq"]):
            params["temperature"] = self.config.get("temperature", 0.7)
        
        return params
    
    def _generate_fallback_story(self) -> Dict[str, Any]:
        """生成备用模板故事。"""
        story = """又是平凡的一天！我的胡须微微颤动，从我最爱的高处俯瞰我的领地。
阳光暖暖的，但是等等——那是什么？一个玩具！我的狩猎本能瞬间觉醒。
我压低身子，尾巴有节奏地摆动。完美的扑击，不愧是本喵！
胜利之后，该好好伸个懒腰，然后小憩一下。当一只如此优秀的猫，真是累人呢。"""
        
        return {
            "story": story,
            "model_used": "fallback_template",
            "tone": "playful"
        }
    
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
