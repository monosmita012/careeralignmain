"""Explainable skill-gap priority and Career Readiness Score calculations."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import math
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

try:
    from .skill_gap_analysis import UnknownTargetRoleError
except ImportError:  # Support ``python backend/career_alignment.py``.
    from skill_gap_analysis import UnknownTargetRoleError


DEFAULT_INDUSTRY_TWIN = (
    Path(__file__).resolve().parent
    / "data/processed/careeralign_industry_skill_twin.parquet"
)

# Priority-score formula: 70% priority tier, 20% observed role frequency,
# and 10% role association. The association contribution is capped at a ratio
# of 2.0 so a rare skill with an unstable high ratio cannot dominate.
_PRIORITY_POINTS = {
    "core": 100.0,
    "common": 75.0,
    "supporting": 50.0,
    "occasional": 25.0,
}
_PRIORITY_SCORE_WEIGHTS = {
    "priority_tier": 0.70,
    "role_frequency": 0.20,
    "role_association": 0.10,
}
_ASSOCIATION_RATIO_CAP = 2.0

# Readiness points: matched earns all tier points, partial earns one half,
# missing earns zero. Higher observed priority tiers have higher weights.
_READINESS_POINTS = {
    "core": 4.0,
    "common": 3.0,
    "supporting": 2.0,
    "occasional": 1.0,
}
_PARTIAL_CREDIT = 0.5


def _read_industry_rows(
    industry_skill_twin: str | Path | Iterable[Mapping[str, Any]] | None,
) -> list[dict[str, Any]]:
    if industry_skill_twin is None:
        path = DEFAULT_INDUSTRY_TWIN
        if not path.is_file():
            raise FileNotFoundError(f"Industry Skill Twin not found: {path}")
        return pq.read_table(path).to_pylist()
    if isinstance(industry_skill_twin, (str, Path)):
        path = Path(industry_skill_twin)
        if not path.is_file():
            raise FileNotFoundError(f"Industry Skill Twin not found: {path}")
        return pq.read_table(path).to_pylist()
    rows = list(industry_skill_twin)
    if any(not isinstance(row, Mapping) for row in rows):
        raise ValueError("Industry Skill Twin rows must be mappings.")
    return [dict(row) for row in rows]


def _positive_gaps(
    skill_gap_result: Mapping[str, Any],
    industry_skill_twin: str | Path | Iterable[Mapping[str, Any]] | None = None,
) -> tuple[str, dict[str, dict[str, Any]]]:
    if not isinstance(skill_gap_result, Mapping):
        raise ValueError("Skill Gap Analysis result must be a mapping.")
    role = skill_gap_result.get("target_role")
    if not isinstance(role, str) or not role.strip():
        raise UnknownTargetRoleError("Skill Gap Analysis result has no target role.")
    role = role.strip()

    gap_by_skill: dict[str, dict[str, Any]] = {}
    for group_name, gap_type in (("matched_skills", "matched"), ("partial_skills", "partial"), ("missing_skills", "missing")):
        items = skill_gap_result.get(group_name, [])
        if not isinstance(items, list):
            raise ValueError(f"{group_name} must be a list.")
        for item in items:
            if not isinstance(item, Mapping) or not isinstance(item.get("skill"), str):
                raise ValueError(f"Invalid skill entry in {group_name}.")
            frequency = item.get("role_frequency_percentage")
            if not isinstance(frequency, (int, float)) or not math.isfinite(float(frequency)) or not 0 <= frequency <= 100:
                raise ValueError(f"Invalid industry frequency for {item.get('skill')!r}.")
            if frequency <= 0:
                # Defensively ignore complete-matrix placeholders.
                continue
            skill = item["skill"]
            if skill in gap_by_skill:
                raise ValueError(f"Skill {skill!r} appears more than once in Skill Gap Analysis groups.")
            row = dict(item)
            row["gap_type"] = gap_type
            gap_by_skill[skill] = row

    rows = _read_industry_rows(industry_skill_twin)
    roles = {row.get("career_role") for row in rows if row.get("career_role")}
    if role not in roles:
        available = ", ".join(sorted(str(value) for value in roles))
        raise UnknownTargetRoleError(f"Unknown target role {role!r}. Available roles: {available}.")
    industry_by_skill: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("career_role") != role:
            continue
        frequency = row.get("role_frequency_percentage")
        if not isinstance(frequency, (int, float)) or not math.isfinite(float(frequency)) or not 0 <= frequency <= 100:
            raise ValueError(f"Invalid Industry Skill Twin frequency for {row.get('skill')!r}.")
        if frequency <= 0:
            continue
        skill = row.get("skill")
        if not isinstance(skill, str) or skill in industry_by_skill:
            raise ValueError(f"Invalid or duplicate Industry Skill Twin skill: {skill!r}.")
        industry_by_skill[skill] = dict(row)
    if set(industry_by_skill) != set(gap_by_skill):
        raise ValueError("Skill Gap Analysis positive-frequency skills do not match the supplied Industry Skill Twin.")
    for skill, gap in gap_by_skill.items():
        # Keep student-side evidence/reasons while taking industry metrics
        # from the explicit Industry Skill Twin input.
        industry = industry_by_skill[skill]
        gap.update({
            "category": industry.get("category", gap.get("category")),
            "role_frequency_percentage": float(industry["role_frequency_percentage"]),
            "role_association_ratio": float(industry.get("role_association_ratio") or 0.0),
            "priority": industry.get("priority"),
        })

    for skill, gap in gap_by_skill.items():
        priority = gap.get("priority")
        if priority not in _PRIORITY_POINTS:
            raise ValueError(f"Invalid Industry Skill Twin priority for {skill!r}: {priority!r}")
        ratio = gap.get("role_association_ratio")
        if not isinstance(ratio, (int, float)) or not math.isfinite(float(ratio)) or ratio < 0:
            raise ValueError(f"Invalid role association ratio for {skill!r}: {ratio!r}")
    return role, gap_by_skill


def _priority_score(gap: Mapping[str, Any]) -> float:
    priority_component = _PRIORITY_POINTS[gap["priority"]]
    frequency_component = float(gap["role_frequency_percentage"])
    association = min(float(gap["role_association_ratio"]), _ASSOCIATION_RATIO_CAP)
    association_component = (association / _ASSOCIATION_RATIO_CAP) * 100
    score = (
        _PRIORITY_SCORE_WEIGHTS["priority_tier"] * priority_component
        + _PRIORITY_SCORE_WEIGHTS["role_frequency"] * frequency_component
        + _PRIORITY_SCORE_WEIGHTS["role_association"] * association_component
    )
    return round(score, 2)


def prioritize_skill_gaps(
    skill_gap_result: Mapping[str, Any],
    industry_skill_twin: str | Path | Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Prioritize missing and partial skills using observed role evidence.

    The score is an explainable project heuristic, not an industry-standard
    benchmark. It uses the existing priority tier, role frequency percentage,
    and association ratio; no new industry importance is inferred.
    """
    role, gaps = _positive_gaps(skill_gap_result, industry_skill_twin)
    output = []
    for skill, gap in gaps.items():
        if gap["gap_type"] == "matched":
            continue
        frequency = float(gap["role_frequency_percentage"])
        ratio = float(gap["role_association_ratio"])
        base = _PRIORITY_POINTS[gap["priority"]]
        score = _priority_score(gap)
        gap_type = gap["gap_type"]
        reasons = gap.get("partial_reasons", []) if gap_type == "partial" else []
        state = "; evidence is partial" + (f" ({', '.join(reasons)})" if reasons else "") if gap_type == "partial" else ""
        reason = (
            f"{gap_type.capitalize()} {gap['priority']} skill{state}: present in "
            f"{frequency:.2f}% of {role} descriptions; association ratio {ratio:.2f}x. "
            f"Priority-tier component: {base:.0f}/100."
        )
        output.append({
            "skill": skill,
            "category": gap.get("category"),
            "gap_type": gap_type,
            "industry_frequency_percentage": frequency,
            "industry_priority": gap["priority"],
            "priority_score": score,
            "priority_label": gap["priority"],
            "role_association_ratio": ratio,
            "reason": reason,
        })
    output.sort(key=lambda item: (-item["priority_score"], -item["industry_frequency_percentage"], item["skill"]))
    return {
        "target_role": role,
        "prioritized_gaps": output,
        "missing_count": sum(item["gap_type"] == "missing" for item in output),
        "partial_count": sum(item["gap_type"] == "partial" for item in output),
        "priority_formula": "0.70 * tier_points + 0.20 * role_frequency_percentage + 0.10 * min(role_association_ratio, 2.0) / 2.0 * 100; tier points: core=100, common=75, supporting=50, occasional=25.",
        "score_note": "A deterministic project heuristic based on observed CareerAlign dataset evidence; not an industry-standard benchmark.",
    }


