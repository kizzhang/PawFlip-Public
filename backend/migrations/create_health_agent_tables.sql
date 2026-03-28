-- ===========================================
-- Health Agent 对话管理表结构
-- 在 Supabase SQL Editor 中执行此脚本
-- ===========================================

-- ===========================================
-- 对话表
-- ===========================================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    pet_id UUID NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
    title VARCHAR(255),                    -- 自动生成的对话标题
    summary TEXT,                          -- 对话摘要（定期更新）
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'archived')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 对话表索引
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_pet_id ON conversations(pet_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC);

-- 对话表注释
COMMENT ON TABLE conversations IS 'Health Agent 对话记录';
COMMENT ON COLUMN conversations.title IS '自动生成的对话标题';
COMMENT ON COLUMN conversations.summary IS '对话摘要，用于长对话压缩';

-- ===========================================
-- 消息表
-- ===========================================
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',           -- 额外信息（症状标签等）
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 消息表索引
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- 消息表注释
COMMENT ON TABLE messages IS 'Health Agent 对话消息';
COMMENT ON COLUMN messages.role IS '消息角色: user 或 assistant';
COMMENT ON COLUMN messages.metadata IS '额外元数据，如症状标签';

-- ===========================================
-- 关键信息表（永不删除，用于长期记忆）
-- ===========================================
CREATE TABLE IF NOT EXISTS key_info (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL CHECK (type IN ('symptom', 'diagnosis', 'advice')),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 关键信息表索引
CREATE INDEX IF NOT EXISTS idx_key_info_conversation_id ON key_info(conversation_id);
CREATE INDEX IF NOT EXISTS idx_key_info_type ON key_info(type);

-- 关键信息表注释
COMMENT ON TABLE key_info IS '对话中提取的关键信息，永不删除';
COMMENT ON COLUMN key_info.type IS '信息类型: symptom(症状), diagnosis(诊断), advice(建议)';

-- ===========================================
-- 更新时间触发器
-- ===========================================
DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations;
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ===========================================
-- Row Level Security (RLS)
-- ===========================================
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE key_info ENABLE ROW LEVEL SECURITY;

-- ===========================================
-- 完成
-- ===========================================
-- Health Agent 表结构创建完成！
