# PawFlip Backend 架构文档

## 目录结构

```
backend/
├── main.py                 # FastAPI 应用入口
├── config.py               # 配置管理（环境变量）
├── database.py             # Supabase 数据库连接
├── auth.py                 # JWT 认证模块
├── base_models.py          # 基础 Pydantic 模型
│
├── agents/                 # AI 智能体定义
│   └── health_agent.py     # 宠物健康智能体（Google ADK）
│
├── models/                 # 数据模型
│   ├── __init__.py         # 模型导出
│   └── health_agent.py     # Health Agent 专用模型
│
├── routers/                # API 路由层
│   ├── auth.py             # 认证 API
│   ├── pets.py             # 宠物管理 API
│   ├── diary.py            # 日记 API
│   ├── health.py           # 健康数据 API
│   ├── health_agent.py     # AI 健康助手 API
│   ├── video.py            # 视频处理 API
│   ├── ai.py               # 通用 AI API
│   ├── social.py           # 社交功能 API
│   └── proxy.py            # 代理 API
│
├── services/               # 业务逻辑层
│   ├── adk_health_service.py  # Health Agent 核心服务
│   ├── ai_service.py          # 通用 AI 服务
│   ├── pet_service.py         # 宠物服务
│   ├── diary_service.py       # 日记服务
│   ├── video_service.py       # 视频处理服务
│   ├── model_3d_service.py    # 3D 模型生成服务
│   └── narrator_simulator.py  # 视频叙事模拟器
│
├── migrations/             # 数据库迁移脚本
│   └── create_health_agent_tables.sql
│
├── models_3d/              # 3D 模型缓存（运行时生成）
├── docs/                   # 技术文档
└── venv/                   # Python 虚拟环境
```

## 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (routers/)                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐   │
│  │  auth   │ │  pets   │ │  diary  │ │  health_agent   │   │
│  └─────────┘ └─────────┘ └─────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Service Layer (services/)                   │
│  ┌─────────────────┐ ┌─────────────────┐ ┌───────────────┐ │
│  │ adk_health_svc  │ │   ai_service    │ │  pet_service  │ │
│  └─────────────────┘ └─────────────────┘ └───────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Google ADK     │ │    Supabase     │ │  Google Gemini  │
│  (Agent框架)    │ │   (数据库)      │ │    (LLM API)    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

## 核心技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| Web 框架 | FastAPI | REST API 服务 |
| 数据库 | Supabase (PostgreSQL) | 数据持久化 |
| 认证 | JWT + bcrypt | 用户认证 |
| AI 框架 | Google ADK | 智能体编排 |
| LLM | Google Gemini | 自然语言处理 |
| 异步 | asyncio | 异步 I/O |

## 请求流程

```
HTTP Request
     │
     ▼
┌─────────────┐
│   main.py   │  ← CORS、异常处理、路由注册
└─────────────┘
     │
     ▼
┌─────────────┐
│   auth.py   │  ← JWT 令牌验证 (get_current_user_id)
└─────────────┘
     │
     ▼
┌─────────────┐
│  routers/*  │  ← 请求验证、参数解析
└─────────────┘
     │
     ▼
┌─────────────┐
│ services/*  │  ← 业务逻辑处理
└─────────────┘
     │
     ▼
┌─────────────┐
│ database.py │  ← Supabase 数据操作
└─────────────┘
     │
     ▼
HTTP Response
```
