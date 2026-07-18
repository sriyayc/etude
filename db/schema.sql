-- ==========================================================
-- USERS TABLE
-- ==========================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
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
-- USER POINTS
-- Computed view, not a base table -- there is no write path for
-- points anywhere in the app; it's a live SUM over quiz_attempts.
-- ==========================================================
CREATE OR REPLACE VIEW user_points AS
SELECT
    u.id AS user_id,
    u.full_name,
    u.srn,
    COALESCE((sum(qa.score) * 100), (0)::bigint) AS points
FROM users u
LEFT JOIN quiz_attempts qa ON (qa.user_id = u.id)
GROUP BY u.id, u.full_name, u.srn;

-- ==========================================================
-- USER STREAKS
-- Computed view, not a base table -- derives the current
-- consecutive-day streak from distinct quiz_attempts dates.
-- ==========================================================
CREATE OR REPLACE VIEW user_streaks AS
WITH attempt_days AS (
    SELECT DISTINCT
        quiz_attempts.user_id,
        (quiz_attempts.attempted_at)::date AS day
    FROM quiz_attempts
), grouped AS (
    SELECT
        attempt_days.user_id,
        attempt_days.day,
        (attempt_days.day - (row_number() OVER (
            PARTITION BY attempt_days.user_id ORDER BY attempt_days.day
        ))::integer) AS grp
    FROM attempt_days
), islands AS (
    SELECT
        grouped.user_id,
        grouped.grp,
        count(*) AS streak_length,
        max(grouped.day) AS last_day
    FROM grouped
    GROUP BY grouped.user_id, grouped.grp
)
SELECT
    user_id,
    streak_length AS current_streak
FROM islands
WHERE (last_day >= (CURRENT_DATE - '1 day'::interval))
ORDER BY user_id;

-- Views can't take RLS policies or ALTER TABLE ... ENABLE ROW LEVEL
-- SECURITY (that errors: "not supported for views"). They also aren't
-- filtered to the querying user's own row -- like the leaderboard
-- views below, they read across all users by design. Restrict them to
-- authenticated only; anon must never see this (matches leaderboard's
-- audience, and neither is granted to anon).
GRANT SELECT ON user_points TO authenticated;
GRANT SELECT ON user_streaks TO authenticated;

-- ==========================================================
-- LEADERBOARD VIEWS
-- (owned by the migration-running role, e.g. `postgres`, so
-- they can read across all users' rows for ranking purposes.)
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

-- Same reasoning as user_points/user_streaks above: explicit grant so
-- visibility doesn't depend on ambient default privileges. Authenticated
-- only, never anon.
GRANT SELECT ON leaderboard TO authenticated;
GRANT SELECT ON leaderboard_full TO authenticated;

-- ==========================================================
-- APP SECRETS
-- RLS is enabled with zero policies below, and no GRANTs are
-- issued to anon/authenticated: PostgREST can never read or
-- write this table under those roles. Only SECURITY DEFINER
-- functions (which run as the table owner) or a direct
-- service_role/postgres connection can touch it. This is where
-- server-validated secrets (like the teacher invite token) live
-- instead of in app-layer env config.
-- ==========================================================
CREATE TABLE IF NOT EXISTS app_secrets (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

ALTER TABLE app_secrets ENABLE ROW LEVEL SECURITY;

-- Placeholder only. After running this migration, set the real
-- value from the Supabase SQL editor (a service_role/postgres
-- connection, never from a migration file that gets committed):
--   UPDATE app_secrets SET value = '<the real invite token>'
--   WHERE key = 'teacher_invite_token';
INSERT INTO app_secrets (key, value)
VALUES ('teacher_invite_token', 'REPLACE_ME_VIA_SUPABASE_SQL_EDITOR')
ON CONFLICT (key) DO NOTHING;

-- ==========================================================
-- RPC: look up a user's auth email by SRN
-- (SECURITY DEFINER so it can be called before login, when the
-- caller has no session yet. PES SRNs are sequential and
-- enumerable, so this must NEVER be reachable by anon or
-- authenticated -- that would let anyone script-harvest every
-- user's email pre-auth. It is granted only to service_role,
-- i.e. only callable from the trusted backend, never directly
-- from a public client holding just the publishable key.)
-- ==========================================================

CREATE OR REPLACE FUNCTION get_email_by_srn(p_srn TEXT)
RETURNS TEXT
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT email FROM users WHERE srn = p_srn LIMIT 1;
$$;

REVOKE ALL ON FUNCTION get_email_by_srn(TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION get_email_by_srn(TEXT) TO service_role;

-- ==========================================================
-- RPC: promote the CALLING user to teacher
-- (SECURITY DEFINER so it can update users.role, which no RLS
-- policy below permits directly. Only ever touches auth.uid()'s
-- own row, and only after checking the invite token against the
-- private app_secrets table above -- never against client-
-- supplied data or app-layer env config.)
-- ==========================================================

CREATE OR REPLACE FUNCTION promote_to_teacher(p_invite_token TEXT)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    IF auth.uid() IS NULL THEN
        RAISE EXCEPTION 'Not authenticated';
    END IF;

    IF p_invite_token IS NULL OR p_invite_token <> (
        SELECT value FROM app_secrets WHERE key = 'teacher_invite_token'
    ) THEN
        RAISE EXCEPTION 'Invalid teacher invite token';
    END IF;

    UPDATE users SET role = 'teacher' WHERE id = auth.uid();
END;
$$;

REVOKE ALL ON FUNCTION promote_to_teacher(TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION promote_to_teacher(TEXT) TO authenticated;

-- ==========================================================
-- ENABLE ROW LEVEL SECURITY
-- ==========================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE syllabus_topics ENABLE ROW LEVEL SECURITY;
ALTER TABLE query_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_attempts ENABLE ROW LEVEL SECURITY;
-- user_points / user_streaks are views (see above), not tables --
-- ENABLE ROW LEVEL SECURITY doesn't apply to them; access is
-- controlled by the GRANTs already issued where they're defined.

-- ==========================================================
-- USERS POLICIES
-- ==========================================================
CREATE POLICY "Users view own profile"
ON users FOR SELECT TO authenticated
USING (auth.uid() = id);

-- role is pinned to 'student' here on purpose: this is the only
-- INSERT path RLS allows, so self-serve signup can never write
-- role = 'teacher' directly. Teacher promotion only happens
-- through promote_to_teacher(), which is invite-token gated.
CREATE POLICY "Users create own profile"
ON users FOR INSERT TO authenticated
WITH CHECK (auth.uid() = id AND role = 'student');

-- ==========================================================
-- DOCUMENTS POLICIES
-- ==========================================================
CREATE POLICY "Authenticated users read documents"
ON documents FOR SELECT TO authenticated
USING (true);

CREATE POLICY "Only teachers insert documents"
ON documents FOR INSERT TO authenticated
WITH CHECK (
    uploaded_by = auth.uid()
    AND (SELECT role FROM users WHERE id = auth.uid()) = 'teacher'
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

-- user_points / user_streaks are views, not tables -- no RLS policy
-- to add here. Access is already scoped to `authenticated` only via
-- the GRANTs issued where the views are defined above.
