from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from backend.main import app
from routes import candidate_profile
from routes.candidate_profile import CandidateExperience, CandidateProfileData
from routes.vacancy_analysis import _profile_support

client = TestClient(app)


class FakeResult:
    def __init__(self, data):
        self.data = data


class FakeTable:
    def __init__(self):
        self.rows = []
        self.operation = "select"
        self.payload = None
        self.filters = []

    def select(self, *args, **kwargs):
        self.operation = "select"
        self.filters = []
        return self

    def insert(self, payload):
        self.operation = "insert"
        self.payload = payload
        self.filters = []
        return self

    def update(self, payload):
        self.operation = "update"
        self.payload = payload
        self.filters = []
        return self

    def delete(self):
        self.operation = "delete"
        self.filters = []
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def _matches(self, row):
        return all(row.get(field) == value for field, value in self.filters)

    def execute(self):
        now = datetime.now(timezone.utc).isoformat()
        if self.operation == "insert":
            row = {"id": "cv-1", "created_at": now, "updated_at": now, **self.payload}
            self.rows.append(row)
            return FakeResult([dict(row)])
        if self.operation == "update":
            updated = []
            for row in self.rows:
                if self._matches(row):
                    row.update(self.payload)
                    updated.append(dict(row))
            return FakeResult(updated)
        if self.operation == "delete":
            removed = [dict(row) for row in self.rows if self._matches(row)]
            self.rows = [row for row in self.rows if not self._matches(row)]
            return FakeResult(removed)
        return FakeResult([dict(row) for row in self.rows if self._matches(row)])


class FakeClient:
    def __init__(self):
        self.evidence = FakeTable()

    def table(self, name):
        assert name == "evidence_cards"
        return self.evidence


def test_fallback_extracts_cv_sections(monkeypatch):
    monkeypatch.setattr(candidate_profile, "_openai_profile", lambda text: None)
    text = """
PROFILE
Operations professional with border, freight and stakeholder experience.

SKILLS
Stakeholder management
Risk assessment
Data analysis

EXPERIENCE
Border Force Officer
Reviewed freight movements and escalated operational risks.
Worked with internal and external stakeholders.

QUALIFICATIONS
Level 3 Certificate in Investigations
BSc Business Management
"""
    profile, provider = candidate_profile.extract_candidate_profile(text)
    assert provider == "fallback"
    assert "Stakeholder management" in profile.skills
    assert profile.experience
    assert any("Level 3 Certificate" in item.name for item in profile.qualifications)


