-- ===========================================
-- PetAI Backend - Supabase 数据库架构
-- 在 Supabase SQL Editor 中执行此脚本
-- ===========================================

-- 启用 UUID 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===========================================
-- 用户表
-- ===========================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100),
    password_hash VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    is_pro BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 用户表索引
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ===========================================
-- 宠物表
-- ===========================================
CREATE TABLE IF NOT EXISTS pets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    breed VARCHAR(100) NOT NULL,
    age VARCHAR(50) NOT NULL,
    avatar_url TEXT,
    battery INTEGER DEFAULT 100 CHECK (battery >= 0 AND battery <= 100),
    health_score INTEGER DEFAULT 100 CHECK (health_score >= 0 AND health_score <= 100),
    steps INTEGER DEFAULT 0 CHECK (steps >= 0),
    next_feeding VARCHAR(10),
    model_3d_url TEXT,
    model_3d_preview TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 宠物表索引
CREATE INDEX IF NOT EXISTS idx_pets_user_id ON pets(user_id);

-- 宠物表注释
COMMENT ON COLUMN pets.model_3d_url IS '3D 模型文件 URL (GLB 格式)';
COMMENT ON COLUMN pets.model_3d_preview IS '3D 模型预览图 URL';

-- ===========================================
-- 日记条目表
-- ===========================================
CREATE TABLE IF NOT EXISTS diary_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    pet_id UUID NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    type VARCHAR(50) DEFAULT 'activity' CHECK (type IN ('activity', 'feeding', 'health', 'social')),
    image_url TEXT,
    video_url TEXT,
    is_video BOOLEAN DEFAULT FALSE,
    duration VARCHAR(20),
    status VARCHAR(50) DEFAULT '正常',
    activity_trend JSONB,
    ai_analysis JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 日记表索引
CREATE INDEX IF NOT EXISTS idx_diary_entries_pet_id ON diary_entries(pet_id);
CREATE INDEX IF NOT EXISTS idx_diary_entries_user_id ON diary_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_diary_entries_created_at ON diary_entries(created_at DESC);

-- ===========================================
-- 健康记录表
-- ===========================================
CREATE TABLE IF NOT EXISTS health_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pet_id UUID NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
    heart_rate INTEGER CHECK (heart_rate >= 0 AND heart_rate <= 300),
    steps INTEGER CHECK (steps >= 0),
    sleep_hours DECIMAL(4,2) CHECK (sleep_hours >= 0 AND sleep_hours <= 24),
    calories INTEGER CHECK (calories >= 0),
    activity_minutes INTEGER CHECK (activity_minutes >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 健康记录表索引
CREATE INDEX IF NOT EXISTS idx_health_records_pet_id ON health_records(pet_id);
CREATE INDEX IF NOT EXISTS idx_health_records_created_at ON health_records(created_at DESC);

-- ===========================================
-- 社交帖子表
-- ===========================================
CREATE TABLE IF NOT EXISTS social_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    pet_id UUID NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    image_url TEXT,
    is_ai_story BOOLEAN DEFAULT FALSE,
    diary_entry_id UUID REFERENCES diary_entries(id) ON DELETE SET NULL,
    likes INTEGER DEFAULT 0 CHECK (likes >= 0),
    comments INTEGER DEFAULT 0 CHECK (comments >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 社交帖子表索引
CREATE INDEX IF NOT EXISTS idx_social_posts_user_id ON social_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_social_posts_pet_id ON social_posts(pet_id);
CREATE INDEX IF NOT EXISTS idx_social_posts_created_at ON social_posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_social_posts_likes ON social_posts(likes DESC);

-- ===========================================
-- 通知表
-- ===========================================
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    icon VARCHAR(50) DEFAULT 'notifications',
    color VARCHAR(50) DEFAULT 'text-gray-500',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 通知表索引
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);

-- ===========================================
-- 设备表
-- ===========================================
CREATE TABLE IF NOT EXISTS devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    pet_id UUID NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    device_type VARCHAR(50) DEFAULT 'collar',
    firmware_version VARCHAR(50),
    is_connected BOOLEAN DEFAULT FALSE,
    battery_level INTEGER DEFAULT 100 CHECK (battery_level >= 0 AND battery_level <= 100),
    last_sync TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 设备表索引
CREATE INDEX IF NOT EXISTS idx_devices_user_id ON devices(user_id);
CREATE INDEX IF NOT EXISTS idx_devices_pet_id ON devices(pet_id);

-- ===========================================
-- 视频处理任务表
-- ===========================================
CREATE TABLE IF NOT EXISTS video_jobs (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    pet_id UUID REFERENCES pets(id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    video_path TEXT,
    result JSONB,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 视频任务表索引
CREATE INDEX IF NOT EXISTS idx_video_jobs_user_id ON video_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_video_jobs_status ON video_jobs(status);

-- ===========================================
-- 更新时间触发器函数
-- ===========================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表添加更新时间触发器
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_pets_updated_at ON pets;
CREATE TRIGGER update_pets_updated_at
    BEFORE UPDATE ON pets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_diary_entries_updated_at ON diary_entries;
CREATE TRIGGER update_diary_entries_updated_at
    BEFORE UPDATE ON diary_entries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_social_posts_updated_at ON social_posts;
CREATE TRIGGER update_social_posts_updated_at
    BEFORE UPDATE ON social_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_devices_updated_at ON devices;
CREATE TRIGGER update_devices_updated_at
    BEFORE UPDATE ON devices
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ===========================================
-- Row Level Security (RLS) 策略
-- ===========================================

-- 启用 RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE pets ENABLE ROW LEVEL SECURITY;
ALTER TABLE diary_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE video_jobs ENABLE ROW LEVEL SECURITY;

-- 注意：实际的 RLS 策略需要根据您的认证方式配置
-- 以下是示例策略，使用服务端 API 时可能需要调整

-- 示例：允许服务端完全访问（使用 service_role key）
-- CREATE POLICY "Service role has full access" ON users
--     FOR ALL
--     USING (true)
--     WITH CHECK (true);

-- ===========================================
-- 完成
-- ===========================================
-- 数据库架构创建完成！
-- 请在 Supabase 控制台中执行此脚本
