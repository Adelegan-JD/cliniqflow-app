-- CLINIQ-FLOW keeps all EMR reads and writes behind its backend API.
-- The public Supabase Data API must never expose clinical data directly to a
-- browser, even to an authenticated staff member.  The backend connects with
-- the deployment database role and applies application-level authorisation.

REVOKE USAGE ON SCHEMA public FROM anon, authenticated;

DO $$
DECLARE
    target_table text;
BEGIN
    FOR target_table IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename <> 'schema_migrations'
    LOOP
        EXECUTE format('ALTER TABLE public.%%I ENABLE ROW LEVEL SECURITY', target_table);
        EXECUTE format('REVOKE ALL ON TABLE public.%%I FROM anon, authenticated', target_table);
    END LOOP;
END $$;
