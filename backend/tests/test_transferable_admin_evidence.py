"""Regression for transferable evidence in generic office and reception roles."""
from fastapi.testclient import TestClient

from backend.lib.evidence_matching import deterministic_match
from backend.main import app
from backend.routes.vacancy_analysis import Evidence

client = TestClient(app)
HEADERS = {"Authorization": "Bearer valid_token"}


def workload_card() -> Evidence:
    return Evidence(
        id="workload",
        title="Managing operational and office workload",
        situation="A duty manager balanced planned staff tasks and unexpected operational demands.",
        task="I needed to organise the team and keep reporting work moving.",
        actions=[
            "I prioritised urgent staffing reports and planned the team's daily task allocations.",
            "I adapted to frequent operational interruptions, alternating between team check-ins and urgent duties.",
            "I tracked unfinished administrative tasks and resumed them when quieter periods allowed.",
        ],
        outcome="The team received its daily allocations and my reporting work was usually up to date across each week.",
    )


def admin_card() -> Evidence:
    return Evidence(
        id="admin",
        title="Administrative records and spreadsheets",
        situation="I supported routine reporting and staff administration.",
        task="Maintain records and share accurate information with colleagues.",
        actions=[
            "I used spreadsheets to compile staffing figures, track rosters and prepare regular reports.",
            "I updated sickness records and arranged training meetings using Outlook.",
        ],
        outcome="Reports and updated staffing records were made available for daily planning.",
    )


def accuracy_card() -> Evidence:
    return Evidence(
        id="accuracy",
        title="Auditing staff absence records",
        situation="An audit identified a discrepancy in a staff record.",
        task="Find the source of the discrepancy and correct the record.",
        actions=[
            "I cross-checked roster records against the absence management system.",
            "I reviewed supporting emails, identified a document recorded against the wrong date and corrected the records.",
        ],
        outcome="The records were corrected and the staff member was informed.",
    )


def communication_card() -> Evidence:
    return Evidence(
        id="communication",
        title="Guiding colleagues from another organisation",
        situation="Visiting colleagues were unfamiliar with specialist workplace terms.",
        task="Explain the process and refer questions to the right contact.",
        actions=[
            "I explained the process in simpler language to the visiting team.",
            "I liaised with the site manager and informed the visitors of the relevant contact.",
        ],
        outcome="The visitors understood the requirements and made a more informed decision.",
    )


def telephone_card() -> Evidence:
    return Evidence(
        id="telephone",
        title="Maintaining welfare contact",
        situation="A colleague was due to return after a long absence.",
        task="Keep the colleague informed about workplace changes.",
        actions=[
            "I maintained weekly phone calls and emails to answer the colleague's questions.",
        ],
        outcome="The colleague felt reassured about returning to work.",
    )


def test_organisation_is_supported_by_planning_real_work_without_exact_label():
    match = deterministic_match("Excellent organisational skills", workload_card())
    assert match["strength"] == "strong"
    assert "recorded personal actions" in match["why"]


def test_administration_is_supported_by_real_system_and_record_tasks():
    match = deterministic_match("Administration experience", admin_card())
    assert match["strength"] == "strong"
    assert "administrative" in match["why"]


def test_flexibility_is_supported_by_adjusting_to_operational_interruptions():
    match = deterministic_match("Flexibility and a can-do approach to meet changing needs and priorities", workload_card())
    assert match["strength"] == "strong"


def test_attention_to_detail_without_deadlines_in_same_example_is_not_full_proof():
    match = deterministic_match("Attention to detail and ability to work to deadlines", accuracy_card())
    assert match["strength"] in {"partial", "weak"}
    assert match["strength"] != "strong"


def test_telephone_welfare_calls_do_not_prove_confident_reception_call_handling():
    match = deterministic_match("Confident telephone manner", telephone_card())
    assert match["strength"] in {"partial", "weak"}
    assert match["strength"] != "strong"


def test_communication_needs_actions_not_bare_labels():
    match = deterministic_match(
        "Outstanding communication skills with the ability to liaise with staff, students and visitors",
        communication_card(),
    )
    assert match["strength"] in {"partial", "strong"}
    assert "personal actions" in match["why"]


def test_bare_administration_label_is_never_strong():
    card = Evidence(id="label", title="Administration experience", skills=["administration experience"])
    assert deterministic_match("Administration experience", card)["strength"] != "strong"


def test_unrelated_security_actions_are_not_administrative_evidence():
    card = Evidence(
        id="risk", title="Operational risk review",
        situation="A shipment needed to be assessed.",
        task="Review operational risk.",
        actions=["I assessed physical security risks and consulted colleagues on options."],
        outcome="The shipment was moved safely.",
    )
    assert deterministic_match("Administration experience", card)["strength"] in {"weak", "missing"}


