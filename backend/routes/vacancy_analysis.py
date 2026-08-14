"""Evidence-based vacancy analysis route."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from lib.evidence_matching import rank_evidence
from lib.evidence_semantic_batch import semantic_assess_batch
from routes.saved_jobs import verify_supabase_user

router = APIRouter(prefix="/vacancy-analysis", tags=["vacancy_analysis"])


class Requirement(BaseModel):
    text: str
    category: Literal["essential", "desirable", "trainable"] = "essential"
    blocker: bool = False


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


@router.post("")
async def vacancy_analysis(request: AnalysisRequest, authorization: str | None = Header(None)) -> dict[str, Any]:
    await verify_supabase_user(authorization)

    ranked_by_index: dict[int, list[tuple[Evidence, dict[str, Any]]]] = {}
    ambiguous_entries: list[tuple[int, str, list[Evidence]]] = []
    for index, requirement in enumerate(request.requirements):
        if requirement.category == "trainable":
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

        strength = top_assessment["strength"]
        analysed.append(
            {
                "requirement": requirement.text,
                "category": requirement.category,
                "blocker": requirement.blocker,
                "status": _status_for_strength(strength, requirement.category),
                "match_strength": strength,
                "confidence": top_assessment["confidence"],
                "why": top_assessment["why"],
                "gaps": top_assessment.get("gaps", []),
                "evidence": evidence,
            }
        )

    hard_gap = any(
        item["blocker"] and item["match_strength"] in {"weak", "missing"}
        for item in analysed
        if item["category"] != "trainable"
    )
    essential_uncertainty = any(
        item["category"] == "essential" and item["match_strength"] in {"partial", "weak", "missing"}
        for item in analysed
    )

    if hard_gap:
        decision = "SKIP"
    elif essential_uncertainty or request.practical_issues:
        decision = "CONSIDER"
    else:
        decision = "APPLY"

    decision_reasons: list[str] = []
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
