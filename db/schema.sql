-- ==========================================================
-- USERS TABLE
-- ==========================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY
        REFERENCES auth.users(id)
        ON DELETE CASCADE,

    email TEXT UNIQUE NOT NULL,

    full_name TEXT,

    srn TEXT UNIQUE,

    role TEXT NOT NULL CHECK (
        role IN ('student', 'teacher')
    ),

    created_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================================
-- DOCUMENTS TABLE
-- ==========================================================

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    uploaded_by UUID NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    title TEXT NOT NULL,

    storage_bucket TEXT NOT NULL,

    storage_path TEXT UNIQUE NOT NULL,

    document_type TEXT NOT NULL CHECK (
        document_type IN (
            'textbook',
            'slides',
            'syllabus'
        )
    ),

    uploaded_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================================
-- SYLLABUS TOPICS
-- ==========================================================

CREATE TABLE IF NOT EXISTS syllabus_topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    document_id UUID NOT NULL
        REFERENCES documents(id)
        ON DELETE CASCADE,

    subject TEXT NOT NULL,

    module_number INTEGER NOT NULL,

    topic_name TEXT NOT NULL,

    status TEXT NOT NULL CHECK (
        status IN (
            'active',
            'stale'
        )
    ),

    syllabus_year INTEGER NOT NULL,

    created_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================================
-- QUERY LOGS
-- ==========================================================

CREATE TABLE IF NOT EXISTS query_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    question TEXT NOT NULL,

    answer TEXT,

    response_time_ms INTEGER,

    created_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================================
-- QUIZ ATTEMPTS
-- ==========================================================

CREATE TABLE IF NOT EXISTS quiz_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    topic_name TEXT NOT NULL,

    score INTEGER NOT NULL,

    total_questions INTEGER NOT NULL,

    attempted_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================================
-- USER POINTS
-- ==========================================================

CREATE TABLE IF NOT EXISTS user_points (
    user_id UUID PRIMARY KEY
        REFERENCES users(id)
        ON DELETE CASCADE,

    points INTEGER NOT NULL DEFAULT 0,

    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================================
-- USER STREAKS
-- ==========================================================

CREATE TABLE IF NOT EXISTS user_streaks (
    user_id UUID PRIMARY KEY
        REFERENCES users(id)
        ON DELETE CASCADE,

    current_streak INTEGER NOT NULL DEFAULT 0,

    last_active_date DATE,

    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================================
-- LEADERBOARD VIEWS
-- (owned by the migration-running role, e.g. `postgres`, so
-- they can read across all users' rows for ranking purposes
-- even though user_points/user_streaks RLS below is
-- own-row-only for direct table access.)
-- ==========================================================

CREATE OR REPLACE VIEW leaderboard AS
SELECT
    p.user_id,
    p.points,
    COALESCE(s.current_streak, 0) AS streak,
    RANK() OVER (ORDER BY p.points DESC) AS rank
FROM user_points p
LEFT JOIN user_streaks s ON s.user_id = p.user_id;

CREATE OR REPLACE VIEW leaderboard_full AS
SELECT
    l.rank,
    u.full_name,
    u.srn,
    l.points,
    l.streak,
    l.user_id
FROM leaderboard l
JOIN users u ON u.id = l.user_id;

-- ==========================================================
-- RPC: look up a user's auth email by SRN
-- (SECURITY DEFINER so it can be called by an unauthenticated
-- client during login, before RLS would otherwise allow a
-- direct read of the users table.)
-- ==========================================================

CREATE OR REPLACE FUNCTION get_email_by_srn(p_srn TEXT)
RETURNS TEXT
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT email FROM users WHERE srn = p_srn LIMIT 1;
$$;

GRANT EXECUTE ON FUNCTION get_email_by_srn(TEXT) TO anon, authenticated;

-- ==========================================================
-- ENABLE ROW LEVEL SECURITY
-- ==========================================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE syllabus_topics ENABLE ROW LEVEL SECURITY;
ALTER TABLE query_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_points ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_streaks ENABLE ROW LEVEL SECURITY;

-- ==========================================================
-- RLS POLICIES
-- ==========================================================

CREATE POLICY "Users can view own profile"
ON users
FOR SELECT
TO authenticated
USING (auth.uid() = id);

CREATE POLICY "Authenticated users can read documents"
ON documents
FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Teachers can upload documents"
ON documents
FOR INSERT
TO authenticated
WITH CHECK (
    uploaded_by = auth.uid()
    AND EXISTS (
        SELECT 1 FROM users
        WHERE id = auth.uid() AND role = 'teacher'
    )
);

CREATE POLICY "Authenticated users can read syllabus topics"
ON syllabus_topics
FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Users can view own query logs"
ON query_logs
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own query logs"
ON query_logs
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own quiz attempts"
ON quiz_attempts
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own quiz attempts"
ON quiz_attempts
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own points"
ON user_points
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

CREATE POLICY "Users can view own streak"
ON user_streaks
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);
