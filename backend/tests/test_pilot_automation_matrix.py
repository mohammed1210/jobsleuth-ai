"""Small automated pilot matrix for the vacancy -> fit journey.

These are intentionally broad, real-world-shaped regressions.  They are not meant
to replace focused unit tests; they catch the kinds of failures that previously
required manual screenshot testing.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from lib.vacancy_extraction import deterministic_extract
from routes.candidate_profile import CandidateExperience, CandidateProfileData
from routes.vacancy_analysis import _profile_support

client = TestClient(app)
HEADERS = {"Authorization": "Bearer valid_token"}


PARKGUARD = """
Patrol Officer

Role Requirements:
Valid SIA Door Supervisor or Close Protection Licence
A Valid UK Driver’s Licence & own means of transport
Able and willing to work unsocial hours (between 11:30am-03:00am dependent on shift)
Excellent spoken & written English language skills and accurate report writing
A good level of understanding of Criminal Law and required legislation
Be physically fit and able to deal with confrontational incidents
Be compassionate and motivated to support and help the public
Excellent personal presentation
Be able to self-task and take responsibility for service delivery
All successful candidates will be required to undergo Full Police Vetting

Benefits of working for Parkguard Ltd:
28 Days Paid Annual Leave
Company Pension Scheme
Free Parking on shift

Full, comprehensive and in-depth training will be provided to all successful candidates

Ideal Candidates & Experience:
Police/Law Enforcement
Security (SIA)
Bailiff
Close Protection
Military
Community Safety / Community Safety Accreditation (CSAS)

Working Days: 5 day week variable
Shifts: Predominantly late turn between 11:30am - 02:30am
Total hours per week: Contracted hours are 45hrs per week
Work Location: In person
"""

SERCO_PCO = """
Prisoner Escort & Custody Driver

We operate 24/6 across early and late shifts, so flexibility is essential. Finishing
times can be unpredictable, and you may need to work beyond your contracted hours.
Shifts are set on a rota provided 12 weeks in advance.

What you need to do the job!
You will receive full training through a 5½-week paid training. Requirements of the role:
Full UK driving licence essential - B1/C1
C1 licence holders should ideally hold a valid CPC
Reasonable fitness for the physical demands of the role
Strong communication skills (written and verbal)
Ability to stay calm and make decisions under pressure
Confidence managing behaviour and de-escalating conflict
Teamwork and the ability to follow processes accurately
Professionalism, integrity, and respect for confidentiality

Eligibility checks and further information
Job offers are subject to Enhanced Disclosure and Barring Service (DBS) clearance,
satisfactory employment references and occupational health checks.
You must have the right to work in the UK.
"""

COMPLIANCE = """
Junior Risk & Compliance Analyst
Hybrid

Requirements:
Strong organisational skills
Ability to think, analyse and use initiative
Attention to detail
Ability to work well under pressure and to tight deadlines
Excellent IT skills
Good interpersonal skills
Law degree min 2:1 or GDL/LPC
Compliance / AML experience
Working within legal practice a bonus
"""

CUSTOMER_SUCCESS = """
Customer Success Manager

About You
5+ years of experience in Customer Success or Account Management
Full lifecycle client ownership
Cross-functional collaboration across delivery, sales, marketing and operations
Strong commercial instincts
Outstanding verbal and written communication skills
High emotional intelligence and adaptability
Experience with customer-success tools and AI in practice
Prior experience in the legal industry is a significant advantage
Prior experience in private markets is a significant advantage

