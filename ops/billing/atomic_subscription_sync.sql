-- REVIEW CANDIDATE ONLY. Do not run against production without explicit approval.
-- Convert to a tracked Supabase migration after isolated PostgreSQL verification.
-- Existing duplicates or null owners deliberately abort; no data is deleted.
begin;
alter table public.subscriptions alter column user_id set not null;
alter table public.subscriptions add column billing_revision bigint not null default 0;
alter table public.subscriptions add column stripe_subscription_created bigint;
alter table public.subscriptions add constraint subscriptions_one_per_user unique (user_id);

create function public.billing_sync_subscription(
    p_user_id uuid, p_customer text, p_subscription text,
    p_subscription_created bigint, p_plan text, p_status text,
    p_expected_revision bigint
) returns text
language plpgsql
security invoker
set search_path = ''
as $$
declare
    current_row public.subscriptions%rowtype;
    safe_plan text;
begin
    if p_user_id is null or p_customer is null or p_customer = ''
       or p_subscription is null or p_subscription = ''
       or p_subscription_created is null or p_subscription_created <= 0
       or p_status is null or p_plan is null
       or p_plan not in ('free', 'career_plus', 'pro') then
        raise exception 'Invalid subscription synchronization parameters';
    end if;
    safe_plan := case when p_status in ('active', 'trialing') then p_plan else 'free' end;
    -- Serialize both the first insert and updates for the same user, including
    -- separate workers/replicas. A hash collision only serializes extra users.
    perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(p_user_id::text, 0));
    select * into current_row from public.subscriptions
        where user_id = p_user_id for update;
    if not found then
        if p_expected_revision is not null then return 'retry'; end if;
        insert into public.subscriptions
            (user_id, stripe_customer_id, stripe_subscription_id, stripe_subscription_created,
             plan, status, billing_revision, updated_at)
        values (p_user_id, p_customer, p_subscription, p_subscription_created,
                safe_plan, p_status, 1, pg_catalog.clock_timestamp());
        return 'applied';
    end if;
    if current_row.billing_revision is distinct from p_expected_revision then
        return 'retry';
    end if;
    if current_row.stripe_customer_id is not null and current_row.stripe_customer_id <> p_customer then
        raise exception 'Subscription customer ownership conflict';
    end if;
    if current_row.stripe_subscription_id = p_subscription then
        if current_row.stripe_subscription_created is not null
           and current_row.stripe_subscription_created <> p_subscription_created then
            raise exception 'Subscription creation timestamp mismatch';
        end if;
        if current_row.status = 'canceled' and p_status <> 'canceled' then
            return 'ignored';
        end if;
    elsif current_row.stripe_subscription_id is not null then
        -- Never guess which subscription wins if the legacy row is unversioned
        -- or both subscriptions were created within the same Stripe second.
        if current_row.stripe_subscription_created is null
           or current_row.stripe_subscription_created = p_subscription_created then
            raise exception 'Ambiguous subscription replacement requires reconciliation';
        end if;
        if current_row.stripe_subscription_created > p_subscription_created then
            return 'ignored';
        end if;
    end if;
    update public.subscriptions set
        stripe_customer_id = p_customer,
        stripe_subscription_id = p_subscription,
        stripe_subscription_created = p_subscription_created,
        plan = safe_plan, status = p_status,
        billing_revision = current_row.billing_revision + 1,
        updated_at = pg_catalog.clock_timestamp()
    where id = current_row.id;
    return 'applied';
end;
$$;
revoke all on function public.billing_sync_subscription(uuid,text,text,bigint,text,text,bigint)
    from public, anon, authenticated;
grant execute on function public.billing_sync_subscription(uuid,text,text,bigint,text,text,bigint)
    to service_role;
commit;
