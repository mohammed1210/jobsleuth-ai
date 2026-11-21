"""Offline only: private transfer checks; no network, accounts or credentials."""
import importlib.util
import unittest
from pathlib import Path
path = Path(__file__).with_name("private_stage2_transfer.py")
spec = importlib.util.spec_from_file_location("private_stage2_transfer", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class TransferGuards(unittest.TestCase):
    def test_project_separation(self):
        old = "postgresql://postgres:TEST@db.wsfemkhxttddztnhthkc.supabase.co/postgres"
        new = "postgresql://postgres:TEST@db.uqvhnqhbushhtkthwrhk.supabase.co/postgres"
        m.ensure_project(old, m.SOURCE_REF)
        m.ensure_project(new, m.TARGET_REF)
        with self.assertRaises(ValueError):
            m.ensure_project(old, m.TARGET_REF)
        with self.assertRaises(ValueError):
            m.ensure_project(new, m.SOURCE_REF)

    def test_pooler_project_ownership(self):
        new = "postgresql://postgres.uqvhnqhbushhtkthwrhk:TEST@aws-0-eu-west-1.pooler.supabase.com/postgres"
        m.ensure_project(new, m.TARGET_REF)
        with self.assertRaises(ValueError):
            m.ensure_project(new, m.SOURCE_REF)

    def test_connection_override_attempts_are_rejected(self):
        base = "postgresql://postgres:TEST@db.uqvhnqhbushhtkthwrhk.supabase.co/postgres"
        for suffix in (
            "?host=db.wsfemkhxttddztnhthkc.supabase.co",
            "?hostaddr=127.0.0.1",
            "?user=postgres.wsfemkhxttddztnhthkc",
            "?service=other",
            "#host=db.wsfemkhxttddztnhthkc.supabase.co",
        ):
            with self.subTest(suffix=suffix):
                with self.assertRaises(ValueError):
                    m.ensure_project(base + suffix, m.TARGET_REF)

    def test_environment_connection_routing_is_rejected(self):
        from unittest.mock import patch
        base = "postgresql://postgres:TEST@db.uqvhnqhbushhtkthwrhk.supabase.co/postgres"
        for name in ("PGHOSTADDR", "PGSERVICE", "PGHOST", "PGUSER"):
            with self.subTest(name=name), patch.dict(m.os.environ, {name: "unexpected"}):
                with self.assertRaises(ValueError):
                    m.ensure_project(base, m.TARGET_REF)

    def test_nonstandard_db_and_user_are_rejected(self):
        with self.assertRaises(ValueError):
            m.ensure_project(
                "postgresql://postgres:TEST@db.uqvhnqhbushhtkthwrhk.supabase.co/other",
                m.TARGET_REF,
            )
        with self.assertRaises(ValueError):
            m.ensure_project(
                "postgresql://unexpected:TEST@db.uqvhnqhbushhtkthwrhk.supabase.co/postgres",
                m.TARGET_REF,
            )

    def test_multi_host_and_socket_paths_are_rejected(self):
        attacks = (
            "postgresql://postgres.uqvhnqhbushhtkthwrhk:TEST@"
            "attacker.example,aws-0-eu-west-2.pooler.supabase.com/postgres",
            "postgresql://postgres.uqvhnqhbushhtkthwrhk:TEST@"
            "%2Ftmp%2Ffake.pooler.supabase.com/postgres",
            "postgresql://postgres.uqvhnqhbushhtkthwrhk:TEST@"
            "aws-0-eu-west-2.pooler.supabase.com%2Ftmp/postgres",
            "postgresql://postgres.uqvhnqhbushhtkthwrhk:TEST@"
            "fake.evil.pooler.supabase.com/postgres",
        )
        for value in attacks:
            with self.subTest(value=value), self.assertRaises(ValueError):
                m.ensure_project(value, m.TARGET_REF)

    def test_owner_list(self):
        self.assertEqual(m.emails_from_env("A@example.com, B@example.com"),
                         ["a@example.com", "b@example.com"])
        for invalid in ("one@example.com", "a@example.com,a@example.com", "a,b,c"):
            with self.assertRaises(ValueError):
                m.emails_from_env(invalid)

    def test_full_field_integrity(self):
        row = {"id": "x", "user_id": "first", "task": "t",
               "actions": ["one", {"another": 1}], "created_at": "a"}
        self.assertTrue(m.same_except_owner(row, {**row, "user_id": "second"}))
        self.assertFalse(m.same_except_owner(row, {**row, "user_id": "second", "task": ""}))
        self.assertFalse(m.same_except_owner(row, {"id": "x", "user_id": "second"}))

    def test_expected_counts_and_fields(self):
        self.assertEqual(m.EXPECTED, {"evidence_cards": 4, "pilot_feedback": 3})
        self.assertEqual(len(m.FIELDS["evidence_cards"]), 16)
        self.assertEqual(len(m.FIELDS["pilot_feedback"]), 13)


if __name__ == "__main__":
    unittest.main()
