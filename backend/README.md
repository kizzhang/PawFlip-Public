# PawFlip Backend

智能宠物管家后端服务，基于 FastAPI + Google ADK 构建。

## 快速开始

```bash
# 1. 创建虚拟环境
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 Supabase 和 Google API 配置

# 4. 启动服务
python main.py
```

访问 http://localhost:8001/docs 查看 API 文档。

## 目录结构

```
backend/
├── main.py              # 应用入口
├── config.py            # 配置管理
├── database.py          # Supabase 连接
├── auth.py              # JWT 认证
├── base_models.py       # 基础数据模型
│
├── agents/              # AI 智能体
│   └── health_agent.py  # 宠物健康 Agent (Google ADK)
│
├── models/              # Pydantic 模型
│   └── health_agent.py  # Health Agent 专用模型
│
├── routers/             # API 路由
│   ├── auth.py          # 认证 API
│   ├── pets.py          # 宠物管理
│   ├── diary.py         # 日记功能
│   ├── health.py        # 健康数据
│   ├── health_agent.py  # AI 健康助手
│   ├── video.py         # 视频处理
│   ├── ai.py            # 通用 AI
│   └── social.py        # 社交功能
│
├── services/            # 业务逻辑
│   ├── adk_health_service.py  # Health Agent 服务
│   ├── ai_service.py          # AI 服务
│   ├── pet_service.py         # 宠物服务
│   └── ...
│
├── migrations/          # 数据库迁移
├── docs/                # 技术文档
└── models_3d/           # 3D 模型缓存
```

## 核心功能

| 功能 | 端点前缀 | 说明 |
|------|----------|------|
| 认证 | `/api/v1/auth` | 注册、登录、JWT |
| 宠物 | `/api/v1/pets` | 宠物档案 CRUD |
| 日记 | `/api/v1/diary` | 日记管理、AI 生成 |
| 健康 | `/api/v1/health` | 健康数据记录 |
| AI 助手 | `/api/v1/health-agent` | 智能健康问诊 |
| 视频 | `/api/v1/video` | 视频分析处理 |
| 社交 | `/api/v1/social` | 动态发布 |

## 技术栈

- **Web 框架**: FastAPI
- **数据库**: Supabase (PostgreSQL)
- **AI 框架**: Google ADK
- **LLM**: Google Gemini
- **认证**: JWT + bcrypt

## 文档

- [架构文档](docs/ARCHITECTURE.md) - 整体架构说明
- [Health Agent 文档](docs/HEALTH_AGENT.md) - AI 健康助手详细说明

## 环境变量

```env
# 必需
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
GOOGLE_API_KEY=AIza...

# 可选
DEBUG=true
API_PORT=8001
GEMINI_MODEL=gemini-2.0-flash
```

## Supabase 数据库重建（误删后恢复）

如果你删除了原有 Supabase 数据库，可以按下面步骤快速恢复。

### 1. 新建 Supabase Project 并更新后端配置

在 Supabase 控制台获取新项目的 `URL`、`anon key`、`service_role key`，写入 `backend/.env`：

```env
SUPABASE_URL=https://your-new-project.supabase.co
SUPABASE_KEY=your-new-anon-key
SUPABASE_SERVICE_KEY=your-new-service-role-key
```

### 2. 执行基础表结构 SQL

打开 Supabase 控制台 -> SQL Editor，执行：

- `backend/database_schema.sql`

### 3. 执行 Health Agent 表结构 SQL

在 SQL Editor 再执行：

- `backend/migrations/create_health_agent_tables.sql`

### 4. 本地校验数据库是否恢复

```bash
cd backend
python scripts/check_supabase_schema.py
```

如果输出 `Schema check passed`，说明数据库结构已恢复完成。