Working arrangements: Hybrid
"""


@pytest.mark.parametrize(
    ("name", "advert", "minimums", "must_contain", "must_not_contain"),
    [
        (
            "parkguard",
            PARKGUARD,
            {"essential": 6, "desirable": 5, "eligibility": 3, "practical": 3, "trainable": 1},
            {
                "eligibility": ["sia", "driver", "police vetting"],
                "essential": ["criminal law", "self-task"],
                "practical": ["working days", "shifts:"],
            },
            ["annual leave", "company pension", "free parking"],
        ),
        (
            "serco-pco",
            SERCO_PCO,
            {"essential": 6, "desirable": 1, "eligibility": 2, "practical": 1, "trainable": 1},
            {
                "essential": ["strong communication", "de-escalating conflict", "confidentiality"],
                "desirable": ["valid cpc"],
                "eligibility": ["driving licence", "right to work"],
                "practical": ["24/6"],
            },
            [],
        ),
        (
            "compliance",
            COMPLIANCE,
            {"essential": 7, "desirable": 1, "practical": 1},
            {
                "essential": ["law degree", "compliance / aml"],
                "desirable": ["legal practice a bonus"],
                "practical": ["hybrid"],
            },
            [],
        ),
        (
            "customer-success",
            CUSTOMER_SUCCESS,
            {"essential": 7, "desirable": 2, "practical": 1},
            {
                "essential": ["cross-functional collaboration", "verbal and written"],
                "desirable": ["legal industry", "private markets"],
                "practical": ["hybrid"],
            },
            [],
        ),
    ],
)
def test_pilot_vacancy_extraction_matrix(name, advert, minimums, must_contain, must_not_contain):
    items = deterministic_extract(advert)
    by_category: dict[str, list[str]] = {}
    for item in items:
        by_category.setdefault(item["category"], []).append(item["text"].lower())

    for category, minimum in minimums.items():
        assert len(by_category.get(category, [])) >= minimum, (
            f"{name}: expected at least {minimum} {category} items, "
            f"got {by_category.get(category, [])}"
        )

    for category, phrases in must_contain.items():
        text = "\n".join(by_category.get(category, []))
        for phrase in phrases:
            assert phrase in text, f"{name}: missing {category} phrase {phrase!r}"

    combined = "\n".join(item["text"].lower() for item in items)
    for phrase in must_not_contain:
        assert phrase not in combined, f"{name}: leaked non-requirement {phrase!r}"


@pytest.mark.parametrize(
    "advert,expected_category,phrase",
    [
        (
            """
HR Advisor
Requirements of the role:
Experience preparing employment references for candidates
Experience supporting recruitment campaigns
""",
            "essential",
            "preparing employment references",
        ),
        (
            """
Learning and Development Officer
Requirements of the role:
Experience delivering paid training programmes to employees
Strong written communication skills
""",
            "essential",
            "delivering paid training programmes",
        ),
        (
            """
Operations Manager
Role Requirements:
Experience scheduling staff across working days and changing priorities
Working Days: Monday to Friday
""",
            "essential",
            "scheduling staff across working days",
        ),
    ],
)
def test_pilot_false_positive_matrix(advert, expected_category, phrase):
    items = deterministic_extract(advert)
    expected = "\n".join(
        item["text"].lower() for item in items if item["category"] == expected_category
    )
    assert phrase in expected


def test_cv_signal_requires_role_grounding_before_conversion():
    profile = CandidateProfileData(
        summary="Operational professional.",
        skills=["communication"],
        experience=[
            CandidateExperience(
                role="Custody Officer",
                organisation="Example",
                dates="2020 - 2022",
                highlights=["Escorted detainees safely and completed custody paperwork."],
                skills=["communication"],
            )
        ],
        qualifications=[],
    )

    support = _profile_support("Strong communication skills (written and verbal)", profile)

    assert support is not None
    assert support["source"] is None


def test_cv_signal_exposes_conversion_source_when_role_actions_support_criterion():
    profile = CandidateProfileData(
        summary="Operational professional.",
        skills=["communication"],
        experience=[
            CandidateExperience(
                role="Custody Officer",
                organisation="Example",
                dates="2020 - 2022",
                highlights=[
                    "Maintained effective communication with police and operational partners.",
                    "Completed routine equipment checks.",
                ],
                skills=["communication"],
            )
        ],
        qualifications=[],
    )

    support = _profile_support("Strong communication skills (written and verbal)", profile)

    assert support is not None
    assert support["source"] is not None
    assert support["source"]["title"] == "Custody Officer at Example"
    assert any("communication with police" in item.lower() for item in support["source"]["actions"])
    assert all("equipment checks" not in item.lower() for item in support["source"]["actions"])


@pytest.mark.parametrize(
    ("answer", "practical_issues", "expected"),
    [
        ("yes", [], "APPLY"),
        ("no", [], "SKIP"),
        ("unsure", [], "CONSIDER"),
        ("yes", ["Late shifts need checking"], "CONSIDER"),
    ],
)
def test_pilot_decision_matrix(answer, practical_issues, expected):
    payload = {
        "job": {"title": "Custody Officer"},
        "requirements": [
            {
                "text": "Valid UK driving licence",
                "category": "eligibility",
                "blocker": True,
                "eligibility_answer": answer,
            },
            {
                "text": "confident decision making",
                "category": "essential",
            },
        ],
        "evidence_cards": [
            {
                "id": "ev-1",
                "title": "Decision example",
                "skills": ["confident decision making"],
                "actions": ["I reviewed the evidence and made a confident decision."],
                "outcome": "The issue was resolved safely.",
            }
        ],
        "practical_issues": practical_issues,
    }

    response = client.post("/vacancy-analysis", headers=HEADERS, json=payload)
    assert response.status_code == 200
    assert response.json()["decision"] == expected