def calculate_career_readiness(
    skill_gap_result: Mapping[str, Any],
    industry_skill_twin: str | Path | Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Calculate an explainable 0–100 Career Readiness Score.

    Formula: 100 × (matched tier points + 0.5 × partial tier points) /
    total tier points, with core=4, common=3, supporting=2, occasional=1.
    Only positive-frequency observed skills contribute.
    """
    role, gaps = _positive_gaps(skill_gap_result, industry_skill_twin)
    components = []
    earned_points = 0.0
    possible_points = 0.0
    counts = {"matched": 0, "partial": 0, "missing": 0}

    for skill in sorted(gaps):
        gap = gaps[skill]
        gap_type = gap["gap_type"]
        weight = _READINESS_POINTS[gap["priority"]]
        possible_points += weight
        if gap_type == "matched":
            counts["matched"] += 1
            earned = weight
        elif gap_type == "partial":
            counts["partial"] += 1
            earned = weight * _PARTIAL_CREDIT
        else:
            counts["missing"] += 1
            earned = 0.0
        earned_points += earned
        components.append({
            "skill": skill,
            "gap_type": gap_type,
            "priority": gap["priority"],
            "weight_points": weight,
            "earned_points": earned,
            "role_frequency_percentage": float(gap["role_frequency_percentage"]),
        })

    available = possible_points > 0
    score = round((earned_points / possible_points) * 100, 2) if available else None
    return {
        "target_role": role,
        "career_readiness_score": score,
        "score_available": available,
        "score_status": "scored" if available else "no_positive_frequency_role_skills",
        "matched_count": counts["matched"],
        "partial_count": counts["partial"],
        "missing_count": counts["missing"],
        "total_positive_frequency_skills": len(gaps),
        "earned_weight_points": round(earned_points, 4),
        "possible_weight_points": round(possible_points, 4),
        "priority_weights": dict(_READINESS_POINTS),
        "partial_credit_factor": _PARTIAL_CREDIT,
        "score_formula": "100 * (sum(matched priority weights) + 0.5 * sum(partial priority weights)) / sum(all positive-frequency role-skill priority weights). Missing skills earn 0.",
        "components": components,
        "interpretation": "Career Readiness Score describes skill alignment with observed job-description evidence for the selected role; it is not a job, placement, or hiring probability.",
    }


def build_career_alignment(
    skill_gap_result: Mapping[str, Any],
    industry_skill_twin: str | Path | Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return prioritized gaps and the Career Readiness Score together."""
    priorities = prioritize_skill_gaps(skill_gap_result, industry_skill_twin)
    readiness = calculate_career_readiness(skill_gap_result, industry_skill_twin)
    return {
        "target_role": skill_gap_result.get("target_role"),
        "prioritized_gaps": priorities["prioritized_gaps"],
        "priority_formula": priorities["priority_formula"],
        "career_readiness": readiness,
    }
