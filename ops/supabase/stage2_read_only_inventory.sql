-- READ ONLY / OLD SHARED PROJECT ONLY. No record content, email, UUID,
-- password or token is selected. Run interactively, not in GitHub Actions.
-- This is a point-in-time inventory, not a migration source or ownership proof.
with per_account as (
  select a.id,
         (select count(*) from public.evidence_cards e where e.user_id=a.id) as evidence_count,
         (select count(*) from public.pilot_feedback f where f.user_id=a.id) as feedback_count,
         (a.email_confirmed_at is not null) as email_confirmed,
         (a.last_sign_in_at is not null) as ever_signed_in
  from auth.users a
)
select 'account_' || row_number() over (order by id) as audit_alias,
       evidence_count,feedback_count,email_confirmed,ever_signed_in
from per_account order by audit_alias;

select
  (select count(*) from auth.users) as auth_accounts,
  (select count(*) from public.evidence_cards) as evidence_cards,
  (select count(distinct user_id) from public.evidence_cards) as evidence_owners,
  (select count(*) from public.pilot_feedback) as pilot_feedback,
  (select count(distinct user_id) from public.pilot_feedback) as feedback_owners,
  (select count(*) from public.evidence_cards e where not exists
      (select 1 from auth.users u where u.id=e.user_id)) as orphan_evidence,
  (select count(*) from public.pilot_feedback f where not exists
      (select 1 from auth.users u where u.id=f.user_id)) as orphan_feedback;
