from fastapi.testclient import TestClient

from backend.main import app
from lib.vacancy_ai import _validate_item
from lib.vacancy_extraction import deterministic_extract
from routes.vacancy_intelligence import _reconcile_items

client = TestClient(app)
HEADERS = {"Authorization": "Bearer valid_token"}

VACANCY = """
Eligibility:
- Applicants must have the right to work in the UK.

Essential criteria:
- Experience analysing complex information and making recommendations.
- You must demonstrate effective stakeholder management.

Desirable:
- Fraud investigation experience is desirable.

Training:
- Successful candidates will receive training in the internal casework system.
- Role-specific legislation and procedures will be taught during training.

Working pattern:
- The role requires a minimum of 30 hours per week across 4 days.
"""

MESSY_CIVIL_SERVICE_VACANCY = """
Job summary
We believe a positive, open and supportive culture is essential to help everyone deliver their best work.

Responsibilities
Leading collaboration discussions and campaign activity with partners.

Working patterns
Due to the business requirements of this role, it is only available on a full-time basis.

Person specification
Essential criteria
You must be able to demonstrate experience of:
Partnership management or stakeholder engagement, influencing internal and external stakeholders at all levels and building and managing productive relationships;
Sourcing, analysing and prioritising relevant sources of data and insight to inform communications activity;
Developing and delivering proposals and presentations;
Leading the development, delivery and evaluation of partnership campaigns designed to drive behaviour change, including working collaboratively with internal and external communications teams; and
Strong organisational and project management skills; able to manage multiple priorities and deadlines.

Desirable criteria
Familiarity with public communications in a large complex organisation.

Behaviours
Working Together
Making Effective Decisions

Technical skills
Communications - Implementation
Communications - Insight

Benefits
National pay locations: Cardiff, Salford, Sheffield £49,850 - £52,850

Things you need to know
Artificial intelligence
Artificial intelligence can be a useful tool to support your application.

Selection process details
Application – by 30th August 2026.
Your CV should consist of your career history, qualifications, and skills/experience, including any key achievements in each role.
The Personal Statement should be aligned to and demonstrate how you meet the skills and experience set out in the essential criteria.
Sift – from 2nd September 2026.
Interview – from 23rd September 2026.
Please note travel expenses incurred by attending an interview will not be reimbursed.
If you experience problems accessing this advert, please contact recruitment@example.gov.uk.

Breaking Tied Scores
The behaviour, technical and experience skills have been ranked in order of importance to enable us to differentiate between candidates with tied interview scores.

Additional Security Checks
As well as successfully obtaining UK Security Vetting clearance, candidates will be subject to a range of additional checks.
"""


def test_deterministic_extraction_groups_grounded_requirements():
    items = deterministic_extract(VACANCY)
    categories = {item["category"] for item in items}

    assert {"eligibility", "essential", "desirable", "practical", "trainable"}.issubset(categories)
    eligibility = next(item for item in items if item["category"] == "eligibility")
    assert eligibility["explicit_blocker"] is True
    assert eligibility["source_text"] in VACANCY
    assert all(item["source_text"] in VACANCY for item in items)


def test_normal_essential_must_language_is_not_a_hard_blocker():
    items = deterministic_extract(VACANCY)
    stakeholder = next(item for item in items if "stakeholder management" in item["text"].lower())

    assert stakeholder["category"] == "essential"
    assert stakeholder["explicit_blocker"] is False


def test_training_language_including_will_be_taught_is_captured():
    items = deterministic_extract(VACANCY)
    trainable = [item for item in items if item["category"] == "trainable"]

    assert len(trainable) == 2
    assert any("will receive training" in item["text"].lower() for item in trainable)
    assert any("will be taught" in item["text"].lower() for item in trainable)


def test_civil_service_admin_copy_does_not_leak_into_requirements():
    items = deterministic_extract(MESSY_CIVIL_SERVICE_VACANCY)
    requirements = [item for item in items if item["category"] in {"essential", "desirable", "trainable"}]
    essentials = [item for item in requirements if item["category"] == "essential"]
    desirables = [item for item in requirements if item["category"] == "desirable"]
    combined = "\n".join(item["text"].lower() for item in items)

    assert len(essentials) == 5
    assert len(desirables) == 1
    assert all("you must be able to demonstrate experience of" not in item["text"].lower() for item in requirements)
    assert "positive, open and supportive culture" not in combined
    assert "application – by" not in combined
    assert "your cv should" not in combined
    assert "personal statement should" not in combined
    assert "sift – from" not in combined
    assert "interview – from" not in combined
    assert "travel expenses" not in combined
    assert "ranked in order of importance" not in combined
    assert "recruitment@example.gov.uk" not in combined
    assert "national pay locations" not in combined
    assert any(item["category"] == "practical" and "full-time basis" in item["text"].lower() for item in items)
    assert any(item["category"] == "eligibility" and "security vetting" in item["text"].lower() for item in items)


