create table if not exists public.evidence_cards (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  situation text not null default '',
  task text not null default '',
  actions jsonb not null default '[]'::jsonb,
  outcome text not null default '',
  reflection text not null default '',
  tags text[] not null default '{}',
  behaviours text[] not null default '{}',
  skills text[] not null default '{}',
  authority_context text,
  source text not null default 'manual',
  confidence integer not null default 70 check (confidence between 0 and 100),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists evidence_cards_user_id_idx on public.evidence_cards (user_id);
create index if not exists evidence_cards_updated_at_idx on public.evidence_cards (updated_at desc);

alter table public.evidence_cards enable row level security;

create policy "Users can read own evidence" on public.evidence_cards
  for select using (auth.uid() = user_id);

create policy "Users can insert own evidence" on public.evidence_cards
  for insert with check (auth.uid() = user_id);

create policy "Users can update own evidence" on public.evidence_cards
  for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "Users can delete own evidence" on public.evidence_cards
  for delete using (auth.uid() = user_id);

create policy "Service role can manage evidence" on public.evidence_cards
  for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
