from fastapi.testclient import TestClient

from backend.main import app
from backend.routes.vacancy_analysis import Evidence
from lib.vacancy_extraction import deterministic_extract

client = TestClient(app)
HEADERS = {"Authorization": "Bearer valid_token"}


COMPLIANCE_SMOKE = """
Junior Risk & Compliance Analyst
Full-Time
Hybrid

Requirements:
- Strong organisational skills
- Ability to think, analyse and use initiative
- Attention to detail
- Ability to work well under pressure and to tight deadlines
- Excellent IT skills
- Good interpersonal skills
- Law degree min 2:1 or GDL/LPC
- Compliance / AML experience
- Working within legal practice a bonus
"""


CUSTOMER_SUCCESS_SMOKE = """
Customer Success Manager

The Company You'll Join
Carta is a private-capital technology company.

The Problems You'll Solve
Own the success and health of a portfolio of clients.

About You
Specifically, we're looking for:
- 5+ years of experience in Customer Success or Account Management.
- Full lifecycle client ownership.
- Cross-functional collaboration across delivery, sales, marketing and operations.
- Strong commercial instincts.
- Outstanding verbal and written communication skills.
- High emotional intelligence and adaptability.
- Experience with customer-success tools and AI in practice.
- Prior experience in the legal industry is a significant advantage.
- Prior experience in private markets is a significant advantage.

Disclosures
Equal opportunity information.

We work on a hybrid schedule where we come into office 3x/week and work remotely the remaining 2 days.
"""


def compliance_card() -> Evidence:
    return Evidence(
        id="ev-compliance-generic",
        title="Operational analysis under pressure",
        situation="A time-sensitive operational issue required careful review and prioritisation.",
        task="I was responsible for analysing the available information and organising the next steps.",
        actions=[
            "I analysed the information, checked details carefully and used my initiative to resolve gaps.",
            "I prioritised competing deadlines and communicated clearly with colleagues and stakeholders.",
        ],
        outcome="The work was completed accurately within the required deadline.",
        skills=["analysis", "organisation", "communication"],
    )


def customer_success_card() -> Evidence:
    return Evidence(
        id="ev-customer",
        title="Client and stakeholder relationship management",
        situation="I supported a portfolio of internal and external stakeholders with competing priorities.",
        task="I was responsible for maintaining relationships, understanding needs and coordinating delivery.",
        actions=[
            "I built trusted relationships with stakeholders and adapted communication to different audiences.",
            "I coordinated across operational teams, resolved issues and identified opportunities to improve service.",
        ],
        outcome="Stakeholders received clearer support and issues were resolved more consistently.",
        skills=["stakeholder management", "communication", "customer service", "collaboration"],
    )


def _requirements(advert: str) -> list[dict]:
    return [
        {
            "text": item["text"],
            "category": item["category"],
            "blocker": item["explicit_blocker"],
        }
        for item in deterministic_extract(advert)
        if item["category"] in {"essential", "desirable", "trainable"}
    ]


def test_live_compliance_pattern_separates_hybrid_and_optional_bonus():
    items = deterministic_extract(COMPLIANCE_SMOKE)
    essentials = [item for item in items if item["category"] == "essential"]
    desirables = [item for item in items if item["category"] == "desirable"]
    practical = [item for item in items if item["category"] == "practical"]

    assert any("law degree" in item["text"].lower() for item in essentials)
    assert any("compliance / aml experience" in item["text"].lower() for item in essentials)
    assert any("legal practice a bonus" in item["text"].lower() for item in desirables)
    assert any("hybrid" in item["text"].lower() for item in practical)


def test_live_customer_success_pattern_handles_about_you_and_advantages():
    items = deterministic_extract(CUSTOMER_SUCCESS_SMOKE)
    essentials = [item for item in items if item["category"] == "essential"]
    desirables = [item for item in items if item["category"] == "desirable"]
    practical = [item for item in items if item["category"] == "practical"]
    combined = "\n".join(item["text"].lower() for item in items)

    assert len(essentials) >= 7
    assert sum("significant advantage" in item["text"].lower() for item in desirables) == 2
    assert "specifically, we're looking for" not in combined
    assert "equal opportunity information" not in combined
    assert any("hybrid schedule" in item["text"].lower() for item in practical)


def test_compliance_matching_stays_grounded_and_leaves_domain_gaps(monkeypatch):
    monkeypatch.setattr("routes.vacancy_analysis.semantic_assess_batch", lambda _entries: None)
    payload = {
        "job": {"title": "Junior Risk & Compliance Analyst"},
        "requirements": _requirements(COMPLIANCE_SMOKE),
        "evidence_cards": [compliance_card().model_dump()],
        "practical_issues": [],
    }

    data = client.post("/vacancy-analysis", headers=HEADERS, json=payload).json()
    by_requirement = {item["requirement"].lower(): item for item in data["requirements"]}

    analysis_item = next(item for key, item in by_requirement.items() if "think, analyse" in key)
    aml_item = next(item for key, item in by_requirement.items() if "compliance / aml" in key)
    degree_item = next(item for key, item in by_requirement.items() if "law degree" in key)

    assert analysis_item["match_strength"] in {"partial", "strong"}
    assert aml_item["match_strength"] in {"weak", "missing"}
    assert degree_item["match_strength"] in {"weak", "missing"}
    assert data["decision"] == "CONSIDER"


def test_customer_success_matching_supports_generic_fit_without_inventing_sector_experience(monkeypatch):
    monkeypatch.setattr("routes.vacancy_analysis.semantic_assess_batch", lambda _entries: None)
    payload = {
        "job": {"title": "Customer Success Manager", "organisation": "Carta"},
        "requirements": _requirements(CUSTOMER_SUCCESS_SMOKE),
        "evidence_cards": [customer_success_card().model_dump()],
        "practical_issues": [],
    }

    data = client.post("/vacancy-analysis", headers=HEADERS, json=payload).json()
    by_requirement = {item["requirement"].lower(): item for item in data["requirements"]}

    collaboration = next(item for key, item in by_requirement.items() if "cross-functional collaboration" in key)
    legal = next(item for key, item in by_requirement.items() if "legal industry" in key)
    private_markets = next(item for key, item in by_requirement.items() if "private markets" in key)

    assert collaboration["match_strength"] in {"partial", "strong"}
    assert legal["match_strength"] in {"weak", "missing"}
    assert private_markets["match_strength"] in {"weak", "missing"}
    assert data["decision"] in {"APPLY", "CONSIDER"}


def test_hybrid_schedule_experience_stays_in_evidence_requirements():
    advert = """
Customer Operations Manager

About You
- Experience coordinating a hybrid schedule across regional teams.
- Experience managing hybrid working arrangements for distributed teams.
"""

    items = deterministic_extract(advert)
    essentials = [item for item in items if item["category"] == "essential"]
    practical = [item for item in items if item["category"] == "practical"]

    assert any("coordinating a hybrid schedule" in item["text"].lower() for item in essentials)
    assert any("managing hybrid working arrangements" in item["text"].lower() for item in essentials)
    assert not any("hybrid schedule" in item["text"].lower() for item in practical)
    assert not any("hybrid working arrangements" in item["text"].lower() for item in practical)
