create table if not exists public.candidate_profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  source_filename text not null default '',
  summary text not null default '',
  skills jsonb not null default '[]'::jsonb,
  experience jsonb not null default '[]'::jsonb,
  qualifications jsonb not null default '[]'::jsonb,
  extraction_provider text not null default 'fallback',
  updated_at timestamptz not null default now()
);

alter table public.candidate_profiles enable row level security;

revoke all on table public.candidate_profiles from anon, authenticated;
grant select, insert, update, delete on table public.candidate_profiles to service_role;

create index if not exists candidate_profiles_updated_at_idx
  on public.candidate_profiles (updated_at desc);
