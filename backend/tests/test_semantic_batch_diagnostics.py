"""Diagnostics must explain fallback without leaking applicant or provider data."""
import json
import logging
from types import SimpleNamespace

import openai
import pytest

from lib import evidence_semantic_batch as batch


@pytest.fixture
def entries(monkeypatch):
    monkeypatch.setattr(batch.settings, "OPENAI_API_KEY", "synthetic-secret-key")
    card = SimpleNamespace(id="private-card-id", title="private applicant text",
                           actions=["I checked records."], outcome="Records corrected.")
    return [(0, "private requirement", [card])]


def _mock_provider(monkeypatch, *, response=None, error=None):
    def create(**kwargs):
        if error is not None:
            raise error
        return response
    monkeypatch.setattr(openai, "OpenAI", lambda **kwargs: SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))))


@pytest.mark.parametrize("status,code,expected", [
    (401, None, "authentication_failed"),
    (429, "insufficient_quota", "quota_exhausted"),
    (429, "rate_limit_exceeded", "rate_limited"),
    (503, None, "provider_unavailable"),
])
def test_provider_failure_is_redacted(monkeypatch, caplog, entries, status, code, expected):
    error = RuntimeError("private applicant text synthetic-secret-key")
    error.status_code = status
    error.code = code
    _mock_provider(monkeypatch, error=error)
    assert batch.semantic_assess_batch(entries) is None
    assert f"status={expected}" in caplog.text
    for private in ("private applicant text", "synthetic-secret-key", "private requirement", "private-card-id"):
        assert private not in caplog.text


def test_truncated_output_is_explicit(monkeypatch, caplog, entries):
    _mock_provider(monkeypatch, response=SimpleNamespace(choices=[
        SimpleNamespace(finish_reason="length", message=SimpleNamespace(content="{"))
    ]))
    assert batch.semantic_assess_batch(entries) is None
    assert "status=truncated_response" in caplog.text


def test_valid_grounded_response_reports_success(monkeypatch, caplog, entries):
    caplog.set_level(logging.INFO, logger=batch.__name__)
    payload = {"assessments": [{"requirement_id": "0", "matches": [{
        "evidence_id": "private-card-id", "strength": "strong", "score": 85,
        "confidence": 0.9, "why": "Checked records", "gaps": [],
        "supporting_facts": [{"field": "actions", "text": "I checked records."}]
    }]}]}
    _mock_provider(monkeypatch, response=SimpleNamespace(choices=[
        SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content=json.dumps(payload)))
    ]))
    assert batch.semantic_assess_batch(entries)[0]["private-card-id"]["strength"] == "strong"
    assert "status=success requested=1 validated=1" in caplog.text
    assert "private-card-id" not in caplog.text


def test_missing_configuration_reports_reason(monkeypatch, caplog, entries):
    monkeypatch.setattr(batch.settings, "OPENAI_API_KEY", None)
    assert batch.semantic_assess_batch(entries) is None
    assert "status=not_configured" in caplog.text


def test_shared_card_catalog_preserves_candidate_scope_and_reduces_payload(monkeypatch, caplog, entries):
    first = entries[0][2][0]
    second = SimpleNamespace(id="other-card", title="Other", actions=["I arranged cover."])
    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        def match(card, action):
            return {"evidence_id": card, "strength": "partial", "score": 60,
                    "confidence": 0.8, "why": "Related", "gaps": [],
                    "supporting_facts": [{"field": "actions", "text": action}]}
        payload = {"assessments": [
            {"requirement_id": "0", "matches": [
                match(first.id, "I checked records."),
                match(second.id, "I arranged cover.")]},
            {"requirement_id": "1", "matches": [
                match(first.id, "I checked records."),
                match(second.id, "I invented an outcome.")]}]}
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop",
            message=SimpleNamespace(content=json.dumps(payload)))],
            usage=SimpleNamespace(prompt_tokens=100, completion_tokens=80))

    monkeypatch.setattr(openai, "OpenAI", lambda **kwargs: SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    caplog.set_level(logging.INFO, logger=batch.__name__)
    result = batch.semantic_assess_batch(entries + [(1, "another requirement", [first, second])])
    assert len(calls) == 1
    payload = json.loads(calls[0]["messages"][1]["content"])
    assert [card["id"] for card in payload["evidence_cards"]] == [first.id, second.id]
    assert payload["requirements"][0]["evidence_ids"] == [first.id]
    assert payload["requirements"][1]["evidence_ids"] == [first.id, second.id]
    assert all("evidence_cards" not in item for item in payload["requirements"])
    assert set(result[0]) == {first.id}
    assert set(result[1]) == {first.id}
    assert "unique_cards=2 candidate_pairs=3 input_tokens=100 output_tokens=80" in caplog.text
    assert first.id not in caplog.text
    assert "private applicant text" not in caplog.text
