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
