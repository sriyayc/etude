-- ==========================================================
-- USERS TABLE
-- ==========================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    role TEXT NOT NULL CHECK (role IN ('student', 'teacher')),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================================
-- DOCUMENTS TABLE
-- ==========================================================
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    uploaded_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    storage_bucket TEXT NOT NULL,
    storage_path TEXT UNIQUE NOT NULL,
    document_type TEXT NOT NULL CHECK (
        document_type IN ('textbook', 'slides', 'syllabus', 'lecture_notes')
    ),
    subject TEXT NOT NULL,
    semester INTEGER NOT NULL,
    content_hash TEXT UNIQUE NOT NULL,
    version INTEGER DEFAULT 1,
    is_current BOOLEAN DEFAULT TRUE,
    uploaded_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================================
-- SYLLABUS TOPICS
-- ==========================================================
CREATE TABLE IF NOT EXISTS syllabus_topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    subject TEXT NOT NULL,
    semester INTEGER NOT NULL,
    unit_number INTEGER NOT NULL,
    unit_title TEXT,
    topic TEXT NOT NULL,
    version INTEGER NOT NULL,
    is_current BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================================
-- QUERY LOGS
-- ==========================================================
CREATE TABLE IF NOT EXISTS query_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    answer TEXT,
    retrieved_chunk_ids TEXT[],
    response_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================================
-- QUIZ ATTEMPTS
-- ==========================================================
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic_name TEXT NOT NULL,
    score INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    questions JSONB,
    attempted_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================================
-- ENABLE RLS ON ALL TABLES
-- ==========================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE syllabus_topics ENABLE ROW LEVEL SECURITY;
ALTER TABLE query_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_attempts ENABLE ROW LEVEL SECURITY;

-- ==========================================================
-- USERS POLICIES
-- ==========================================================
CREATE POLICY "Users view own profile"
ON users FOR SELECT TO authenticated
USING (auth.uid() = id);

CREATE POLICY "Users create own profile"
ON users FOR INSERT TO authenticated
WITH CHECK (auth.uid() = id);

-- ==========================================================
-- DOCUMENTS POLICIES
-- ==========================================================
CREATE POLICY "Authenticated users read documents"
ON documents FOR SELECT TO authenticated
USING (true);

CREATE POLICY "Only teachers insert documents"
ON documents FOR INSERT TO authenticated
WITH CHECK (
    (SELECT role FROM users WHERE id = auth.uid()) = 'teacher'
);

CREATE POLICY "Only teachers update documents"
ON documents FOR UPDATE TO authenticated
USING (
    (SELECT role FROM users WHERE id = auth.uid()) = 'teacher'
);

CREATE POLICY "Only teachers delete documents"
ON documents FOR DELETE TO authenticated
USING (
    (SELECT role FROM users WHERE id = auth.uid()) = 'teacher'
);

-- ==========================================================
-- SYLLABUS TOPICS POLICIES
-- ==========================================================
CREATE POLICY "Authenticated users read syllabus"
ON syllabus_topics FOR SELECT TO authenticated
USING (true);

CREATE POLICY "Only teachers manage syllabus"
ON syllabus_topics FOR ALL TO authenticated
USING (
    (SELECT role FROM users WHERE id = auth.uid()) = 'teacher'
);

-- ==========================================================
-- QUERY LOGS POLICIES
-- ==========================================================
CREATE POLICY "Users see own queries"
ON query_logs FOR SELECT TO authenticated
USING (user_id = auth.uid());

CREATE POLICY "Users create own queries"
ON query_logs FOR INSERT TO authenticated
WITH CHECK (user_id = auth.uid());

-- ==========================================================
-- QUIZ ATTEMPTS POLICIES
-- ==========================================================
CREATE POLICY "Users see own quiz attempts"
ON quiz_attempts FOR SELECT TO authenticated
USING (user_id = auth.uid());

CREATE POLICY "Users create own quiz attempts"
ON quiz_attempts FOR INSERT TO authenticated
WITH CHECK (user_id = auth.uid());