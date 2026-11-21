-- Disposable synthetic PostgreSQL ONLY. This is not a production migration.
-- Assumes stage2_synthetic_rehearsal.sql has created TWO synthetic target
-- users and 4 cards + 3 feedback rows. The original 2-to-2 state is restored
-- at the end through ROLLBACK.
begin;

insert into auth.users(id) values ('00000000-0000-4000-8000-000000000033');

create temp table owner_approved_mapping (
  old_user_id uuid primary key,
  new_user_id uuid not null,
  owner_verified boolean not null
) on commit drop;

-- Deliberate many-to-one remapping, authorized only for these fake owners.
insert into owner_approved_mapping values
 ('00000000-0000-4000-8000-000000000031','00000000-0000-4000-8000-000000000033',true),
 ('00000000-0000-4000-8000-000000000032','00000000-0000-4000-8000-000000000033',true);

create temp table staged_evidence on commit drop
  as select * from public.evidence_cards;
create temp table staged_feedback on commit drop
  as select * from public.pilot_feedback;

do $preflight$
begin
  if (select count(distinct old_user_id) from owner_approved_mapping) <> 2
    or (select count(distinct new_user_id) from owner_approved_mapping) <> 1
    or exists(select 1 from owner_approved_mapping where not owner_verified)
    or exists(select 1 from owner_approved_mapping m
              where not exists(select 1 from auth.users u where u.id=m.new_user_id))
    or exists(select 1 from staged_evidence s
              left join owner_approved_mapping m on m.old_user_id=s.user_id
              where m.new_user_id is null)
    or exists(select 1 from staged_feedback s
              left join owner_approved_mapping m on m.old_user_id=s.user_id
              where m.new_user_id is null)
  then raise exception 'Unverified, ambiguous or missing source owner mapping'; end if;
  if (select count(*) from staged_evidence) <> 4 or
     (select count(*) from staged_feedback) <> 3 then
    raise exception 'Unexpected synthetic source record totals'; end if;
end
$preflight$;

-- Local synthetic-only clearing enables checking retention of the exact
-- original record IDs. NEVER run these DELETEs against either Supabase project.
delete from public.evidence_cards;
delete from public.pilot_feedback;

insert into public.evidence_cards
  (id,user_id,title,situation,task,actions,outcome,reflection,
   tags,behaviours,skills,authority_context,source,confidence,created_at,updated_at)
select s.id,m.new_user_id,s.title,s.situation,s.task,s.actions,s.outcome,s.reflection,
       s.tags,s.behaviours,s.skills,s.authority_context,s.source,s.confidence,
       s.created_at,s.updated_at
from staged_evidence s
join owner_approved_mapping m on m.old_user_id=s.user_id;

insert into public.pilot_feedback
  (id,user_id,provider,recommendation,application_type,word_count,usefulness,
   would_submit,recommendation_trust,material_time_saving,would_use_again,
   payment_signal,created_at)
select s.id,m.new_user_id,s.provider,s.recommendation,s.application_type,s.word_count,
       s.usefulness,s.would_submit,s.recommendation_trust,s.material_time_saving,
       s.would_use_again,s.payment_signal,s.created_at
from staged_feedback s
join owner_approved_mapping m on m.old_user_id=s.user_id;

do $verification$
begin
  if (select count(*) from public.evidence_cards) <> 4
    or (select count(*) from public.pilot_feedback) <> 3
    or (select count(*) from public.evidence_cards
        where user_id = '00000000-0000-4000-8000-000000000033') <> 4
    or (select count(*) from public.pilot_feedback
        where user_id = '00000000-0000-4000-8000-000000000033') <> 3
  then raise exception 'Consolidated record count or ownership mismatch'; end if;

  if (select count(*)
      from staged_evidence s
      join owner_approved_mapping m on m.old_user_id=s.user_id
      join public.evidence_cards d on d.id=s.id
      where d.user_id=m.new_user_id
        and (to_jsonb(d) - 'user_id') = (to_jsonb(s) - 'user_id')) <> 4
  then raise exception 'Consolidated evidence lost fields, IDs or timestamps'; end if;

  if (select count(*)
      from staged_feedback s
      join owner_approved_mapping m on m.old_user_id=s.user_id
      join public.pilot_feedback d on d.id=s.id
      where d.user_id=m.new_user_id
        and (to_jsonb(d) - 'user_id') = (to_jsonb(s) - 'user_id')) <> 3
  then raise exception 'Consolidated feedback lost fields, IDs or timestamps'; end if;
end
$verification$;

-- Return disposable fixture to the two-user state for the existing RLS tests.
rollback;
