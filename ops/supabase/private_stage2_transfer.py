#!/usr/bin/env python3
"""Private operator-only JobSleuth transfer; never run in CI or against PropNexus.
Dry run by default. Requires existing verified target Supabase Auth account.
"""
import argparse
import os
from urllib.parse import urlsplit, unquote

SOURCE_REF = "wsfemkhxttddztnhthkc"
TARGET_REF = "uqvhnqhbushhtkthwrhk"
EXPECTED = {"evidence_cards": 4, "pilot_feedback": 3}
FIELDS = {
    "evidence_cards": ("id", "user_id", "title", "situation", "task", "actions",
        "outcome", "reflection", "tags", "behaviours", "skills", "authority_context",
        "source", "confidence", "created_at", "updated_at"),
    "pilot_feedback": ("id", "user_id", "provider", "recommendation",
        "application_type", "word_count", "usefulness", "would_submit",
        "recommendation_trust", "material_time_saving", "would_use_again",
        "payment_signal", "created_at"),
}
ACK = "CONFIRM_4_EVIDENCE_3_FEEDBACK"


def ensure_project(url, ref):
    u = urlsplit(url)
    if u.scheme not in ("postgresql", "postgres") or not u.password:
        raise ValueError("Use a password-protected Supabase PostgreSQL connection URL")
    # libpq permits query-string host, hostaddr, user and service overrides.
    # Forbid ALL connection URL options so the effective destination cannot
    # differ from the URL's verified hostname/project ID.
    if u.query or u.fragment:
        raise ValueError("Connection URL query/fragment overrides are forbidden")
    if u.path != "/postgres" or u.port not in (None, 5432, 6543):
        raise ValueError("Expected the standard Supabase postgres database/port")
    if any(os.environ.get(name) for name in (
        "PGHOSTADDR", "PGHOST", "PGSERVICE", "PGSERVICEFILE", "PGUSER",
        "PGDATABASE", "PGPORT", "PGOPTIONS",
    )):
        raise ValueError("Remove inherited libpq PG* connection-routing variables")
    # libpq accepts comma-delimited failover hosts and percent-encoded socket
    # directory paths. Both can bypass a naive pooler suffix check.
    hostname = u.hostname or ""
    if unquote(hostname) != hostname or any(
        c not in "abcdefghijklmnopqrstuvwxyz0123456789.-" for c in hostname
    ) or hostname.startswith(".") or ".." in hostname:
        raise ValueError("Reject encoded, socket, multi-host or invalid database hosts")
    direct = hostname == "db." + ref + ".supabase.co"
    if direct and unquote(u.username or "") != "postgres":
        raise ValueError("Unexpected direct-database user")
    pooler = (hostname.endswith(".pooler.supabase.com")
              and hostname.startswith("aws-")
              and hostname.count(".") == 3
              and unquote(
        u.username or "") == "postgres." + ref)
    if not (direct or pooler):
        raise ValueError("Database project reference does not match approved source/target")


def emails_from_env(value):
    emails = [v.strip().lower() for v in value.split(",") if v.strip()]
    if len(emails) != 2 or len(set(emails)) != 2 or any("@" not in x for x in emails):
        raise ValueError("Provide exactly two distinct source account emails")
    return emails


def same_except_owner(a, b):
    return {k: v for k, v in a.items() if k != "user_id"} == {
        k: v for k, v in b.items() if k != "user_id"}


def accounts(db, emails):
    rows = db.execute(
        "select id,lower(email) as email,email_confirmed_at is not null as verified "
        "from auth.users where lower(email)=any(%s)", (emails,)).fetchall()
    if len(rows) != len(emails) or set(r["email"] for r in rows) != set(emails):
        raise ValueError("Selected Auth accounts not uniquely identified")
    if not all(r["verified"] for r in rows):
        raise ValueError("Selected Auth email not yet verified")
    return rows


