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
- Hybrid working experience is essential for this role.

Working arrangements: Hybrid
"""

    items = deterministic_extract(advert)
    essentials = [item for item in items if item["category"] == "essential"]
    practical = [item for item in items if item["category"] == "practical"]

    assert any("coordinating a hybrid schedule" in item["text"].lower() for item in essentials)
    assert any("managing hybrid working arrangements" in item["text"].lower() for item in essentials)
    assert any("hybrid working experience is essential" in item["text"].lower() for item in essentials)
    assert not any("hybrid schedule" in item["text"].lower() for item in practical)
    assert not any("hybrid working arrangements" in item["text"].lower() for item in practical)
    assert not any("hybrid working experience" in item["text"].lower() for item in practical)
    assert any("working arrangements: hybrid" in item["text"].lower() for item in practical)


PARKGUARD_PATROL_SMOKE = """
Patrol Officer

Role Requirements:
Valid SIA Door Supervisor or Close Protection Licence
A Valid UK Driver’s Licence & own means of transport
Able and willing to work unsocial hours (between 11:30am-03:00am dependent on shift)
Excellent spoken & written English language skills – Ability to communicate effectively with the public and external organisations. Computer Literacy is essential for writing accurate reports and communicating via Email both internally and externally.
A good level of understanding of Criminal Law and an ability to learn policy, process and required, specific legislation
Be physically fit and able to patrol on foot and work from a vehicle for the duration of each shift, with ability to deal with confrontational, volatile and physical incidents as and when required
Be compassionate and motivated to support and help the public.
Excellent personal presentation.
Be able to self-task and take responsibility for service delivery and development.
All successful candidates will be required to undergo Full Police Vetting.

Full, comprehensive and in-depth training will be provided to all successful candidates.

Ideal Candidates & Experience:
Police/Law Enforcement
Security (SIA)
Bailiff
Close Protection
Military
Enforcement
Community Safety / Community Safety Accreditation (CSAS)

Salary: £15+/PH
Working Days: 5 day week variable (Friday, Saturday & Sundays priority days with longer shifts)
Shifts: Predominantly late turn between 11:30am - 02:30am
Total hours per week: Contracted hours are 45hrs per week with overtime available
Job Types: Full-time, Permanent
Pay: From £15.00 per hour
Work Location: In person
"""


def test_parkguard_pattern_extracts_role_requirements_without_leaking_metadata():
    items = deterministic_extract(PARKGUARD_PATROL_SMOKE)
    essentials = [item for item in items if item["category"] == "essential"]
    desirables = [item for item in items if item["category"] == "desirable"]
    eligibility = [item for item in items if item["category"] == "eligibility"]
    practical = [item for item in items if item["category"] == "practical"]
    trainable = [item for item in items if item["category"] == "trainable"]
    combined = "\n".join(item["text"].lower() for item in items)

    assert len(essentials) >= 6
    assert any("criminal law" in item["text"].lower() for item in essentials)
    assert any("self-task" in item["text"].lower() for item in essentials)
    assert any("compassionate" in item["text"].lower() for item in essentials)
    assert any("sia" in item["text"].lower() for item in eligibility)
    assert any("driver" in item["text"].lower() for item in eligibility)
    assert any("police vetting" in item["text"].lower() for item in eligibility)
    assert len(eligibility) == 3
    assert len(desirables) >= 5
    assert any("community safety" in item["text"].lower() for item in desirables)
    assert any("working days" in item["text"].lower() for item in practical)
    assert any("shifts:" in item["text"].lower() for item in practical)
    assert any("45hrs" in item["text"].lower() for item in practical)
    assert any("training will be provided" in item["text"].lower() for item in trainable)
    assert "salary: £15+/ph" not in combined
    assert "pay: from £15.00 per hour" not in combined


def test_schedule_words_inside_experience_criteria_stay_essential():
    advert = """
Operations Manager

Role Requirements:
Experience scheduling staff across working days and changing priorities
Experience calculating contracted hours for payroll reporting

Working Days: Monday to Friday
Shifts: 08:00-16:00
"""

    items = deterministic_extract(advert)
    essentials = [item["text"].lower() for item in items if item["category"] == "essential"]
    practical = [item["text"].lower() for item in items if item["category"] == "practical"]

    assert any("scheduling staff across working days" in item for item in essentials)
    assert any("calculating contracted hours" in item for item in essentials)
    assert any(item.startswith("working days:") for item in practical)
    assert any(item.startswith("shifts:") for item in practical)


def test_benefits_section_does_not_become_candidate_criteria():
    advert = """
Patrol Officer

Role Requirements:
Excellent spoken and written communication skills
Be able to self-task and take responsibility for service delivery.

Benefits of working for Parkguard Ltd:
28 Days Paid Annual Leave
Enhanced Bank Holiday Pay
Free Parking on shift
Company Pension Scheme
Employee Wellness Program
Full Uniform & Kit (Made to Measure)
One to One & Online Training Courses

