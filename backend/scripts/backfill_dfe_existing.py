"""Manually enrich existing DfE vacancies with verified salaries/descriptions.

Read-only by default. Never inserts jobs or deactivates absent vacancies.
Requires dedicated JobSleuth backend secrets even for read-only comparison.
"""
from __future__ import annotations

import argparse
import json

import httpx

from lib.dfe_backfill import enrich_existing
from lib.dfe_ingestion import FeedError
from lib.supabase import get_supabase_client


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apply", action="store_true", help="Write reviewed enrichment to existing records")
    p.add_argument("--max-records", type=int, default=100, help="Bounded existing record count, max 100")
    args = p.parse_args()
    try:
        storage = get_supabase_client()
        with httpx.Client(follow_redirects=False, trust_env=False,
                          headers={"User-Agent": "JobSleuth-LicensedFeedVerifier/1.0"}) as client:
            result = enrich_existing(
                client=client, storage=storage, apply=args.apply, max_records=args.max_records
            )
        print(json.dumps(result, sort_keys=True))
    except (httpx.HTTPError, FeedError, ValueError):
        print("DfE existing-job enrichment halted safely; NO unverified data imported.")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