def preflight(db, source=False, owners=None):
    data = {}
    for table, cols in FIELDS.items():
        column_sql = ", ".join(cols)  # fixed allowlist
        if source:
            rows = db.execute(
                f"select {column_sql} from public.{table} where user_id=any(%s) order by id",
                (owners,)).fetchall()
        else:
            rows = []
        total = db.execute(f"select count(*) as n from public.{table}").fetchone()["n"]
        if source:
            if total != EXPECTED[table] or len(rows) != EXPECTED[table]:
                raise ValueError("Source total changed or an owner was missed")
        elif total != 0:
            raise ValueError("Destination already has records; never overwrite")
        data[table] = rows
    return data


def migrate(dst, dataset, new_user_id, Jsonb):
    for table, records in dataset.items():
        columns = FIELDS[table]
        insert = (f"insert into public.{table} ({', '.join(columns)}) values "
                  f"({', '.join(['%s'] * len(columns))}) returning {', '.join(columns)}")
        for row in records:
            values = [new_user_id if col == "user_id" else
                      Jsonb(row[col]) if col == "actions" else row[col]
                      for col in columns]
            imported = dst.execute(insert, values).fetchone()
            if imported["user_id"] != new_user_id or not same_except_owner(row, imported):
                raise ValueError("Field/timestamp integrity check failed")
        n = dst.execute(f"select count(*) as n from public.{table}").fetchone()["n"]
        if n != EXPECTED[table]:
            raise ValueError("Post-import record count mismatch")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args()
    if args.commit and args.confirm != ACK:
        parser.error("Explicit --confirm " + ACK + " required")
    try:
        srcurl = os.environ["JOBSLEUTH_SOURCE_DB_URL"]
        dsturl = os.environ["JOBSLEUTH_TARGET_DB_URL"]
        source_emails = emails_from_env(os.environ["JOBSLEUTH_SOURCE_EMAILS"])
        dest_email = os.environ["JOBSLEUTH_DEST_EMAIL"].strip().lower()
        if "@" not in dest_email:
            raise ValueError("Missing valid target Auth email")
        ensure_project(srcurl, SOURCE_REF)
        ensure_project(dsturl, TARGET_REF)
    except (ValueError, KeyError) as err:
        parser.error(str(err))
    try:
        import psycopg
        from psycopg.rows import dict_row
        from psycopg.types.json import Jsonb
    except ImportError:
        parser.error("Install psycopg[binary] on the private operator machine")

    src = dst = None
    try:
        src = psycopg.connect(srcurl, autocommit=True, row_factory=dict_row,
                              sslmode="require", connect_timeout=10)
        dst = psycopg.connect(dsturl, autocommit=True, row_factory=dict_row,
                              sslmode="require", connect_timeout=10)
        src.execute("begin isolation level repeatable read read only")
        dst.execute("begin isolation level serializable read write" if args.commit
                    else "begin isolation level repeatable read read only")
        if args.commit:
            dst.execute("lock table public.evidence_cards,public.pilot_feedback "
                        "in share row exclusive mode")
        old = accounts(src, source_emails)
        new = accounts(dst, [dest_email])[0]
        if dst.execute("select count(*) as n from auth.users").fetchone()["n"] != 1:
            raise ValueError("Destination must contain exactly one Auth account")
        if dst.execute("select count(*) as n from public.subscriptions").fetchone()["n"]:
            raise ValueError("Destination contains billing data")
        preflight(dst)
        dataset = preflight(src, source=True, owners=[u["id"] for u in old])
        print("Verified: 2 old owners, 1 new owner, 4 evidence cards and 3 feedback rows.")
        if args.commit:
            migrate(dst, dataset, new["id"], Jsonb)
            dst.execute("commit")
            print("Transfer committed. Original source records remain untouched.")
        else:
            dst.execute("rollback")
            print("Dry run: no records were changed.")
        src.execute("rollback")
    except Exception as exc:
        if dst is not None:
            try:
                dst.execute("rollback")
            except Exception:
                pass
        print("Transfer stopped (" + type(exc).__name__ + "). No automatic retry.")
        raise SystemExit(1) from None
    finally:
        if src is not None:
            src.close()
        if dst is not None:
            dst.close()


if __name__ == "__main__":
    main()