Ideal Candidates & Experience:
Police/Law Enforcement
Security (SIA)
"""

    items = deterministic_extract(advert)
    combined = "\n".join(item["text"].lower() for item in items)

    assert "excellent spoken and written communication skills" in combined
    assert "police/law enforcement" in combined
    assert "28 days paid annual leave" not in combined
    assert "enhanced bank holiday pay" not in combined
    assert "free parking on shift" not in combined
    assert "company pension scheme" not in combined
    assert "employee wellness program" not in combined
    assert "full uniform & kit" not in combined
    assert "one to one & online training courses" not in combined


SERCO_PCO_SMOKE = """
Prisoner Escort & Custody Driver

We operate 24/6 across early and late shifts, so flexibility is essential. Finishing times can be unpredictable, and you may need to work beyond your contracted hours to meet operational demands. Shifts are set on a rota provided 12 weeks in advance. Part-time working may be considered, but this must be across full working days, as reduced daily hours are not available.

What you need to do the job!

Our PCOs come from a range of backgrounds. In return you'll receive full training through a 5½-week paid training.

Requirements of the role:
Full UK driving licence essential - B1/C1 (subject to requirements)
C1 Licenses holders should ideally hold a valid CPC
Reasonable fitness for the physical demands of the role
Strong communication skills (written and verbal)
Ability to stay calm and make decisions under pressure
Confidence managing behaviour and de-escalating conflict
Teamwork and the ability to follow processes accurately
Professionalism, integrity, and respect for confidentiality

What we offer
Holidays and pension

Our recruitment process
Initial right to work and vetting documentation checks

Eligibility checks and further information
Job offers are subject to Ministry of Justice Enhanced Level 2 checks with Enhanced Disclosure and Barring Service (DBS) clearance, satisfactory employment references and occupational health checks.
This role is not eligible for Skilled Worker visa sponsorship under current UK Home Office regulations. You must have the right to work in the UK.
"""


def test_serco_pco_pattern_extracts_real_requirements_and_practical_fit():
    items = deterministic_extract(SERCO_PCO_SMOKE)
    essentials = [item for item in items if item["category"] == "essential"]
    desirables = [item for item in items if item["category"] == "desirable"]
    eligibility = [item for item in items if item["category"] == "eligibility"]
    practical = [item for item in items if item["category"] == "practical"]
    trainable = [item for item in items if item["category"] == "trainable"]

    essential_text = "\n".join(item["text"].lower() for item in essentials)
    desirable_text = "\n".join(item["text"].lower() for item in desirables)
    eligibility_text = "\n".join(item["text"].lower() for item in eligibility)
    practical_text = "\n".join(item["text"].lower() for item in practical)
    trainable_text = "\n".join(item["text"].lower() for item in trainable)

    assert len(essentials) >= 6
    assert "strong communication skills" in essential_text
    assert "stay calm and make decisions under pressure" in essential_text
    assert "de-escalating conflict" in essential_text
    assert "teamwork" in essential_text
    assert "respect for confidentiality" in essential_text
    assert "valid cpc" in desirable_text
    assert "valid cpc" not in essential_text

    assert "full uk driving licence essential" in eligibility_text
    assert "disclosure and barring service" in eligibility_text
    assert "employment references" in eligibility_text
    assert "occupational health checks" in eligibility_text
    assert "right to work in the uk" in eligibility_text

    assert "24/6 across early and late shifts" in practical_text
    assert "work beyond your contracted hours" in practical_text
    assert "rota provided 12 weeks in advance" in practical_text

    assert "receive full training" in trainable_text
    assert not any("24/6 across early and late shifts" in item["text"].lower() for item in essentials)


def test_hr_experience_with_employment_references_stays_essential():
    advert = """
HR Advisor

Requirements of the role:
Experience preparing employment references for candidates
Experience supporting recruitment campaigns
"""
    items = deterministic_extract(advert)
    essentials = [item["text"].lower() for item in items if item["category"] == "essential"]
    eligibility = [item["text"].lower() for item in items if item["category"] == "eligibility"]

    assert any("preparing employment references" in item for item in essentials)
    assert not any("preparing employment references" in item for item in eligibility)


def test_paid_training_delivery_experience_stays_essential():
    advert = """
Learning and Development Officer

Requirements of the role:
Experience delivering paid training programmes to employees
Strong written communication skills
"""
    items = deterministic_extract(advert)
    essentials = [item["text"].lower() for item in items if item["category"] == "essential"]
    trainable = [item["text"].lower() for item in items if item["category"] == "trainable"]

    assert any("delivering paid training programmes" in item for item in essentials)
    assert not any("delivering paid training programmes" in item for item in trainable)


def test_inline_requirements_heading_is_split_from_trainable_sentence():
    advert = """
Prisoner Escort Officer

What you need to do the job!
You will receive full training through a paid induction, plus ongoing support. Requirements of the role:
Strong communication skills
Ability to stay calm under pressure
"""

    items = deterministic_extract(advert)
    trainable = [item["text"] for item in items if item["category"] == "trainable"]
    essentials = [item["text"] for item in items if item["category"] == "essential"]

    assert any("receive full training" in item.lower() for item in trainable)
    assert all("requirements of the role" not in item.lower() for item in trainable)
    assert "Strong communication skills" in essentials
    assert "Ability to stay calm under pressure" in essentials
