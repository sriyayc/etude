-- ================================================================
-- Etude security hardening patch
-- Run this in the Supabase SQL editor AFTER the main schema.sql.
-- Safe to run more than once (idempotent where it matters).
-- ================================================================

-- pgcrypto gives us digest() for hashing. Supabase ships it; this is a no-op
-- if already enabled.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ----------------------------------------------------------------
-- 1. Freeze the role column against self-service UPDATE.
--    Today no UPDATE policy exists, so role-PATCH already fails --
--    but this trigger makes it fail even if someone later adds a
--    naive "users edit own profile" UPDATE policy. Defense that
--    survives future edits.
-- ----------------------------------------------------------------
CREATE OR REPLACE FUNCTION prevent_role_self_change()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    -- Allow role changes only when NOT coming from the row's own user.
    -- promote_to_teacher() runs as SECURITY DEFINER (role = postgres),
    -- so auth.uid() there is still the caller -- we instead let that
    -- function bypass by checking a session flag it sets.
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

-- Explicit UPDATE policy so profile edits (name, etc.) still work,
-- while the trigger above guards the role column specifically.
DROP POLICY IF EXISTS "Users update own profile" ON users;
CREATE POLICY "Users update own profile"
ON users FOR UPDATE TO authenticated
USING (auth.uid() = id)
WITH CHECK (auth.uid() = id);

-- ----------------------------------------------------------------
-- 2. Store the invite token as a SHA-256 hash, and compare in a
--    way that doesn't leak length/content via timing. Also reject
--    the un-configured placeholder outright.
-- ----------------------------------------------------------------
CREATE OR REPLACE FUNCTION promote_to_teacher(p_invite_token TEXT)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    stored_hash TEXT;
    input_hash  TEXT;
BEGIN
    IF auth.uid() IS NULL THEN
        RAISE EXCEPTION 'Not authenticated';
    END IF;

    SELECT value INTO stored_hash
    FROM app_secrets WHERE key = 'teacher_invite_token_sha256';

    IF stored_hash IS NULL OR stored_hash = 'REPLACE_ME_VIA_SUPABASE_SQL_EDITOR' THEN
        RAISE LOG 'promote_to_teacher: invite system not configured';
        RAISE EXCEPTION 'invite system not configured';
    END IF;

    input_hash := encode(digest(coalesce(p_invite_token, ''), 'sha256'), 'hex');

    -- Both sides are fixed-length hex -> comparison time is uniform.
    IF input_hash <> stored_hash THEN
        RAISE LOG 'promote_to_teacher: bad token from %', auth.uid();
        RAISE EXCEPTION 'Invalid teacher invite token';
    END IF;

    -- Flag the session so the role-freeze trigger permits this one write.
    PERFORM set_config('etude.allow_role_change', 'on', true);
    UPDATE users SET role = 'teacher' WHERE id = auth.uid();
    PERFORM set_config('etude.allow_role_change', 'off', true);
END;
$$;

REVOKE ALL ON FUNCTION promote_to_teacher(TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION promote_to_teacher(TEXT) TO authenticated;

-- ----------------------------------------------------------------
-- 3. Seed the hashed-token key. You will set the REAL value in the
--    next manual step (see the guide). Old plaintext key is removed.
-- ----------------------------------------------------------------
DELETE FROM app_secrets WHERE key = 'teacher_invite_token';
INSERT INTO app_secrets (key, value)
VALUES ('teacher_invite_token_sha256', 'REPLACE_ME_VIA_SUPABASE_SQL_EDITOR')
ON CONFLICT (key) DO NOTHING;
