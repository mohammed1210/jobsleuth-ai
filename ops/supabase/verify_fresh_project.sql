-- Execute only in a disposable PostgreSQL fixture, never against customers.
do $checks$
declare
  r record;
begin
  for r in
    select relname, relrowsecurity
    from pg_catalog.pg_class c
    join pg_catalog.pg_namespace n on n.oid=c.relnamespace
    where n.nspname='public'
      and relname in ('jobs','user_profiles','saved_jobs','subscriptions','evidence_cards','pilot_feedback')
      and relkind='r'
  loop
    if not r.relrowsecurity then
      raise exception 'RLS missing on %', r.relname;
    end if;
  end loop;
  if (select count(*) from pg_catalog.pg_class c join pg_catalog.pg_namespace n on n.oid=c.relnamespace
      where n.nspname='public' and c.relkind='r'
      and c.relname in ('jobs','user_profiles','saved_jobs','subscriptions','evidence_cards','pilot_feedback')) <> 6 then
    raise exception 'Missing application tables';
  end if;
  if has_table_privilege('anon','public.subscriptions','select')
     or has_table_privilege('anon','public.evidence_cards','select')
     or has_table_privilege('authenticated','public.subscriptions','insert') then
    raise exception 'Unexpected public billing/evidence table grants';
  end if;
  if not has_table_privilege('authenticated','public.evidence_cards','insert')
     or not has_table_privilege('service_role','public.subscriptions','update') then
    raise exception 'Expected application privileges missing';
  end if;
  if to_regprocedure('public.rls_auto_enable()') is not null then
    if has_function_privilege('anon','public.rls_auto_enable()','execute')
       or has_function_privilege('authenticated','public.rls_auto_enable()','execute') then
      raise exception 'Public rls_auto_enable execution remains enabled';
    end if;
  end if;
end
$checks$;
