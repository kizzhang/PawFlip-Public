# Health Agent 技术文档

## 设计理念

Health Agent 是一个**真正自主**的 AI 智能体，它能够：
- **主动获取数据**：通过工具函数从数据库查询宠物信息
- **自主决策**：决定何时调用什么工具
- **记录关键信息**：自动记录症状和建议到数据库

## 架构

```
用户消息
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                  ADKHealthService                            │
│                                                              │
│  1. 设置上下文 (set_agent_context)                           │
│  2. 创建 Agent (create_health_agent)                         │
│  3. 运行 Agent (runner.run_async)                            │
│  4. 保存消息                                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Google ADK Agent                          │
│                                                              │
│  Agent 自主决定:                                             │
│  - 是否调用 get_pet_profile() 获取宠物信息                   │
│  - 是否调用 get_health_records() 查看健康数据                │
│  - 是否调用 record_symptom() 记录症状                        │
│  - 如何组织回复                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      工具函数                                │
│                                                              │
│  get_pet_profile()      → 查询 pets 表                       │
│  get_health_records()   → 查询 health_records 表             │
│  get_recent_diary()     → 查询 diary_entries 表              │
│  record_symptom()       → 写入 key_info 表                   │
│  record_advice()        → 写入 key_info 表                   │
│  get_conversation_history() → 查询 key_info 表               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                         Supabase DB
```

## 工具函数

| 函数 | 作用 | 数据库操作 |
|------|------|-----------|
| `get_pet_profile()` | 获取宠物档案 | SELECT pets |
| `get_health_records(days)` | 获取健康数据 | SELECT health_records |
| `get_recent_diary(limit)` | 获取日记 | SELECT diary_entries |
| `record_symptom(symptom, severity)` | 记录症状 | INSERT key_info |
| `record_advice(advice, category)` | 记录建议 | INSERT key_info |
| `get_conversation_history()` | 获取历史 | SELECT key_info |

## 上下文传递

工具函数需要知道当前的 user_id、pet_id、conversation_id。通过全局上下文实现：

```python
# 设置上下文
set_agent_context(user_id, pet_id, conversation_id)

# 工具函数内部访问
def get_pet_profile():
    pet_id = _current_context.get("pet_id")
    # 使用 pet_id 查询数据库
```

## Agent 指令

```
你是"AI 宠物健康顾问"，帮助宠物主人了解和管理宠物健康。

## 工作方式
1. 首次对话时，先调用 get_pet_profile() 了解宠物基本信息
2. 当用户描述症状时，调用 record_symptom() 记录
3. 需要了解健康状况时，调用 get_health_records() 查看数据
4. 需要了解近期情况时，调用 get_recent_diary() 查看日记
5. 给出重要建议时，调用 record_advice() 记录

## 回复原则
- 亲切专业，像一个有经验的宠物医生朋友
- 基于获取到的真实数据给出建议
- 不做确定性诊断，只提供参考
- 严重情况建议及时就医
- 回复简洁，避免冗长
```

## 对话示例

```
用户: 你好

Agent 思考: 新对话，需要了解宠物信息
Agent 调用: get_pet_profile()
返回: {name: "小白", breed: "英短", age: "2岁"}

Agent 回复: 你好！我是 AI 宠物健康顾问。我看到你的宠物是一只2岁的英短猫咪小白，
           请问有什么可以帮你的吗？

---

用户: 它最近不太爱吃东西

Agent 思考: 用户描述了食欲下降的症状，需要记录
Agent 调用: record_symptom("食欲下降", "moderate")
Agent 调用: get_health_records(7)
返回: {records: [...], summary: {avg_heart_rate: 120, ...}}

Agent 回复: 食欲下降可能有多种原因。我看了小白最近的健康数据，
           心率和活动量都在正常范围。请问这种情况持续多久了？
           有没有其他症状，比如呕吐或精神不振？
```

## 与旧版本的区别

| 方面 | 旧版本 | 新版本 |
|------|--------|--------|
| 数据获取 | 预先注入到 instruction | Agent 主动调用工具获取 |
| 工具函数 | 返回固定消息 | 真正查询数据库 |
| 症状记录 | 硬编码关键词匹配 | Agent 自主判断并调用工具 |
| 建议生成 | 预设模板 | Agent 自主生成 |
| 灵活性 | 低 | 高 |
