-- ==========================================================
-- USERS TABLE
-- ==========================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    srn TEXT UNIQUE,
    role TEXT NOT NULL CHECK (
        role IN ('student', 'admin')
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
-- UNIT-GENERATED CONTENT CACHE (quiz / flashcards / notes)
-- Generated once per (subject, semester, unit_number) and shared by
-- every student who opens that unit -- not regenerated per student
-- per visit. Whichever student opens the unit first pays the
-- LLM-generation latency; everyone after gets the cached row.
-- ==========================================================
CREATE TABLE IF NOT EXISTS unit_quizzes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject TEXT NOT NULL,
    semester INTEGER NOT NULL,
    unit_number INTEGER NOT NULL,
    unit_title TEXT NOT NULL,
    questions JSONB NOT NULL,
    sources JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (subject, semester, unit_number)
);

CREATE TABLE IF NOT EXISTS unit_flashcards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject TEXT NOT NULL,
    semester INTEGER NOT NULL,
    unit_number INTEGER NOT NULL,
    unit_title TEXT NOT NULL,
    cards JSONB NOT NULL,
    sources JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (subject, semester, unit_number)
);

CREATE TABLE IF NOT EXISTS unit_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject TEXT NOT NULL,
    semester INTEGER NOT NULL,
    unit_number INTEGER NOT NULL,
    unit_title TEXT NOT NULL,
    notes_md TEXT NOT NULL,
    sources JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (subject, semester, unit_number)
);

ALTER TABLE unit_quizzes ENABLE ROW LEVEL SECURITY;
ALTER TABLE unit_flashcards ENABLE ROW LEVEL SECURITY;
ALTER TABLE unit_notes ENABLE ROW LEVEL SECURITY;

-- UPDATE is needed alongside INSERT because these rows are written via
-- upsert() -- the on-conflict path is a real UPDATE under the hood.
GRANT SELECT, INSERT, UPDATE ON unit_quizzes TO authenticated;
GRANT SELECT, INSERT, UPDATE ON unit_flashcards TO authenticated;
GRANT SELECT, INSERT, UPDATE ON unit_notes TO authenticated;

-- Any authenticated student can read; any authenticated student can
-- write, since the whole point is that whichever student opens the
-- unit first is the one who populates the cache for everyone else.
DROP POLICY IF EXISTS "Authenticated read unit_quizzes" ON unit_quizzes;
CREATE POLICY "Authenticated read unit_quizzes"
ON unit_quizzes FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Authenticated create unit_quizzes" ON unit_quizzes;
CREATE POLICY "Authenticated create unit_quizzes"
ON unit_quizzes FOR INSERT TO authenticated WITH CHECK (true);

-- Needed alongside INSERT because these rows are written via upsert() --
-- the on-conflict path is a real UPDATE under the hood.
DROP POLICY IF EXISTS "Authenticated update unit_quizzes" ON unit_quizzes;
CREATE POLICY "Authenticated update unit_quizzes"
ON unit_quizzes FOR UPDATE TO authenticated USING (true);

DROP POLICY IF EXISTS "Authenticated read unit_flashcards" ON unit_flashcards;
CREATE POLICY "Authenticated read unit_flashcards"
ON unit_flashcards FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Authenticated create unit_flashcards" ON unit_flashcards;
CREATE POLICY "Authenticated create unit_flashcards"
ON unit_flashcards FOR INSERT TO authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "Authenticated update unit_flashcards" ON unit_flashcards;
CREATE POLICY "Authenticated update unit_flashcards"
ON unit_flashcards FOR UPDATE TO authenticated USING (true);

