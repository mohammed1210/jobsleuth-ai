"""Read-only DfE API first-page check, no database access, no applicant data.

A one-off probe validates whether the official published JSON endpoint serves
the documented fields to the JobSleuth origin. Never prints vacancy text.
"""
from datetime import datetime, timezone

import httpx

from lib.dfe_ingestion import FeedError, _page


def main():
    try:
        now = datetime.now(timezone.utc)
        with httpx.Client(
            follow_redirects=False, trust_env=False,
            headers={"User-Agent": "JobSleuth-SourceContractCheck/1.0"},
            timeout=15,
        ) as client:
            rows, pages, count = _page(client, 1, now)
        print(f"DfE live JSON contract passed: first-page rows={len(rows)}; "
              f"total pages={pages}; published records={count}. NO DATA WRITTEN.")
    except (FeedError, httpx.HTTPError, ValueError):
        print("DfE live JSON contract could not be verified. NO DATA WRITTEN.")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
