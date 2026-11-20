-- Synthetic disposable PostgreSQL integration fixture. Never use live data.
set role service_role;
do $$
declare
    u uuid := '00000000-0000-4000-8000-000000000001';
    ans text;
begin
    if has_function_privilege('anon', 'public.billing_sync_subscription(uuid,text,text,bigint,text,text,bigint)', 'EXECUTE')
       or has_function_privilege('authenticated', 'public.billing_sync_subscription(uuid,text,text,bigint,text,text,bigint)', 'EXECUTE')
       or not has_function_privilege('service_role', 'public.billing_sync_subscription(uuid,text,text,bigint,text,text,bigint)', 'EXECUTE') then
        raise exception 'Unexpected RPC permissions';
    end if;
    ans := public.billing_sync_subscription(u,'cus_one','sub_one',100,'pro','active',null);
    if ans <> 'applied' then raise exception 'First insert failed'; end if;
    ans := public.billing_sync_subscription(u,'cus_one','sub_one',100,'pro','active',null);
    if ans <> 'retry' then raise exception 'Concurrent insert not rejected'; end if;
    ans := public.billing_sync_subscription(u,'cus_one','sub_one',100,'pro','canceled',1);
    if ans <> 'applied' then raise exception 'Cancellation failed'; end if;
    ans := public.billing_sync_subscription(u,'cus_one','sub_one',100,'pro','active',1);
    if ans <> 'retry' then raise exception 'Stale revision not rejected'; end if;
    ans := public.billing_sync_subscription(u,'cus_one','sub_one',100,'pro','active',2);
    if ans <> 'ignored' then raise exception 'Canceled subscription resurrected'; end if;
    ans := public.billing_sync_subscription(u,'cus_one','sub_two',200,'career_plus','active',2);
    if ans <> 'applied' then raise exception 'Replacement failed'; end if;
    ans := public.billing_sync_subscription(u,'cus_one','sub_one',100,'free','canceled',3);
    if ans <> 'ignored' then raise exception 'Old cancellation revoked replacement'; end if;
    ans := public.billing_sync_subscription(u,'cus_one','sub_one',100,'pro','active',3);
    if ans <> 'ignored' then raise exception 'Older active subscription replaced new one'; end if;
    begin
        perform public.billing_sync_subscription(u,'cus_other','sub_three',300,'pro','active',3);
        raise exception 'Expected ownership rejection' using errcode='ZX001';
    exception when sqlstate 'P0001' then null;
    end;
    begin
        perform public.billing_sync_subscription(u,'cus_one','sub_three',200,'pro','active',3);
        raise exception 'Expected ambiguous replacement rejection' using errcode='ZX001';
    exception when sqlstate 'P0001' then null;
    end;
    if not exists (select 1 from public.subscriptions where user_id=u and plan='career_plus'
        and stripe_subscription_id='sub_two' and billing_revision=3) then
        raise exception 'Unexpected final entitlement';
    end if;
    if (select count(*) from public.subscriptions where user_id=u) <> 1 then
        raise exception 'Duplicate records';
    end if;
end $$;

reset role;
