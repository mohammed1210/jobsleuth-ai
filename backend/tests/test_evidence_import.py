import sys
from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend.main import app
from routes import evidence_bank
from routes.evidence_bank import EvidenceImportDraft

client = TestClient(app)
HEADERS = {"Authorization": "Bearer valid_token"}


def test_import_application_documents_returns_review_drafts_without_saving(monkeypatch):
    captured = {}

    def fake_extract(documents):
        captured["documents"] = documents
        return [
            EvidenceImportDraft(
                source_filename="statement-one.txt",
                title="Multi-agency operational response",
                situation="A live operational issue required coordination.",
                task="I was responsible for gathering information and updating colleagues.",
                actions=["I contacted partner agencies and communicated changes as they developed."],
                outcome="The operation continued safely.",
                reflection="I would establish a named liaison earlier next time.",
                skills=["communication", "stakeholder management"],
                source="imported_application",
                confidence=55,
            ),
            EvidenceImportDraft(
                source_filename="statement-two.txt",
                title="Decision under pressure",
                actions=["I assessed the available information and made a measured recommendation."],
                skills=["decision making"],
                source="imported_application",
                confidence=55,
            ),
        ]

    monkeypatch.setattr(evidence_bank, "_openai_import_evidence", fake_extract)

    response = client.post(
        "/evidence/import-documents",
        headers=HEADERS,
        files=[
            ("files", ("statement-one.txt", b"A" * 120, "text/plain")),
            ("files", ("statement-two.txt", b"B" * 120, "text/plain")),
        ],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["files_processed"] == 2
    assert body["provider"] == "openai"
    assert len(body["drafts"]) == 2
    assert body["drafts"][0]["source"] == "imported_application"
    assert body["drafts"][0]["source_filename"] == "statement-one.txt"
    assert len(captured["documents"]) == 2


def test_import_application_documents_rejects_unsupported_format():
    response = client.post(
        "/evidence/import-documents",
        headers=HEADERS,
        files=[("files", ("statement.rtf", b"example application text" * 10, "application/rtf"))],
    )

    assert response.status_code == 415
    assert "pdf, docx or txt" in response.json()["detail"].lower()


def test_import_application_documents_uses_grounded_fallback(monkeypatch):
    monkeypatch.setattr(evidence_bank, "_openai_import_evidence", lambda documents: None)

    paragraph = (
        "During a difficult operational incident I gathered information from colleagues, "
        "communicated updates to partner agencies and recorded the agreed next steps. "
        "The issue was resolved safely and I reviewed the process afterwards."
    )

    response = client.post(
        "/evidence/import-documents",
        headers=HEADERS,
        files=[("files", ("old-statement.txt", (paragraph + "\n\n" + paragraph).encode(), "text/plain"))],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "fallback"
    assert body["drafts"]
    assert body["drafts"][0]["source_filename"] == "old-statement.txt"
    assert paragraph[:80] in body["drafts"][0]["actions"][0]


def test_import_application_documents_limits_batch_size():
    files = [
        ("files", (f"statement-{index}.txt", b"Enough readable application text. " * 6, "text/plain"))
        for index in range(9)
    ]

    response = client.post("/evidence/import-documents", headers=HEADERS, files=files)

    assert response.status_code == 400
    assert "up to 8 files" in response.json()["detail"].lower()


def test_openai_import_processes_each_long_file_without_tail_truncation(monkeypatch):
    calls = []

    class FakeCompletions:
        def create(self, **kwargs):
            content = kwargs["messages"][1]["content"]
            calls.append(content)
            filename = "first.txt" if "first.txt" in content else "second.txt"
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content=(
                                '{"examples":[{"source_filename":"'
                                + filename
                                + '","title":"Example from '
                                + filename
                                + '","actions":["Grounded action from '
                                + filename
                                + '"]}]}'
                            )
                        )
                    )
                ]
            )

    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    monkeypatch.setattr(evidence_bank.settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=lambda api_key: fake_client))

    drafts = evidence_bank._openai_import_evidence(
        [
            ("first.txt", "A" * 50000),
            ("second.txt", "B" * 50000),
        ]
    )

    assert drafts is not None
    assert {draft.source_filename for draft in drafts} == {"first.txt", "second.txt"}
    assert len(calls) == 2
    assert "second.txt" in calls[1]
