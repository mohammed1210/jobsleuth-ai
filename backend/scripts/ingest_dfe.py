"""Operator-run licensed DfE Teaching Vacancies import.

Dry run (default):
    cd backend && python -m scripts.ingest_dfe
Write mode must be explicitly unlocked after reviewed schema migration:
    cd backend && python -m scripts.ingest_dfe --apply
"""
from __future__ import annotations

import argparse
import json

import httpx

from lib.dfe_ingestion import FeedError, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Commit source postings to dedicated Supabase")
    parser.add_argument("--pilot", action="store_true",
                        help="Use only page one; upserts only, never deactivate missing jobs")
    args = parser.parse_args()
    try:
        with httpx.Client(follow_redirects=False, trust_env=False,
                          headers={"User-Agent": "JobSleuth-LicensedFeedVerifier/1.0"}) as client:
            storage = None
            if args.apply:
                from lib.supabase import get_supabase_client
                storage = get_supabase_client()
            output = run(client=client, apply=args.apply, storage=storage, pilot=args.pilot)
        # Print ONLY aggregate counts, never raw feed content/credentials.
        print(json.dumps(output, sort_keys=True))
    except (httpx.HTTPError, FeedError, ValueError):
        print("DfE feed halted safely; source/schema/rights controls not satisfied.")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
