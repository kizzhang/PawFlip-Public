"""
PetVision Narrator 模拟器
当真实的 pet-vision-narrator 不可用时使用
"""

import logging
import random
import time
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class VideoProcessorSimulator:
    """
    视频处理器模拟器
    模拟 pet-vision-narrator 的视频分析功能
    """
    
    def analyze_video(self, video_path: str, mode: str = "api") -> Dict[str, Any]:
        """
        模拟视频分析
        
        Args:
            video_path: 视频文件路径
            mode: 处理模式
            
        Returns:
            分析结果
        """
        logger.info(f"🎬 模拟分析视频: {video_path}")
        
        # 模拟处理时间
        time.sleep(random.uniform(1, 3))
        
        # 检查文件是否存在
        if not Path(video_path).exists():
            return {
                "success": False,
                "error": f"视频文件不存在: {video_path}"
            }
        
        # 生成模拟分析结果
        activities = random.choices(
            ["playing", "eating", "sleeping", "exploring", "running", "sitting"],
            k=random.randint(2, 4)
        )
        
        emotions = random.choices(
            ["happy", "curious", "playful", "calm", "excited"],
            k=random.randint(1, 3)
        )
        
        objects = random.choices(
            ["toy", "food_bowl", "bed", "window", "door", "carpet", "sofa", "human"],
            k=random.randint(3, 6)
        )
        
        analysis = {
            "summary": f"视频显示宠物在进行 {', '.join(activities[:2])} 等活动，表现出 {', '.join(emotions)} 的情绪状态。",
            "scenes": [
                {
                    "description": f"宠物在 {random.choice(['客厅', '卧室', '厨房', '阳台'])} {random.choice(activities)}",
                    "timestamp": f"0:00-0:{random.randint(10, 30):02d}",
                    "confidence": f"{random.uniform(0.7, 0.95):.2f}"
                },
                {
                    "description": f"与 {random.choice(objects)} 互动",
                    "timestamp": f"0:00-0:{random.randint(10, 30):02d}",
                    "confidence": f"{random.uniform(0.6, 0.9):.2f}"
                }
            ],
            "detected_objects": objects,
            "activities": activities,
            "emotional_context": emotions,
            "technical_info": {
                "duration_seconds": random.randint(15, 120),
                "fps": 30,
                "resolution": "1920x1080",
                "format": "mp4"
            }
        }
        
        return {
            "success": True,
            "analysis": analysis,
            "processing_time": random.uniform(1.5, 4.0),
            "vision_model": f"simulator-v1.0-{mode}",
            "confidence_score": random.uniform(0.75, 0.95)
        }


class StoryGeneratorSimulator:
    """
    故事生成器模拟器
    模拟 pet-vision-narrator 的故事生成功能
    """
    
    def __init__(self):
        # 预定义的故事模板
        self.story_templates = [
            "今天我发现了一个超级有趣的{object}！我围着它转了好几圈，用爪子轻轻碰了碰。主人看到我这么{emotion}，也跟着笑了起来。",
            "午后的阳光洒在地板上，我找到了一个完美的位置{activity}。这种{emotion}的感觉真是太棒了！",
            "我在{location}发现了一些有趣的东西。经过仔细的{activity}，我觉得这里很适合我的探险活动。",
            "今天的{activity}时间特别愉快！我感到非常{emotion}，甚至想要和每个人分享这份快乐。",
            "当我看到{object}的时候，我的好奇心被彻底激发了。我小心翼翼地{activity}，生怕错过任何细节。"
        ]
        
        self.locations = ["客厅", "阳台", "卧室", "厨房", "花园"]
        self.emotions_cn = {
            "happy": "开心",
            "curious": "好奇",
            "playful": "顽皮",
            "calm": "平静",
            "excited": "兴奋"
        }
        self.activities_cn = {
            "playing": "玩耍",
            "eating": "进食",
            "sleeping": "休息",
            "exploring": "探索",
            "running": "奔跑",
            "sitting": "坐着观察"
        }
        self.objects_cn = {
            "toy": "玩具",
            "food_bowl": "食盆",
            "bed": "小床",
            "window": "窗户",
            "door": "门",
            "carpet": "地毯",
            "sofa": "沙发",
            "human": "主人"
        }
    
    def generate_story(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        模拟故事生成
        
        Args:
            analysis: 视频分析结果
            
        Returns:
            生成的故事
        """
        logger.info("📝 模拟生成 AI 故事")
        
        # 模拟处理时间
        time.sleep(random.uniform(0.5, 2.0))
        
        if not analysis:
            return {
                "success": False,
                "error": "分析结果为空，无法生成故事"
            }
        
        try:
            # 从分析结果中提取信息
            activities = analysis.get("activities", ["playing"])
            emotions = analysis.get("emotional_context", ["happy"])
            objects = analysis.get("detected_objects", ["toy"])
            
            # 随机选择模板和填充内容
            template = random.choice(self.story_templates)
            
            # 转换为中文
            activity_cn = self.activities_cn.get(random.choice(activities), "玩耍")
            emotion_cn = self.emotions_cn.get(random.choice(emotions), "开心")
            object_cn = self.objects_cn.get(random.choice(objects), "玩具")
            location_cn = random.choice(self.locations)
            
            # 生成故事
            story = template.format(
                activity=activity_cn,
                emotion=emotion_cn,
                object=object_cn,
                location=location_cn
            )
            
            # 添加一些随机的结尾
            endings = [
                "这真是美好的一天！",
                "我期待着明天的新冒险。",
                "生活中的小确幸就是这样简单。",
                "每一天都有新的发现等着我。",
                "和主人在一起的时光总是这么温馨。"
            ]
            
            story += " " + random.choice(endings)
            
            return {
                "success": True,
                "story": {
                    "story": story,
                    "style": "first-person pet POV",
                    "tone": "playful and warm",
                    "word_count": len(story),
                    "themes": [activity_cn, emotion_cn],
                    "generated_at": time.time()
                },
                "llm_model": "simulator-storyteller-v1.0",
                "processing_time": random.uniform(0.8, 2.5)
            }
            
        except Exception as e:
            logger.error(f"故事生成模拟失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# 创建全局实例
video_processor_simulator = VideoProcessorSimulator()
story_generator_simulator = StoryGeneratorSimulator()