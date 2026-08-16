create table if not exists public.pilot_feedback (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  provider text not null default '',
  recommendation text not null default '',
  application_type text not null default '',
  word_count integer not null default 0 check (word_count >= 0),
  usefulness integer check (usefulness between 1 and 10),
  would_submit boolean,
  recommendation_trust boolean,
  material_time_saving boolean,
  would_use_again boolean,
  payment_signal text check (payment_signal in ('yes', 'maybe', 'no')),
  created_at timestamptz not null default now()
);

create index if not exists pilot_feedback_user_id_idx on public.pilot_feedback (user_id);
create index if not exists pilot_feedback_created_at_idx on public.pilot_feedback (created_at desc);

alter table public.pilot_feedback enable row level security;

create policy "Users can read own pilot feedback" on public.pilot_feedback
  for select using (auth.uid() = user_id);

create policy "Users can insert own pilot feedback" on public.pilot_feedback
  for insert with check (auth.uid() = user_id);

create policy "Service role can manage pilot feedback" on public.pilot_feedback
  for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
