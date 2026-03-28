"""
视频分析模块 - 使用 LLM 提取结构化信息
"""

import logging
import json
from typing import Dict, Any, Optional
from pathlib import Path

from .api_client import APIClientFactory

logger = logging.getLogger(__name__)


class VideoAnalyzer:
    """分析 VLM 输出，提取结构化信息。"""
    
    def __init__(self, config):
        self.config = config
        self.llm_client = None
        self.debug_session_id = None
        
        if self.config.get("save_debug_output", True):
            self.debug_dir = Path(self.config.get("debug_output_dir", "debug_outputs"))
            self.debug_dir.mkdir(exist_ok=True)
        else:
            self.debug_dir = None
    
    async def analyze_description(
        self,
        vlm_description: str,
        llm_mode: Optional[str] = None,
        debug_session_id: str = None
    ) -> Dict[str, Any]:
        """分析 VLM 描述，提取结构化信息。"""
        self.debug_session_id = debug_session_id
        
        if not self.config.get("enable_llm_analysis", True):
            logger.info("  LLM 分析已禁用")
            return {
                "raw_description": vlm_description,
                "scenes": [],
                "objects": [],
                "activities": [],
                "emotions": [],
                "analysis_performed": False
            }
        
        logger.info("  → 使用 LLM 分析 VLM 输出...")
        
        prompt = self._create_analysis_prompt(vlm_description)
        self._save_debug_output("analysis_prompt.txt", prompt)
        
        mode = llm_mode or self.config.get("llm_mode", "local")
        
        if mode == "local":
            return await self._analyze_local(prompt, vlm_description)
        else:
            return await self._analyze_api(prompt, vlm_description)
    
    def _create_analysis_prompt(self, description: str) -> str:
        return f"""Analyze this cat POV video description and extract structured information.

VIDEO DESCRIPTION:
{description}

Extract in JSON format:
{{
  "scenes": [{{"description": "...", "timestamp": "..."}}],
  "objects": ["list", "of", "objects"],
  "activities": ["list", "of", "activities"],
  "emotions": ["list", "of", "emotions"]
}}

Return ONLY the JSON object."""
    
    async def _analyze_local(self, prompt: str, vlm_description: str) -> Dict[str, Any]:
        """使用本地 Ollama 分析。"""
        import aiohttp
        
        try:
            ollama_url = self.config.get("ollama_url", "http://localhost:11434")
            model = self.config.get("analysis_llm_model", "llama3")
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.3, "num_predict": 500}
                }
                
                async with session.post(f"{ollama_url}/api/generate", json=payload) as response:
                    if response.status != 200:
                        raise Exception(f"Ollama 返回 {response.status}")
                    
                    result = await response.json()
                    analysis_text = result.get("response", "")
                    
                    if not analysis_text:
                        return self._fallback_analysis(vlm_description)
                    
                    try:
                        analysis = json.loads(analysis_text)
                    except json.JSONDecodeError:
                        return self._fallback_analysis(vlm_description)
                    
                    analysis["raw_description"] = vlm_description
                    analysis["analysis_performed"] = True
                    analysis["analysis_model"] = model
                    
                    self._save_debug_output("analysis_output.json", analysis)
                    return analysis
                    
        except Exception as e:
            logger.error(f"  ✗ Ollama 分析错误: {e}")
            return self._fallback_analysis(vlm_description)
    
    async def _analyze_api(self, prompt: str, vlm_description: str) -> Dict[str, Any]:
        """使用云端 API 分析。"""
        try:
            provider = self.config.get("llm_api_provider", "openai")
            api_key = self.config.get_api_key("llm")
            base_url = self.config.get("llm_api_base_url")
            model = self.config.get("llm_model", "gpt-4")
            
            if not self.llm_client:
                self.llm_client = APIClientFactory.create_client(
                    provider=provider,
                    api_key=api_key,
                    base_url=base_url
                )
            
            response = await self.llm_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            analysis_text = response.choices[0].message.content
            
            try:
                analysis = json.loads(analysis_text)
            except json.JSONDecodeError:
                return self._fallback_analysis(vlm_description)
            
            analysis["raw_description"] = vlm_description
            analysis["analysis_performed"] = True
            analysis["analysis_model"] = f"{provider}/{model}"
            
            self._save_debug_output("analysis_output.json", analysis)
            return analysis
            
        except Exception as e:
            logger.error(f"  ✗ API 分析错误: {e}")
            return self._fallback_analysis(vlm_description)
    
    def _fallback_analysis(self, description: str) -> Dict[str, Any]:
        """备用关键词提取。"""
        desc_lower = description.lower()
        
        object_keywords = ['toy', 'ball', 'mouse', 'bird', 'food', 'bowl', 'bed', 'window', 'door']
        objects = [obj for obj in object_keywords if obj in desc_lower]
        
        activity_keywords = ['playing', 'hunting', 'stalking', 'jumping', 'sleeping', 'eating', 'watching']
        activities = [act for act in activity_keywords if act in desc_lower]
        
        emotion_map = {
            'playful': ['playful', 'playing'],
            'curious': ['curious', 'exploring'],
            'alert': ['alert', 'focused', 'hunting'],
            'relaxed': ['relaxed', 'calm', 'resting']
        }
        emotions = [e for e, kws in emotion_map.items() if any(kw in desc_lower for kw in kws)]
        
        return {
            "raw_description": description,
            "scenes": [],
            "objects": objects[:10],
            "activities": activities,
            "emotions": emotions or ['neutral'],
            "analysis_performed": False,
            "analysis_model": "keyword_fallback"
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