DROP POLICY IF EXISTS "Authenticated read unit_notes" ON unit_notes;
CREATE POLICY "Authenticated read unit_notes"
ON unit_notes FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Authenticated create unit_notes" ON unit_notes;
CREATE POLICY "Authenticated create unit_notes"
ON unit_notes FOR INSERT TO authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "Authenticated update unit_notes" ON unit_notes;
CREATE POLICY "Authenticated update unit_notes"
ON unit_notes FOR UPDATE TO authenticated USING (true);

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
-- server-validated secrets (like the admin invite token) live
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
--   WHERE key = 'admin_invite_token';
-- (db/hardening_patch.sql upgrades this to a hashed key --
-- 'admin_invite_token_sha256' -- run it after this file.)
INSERT INTO app_secrets (key, value)
VALUES ('admin_invite_token', 'REPLACE_ME_VIA_SUPABASE_SQL_EDITOR')
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

-- REVOKE ... FROM PUBLIC alone does NOT undo a grant made directly to a
-- named role -- and the pre-existing live deployment of this function
-- had `GRANT EXECUTE ... TO anon, authenticated` applied explicitly.
-- Revoke from those roles by name, not just PUBLIC, or the original
-- anon-callable grant silently survives underneath.
REVOKE ALL ON FUNCTION get_email_by_srn(TEXT) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION get_email_by_srn(TEXT) TO service_role;

-- ==========================================================
-- TRIGGER: block direct role changes on users
-- (Defence in depth against a client updating its own row's role
-- via a normal UPDATE, even though no RLS policy currently permits
-- that. promote_to_admin() below is the one sanctioned path --
-- it opts in per-transaction via the etude.allow_role_change flag.)
-- ==========================================================

CREATE OR REPLACE FUNCTION prevent_role_self_change()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    IF NEW.role IS DISTINCT FROM OLD.role
       AND current_setting('etude.allow_role_change', true) IS DISTINCT FROM 'on'
    THEN
        RAISE EXCEPTION 'role cannot be changed directly';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_prevent_role_self_change ON users;
CREATE TRIGGER trg_prevent_role_self_change
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION prevent_role_self_change();

-- ==========================================================
-- RPC: promote the CALLING user to admin
-- (SECURITY DEFINER so it can update users.role, which no RLS
-- policy below permits directly. Only ever touches auth.uid()'s
-- own row, and only after checking the invite token against the
-- private app_secrets table above -- never against client-
-- supplied data or app-layer env config.
--
-- This is the plaintext baseline; db/hardening_patch.sql replaces
-- it with a version that compares a SHA-256 hash instead -- run
-- that file after this one in any real deployment.)
-- ==========================================================

CREATE OR REPLACE FUNCTION promote_to_admin(p_invite_token TEXT)
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
        SELECT value FROM app_secrets WHERE key = 'admin_invite_token'
    ) THEN
        RAISE EXCEPTION 'Invalid admin invite token';
    END IF;

    -- trg_prevent_role_self_change blocks role UPDATEs by default;
    -- this transaction-local flag (auto-resets at commit) is the
    -- one sanctioned opt-in, scoped to just this UPDATE.
    PERFORM set_config('etude.allow_role_change', 'on', true);
    UPDATE users SET role = 'admin' WHERE id = auth.uid();
END;
$$;

REVOKE ALL ON FUNCTION promote_to_admin(TEXT) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION promote_to_admin(TEXT) TO authenticated;

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
-- Every CREATE POLICY below is preceded by a DROP POLICY IF EXISTS
-- so this script is safely re-runnable against a live instance
-- that already has some (possibly differently-shaped) policies
-- applied from before this migration existed.
-- ==========================================================
DROP POLICY IF EXISTS "Users view own profile" ON users;
CREATE POLICY "Users view own profile"
ON users FOR SELECT TO authenticated
USING (auth.uid() = id);

