-- SYNTHETIC / disposable Postgres only. No project URLs, credentials
-- or real records. Assumes the isolated Stage 1 schema has been installed.
begin;
create temp table private_owner_map (
  old_user_id uuid primary key,
  new_user_id uuid not null unique
) on commit drop;

-- Stage-shaped rows have column defaults but not the original foreign keys.
create temp table staged_evidence (like public.evidence_cards including defaults) on commit drop;
create temp table staged_feedback (like public.pilot_feedback including defaults) on commit drop;

insert into auth.users (id) values
 ('00000000-0000-4000-8000-000000000031'),
 ('00000000-0000-4000-8000-000000000032');

insert into private_owner_map (old_user_id,new_user_id) values
 ('00000000-0000-4000-8000-000000000021','00000000-0000-4000-8000-000000000031'),
 ('00000000-0000-4000-8000-000000000022','00000000-0000-4000-8000-000000000032');

-- One card belongs to synthetic account A, three to account B.
insert into staged_evidence
 (id,user_id,title,situation,actions,tags,created_at,updated_at) values
 ('10000000-0000-4000-8000-000000000101','00000000-0000-4000-8000-000000000021',
  'Synthetic card A','Synthetic situation','["synthetic"]'::jsonb,array['fixture'],
  '2026-01-01T00:00:00Z','2026-01-02T00:00:00Z'),
 ('10000000-0000-4000-8000-000000000102','00000000-0000-4000-8000-000000000022',
  'Synthetic card B1','Synthetic situation','["synthetic"]'::jsonb,array['fixture'],
  '2026-02-01T00:00:00Z','2026-02-02T00:00:00Z'),
 ('10000000-0000-4000-8000-000000000103','00000000-0000-4000-8000-000000000022',
  'Synthetic card B2','Synthetic situation','["synthetic"]'::jsonb,array['fixture'],
  '2026-02-01T00:00:00Z','2026-02-02T00:00:00Z'),
 ('10000000-0000-4000-8000-000000000104','00000000-0000-4000-8000-000000000022',
  'Synthetic card B3','Synthetic situation','["synthetic"]'::jsonb,array['fixture'],
  '2026-02-01T00:00:00Z','2026-02-02T00:00:00Z');

insert into staged_feedback (id,user_id,provider,recommendation,created_at) values
 ('20000000-0000-4000-8000-000000000201','00000000-0000-4000-8000-000000000022','synthetic','fixture','2026-03-01T00:00:00Z'),
 ('20000000-0000-4000-8000-000000000202','00000000-0000-4000-8000-000000000022','synthetic','fixture','2026-03-02T00:00:00Z'),
 ('20000000-0000-4000-8000-000000000203','00000000-0000-4000-8000-000000000022','synthetic','fixture','2026-03-03T00:00:00Z');

-- Fail closed on any unmapped or missing-account owner and duplicate target ID.
do $preflight$
begin
 if exists(select 1 from staged_evidence s
  left join private_owner_map m on m.old_user_id=s.user_id
  left join auth.users a on a.id=m.new_user_id where m.new_user_id is null or a.id is null)
 or exists(select 1 from staged_feedback s
  left join private_owner_map m on m.old_user_id=s.user_id
  left join auth.users a on a.id=m.new_user_id where m.new_user_id is null or a.id is null)
 then raise exception 'Unmapped or unverified target account'; end if;
 if exists(select 1 from staged_evidence s join public.evidence_cards t on t.id=s.id)
 or exists(select 1 from staged_feedback s join public.pilot_feedback t on t.id=s.id)
 then raise exception 'A target record ID already exists'; end if;
end
$preflight$;

-- Explicit field allowlist; preserve source IDs, content and timestamps.
insert into public.evidence_cards
 (id,user_id,title,situation,task,actions,outcome,reflection,
  tags,behaviours,skills,authority_context,source,confidence,created_at,updated_at)
select s.id,m.new_user_id,s.title,s.situation,s.task,s.actions,s.outcome,s.reflection,
       s.tags,s.behaviours,s.skills,s.authority_context,s.source,s.confidence,
       s.created_at,s.updated_at
from staged_evidence s join private_owner_map m on m.old_user_id=s.user_id;

insert into public.pilot_feedback
 (id,user_id,provider,recommendation,application_type,word_count,usefulness,
  would_submit,recommendation_trust,material_time_saving,would_use_again,
  payment_signal,created_at)
select s.id,m.new_user_id,s.provider,s.recommendation,s.application_type,s.word_count,
       s.usefulness,s.would_submit,s.recommendation_trust,s.material_time_saving,
       s.would_use_again,s.payment_signal,s.created_at
from staged_feedback s join private_owner_map m on m.old_user_id=s.user_id;

do $verify$
begin
 if (select count(*) from public.evidence_cards) <> 4
   or (select count(*) from public.pilot_feedback) <> 3
 then raise exception 'Unexpected total count'; end if;
 if (select count(*) from public.evidence_cards where user_id='00000000-0000-4000-8000-000000000031') <> 1
   or (select count(*) from public.evidence_cards where user_id='00000000-0000-4000-8000-000000000032') <> 3
   or (select count(*) from public.pilot_feedback where user_id='00000000-0000-4000-8000-000000000032') <> 3
 then raise exception 'Incorrect remapped ownership'; end if;
 if (select count(*) from staged_evidence s join private_owner_map m on m.old_user_id=s.user_id
     join public.evidence_cards d on d.id=s.id
     where d.user_id=m.new_user_id and d.title is not distinct from s.title
       and d.situation is not distinct from s.situation
       and d.actions is not distinct from s.actions
       and d.tags is not distinct from s.tags
       and d.created_at=s.created_at and d.updated_at=s.updated_at) <> 4
 then raise exception 'Evidence content or timestamps changed'; end if;
 if (select count(*) from staged_feedback s join private_owner_map m on m.old_user_id=s.user_id
     join public.pilot_feedback d on d.id=s.id
     where d.user_id=m.new_user_id and d.provider is not distinct from s.provider
     and d.recommendation is not distinct from s.recommendation
     and d.created_at=s.created_at) <> 3
 then raise exception 'Feedback content or timestamps changed'; end if;
end
$verify$;
commit;
