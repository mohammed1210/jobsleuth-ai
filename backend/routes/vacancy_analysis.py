"""Evidence-based vacancy analysis route."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from lib.evidence_matching import deterministic_match, has_personal_management_scope, rank_evidence, requires_personal_management_scope
from lib.evidence_semantic_batch import semantic_assess_batch
from routes.candidate_profile import CandidateProfileData
from routes.saved_jobs import verify_supabase_user

router = APIRouter(prefix="/vacancy-analysis", tags=["vacancy_analysis"])


class Requirement(BaseModel):
    text: str
    category: Literal["eligibility", "essential", "desirable", "trainable"] = "essential"
    blocker: bool = False
    eligibility_answer: Literal["yes", "no", "unsure"] | None = None


class Evidence(BaseModel):
    id: str | None = None
    title: str = ""
    situation: str = ""
    task: str = ""
    tags: list[str] = Field(default_factory=list)
    behaviours: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    outcome: str = ""
    reflection: str = ""
    authority_context: str | None = None
    confidence: int = Field(default=70, ge=0, le=100)


class AnalysisRequest(BaseModel):
    job: dict[str, Any]
    requirements: list[Requirement] = Field(default_factory=list)
    evidence_cards: list[Evidence] = Field(default_factory=list)
    candidate_profile: CandidateProfileData | None = None
    practical_issues: list[str] = Field(default_factory=list)


def _status_for_strength(strength: str, category: str) -> str:
    if category == "trainable":
        return "trainable"
    if strength == "strong":
        return "met"
    if strength == "partial":
        return "partial"
    return "gap"


def _evidence_payload(card: Evidence, assessment: dict[str, Any]) -> dict[str, Any]:
    signals = assessment.get("signals", {})
    return {
        "id": card.id,
        "title": card.title,
        "strength": assessment["strength"],
        "score": assessment["score"],
        "confidence": assessment["confidence"],
        "why": assessment["why"],
        "gaps": assessment.get("gaps", []),
        "supporting_facts": assessment.get("supporting_facts", []),
        "signals": signals,
        "matched_terms": signals.get("matched_terms", []),
    }


def _profile_evidence(profile: CandidateProfileData) -> list[Evidence]:
    cards: list[Evidence] = []
    qualification_names = [item.name for item in profile.qualifications if item.name]
    for index, item in enumerate(profile.experience):
        title = item.role or "CV experience"
        if item.organisation:
            title = f"{title} at {item.organisation}"
        cards.append(
            Evidence(
                id=f"cv-profile-{index}",
                title=title,
                situation=item.dates,
                task=item.role,
                actions=item.highlights,
                tags=[],
                skills=[],
                confidence=55,
            )
        )
    if profile.skills or profile.qualifications or profile.summary:
        cards.append(
            Evidence(
                id="cv-profile-overview",
                title="CV qualifications and skills",
                situation=profile.summary,
                actions=qualification_names,
                tags=qualification_names,
                skills=profile.skills,
                confidence=50,
            )
        )
    return cards


def _criterion_specific_cv_source(requirement: str, card: Evidence) -> dict[str, Any] | None:
    if not str(card.id).startswith("cv-profile-") or str(card.id) == "cv-profile-overview":
        return None

    ranked_actions: list[tuple[float, str]] = []
    for action in card.actions or []:
        action_card = Evidence(
            id="cv-action",
            title="",
            situation="",
            task="",
            actions=[action],
            skills=[],
            tags=[],
            confidence=50,
        )
        assessment = deterministic_match(requirement, action_card)
        if assessment.get("strength") != "missing":
            ranked_actions.append((float(assessment.get("score", 0.0)), action))

    ranked_actions.sort(key=lambda item: item[0], reverse=True)
    actions = [action for _score, action in ranked_actions[:4]]
    if not actions:
        return None

    action_probe = Evidence(
        id="cv-action-probe",
        title="",
        situation="",
        task="",
        actions=actions,
        skills=[],
        tags=[],
        confidence=50,
    )
    probe = deterministic_match(requirement, action_probe)
    matched_terms = list(probe.get("signals", {}).get("matched_terms", []))

    return {
        "title": card.title,
        "situation": card.situation,
        "task": card.task,
        "actions": actions,
        "skills": matched_terms[:8],
    }


def _profile_support(requirement: str, profile: CandidateProfileData | None) -> dict[str, Any] | None:
    if profile is None:
        return None
    cards = _profile_evidence(profile)
    if not cards:
        return None
    ranked = rank_evidence(requirement, cards)
    if not ranked:
        return None
    card, assessment = ranked[0]
    conversion_source = _criterion_specific_cv_source(requirement, card)

    # Prefer a role-specific CV card when its own action bullets independently
    # support the criterion. Generic profile skills remain a signal, but they
    # should not hide a stronger grounded role example or masquerade as one.
    if conversion_source is None:
        for candidate, candidate_assessment in ranked[1:]:
            candidate_source = _criterion_specific_cv_source(requirement, candidate)
            if candidate_source is not None:
                card = candidate
                assessment = candidate_assessment
                conversion_source = candidate_source
                break

    strength = assessment.get("strength", "missing")
    if requires_personal_management_scope(requirement) and not has_personal_management_scope(card):
        strength = "weak" if strength in {"strong", "partial"} else strength
    elif strength == "strong":
        strength = "partial"

    if strength == "missing":
        return None

    signals = assessment.get("signals", {})
    return {
        "strength": strength,
        "score": min(float(assessment.get("score", 0.0)), 69.0 if strength == "partial" else 39.0),
        "confidence": min(float(assessment.get("confidence", 0.0)), 0.7),
        "title": card.title,
        "why": (
            "The CV profile contains related experience or skills, but CV shorthand is treated as a signal rather than verified Evidence Bank proof."
        ),
        "matched_terms": signals.get("matched_terms", []),
        "source": conversion_source,
    }


@router.post("")
async def vacancy_analysis(request: AnalysisRequest, authorization: str | None = Header(None)) -> dict[str, Any]:
    await verify_supabase_user(authorization)

    ranked_by_index: dict[int, list[tuple[Evidence, dict[str, Any]]]] = {}
    ambiguous_entries: list[tuple[int, str, list[Evidence]]] = []
    for index, requirement in enumerate(request.requirements):
        if requirement.category in {"eligibility", "trainable"}:
            continue
        ranked = rank_evidence(requirement.text, request.evidence_cards)
        ranked_by_index[index] = ranked
        top_strength = ranked[0][1]["strength"] if ranked else "missing"
        if top_strength != "strong" and ranked:
            ambiguous_entries.append((index, requirement.text, [card for card, _assessment in ranked[:3]]))

    semantic_by_index = semantic_assess_batch(ambiguous_entries) or {}
    semantic_used = bool(semantic_by_index)
    analysed: list[dict[str, Any]] = []

    for index, requirement in enumerate(request.requirements):
        if requirement.category == "eligibility":
            answer = requirement.eligibility_answer
            if answer == "yes":
                analysed.append(
                    {
                        "requirement": requirement.text,
                        "category": "eligibility",
                        "blocker": True,
                        "status": "met",
                        "match_strength": "strong",
                        "confidence": 1.0,
                        "why": "You confirmed that you meet this mandatory eligibility requirement.",
                        "gaps": [],
                        "evidence": [],
                        "profile_support": None,
                    }
                )
            elif answer == "no":
                analysed.append(
                    {
                        "requirement": requirement.text,
                        "category": "eligibility",
                        "blocker": True,
                        "status": "not-met",
                        "match_strength": "missing",
                        "confidence": 1.0,
                        "why": "You confirmed that you do not currently meet this mandatory eligibility requirement.",
                        "gaps": ["This mandatory eligibility requirement is not met."],
                        "evidence": [],
                        "profile_support": None,
                    }
                )
            else:
                analysed.append(
                    {
                        "requirement": requirement.text,
                        "category": "eligibility",
                        "blocker": True,
                        "status": "unconfirmed",
                        "match_strength": "missing",
                        "confidence": 1.0,
                        "why": "Confirm whether you meet this mandatory eligibility requirement before relying on the recommendation.",
                        "gaps": ["Eligibility has not been confirmed."],
                        "evidence": [],
                        "profile_support": None,
                    }
                )
            continue

        if requirement.category == "trainable":
            analysed.append(
                {
                    "requirement": requirement.text,
                    "category": requirement.category,
                    "blocker": requirement.blocker,
                    "status": "trainable",
                    "match_strength": "trainable",
                    "confidence": 1.0,
                    "why": "The vacancy identifies this as trainable rather than requiring existing evidence.",
                    "gaps": [],
                    "evidence": [],
                }
            )
            continue

        ranked = ranked_by_index.get(index, [])
        semantic = semantic_by_index.get(index, {})
        merged: list[tuple[Evidence, dict[str, Any]]] = []
        for card, deterministic in ranked:
            assessment = semantic.get(str(card.id), deterministic)
            if (
                requires_personal_management_scope(requirement.text)
                and not has_personal_management_scope(card)
                and assessment.get("strength") in {"strong", "partial"}
            ):
                assessment = dict(assessment)
                assessment["strength"] = "weak"
                assessment["score"] = min(float(assessment.get("score", 0.0)), 39.0)
                gaps = list(assessment.get("gaps", []))
                management_gap = "The evidence does not demonstrate management or supervisory responsibility at the required level."
                if management_gap not in gaps:
                    gaps.append(management_gap)
                assessment["gaps"] = gaps[:3]
                assessment["why"] = (
                    "Related operational evidence is recorded, but the candidate's own management or supervisory responsibility is not demonstrated."
                )
            merged.append((card, assessment))
        merged.sort(key=lambda item: item[1]["score"], reverse=True)

        useful = [(card, assessment) for card, assessment in merged if assessment["strength"] != "missing"]
        evidence = [_evidence_payload(card, assessment) for card, assessment in useful[:3]]
        top_assessment = merged[0][1] if merged else {
            "strength": "missing",
            "score": 0.0,
            "confidence": 0.9,
            "why": "No Evidence Cards are available for this requirement.",
            "gaps": ["No relevant evidence is recorded for this requirement."],
        }

        profile_support = _profile_support(requirement.text, request.candidate_profile)
        strength = top_assessment["strength"]
        why = top_assessment["why"]
        confidence = top_assessment["confidence"]
        gaps = list(top_assessment.get("gaps", []))

        if (
            profile_support
            and not requirement.blocker
            and profile_support["strength"] == "partial"
            and strength in {"weak", "missing"}
        ):
            strength = "partial"
            why = profile_support["why"]
            confidence = profile_support["confidence"]
            cv_gap = "Add or strengthen an Evidence Bank example to verify the CV signal before drafting against this criterion."
            if cv_gap not in gaps:
                gaps.insert(0, cv_gap)
            gaps = gaps[:3]

        analysed.append(
            {
                "requirement": requirement.text,
                "category": requirement.category,
                "blocker": requirement.blocker,
                "status": _status_for_strength(strength, requirement.category),
                "match_strength": strength,
                "confidence": confidence,
                "why": why,
                "gaps": gaps,
                "evidence": evidence,
                "profile_support": profile_support,
            }
        )

    eligibility_not_met = any(
        item["category"] == "eligibility" and item["status"] == "not-met"
        for item in analysed
    )
    eligibility_unconfirmed = any(
        item["category"] == "eligibility" and item["status"] == "unconfirmed"
        for item in analysed
    )
    hard_gap = any(
        item["blocker"] and item["match_strength"] in {"weak", "missing"}
        for item in analysed
        if item["category"] not in {"trainable", "eligibility"}
    )
    essential_uncertainty = any(
        item["category"] == "essential" and item["match_strength"] in {"partial", "weak", "missing"}
        for item in analysed
    )

    if eligibility_not_met or hard_gap:
        decision = "SKIP"
    elif eligibility_unconfirmed or essential_uncertainty or request.practical_issues:
        decision = "CONSIDER"
    else:
        decision = "APPLY"

    decision_reasons: list[str] = []
    if eligibility_not_met:
        decision_reasons.append("At least one mandatory eligibility requirement is not met.")
    if eligibility_unconfirmed:
        decision_reasons.append("Mandatory eligibility still needs to be confirmed.")
    if hard_gap:
        decision_reasons.append("At least one explicit blocker lacks sufficient supporting evidence.")
    if essential_uncertainty:
        decision_reasons.append("At least one essential requirement is only partially supported or has an evidence gap.")
    if request.practical_issues:
        decision_reasons.append("Practical fit still needs checking.")
    if decision == "APPLY":
        decision_reasons.append("Essential requirements are strongly supported by the recorded Evidence Bank.")

    return {
        "ok": True,
        "analysis_provider": "hybrid-semantic-v2" if semantic_used else "structured-evidence-v2",
        "decision": decision,
        "decision_reasons": decision_reasons,
        "requirements": analysed,
        "practical_fit": {
            "status": "concern" if request.practical_issues else "fit",
            "issues": request.practical_issues,
        },
    }
