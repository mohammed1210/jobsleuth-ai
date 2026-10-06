import pytest

from lib.vacancy_extraction import deterministic_extract


CASES = [
    {
        "id": "security-patrol",
        "advert": """
Patrol Officer

Role Requirements:
Valid SIA Door Supervisor Licence
Valid UK driving licence
Excellent written and verbal communication
Knowledge of criminal law
Able to self-task and take responsibility for service delivery
Able to deal with confrontational incidents

Benefits:
Company pension
Free parking
28 days annual leave

Ideal Candidates & Experience:
Police/Law Enforcement
Community Safety

Working Days: variable weekends included
Work Location: In person
""",
        "must": {
            "eligibility": ["sia door supervisor", "uk driving licence"],
            "essential": ["written and verbal communication", "criminal law", "self-task", "confrontational incidents"],
            "desirable": ["police/law enforcement", "community safety"],
            "practical": ["working days", "work location"],
        },
        "never": ["company pension", "free parking", "28 days annual leave"],
    },
    {
        "id": "custody-driver",
        "advert": """
Prisoner Escort & Custody Driver

We operate 24/6 across early and late shifts. Finishing times can be unpredictable and you may need to work beyond contracted hours.

Requirements of the role:
Full UK driving licence essential
C1 licence holders should ideally hold a valid CPC
Reasonable fitness
Strong communication skills
Ability to stay calm and make decisions under pressure
Confidence managing behaviour and de-escalating conflict
Teamwork and the ability to follow processes accurately
Professionalism, integrity and respect for confidentiality

You will receive full training through a paid induction.

Eligibility checks and further information:
Job offers are subject to Enhanced DBS clearance, satisfactory employment references and occupational health checks.
You must have the right to work in the UK.
""",
        "must": {
            "eligibility": ["full uk driving licence", "dbs clearance", "employment references", "occupational health", "right to work"],
            "essential": ["reasonable fitness", "communication skills", "stay calm", "de-escalating conflict", "teamwork", "confidentiality"],
            "desirable": ["valid cpc"],
            "practical": ["24/6", "work beyond contracted hours"],
            "trainable": ["receive full training"],
        },
        "never": [],
    },
    {
        "id": "compliance-analyst",
        "advert": """
Junior Risk & Compliance Analyst

Requirements:
Strong organisational skills
Ability to analyse and use initiative
Attention to detail
Work well under pressure
Law degree minimum 2:1
Compliance / AML experience
Working within legal practice a bonus

Working arrangement: Hybrid
""",
        "must": {
            "essential": ["organisational skills", "analyse and use initiative", "attention to detail", "law degree", "compliance / aml"],
            "desirable": ["legal practice a bonus"],
            "practical": ["hybrid"],
        },
        "never": [],
    },
    {
        "id": "customer-success",
        "advert": """
Customer Success Manager

About You:
5+ years of experience in Customer Success or Account Management
Full lifecycle client ownership
Cross-functional collaboration across sales, operations and delivery
Outstanding verbal and written communication skills
Experience with customer-success tools
Prior experience in the legal industry is a significant advantage
Prior experience in private markets is a significant advantage

Disclosures:
Equal opportunity information

Working arrangement: Hybrid schedule, three days in office
""",
        "must": {
            "essential": ["customer success", "client ownership", "cross-functional collaboration", "written communication", "customer-success tools"],
            "desirable": ["legal industry", "private markets"],
            "practical": ["hybrid schedule"],
        },
        "never": ["equal opportunity information"],
    },
    {
        "id": "hr-advisor",
        "advert": """
HR Advisor

Requirements of the role:
Experience preparing employment references for candidates
Experience supporting recruitment campaigns
Strong written communication skills

What we offer:
Employee assistance programme
Company pension
""",
        "must": {
            "essential": ["preparing employment references", "recruitment campaigns", "written communication"],
        },
        "never": ["employee assistance programme", "company pension"],
    },
    {
        "id": "learning-development",
        "advert": """
Learning and Development Officer

Requirements of the role:
Experience delivering paid training programmes to employees
Experience evaluating learning outcomes
Strong presentation skills

Benefits:
Paid training for your own development
Retail discounts
""",
        "must": {
            "essential": ["delivering paid training programmes", "evaluating learning outcomes", "presentation skills"],
        },
        "never": ["retail discounts"],
    },
    {
        "id": "operations-manager",
        "advert": """
Operations Manager

Essential Criteria:
Experience scheduling staff across changing priorities
Experience managing a team of direct reports
Strong decision-making skills

Desirable:
Experience in a regulated environment

Working pattern: Monday to Friday
Salary: £48,000
""",
        "must": {
            "essential": ["scheduling staff", "managing a team", "decision-making"],
            "desirable": ["regulated environment"],
            "practical": ["working pattern"],
        },
        "never": ["salary: £48,000"],
    },
    {
        "id": "field-engineer",
        "advert": """
Field Service Engineer

What you'll need:
Full UK driving licence required
Experience diagnosing electrical faults
Experience using test equipment
Ability to work independently

Travel:
Regional travel required with occasional overnight stays

Benefits:
Company vehicle
Private medical insurance
""",
        "must": {
            "eligibility": ["full uk driving licence"],
            "essential": ["diagnosing electrical faults", "test equipment", "work independently"],
            "practical": ["regional travel", "overnight stays"],
        },
        "never": ["company vehicle", "private medical insurance"],
    },
]


def _texts(items, category):
    return [item["text"].casefold() for item in items if item["category"] == category]


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_golden_vacancy_matrix(case):
    items = deterministic_extract(case["advert"])
    combined = "\n".join(item["text"].casefold() for item in items)

    for category, fragments in case.get("must", {}).items():
        texts = _texts(items, category)
        for fragment in fragments:
            assert any(fragment.casefold() in text for text in texts), (
                f"{case['id']}: expected {fragment!r} in {category}, got {texts}"
            )

    for fragment in case.get("never", []):
        assert fragment.casefold() not in combined, (
            f"{case['id']}: forbidden fragment leaked into extracted items: {fragment!r}"
        )


def test_golden_matrix_has_cross_sector_coverage():
    ids = {case["id"] for case in CASES}
    assert {
        "security-patrol",
        "custody-driver",
        "compliance-analyst",
        "customer-success",
        "hr-advisor",
        "learning-development",
        "operations-manager",
        "field-engineer",
    } <= ids
