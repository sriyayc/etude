```sql
-- ==========================================================
-- USERS TABLE
-- ==========================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY
        REFERENCES auth.users(id)
        ON DELETE CASCADE,

    email TEXT UNIQUE NOT NULL,

    full_name TEXT,

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
-- ENABLE ROW LEVEL SECURITY
-- ==========================================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE syllabus_topics ENABLE ROW LEVEL SECURITY;
ALTER TABLE query_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_attempts ENABLE ROW LEVEL SECURITY;

-- ==========================================================
-- BASIC RLS POLICIES
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
```
