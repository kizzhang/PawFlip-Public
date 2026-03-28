# 🐾 PawFlip - 智能宠物管家

从宠物的视角，探索奇妙世界。上传视频，AI 自动生成宠物第一人称日记。

## ✨ 核心功能

- 📔 **AI 日记** - 上传视频，自动生成宠物视角的故事日记
- 🐕 **宠物档案** - 创建宠物资料，追踪健康状态
- 👥 **社交分享** - 分享宠物动态，与其他宠物主人互动
- 💊 **健康监测** - 记录健康数据，AI 提供建议

---

## 🚀 快速开始

### 1. 环境准备

确保已安装：
- Python 3.10+
- Node.js 18+

### 2. 安装依赖

```bash
# 前端依赖
npm install

# Python 依赖（后端 + 视频分析，统一环境）
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
pip install -r ../pet-vision-narrator/requirements.txt
```

### 3. 配置环境变量

```bash
# 后端配置
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入：
# - SUPABASE_URL / SUPABASE_KEY（数据库）
# - GOOGLE_API_KEY（AI 服务）

# 视频分析配置
cp pet-vision-narrator/.env.example pet-vision-narrator/.env
# 编辑 pet-vision-narrator/.env，填入：
# - VLM_API_KEY / LLM_API_KEY（同一个 Google API Key 即可）
```

### 4. 启动服务

需要开启 3 个终端：

```bash
# 终端 1 - 后端 API
cd backend
venv\Scripts\activate
python main.py

# 终端 2 - 视频分析服务
cd pet-vision-narrator
..\backend\venv\Scripts\activate
python api_server.py

# 终端 3 - 前端
npm run dev
```

### 5. 访问应用

- 前端：http://localhost:5173
- 后端 API 文档：http://localhost:8000/docs

---

## 📁 项目结构

```
PawFlip/
├── backend/                 # 后端 API 服务
│   ├── agents/             # ADK 智能体定义
│   ├── services/           # 业务逻辑
│   ├── routers/            # API 路由
│   ├── main.py             # 入口
│   └── .env                # 配置
├── pet-vision-narrator/    # 视频分析服务
│   ├── src/                # 核心逻辑
│   ├── api_server.py       # API 服务
│   └── .env                # 配置
├── views/                  # 前端页面
├── services/               # 前端 API 服务
├── components/             # 前端组件
└── App.tsx                 # 前端入口
```

---

## ⚙️ 配置说明

### 必需配置

| 配置项 | 说明 | 获取方式 |
|--------|------|----------|
| `SUPABASE_URL` | 数据库地址 | [Supabase](https://supabase.com) 控制台 |
| `SUPABASE_KEY` | 数据库密钥 | 同上 |
| `GOOGLE_API_KEY` | AI 服务密钥 | [Google AI Studio](https://aistudio.google.com) |

### 可选配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `HUNYUAN_API_KEY` | 3D 模型生成（混元） | 不配置则使用本地模式 |
| `AI_PROVIDER` | AI 提供商 | `gemini` |

---

## 🔧 常见问题

**Q: 后端启动报错？**
```bash
cd backend && pip install -r requirements.txt
```

**Q: 视频上传后没反应？**
- 确认 pet-vision-narrator 服务已启动
- 检查 `pet-vision-narrator/.env` 中的 API Key

**Q: 401 错误？**
- 正常现象，需要先注册登录

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 19 + TypeScript + Vite + Tailwind |
| 后端 | FastAPI + Supabase |
| AI 智能体 | Google ADK (Agent Development Kit) |
| AI 模型 | Google Gemini API |
| 视频分析 | OpenCV + Gemini Vision |

---

**版本**: 1.0.0 | **更新**: 2026-01-30
