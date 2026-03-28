# PetVision Narrator

分析猫咪第一人称 POV 视频，生成有趣的猫咪视角叙事故事。

## 项目结构

```
pet-vision-narrator/
├── src/                    # 核心源代码
│   ├── __init__.py
│   ├── config.py           # 配置管理
│   ├── api_client.py       # API 客户端
│   ├── video_processor.py  # 视频处理 (SmolVLM2)
│   ├── video_analyzer.py   # LLM 结构化分析
│   ├── story_generator.py  # 故事生成
│   └── tool_definition.py  # ADK 工具接口
├── scripts/                # 脚本工具
│   ├── start_api.bat       # Windows 启动脚本
│   ├── start_api.sh        # Linux/Mac 启动脚本
│   └── batch_process.py    # 批量处理
├── docker/                 # Docker 配置
│   ├── Dockerfile
│   └── docker-compose.yml
├── docs/                   # 文档
├── api_server.py           # API 服务器入口
├── .env.example            # 环境变量示例
├── requirements.txt        # Python 依赖
└── README.md
```

## 快速开始

```bash
# 1. 安装依赖
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt

# 2. 配置
cp .env.example .env
# 编辑 .env 设置 API 密钥

# 3. 启动 API 服务器
python api_server.py
# 访问 http://localhost:8000/docs
```

## 配置

编辑 `.env` 文件：

```bash
# 模式选择
PETVISION_VLM_MODE=api    # local 或 api
PETVISION_LLM_MODE=api    # local 或 api

# VLM 配置
VLM_PROVIDER=google       # openai, google, anthropic, deepseek
VLM_MODEL=gemini-3-flash-preview
VLM_API_KEY=your_api_key

# LLM 配置
LLM_PROVIDER=google
LLM_MODEL=gemini-3-flash-preview
LLM_API_KEY=your_api_key
```

## API 使用

```bash
# 上传视频（异步）
curl -X POST "http://localhost:8000/api/v1/process/async" \
  -F "file=@cat_video.mp4"

# 查询状态
curl http://localhost:8000/api/v1/jobs/{job_id}
```

## Python 使用

```python
import asyncio
from src import PetVisionNarrator

async def main():
    narrator = PetVisionNarrator()
    result = await narrator.process_pet_video(
        video_path="cat_video.mp4",
        vlm_mode="api",
        llm_mode="api"
    )
    print(result["narrative"]["story"])

asyncio.run(main())
```

## Docker 部署

```bash
cd docker
docker-compose up -d
```

## 文档

- [快速开始](docs/QUICKSTART.md)
- [API 指南](docs/API_GUIDE.md)
- [架构说明](docs/ARCHITECTURE.md)
- [部署指南](docs/DEPLOYMENT.md)

## License

Apache 2.0
