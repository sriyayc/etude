-- ==========================================================
-- Email verification support
-- ==========================================================
-- Problem this solves:
--   signup previously did sign_up() then INSERT INTO public.users from the
--   client. With email confirmation ENABLED, sign_up() returns a user but NO
--   session, so that insert runs unauthenticated and the RLS policy
--   (auth.uid() = id) rejects it -- the auth account exists but the profile
--   never gets created.
--
--   Fix: create the profile from a SECURITY DEFINER trigger on auth.users, so
--   it happens server-side at account-creation time regardless of session.
-- ==========================================================

-- Personal email is what the user signs up with and what password-reset /
-- confirmation mail goes to. SRN stays the login identifier.
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    -- Rollout guard. The pre-email client calls sign_up() without srn/full_name
    -- metadata and inserts the profile itself; if this trigger fired for it too,
    -- it would win the race and create a profile with a NULL srn -- breaking
    -- login-by-SRN and making a retry report "User already registered".
    -- Only take ownership when the new client's metadata is present.
    IF NOT (NEW.raw_user_meta_data ? 'srn') THEN
        RETURN NEW;
    END IF;

    INSERT INTO public.users (id, email, full_name, srn, role)
    VALUES (
        NEW.id,
        NEW.email,
        NULLIF(TRIM(NEW.raw_user_meta_data ->> 'full_name'), ''),
        NULLIF(UPPER(TRIM(NEW.raw_user_meta_data ->> 'srn')), ''),
        -- Role is hard-coded, never read from client-supplied metadata.
        -- Admin promotion stays behind the promote_to_admin() invite-token RPC.
        'student'
    )
    ON CONFLICT (id) DO NOTHING;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
AFTER INSERT ON auth.users
FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();


-- ----------------------------------------------------------
-- SRN availability pre-check
-- ----------------------------------------------------------
-- users.srn is UNIQUE, so a taken SRN makes the trigger raise
-- unique_violation, which aborts the auth.users insert and surfaces to the
-- client as an opaque "Database error saving new user". Checking first lets
-- the UI say something useful.
--
-- SECURITY DEFINER because anon must be able to call it pre-signup, but must
-- NOT be able to read the users table. It returns only a boolean -- no
-- enumeration of names/emails.
CREATE OR REPLACE FUNCTION public.srn_available(p_srn TEXT)
RETURNS BOOLEAN
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT NOT EXISTS (
        SELECT 1 FROM public.users
        WHERE srn = UPPER(TRIM(p_srn))
    );
$$;

REVOKE ALL ON FUNCTION public.srn_available(TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.srn_available(TEXT) TO anon, authenticated;
