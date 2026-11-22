"""CLI to preview employer vacancies; operator-only --apply, disabled by default.

From backend/:
  python -m scripts.ingest_greenhouse
  python -m scripts.ingest_greenhouse --apply
"""
import argparse
import json
import os
import httpx

from lib.greenhouse_ingestion import FeedError, parse_boards, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="Write to dedicated Supabase after explicit feed rights gate")
    args = parser.parse_args()
    try:
        boards = parse_boards(os.environ.get("JOBSLEUTH_GREENHOUSE_BOARDS", ""))
        # Never call an arbitrary user-provided URL; all board paths are
        # validated and pinned to boards-api.greenhouse.io.
        with httpx.Client(follow_redirects=False, trust_env=False,
                          headers={"User-Agent": "JobSleuth-FeedVerifier/1.0"}) as client:
            storage = None
            if args.apply:
                from lib.supabase import get_supabase_client
                storage = get_supabase_client()
            result = run(boards, apply=args.apply, client=client, storage=storage)
        print(json.dumps({"mode": "apply" if args.apply else "dry-run", "boards": result}))
    except (FeedError, httpx.HTTPError, ValueError) as exc:
        # Errors omit raw payload, private tokens and applicant content.
        print(f"Feed ingest halted: {type(exc).__name__}")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
