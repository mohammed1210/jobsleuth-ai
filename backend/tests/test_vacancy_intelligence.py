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



PRIVATE_SECTOR_VACANCY = """
Senior Operations Analyst
Acme Technology

What you'll bring
- Experience analysing operational data and turning findings into clear recommendations.
- Strong stakeholder management and written communication skills.
- Ability to manage competing priorities in a fast-paced environment.

Preferred qualifications
- Experience working in a regulated industry.
- Familiarity with SQL or business intelligence tools.

Hybrid working
- You will be expected to work from the London office at least two days per week.
"""


PRIVATE_SECTOR_BOUNDARY_VACANCY = """
Operations Manager

Requirements
- Experience leading operational teams.
- Strong analytical and stakeholder-management skills.

What we offer
Private medical insurance
Annual learning allowance
A collaborative and inclusive culture
"""


PRIVATE_SECTOR_CURLY_HEADING_VACANCY = """
Product Operations Lead

What you’ll bring
- Experience improving operational processes.
- Strong written communication skills.

What we’re looking for
- Ability to manage competing priorities.
"""


PRIVATE_SECURITY_VACANCY = """
Job details
Job type
Permanent
Full-time
Shift and schedule
Weekend availability
Nights as needed

About the Role
H&M Security Services, an ACS-accredited security provider, is seeking an experienced Manned Guarding Operations Manager to join our team.

Requirements

Essential:
Valid and in-date Frontline SIA Licence
Strong background in the Manned Guarding industry
Previous experience at management level within security operations
Full Manual UK Driving Licence
Excellent written and verbal English communication skills
High level of IT proficiency, including Microsoft Office and rostering systems
Ability to work independently and within a team
5-year checkable employment history
Ability to pass SC Clearance

What We Offer
Competitive salary
Annual leave

Work Location: In person
"""


PRIVATE_SECTOR_OPTIONAL_LICENCE_VACANCY = """
Operations Coordinator

Desirable:
A full UK driving licence would be advantageous.
"""

PRIVATE_SECTOR_FULL_TIME_EXPERIENCE_VACANCY = """
Security Operations Manager

Essential:
At least three years of full-time experience in security operations.
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




def test_private_sector_headings_extract_core_requirements_without_civil_service_language():
    items = deterministic_extract(PRIVATE_SECTOR_VACANCY)
    essentials = [item for item in items if item["category"] == "essential"]
    desirables = [item for item in items if item["category"] == "desirable"]
    practical = [item for item in items if item["category"] == "practical"]

    assert len(essentials) == 3
    assert len(desirables) == 2
    assert any("operational data" in item["text"].lower() for item in essentials)
    assert any("regulated industry" in item["text"].lower() for item in desirables)
    assert any("two days per week" in item["text"].lower() for item in practical)
    assert all(item["source_text"] in PRIVATE_SECTOR_VACANCY for item in items)


def test_private_sector_non_criteria_heading_terminates_essential_section():
    items = deterministic_extract(PRIVATE_SECTOR_BOUNDARY_VACANCY)
    essentials = [item for item in items if item["category"] == "essential"]
    combined = "\n".join(item["text"].lower() for item in items)

    assert len(essentials) == 2
    assert "private medical insurance" not in combined
    assert "annual learning allowance" not in combined
    assert "collaborative and inclusive culture" not in combined


def test_private_sector_curly_apostrophe_headings_are_recognised():
    items = deterministic_extract(PRIVATE_SECTOR_CURLY_HEADING_VACANCY)
    essentials = [item for item in items if item["category"] == "essential"]

    assert len(essentials) == 3
    assert any("operational processes" in item["text"].lower() for item in essentials)
    assert any("competing priorities" in item["text"].lower() for item in essentials)


def test_private_security_advert_separates_credentials_and_practical_constraints():
    items = deterministic_extract(PRIVATE_SECURITY_VACANCY)
    essentials = [item for item in items if item["category"] == "essential"]
    eligibility = [item for item in items if item["category"] == "eligibility"]
    practical = [item for item in items if item["category"] == "practical"]
    combined_essential = "\n".join(item["text"].lower() for item in essentials)

    assert "essential" not in {item["text"].lower().rstrip(":") for item in essentials}
    assert any("manned guarding industry" in item["text"].lower() for item in essentials)
    assert any("sia licence" in item["text"].lower() for item in eligibility)
    assert any("driving licence" in item["text"].lower() for item in eligibility)
    assert any("checkable employment history" in item["text"].lower() for item in eligibility)
    assert any("sc clearance" in item["text"].lower() for item in eligibility)
    assert any("weekend availability" in item["text"].lower() for item in practical)
    assert any("nights as needed" in item["text"].lower() for item in practical)
    assert any("work location: in person" in item["text"].lower() for item in practical)
    assert "competitive salary" not in combined_essential


def test_desirable_driving_licence_is_not_promoted_to_mandatory_eligibility():
    items = deterministic_extract(PRIVATE_SECTOR_OPTIONAL_LICENCE_VACANCY)
    assert any(
        item["category"] == "desirable" and "driving licence" in item["text"].lower()
        for item in items
    )
    assert not any(
        item["category"] == "eligibility" and "driving licence" in item["text"].lower()
        for item in items
    )


def test_full_time_experience_remains_an_essential_criterion():
    items = deterministic_extract(PRIVATE_SECTOR_FULL_TIME_EXPERIENCE_VACANCY)
    assert any(
        item["category"] == "essential" and "full-time experience" in item["text"].lower()
        for item in items
    )
    assert not any(
        item["category"] == "practical" and "full-time experience" in item["text"].lower()
        for item in items
    )


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

    assert provider == "hybrid-grounded-v4"
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
    assert data["provider"] == "hybrid-grounded-v4"
    assert data["summary"]["items"] >= 7
    assert len([item for item in data["requirements"] if item["category"] == "trainable"]) == 2
