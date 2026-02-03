-- ================================================
-- SUPABASE TABLE SETUP
-- Run this SQL in Supabase SQL Editor
-- ================================================

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    telegram_user_id TEXT UNIQUE NOT NULL,
    name TEXT,
    timezone TEXT DEFAULT 'Asia/Makassar',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. TASKS TABLE
CREATE TABLE IF NOT EXISTS tasks (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'open',
    priority INTEGER DEFAULT 0,
    due_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. MESSAGES TABLE
CREATE TABLE IF NOT EXISTS messages (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    source TEXT DEFAULT 'telegram',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. APPROVAL REQUESTS TABLE
CREATE TABLE IF NOT EXISTS approval_requests (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    action_type TEXT NOT NULL,
    action_payload_json JSONB,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- 5. MEMORY TABLE (preferences, reflections)
CREATE TABLE IF NOT EXISTS memory (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    memory_type TEXT DEFAULT 'preference',
    key TEXT,
    value TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. IMPROVEMENT PROPOSALS TABLE
CREATE TABLE IF NOT EXISTS improvement_proposals (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    proposal_json JSONB,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. ACTIVE RULES TABLE
CREATE TABLE IF NOT EXISTS active_rules (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    rule_type TEXT NOT NULL,
    rule_json JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    proposal_id BIGINT REFERENCES improvement_proposals(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- INDEXES
CREATE INDEX idx_tasks_user_status ON tasks(user_id, status);
CREATE INDEX idx_messages_user ON messages(user_id);
CREATE INDEX idx_approval_user_status ON approval_requests(user_id, status);

-- Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE approval_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE improvement_proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE active_rules ENABLE ROW LEVEL SECURITY;

-- Policy: Allow all for anon (for bot usage)
-- NOTE: In production, use service_role key instead
CREATE POLICY "Allow all for anon" ON users FOR ALL USING (true);
CREATE POLICY "Allow all for anon" ON tasks FOR ALL USING (true);
CREATE POLICY "Allow all for anon" ON messages FOR ALL USING (true);
CREATE POLICY "Allow all for anon" ON approval_requests FOR ALL USING (true);
CREATE POLICY "Allow all for anon" ON memory FOR ALL USING (true);
CREATE POLICY "Allow all for anon" ON improvement_proposals FOR ALL USING (true);
CREATE POLICY "Allow all for anon" ON active_rules FOR ALL USING (true);
