"""Read-only DfE API first-page check, no database access, no applicant data.

A one-off probe validates whether the official published JSON endpoint serves
the documented fields to the JobSleuth origin. Never prints vacancy text.
"""
import argparse
from datetime import datetime, timezone

import httpx

from lib.dfe_ingestion import FeedError, _page, fetch_all
from lib.dfe_backfill import fetch_one


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", action="store_true",
                        help="Check the entire official DfE feed without writing any data")
    parser.add_argument("--individual", action="store_true",
                        help="Read-only check of one DfE publisher detail record")
    args = parser.parse_args()
    try:
        now = datetime.now(timezone.utc)
        with httpx.Client(
            follow_redirects=False, trust_env=False,
            headers={"User-Agent": "JobSleuth-SourceContractCheck/1.0"},
            timeout=15,
        ) as client:
            if args.individual:
                rows, _, _ = _page(client, 1, now)
                detail = fetch_one(client, rows[0]["external_id"], now)
                if detail is None:
                    raise FeedError("Selected DfE detail endpoint not available")
                print(f"DfE per-vacancy JSON passed: publisher ID verified, "
                      f"salary provided={bool(detail['salary'])}, "
                      f"description length={len(detail['description'] or '')}. NO DATA WRITTEN.")
            elif args.full:
                rows = fetch_all(client, now)
                print(f"DfE FULL live feed validated: unique jobs={len(rows)}. NO DATA WRITTEN.")
            else:
                rows, pages, count = _page(client, 1, now)
                print(f"DfE live JSON contract passed: first-page rows={len(rows)}; "
                      f"total pages={pages}; published records={count}. NO DATA WRITTEN.")
    except (FeedError, httpx.HTTPError, ValueError) as exc:
        # Diagnostic category only: do not expose source rows, URL query
        # strings, upstream response bodies, tokens or applicant content.
        status = (
            exc.response.status_code
            if isinstance(exc, httpx.HTTPStatusError) else None
        )
        reason = str(exc) if isinstance(exc, FeedError) else type(exc).__name__
        print(f"DfE API probe failed: {reason}; HTTP status={status}. NO DATA WRITTEN.")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
