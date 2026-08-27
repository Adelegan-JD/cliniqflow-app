-- The migration ledger is operational metadata and must not be exposed via
-- the Supabase Data API either.

REVOKE ALL ON TABLE public.schema_migrations FROM anon, authenticated;