def test_receptionist_fixture_with_semantic_fallback(monkeypatch):
    monkeypatch.setattr("routes.vacancy_analysis.semantic_assess_batch", lambda _entries: None)
    requirements = [
        "Excellent organisational skills",
        "Outstanding communication skills with the ability to liaise with staff, students and visitors",
        "Confident telephone manner",
        "Attention to detail and ability to work to deadlines",
        "Ability to work independently and as part of a team",
        "Administration experience",
        "Flexibility and a can-do approach to meet changing needs and priorities",
    ]
    response = client.post(
        "/vacancy-analysis", headers=HEADERS,
        json={
            "job": {"title": "Afternoon Receptionist"},
            "requirements": [{"text": text, "category": "essential"} for text in requirements],
            "evidence_cards": [
                card.model_dump()
                for card in [workload_card(), admin_card(), accuracy_card(), communication_card(), telephone_card()]
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()
    strength = {r["requirement"]: r["match_strength"] for r in data["requirements"]}
    assert strength[requirements[0]] == "strong"
    assert strength[requirements[5]] == "strong"
    assert strength[requirements[6]] == "strong"
    assert strength[requirements[2]] != "strong"
    assert data["analysis_provider"] == "structured-evidence-v2"


def test_technical_system_administration_is_not_office_administration():
    for requirement in (
        "Experience with Linux system administration",
        "Database administration experience",
        "Network administration experience",
        "Cloud infrastructure administration experience",
    ):
        match = deterministic_match(requirement, admin_card())
        assert match["strength"] in {"weak", "missing"}, (requirement, match)


def test_watching_a_manager_do_admin_is_not_personal_administration_experience():
    card = Evidence(
        id="observer",
        title="Shadowing a manager",
        situation="I shadowed the reporting process for training.",
        task="Observe the manager compiling staffing returns.",
        actions=["I observed while my manager compiled staffing reports and updated the roster."],
        outcome="The manager completed the staffing report.",
    )
    match = deterministic_match("Administration experience", card)
    assert match["strength"] in {"weak", "missing"}


def test_observing_others_organise_work_is_not_organisational_achievement():
    card = Evidence(
        id="observer-workload",
        title="Shadowing another team",
        situation="I was present while another team planned its work.",
        task="Observe the process.",
        actions=["I watched as the team manager allocated shifts and organised team tasks."],
        outcome="The manager allocated work for the team.",
    )
    assert deterministic_match("Excellent organisational skills", card)["strength"] != "strong"


def test_stating_planning_skill_is_not_a_planning_action():
    card = Evidence(
        id="claims", title="Generic skills",
        situation="I applied for office work.",
        task="Describe my skills.",
        actions=["I have good planning skills and staff organisation."],
        outcome="I completed the form.",
    )
    assert deterministic_match("Excellent organisational skills", card)["strength"] != "strong"


def test_email_only_communication_cannot_prove_telephone_manner():
    card = Evidence(
        id="email", title="Email update",
        situation="Colleagues needed written guidance.",
        task="Provide updates.",
        actions=["I explained the process by email to colleagues."],
        outcome="Colleagues were informed.",
    )
    match = deterministic_match("Confident telephone manner and excellent communication skills", card)
    assert match["strength"] != "strong"
    assert any("telephone enquiries" in gap for gap in match["gaps"])


def test_missing_deadline_cannot_be_converted_into_success():
    card = Evidence(
        id="late", title="Careful late correction",
        situation="A reporting file contained an error.",
        task="Identify the cause and update records.",
        actions=["I reviewed records, corrected errors and reported the discrepancy."],
        outcome="The records were corrected but I missed the deadline.",
    )
    match = deterministic_match("Attention to detail and ability to work to deadlines", card)
    assert match["strength"] != "strong"
    assert any("deadline" in gap for gap in match["gaps"])


def test_accuracy_only_reason_does_not_claim_deadline_delivery():
    match = deterministic_match("Attention to detail", accuracy_card())
    assert match["strength"] == "strong"
    assert "delivering work on time" not in match["why"]


def test_compound_accuracy_and_deadline_may_be_strong_when_both_are_proved():
    card = Evidence(
        id="timely-audit", title="Auditing time-critical records",
        situation="A daily report had a midday deadline.",
        task="Verify records and share a correct update.",
        actions=[
            "I cross-checked records against the audit log and corrected discrepancies.",
            "I updated the verified reporting file before midday.",
        ],
        outcome="The accurate report was updated before midday for the planning team.",
    )
    assert deterministic_match(
        "Attention to detail and ability to work to deadlines", card
    )["strength"] == "strong"


def test_handling_enquiries_by_email_does_not_prove_telephone_manner():
    card = Evidence(
        id="email-enquiries", title="Written enquiry handling",
        situation="I supported an office inbox.",
        task="Respond to customer queries in writing.",
        actions=["I handled customer enquiries by email."],
        outcome="The customers received their email replies.",
    )
    match = deterministic_match("Confident telephone manner", card)
    assert match["strength"] != "strong"
    assert any("telephone" in gap for gap in match["gaps"])


def test_actual_handling_of_telephone_calls_can_be_supported():
    card = Evidence(
        id="phone-enquiries", title="Handling telephone enquiries",
        situation="I was responsible for a customer service phone line.",
        task="Answer callers' questions accurately and politely.",
        actions=["I answered incoming telephone calls and handled customers' questions."],
        outcome="Callers received the information they needed.",
    )
    match = deterministic_match("Confident telephone manner", card)
    assert match["strength"] == "strong"


def test_submission_after_deadline_is_not_treated_as_timely():
    card = Evidence(
        id="too-late", title="Late report correction",
        situation="A staff report contained discrepancies and was due by midday.",
        task="Check the records and update the report.",
        actions=[
            "I reviewed records and corrected errors.",
            "I updated the reporting file.",
        ],
        outcome="The accurate report was submitted after the deadline.",
    )
    match = deterministic_match("Attention to detail and ability to work to deadlines", card)
    assert match["strength"] != "strong"
    assert any("deadline" in gap for gap in match["gaps"])


def test_office_work_does_not_prove_business_admin_credential():
    for criterion in (
        "Level 3 qualification in Business Administration",
        "Recognised Business Administration diploma",
        "Business Administration certification",
    ):
        strength = deterministic_match(criterion, admin_card())["strength"]
        assert strength != "strong", (criterion, strength)
