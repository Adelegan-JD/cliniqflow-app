# Database migrations

Migrations are additive and are intentionally not executed on application
startup. Production changes must run through a reviewed deployment step, after
a tested backup, using a dedicated migration account.

Apply it to PostgreSQL once, after `database/schema.py` has created the legacy
tables:

```powershell
python -m database.migrate
```

The runner holds a PostgreSQL advisory lock, applies all numbered migrations in
one transaction, and records a checksum in `schema_migrations`. Never edit an
applied migration; add the next numbered migration instead.

`008_rag_governance.sql` adds reviewed knowledge-source metadata, immutable
dose-check snapshots, and explicit clinician override records. Only approved,
in-date medication content should be exposed to production RAG retrieval.

Payment records use integer kobo amounts and provider references only. Card
numbers, CVVs, bank credentials, and payment-provider secrets must never enter
the application database, application logs, or audit event payloads.
