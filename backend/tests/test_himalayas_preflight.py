import json
import unittest

import httpx

from scripts.probe_himalayas import probe, summarize


def job(**changes):
    return {
        "guid": "synthetic-job",
        "title": "Synthetic developer",
        "companyName": "Example employer",
        "applicationLink": "https://example.com/apply?ref=original",
        "expiryDate": 200,
        **changes,
    }


class HimalayasPreflightTests(unittest.TestCase):
    def test_counts_without_exposing_advert(self):
        result = summarize({"jobs": [job(), job(guid="closed", expiryDate=100)]}, 100)
        self.assertEqual(result["unexpired_on_page"], 1)
        self.assertEqual(result["expired_on_page"], 1)
        self.assertFalse(result["applied"])
        self.assertFalse(result["missing_job_expiry"])
        self.assertNotIn("Synthetic developer", json.dumps(result))

    def test_bad_records_fail_closed(self):
        for jobs in ([job(), job()], [job(expiryDate=True)],
                     [job(applicationLink="javascript:alert(1)")],
                     [job(applicationLink="https://user:pass@example.com/apply")],
                     [job(applicationLink="https://example.com:444/apply")],
                     [job(guid="")], [job()] * 21):
            with self.subTest(jobs=jobs), self.assertRaises(ValueError):
                summarize({"jobs": jobs}, 100)

    def test_empty_page_is_not_complete_snapshot(self):
        result = summarize({"jobs": []}, 100)
        self.assertEqual(result["records"], 0)
        self.assertEqual(result["scope"], "one_page_only")
        self.assertFalse(result["missing_job_expiry"])

    def test_fixed_endpoint_and_no_redirect(self):
        def respond(request):
            self.assertEqual(request.url.host, "himalayas.app")
            self.assertEqual(request.url.path, "/jobs/api/search")
            self.assertEqual(dict(request.url.params), {"country": "GB", "page": "1"})
            return httpx.Response(200, json={"jobs": [job()]})
        with httpx.Client(transport=httpx.MockTransport(respond)) as client:
            self.assertEqual(probe(client, 100)["records"], 1)
        with httpx.Client(follow_redirects=True, transport=httpx.MockTransport(
            lambda request: httpx.Response(302, headers={"Location": "https://example.com"})
        )) as client:
            with self.assertRaises(httpx.HTTPStatusError):
                probe(client, 100)

    def test_rate_limit_is_not_empty_page(self):
        with httpx.Client(transport=httpx.MockTransport(
            lambda request: httpx.Response(429)
        )) as client:
            with self.assertRaises(httpx.HTTPStatusError):
                probe(client, 100)

    def test_oversize_response_rejected(self):
        with httpx.Client(transport=httpx.MockTransport(
            lambda request: httpx.Response(200, content=b"x" * 1_500_001)
        )) as client:
            with self.assertRaises(ValueError):
                probe(client, 100)
