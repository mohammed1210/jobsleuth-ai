-- Stage 4: provenance and expiry metadata for externally-sourced vacancies.
-- Apply ONLY to dedicated JobSleuth Supabase uqvhnqhbushhtkthwrhk.
-- Additive; old saved_jobs and evidence remain untouched.
-- Must be applied with Supabase's tracked apply_migration AFTER review.
alter table public.jobs
  add column if not exists source_board text,
  add column if not exists external_id text,
  add column if not exists is_active boolean not null default true,
  add column if not exists last_seen_at timestamptz,
  add column if not exists source_updated_at timestamptz;

-- NULLs remain distinct, allowing legacy/manual jobs with no external ID.
-- Upsert explicitly targets these three columns; do not use a partial index.
create unique index if not exists jobs_provider_identity_unique
  on public.jobs(source, source_board, external_id);

create index if not exists jobs_live_created_idx
  on public.jobs(created_at desc, id desc) where is_active=true;

-- Jobs remain public READ only; only the backend's service-role client writes.
-- No new Auth, billing, RLS or subscription policies are introduced here.