def test_txt_cv_upload_persists_only_structured_profile(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(candidate_profile, "get_supabase_client", lambda: fake)
    monkeypatch.setattr(candidate_profile, "_openai_profile", lambda text: None)
    headers = {"Authorization": "Bearer valid_token"}
    cv = b"""PROFILE
Operations professional with substantial stakeholder experience.

SKILLS
Stakeholder management
Risk assessment

EXPERIENCE
Border Force Officer
Reviewed operational risks and worked with partner agencies.

QUALIFICATIONS
Level 3 Certificate in Investigations
"""

    response = client.post(
        "/candidate-profile/cv-upload",
        headers=headers,
        files={"file": ("candidate.txt", cv, "text/plain")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["source_filename"] == "candidate.txt"
    assert "Stakeholder management" in body["skills"]
    assert fake.evidence.rows[0]["source"] == "cv_profile"
    assert fake.evidence.rows[0]["title"] == "CV profile"
    assert "PROFILE\n" not in fake.evidence.rows[0]["reflection"]

    loaded = client.get("/candidate-profile", headers=headers)
    assert loaded.status_code == 200
    assert loaded.json()["skills"] == body["skills"]


def test_cv_upload_rejects_unsupported_file_type(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(candidate_profile, "get_supabase_client", lambda: fake)
    response = client.post(
        "/candidate-profile/cv-upload",
        headers={"Authorization": "Bearer valid_token"},
        files={"file": ("candidate.rtf", b"some cv content" * 20, "application/rtf")},
    )
    assert response.status_code == 415


def test_profile_support_is_capped_at_partial():
    profile = CandidateProfileData(
        summary="Experienced operational professional.",
        skills=["stakeholder management", "risk assessment"],
        experience=[
            CandidateExperience(
                role="Operations Officer",
                organisation="Example",
                highlights=[
                    "Worked with internal and external stakeholders to resolve operational risks.",
                    "Completed risk assessments and documented findings.",
                ],
                skills=["stakeholder management", "risk assessment"],
            )
        ],
        qualifications=[],
    )
    support = _profile_support(
        "Strong stakeholder management and risk assessment experience",
        profile,
    )
    assert support is not None
    assert support["strength"] in {"partial", "weak"}
    assert support["strength"] != "strong"


def test_profile_does_not_fake_people_management_scope():
    profile = CandidateProfileData(
        skills=["security operations", "risk management"],
        experience=[
            CandidateExperience(
                role="Security Officer",
                highlights=["Managed security risks across operational activity."],
                skills=["security operations", "risk management"],
            )
        ],
        qualifications=[],
    )
    support = _profile_support(
        "Experience at management level within security operations",
        profile,
    )
    assert support is None or support["strength"] != "partial"


def test_cv_profile_can_support_qualification_without_becoming_strong():
    profile = CandidateProfileData(
        summary="Operations professional.",
        skills=[],
        experience=[],
        qualifications=[
            {"name": "BSc Business Management", "institution": "Example University", "date": "2020"}
        ],
    )
    support = _profile_support("BSc Business Management qualification", profile)
    assert support is not None
    assert support["strength"] == "partial"


def test_cv_signal_cannot_clear_explicit_blocker():
    response = client.post(
        "/vacancy-analysis",
        headers={"Authorization": "Bearer valid_token"},
        json={
            "job": {"title": "Security Manager"},
            "requirements": [
                {
                    "text": "Strong stakeholder management and risk assessment experience",
                    "category": "essential",
                    "blocker": True,
                }
            ],
            "evidence_cards": [],
            "candidate_profile": {
                "summary": "Operational professional.",
                "skills": ["stakeholder management", "risk assessment"],
                "experience": [
                    {
                        "role": "Operations Officer",
                        "organisation": "Example",
                        "dates": "",
                        "highlights": [
                            "Worked with stakeholders and completed risk assessments."
                        ],
                        "skills": ["stakeholder management", "risk assessment"],
                    }
                ],
                "qualifications": [],
            },
            "practical_issues": [],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "SKIP"
    assert body["requirements"][0]["match_strength"] in {"weak", "missing"}
    assert body["requirements"][0]["profile_support"] is not None


def test_docx_extraction_includes_table_cells():
    import io

    from docx import Document

    document = Document()
    document.add_paragraph("Candidate profile")
    table = document.add_table(rows=2, cols=1)
    table.cell(0, 0).text = "SKILLS"
    table.cell(1, 0).text = "Stakeholder management\nRisk assessment"
    buffer = io.BytesIO()
    document.save(buffer)

    text = candidate_profile._extract_docx(buffer.getvalue())
    assert "Stakeholder management" in text
    assert "Risk assessment" in text


def test_fallback_recognises_common_cv_heading_variants(monkeypatch):
    monkeypatch.setattr(candidate_profile, "_openai_profile", lambda text: None)
    text = """
PROFESSIONAL PROFILE
Operational professional with public-facing enforcement experience.

KEY COMPETENCIES
Stakeholder Management
Report Writing
Risk Assessment

PROFESSIONAL EXPERIENCE
Border Force Officer
Gathered intelligence, assessed risk and worked with partner agencies.

EDUCATION & QUALIFICATIONS
Level 3 Certificate in Investigations
"""
    profile, provider = candidate_profile.extract_candidate_profile(text)
    assert provider == "fallback"
    assert "Stakeholder Management" in profile.skills
    assert profile.experience
    assert any("Level 3 Certificate" in item.name for item in profile.qualifications)


def test_upload_rejects_empty_structured_profile(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(candidate_profile, "get_supabase_client", lambda: fake)
    monkeypatch.setattr(
        candidate_profile,
        "extract_candidate_profile",
        lambda _text: (CandidateProfileData(summary="Readable CV text only."), "fallback"),
    )
    response = client.post(
        "/candidate-profile/cv-upload",
        headers={"Authorization": "Bearer valid_token"},
        files={"file": ("candidate.txt", b"A readable CV with enough text to pass the file extraction threshold. " * 4, "text/plain")},
    )
    assert response.status_code == 422
    assert "could not reliably identify" in response.json()["detail"].lower()
    assert fake.evidence.rows == []


def test_fallback_extracts_role_date_cv_without_experience_heading(monkeypatch):
    monkeypatch.setattr(candidate_profile, "_openai_profile", lambda text: None)
    text = """
CANDIDATE NAME
D.O.B: 01/01/1990
London | Tel: 07000000000 | candidate@example.com

OBJECTIVE
Operational professional with strong communication and customer service skills.

SKILLS PROFILE
Degree qualification
Level 3 professional training
First aid at work
Multi-agency working

Border Operations Officer: Public Sector Employer
January 2021 – Present
Perform duties in a regulated operational environment.
Collaborate with multi-agency partners to manage high-pressure situations.
Provide customer service while maintaining security standards.

Custody Operations Manager: Example Employer
June 2019 – January 2020
Managed custody operations and oversaw a team of officers.
Conducted planning and risk assessments.
Delivered training and guidance to staff.

Custody Officer: Example Contractor
February 2016 – June 2019
Escorted individuals safely and securely.
Worked with police and operational partners.

EDUCATION/TRAINING
October 2012 – April 2015: Example University
BSc Example Degree
July 2012 – August 2012: Example Provider
NVQ Level 2 Example Qualification

INTERESTS
Sport and volunteering.
"""
    profile, provider = candidate_profile.extract_candidate_profile(text)

    assert provider == "fallback"
    assert "Multi-agency working" in profile.skills
    assert [item.role for item in profile.experience] == [
        "Border Operations Officer",
        "Custody Operations Manager",
        "Custody Officer",
    ]
    assert profile.experience[1].organisation == "Example Employer"
    assert any("Managed custody operations" in item for item in profile.experience[1].highlights)
    assert any(item.name == "BSc Example Degree" for item in profile.qualifications)
    assert any(item.name == "NVQ Level 2 Example Qualification" for item in profile.qualifications)
    assert "D.O.B" not in profile.summary
    assert "candidate@example.com" not in profile.summary


def test_ai_profile_uses_dated_source_roles_as_canonical_employment(monkeypatch):
    text = """
OBJECTIVE
Operational professional.

SKILLS PROFILE
Stakeholder management
Teaching assistant experience
Mentoring experience

Operations Officer: Example Agency
January 2021 – Present
Worked with partner agencies and assessed operational risk.

Custody Manager: Example Employer
June 2019 – January 2020
Managed a team and coordinated with police.

Custody Officer: Example Contractor
February 2016 – June 2019
Maintained secure operational workflows.

EDUCATION/TRAINING
October 2012 – April 2015: Example University
BSc Example Degree
"""
    inflated = CandidateProfileData(
        summary="Operational professional.",
        skills=["Stakeholder management", "Teaching assistant experience", "Mentoring experience"],
        experience=[
            CandidateExperience(role=f"AI inferred experience {index}", highlights=["Background item"])
            for index in range(9)
        ],
        qualifications=[],
    )
    monkeypatch.setattr(candidate_profile, "_openai_profile", lambda _text: inflated)

    profile, provider = candidate_profile.extract_candidate_profile(text)

    assert provider == "openai"
    assert [item.role for item in profile.experience] == [
        "Operations Officer",
        "Custody Manager",
        "Custody Officer",
    ]
    assert "Teaching assistant experience" in profile.skills


def test_repeated_docx_layout_blocks_do_not_duplicate_employment(monkeypatch):
    monkeypatch.setattr(candidate_profile, "_openai_profile", lambda text: None)
    block = """
Border Operations Officer: Example Agency
January 2021 – Present
Worked with partner agencies.

Custody Operations Manager: Example Employer
June 2019 – January 2020
Managed operational activity and staff.

Custody Officer: Example Contractor
February 2016 – June 2019
Maintained secure operational workflows.
"""
    text = f"""
OBJECTIVE
Operational professional.

SKILLS PROFILE
Stakeholder management
Risk assessment

{block}
{block}
{block}

EDUCATION/TRAINING
October 2012 – April 2015: Example University
BSc Example Degree
"""

    profile, provider = candidate_profile.extract_candidate_profile(text)

    assert provider == "fallback"
    assert [item.role for item in profile.experience] == [
        "Border Operations Officer",
        "Custody Operations Manager",
        "Custody Officer",
    ]