-- "Users can insert own profile" was a duplicate of "Users create
-- own profile" left over from the two branches that got merged
-- into this file -- both had WITH CHECK (auth.uid() = id) with NO
-- role restriction. Permissive RLS policies are OR'd together, so
-- leaving either one in place independently re-opens the exact
-- role-escalation hole the policy below closes. Drop both names,
-- recreate only the hardened one.
DROP POLICY IF EXISTS "Users can insert own profile" ON users;
DROP POLICY IF EXISTS "Users create own profile" ON users;
-- role is pinned to 'student' here on purpose: this is the only
-- INSERT path RLS allows, so self-serve signup can never write
-- role = 'admin' directly. Admin promotion only happens
-- through promote_to_admin(), which is invite-token gated.
CREATE POLICY "Users create own profile"
ON users FOR INSERT TO authenticated
WITH CHECK (auth.uid() = id AND role = 'student');

-- ==========================================================
-- DOCUMENTS POLICIES
-- ==========================================================
DROP POLICY IF EXISTS "Authenticated users read documents" ON documents;
CREATE POLICY "Authenticated users read documents"
ON documents FOR SELECT TO authenticated
USING (true);

DROP POLICY IF EXISTS "Only teachers insert documents" ON documents;
DROP POLICY IF EXISTS "Only admin insert documents" ON documents;
CREATE POLICY "Only admin insert documents"
ON documents FOR INSERT TO authenticated
WITH CHECK (
    uploaded_by = auth.uid()
    AND (SELECT role FROM users WHERE id = auth.uid()) = 'admin'
);

DROP POLICY IF EXISTS "Only teachers update documents" ON documents;
DROP POLICY IF EXISTS "Only admin update documents" ON documents;
CREATE POLICY "Only admin update documents"
ON documents FOR UPDATE TO authenticated
USING (
    (SELECT role FROM users WHERE id = auth.uid()) = 'admin'
);

DROP POLICY IF EXISTS "Only teachers delete documents" ON documents;
DROP POLICY IF EXISTS "Only admin delete documents" ON documents;
CREATE POLICY "Only admin delete documents"
ON documents FOR DELETE TO authenticated
USING (
    (SELECT role FROM users WHERE id = auth.uid()) = 'admin'
);

-- ==========================================================
-- SYLLABUS TOPICS POLICIES
-- ==========================================================
DROP POLICY IF EXISTS "Authenticated users read syllabus" ON syllabus_topics;
CREATE POLICY "Authenticated users read syllabus"
ON syllabus_topics FOR SELECT TO authenticated
USING (true);

DROP POLICY IF EXISTS "Only teachers manage syllabus" ON syllabus_topics;
DROP POLICY IF EXISTS "Only admin manage syllabus" ON syllabus_topics;
CREATE POLICY "Only admin manage syllabus"
ON syllabus_topics FOR ALL TO authenticated
USING (
    (SELECT role FROM users WHERE id = auth.uid()) = 'admin'
);

-- ==========================================================
-- QUERY LOGS POLICIES
-- ==========================================================
DROP POLICY IF EXISTS "Users see own queries" ON query_logs;
CREATE POLICY "Users see own queries"
ON query_logs FOR SELECT TO authenticated
USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Users create own queries" ON query_logs;
CREATE POLICY "Users create own queries"
ON query_logs FOR INSERT TO authenticated
WITH CHECK (user_id = auth.uid());

-- ==========================================================
-- QUIZ ATTEMPTS POLICIES
-- ==========================================================
-- Same duplicate-policy situation as users above: "Users can view
-- own quiz attempts" and "Users see own quiz attempts" are two
-- differently-named copies of the identical SELECT check. Not a
-- security gap (both are equally restrictive), but redundant and
-- worth collapsing to one while we're here.
DROP POLICY IF EXISTS "Users can view own quiz attempts" ON quiz_attempts;
DROP POLICY IF EXISTS "Users see own quiz attempts" ON quiz_attempts;
CREATE POLICY "Users see own quiz attempts"
ON quiz_attempts FOR SELECT TO authenticated
USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Users create own quiz attempts" ON quiz_attempts;
CREATE POLICY "Users create own quiz attempts"
ON quiz_attempts FOR INSERT TO authenticated
WITH CHECK (user_id = auth.uid());