def test_ai_validation_rejects_ungrounded_source_text():
    raw = {
        "text": "Five years of management experience",
        "category": "essential",
        "source_text": "Five years of management experience is required.",
        "confidence": 0.9,
        "explicit_blocker": True,
    }
    assert _validate_item(raw, VACANCY) is None


def test_ai_validation_rejects_administrative_copy_even_when_grounded():
    source = "Application – by 30th August 2026."
    raw = {
        "text": source,
        "category": "desirable",
        "source_text": source,
        "confidence": 0.9,
        "explicit_blocker": False,
    }
    assert _validate_item(raw, MESSY_CIVIL_SERVICE_VACANCY) is None


def test_ai_validation_rejects_culture_copy_as_essential():
    source = "We believe a positive, open and supportive culture is essential to help everyone deliver their best work."
    raw = {
        "text": source,
        "category": "essential",
        "source_text": source,
        "confidence": 0.9,
        "explicit_blocker": False,
    }
    assert _validate_item(raw, MESSY_CIVIL_SERVICE_VACANCY) is None


def test_ai_validation_does_not_promote_normal_essential_to_hard_blocker():
    source = "You must demonstrate effective stakeholder management."
    raw = {
        "text": source,
        "category": "essential",
        "source_text": source,
        "confidence": 0.9,
        "explicit_blocker": True,
    }

    item = _validate_item(raw, VACANCY)
    assert item is not None
    assert item["explicit_blocker"] is False


def test_reconcile_supplements_semantic_omissions_without_duplicates():
    deterministic = deterministic_extract(VACANCY)
    semantic = [
        {
            "text": "Applicants must have the right to work in the UK.",
            "category": "eligibility",
            "source_text": "Applicants must have the right to work in the UK.",
            "confidence": 1.0,
            "explicit_blocker": True,
        },
        {
            "text": "Experience analysing complex information and making recommendations.",
            "category": "essential",
            "source_text": "Experience analysing complex information and making recommendations.",
            "confidence": 1.0,
            "explicit_blocker": False,
        },
    ]

    merged, provider = _reconcile_items(semantic, deterministic)

    assert provider == "hybrid-grounded-v3"
    assert len(merged) == len(deterministic)
    assert sum(1 for item in merged if "right to work" in item["text"].lower()) == 1
    assert any("stakeholder management" in item["text"].lower() for item in merged)
    assert len([item for item in merged if item["category"] == "trainable"]) == 2


def test_reconcile_deduplicates_semantic_items_before_supplementing():
    semantic = [
        {
            "text": "Experience analysing complex information and making recommendations.",
            "category": "essential",
            "source_text": "Experience analysing complex information and making recommendations.",
            "confidence": 1.0,
            "explicit_blocker": False,
        },
        {
            "text": "Experience analysing complex information",
            "category": "essential",
            "source_text": "Experience analysing complex information and making recommendations.",
            "confidence": 0.9,
            "explicit_blocker": False,
        },
    ]
    merged, _ = _reconcile_items(semantic, [])
    assert len(merged) == 1


def test_reconcile_uses_deterministic_when_semantic_unavailable():
    deterministic = deterministic_extract(VACANCY)
    merged, provider = _reconcile_items(None, deterministic)

    assert provider == "deterministic-v2"
    assert merged == deterministic


def test_route_requires_authentication():
    response = client.post("/vacancy-intelligence", json={"vacancy_text": VACANCY})
    assert response.status_code == 401


def test_route_returns_structured_fallback(monkeypatch):
    monkeypatch.setattr("routes.vacancy_intelligence.semantic_extract", lambda _text: None)

    response = client.post(
        "/vacancy-intelligence",
        headers=HEADERS,
        json={"vacancy_text": VACANCY},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "deterministic-v2"
    assert data["eligibility"]
    assert data["requirements"]
    assert data["practical"]
    assert data["summary"]["items"] == len(data["eligibility"]) + len(data["requirements"]) + len(data["practical"])
    assert all("source_text" in item and "confidence" in item for item in data["requirements"])


def test_route_supplements_under_extracted_semantic_result(monkeypatch):
    monkeypatch.setattr(
        "routes.vacancy_intelligence.semantic_extract",
        lambda _text: [
            {
                "text": "Applicants must have the right to work in the UK.",
                "category": "eligibility",
                "source_text": "Applicants must have the right to work in the UK.",
                "confidence": 1.0,
                "explicit_blocker": True,
            }
        ],
    )

    response = client.post(
        "/vacancy-intelligence",
        headers=HEADERS,
        json={"vacancy_text": VACANCY},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "hybrid-grounded-v3"
    assert data["summary"]["items"] >= 7
    assert len([item for item in data["requirements"] if item["category"] == "trainable"]) == 2