-- user_points / user_streaks are views, not tables -- no RLS policy
-- to add here. Access is already scoped to `authenticated` only via
-- the GRANTs issued where the views are defined above.

-- ==========================================================
-- STORAGE: "documents" bucket policies
-- (The bucket itself is created via the Supabase dashboard/API, not
-- here. Without these, storage.objects has zero policies and every
-- upload/download call fails regardless of caller role -- confirmed
-- via storage_service.upload_pdf raising "row-level security policy"
-- for an authenticated admin.)
-- ==========================================================

DROP POLICY IF EXISTS "Teachers upload to documents bucket" ON storage.objects;
DROP POLICY IF EXISTS "Admin upload to documents bucket" ON storage.objects;
CREATE POLICY "Admin upload to documents bucket"
ON storage.objects FOR INSERT TO authenticated
WITH CHECK (
    bucket_id = 'documents'
    AND (SELECT role FROM public.users WHERE id = auth.uid()) = 'admin'
);

DROP POLICY IF EXISTS "Authenticated users read documents bucket" ON storage.objects;
CREATE POLICY "Authenticated users read documents bucket"
ON storage.objects FOR SELECT TO authenticated
USING (bucket_id = 'documents');

DROP POLICY IF EXISTS "Teachers update documents bucket" ON storage.objects;
DROP POLICY IF EXISTS "Admin update documents bucket" ON storage.objects;
CREATE POLICY "Admin update documents bucket"
ON storage.objects FOR UPDATE TO authenticated
USING (
    bucket_id = 'documents'
    AND (SELECT role FROM public.users WHERE id = auth.uid()) = 'admin'
);

DROP POLICY IF EXISTS "Teachers delete from documents bucket" ON storage.objects;
DROP POLICY IF EXISTS "Admin delete from documents bucket" ON storage.objects;
CREATE POLICY "Admin delete from documents bucket"
ON storage.objects FOR DELETE TO authenticated
USING (
    bucket_id = 'documents'
    AND (SELECT role FROM public.users WHERE id = auth.uid()) = 'admin'
);

-- ==========================================================
-- SUBJECTS / SLIDES POLICIES
-- (These two tables are a pre-existing resources-browsing catalog
-- that predates this schema file -- their CREATE TABLE isn't tracked
-- here, only the write policies added when the upload flow was wired
-- to populate them via services/catalog_service.py.)
-- ==========================================================
DROP POLICY IF EXISTS "Only teachers insert subjects" ON subjects;
DROP POLICY IF EXISTS "Only admin insert subjects" ON subjects;
CREATE POLICY "Only admin insert subjects"
ON subjects FOR INSERT TO authenticated
WITH CHECK (
    (SELECT role FROM users WHERE id = auth.uid()) = 'admin'
);

DROP POLICY IF EXISTS "Only teachers update subjects" ON subjects;
DROP POLICY IF EXISTS "Only admin update subjects" ON subjects;
CREATE POLICY "Only admin update subjects"
ON subjects FOR UPDATE TO authenticated
USING (
    (SELECT role FROM users WHERE id = auth.uid()) = 'admin'
);

DROP POLICY IF EXISTS "Only teachers insert slides" ON slides;
DROP POLICY IF EXISTS "Only admin insert slides" ON slides;
CREATE POLICY "Only admin insert slides"
ON slides FOR INSERT TO authenticated
WITH CHECK (
    (SELECT role FROM users WHERE id = auth.uid()) = 'admin'
);

DROP POLICY IF EXISTS "Only teachers update slides" ON slides;
DROP POLICY IF EXISTS "Only admin update slides" ON slides;
CREATE POLICY "Only admin update slides"
ON slides FOR UPDATE TO authenticated
USING (
    (SELECT role FROM users WHERE id = auth.uid()) = 'admin'
);
