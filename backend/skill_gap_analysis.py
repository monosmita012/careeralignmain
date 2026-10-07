"""Explainable comparison of Student and Industry Skill Twin evidence."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

try:
    from .student_skill_twin import (
        CONFIDENCE_LEVELS,
        PROFICIENCY_LEVELS,
        SOURCE_TYPES,
        InvalidEvidenceError,
        UnknownSkillError,
    )
    from .skill_taxonomy import normalize_skill
except ImportError:  # Support ``python backend/skill_gap_analysis.py``.
    from student_skill_twin import (
        CONFIDENCE_LEVELS,
        PROFICIENCY_LEVELS,
        SOURCE_TYPES,
        InvalidEvidenceError,
        UnknownSkillError,
    )
    from skill_taxonomy import normalize_skill


DEFAULT_INDUSTRY_TWIN = (
    Path(__file__).resolve().parent
    / "data/processed/careeralign_industry_skill_twin.parquet"
)
_STRONG_PROFICIENCY = {"intermediate", "advanced", "expert"}
_UNCERTAIN_PROFICIENCY = {"exposure", "beginner", "unknown"}


class UnknownTargetRoleError(ValueError):
    """Raised when the target role is absent from the Industry Skill Twin."""


def _load_industry_rows(
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


def _industry_for_role(
    rows: list[dict[str, Any]], target_role: str
) -> tuple[dict[str, dict[str, Any]], set[str]]:
    roles = {row.get("career_role") for row in rows if row.get("career_role")}
    if target_role not in roles:
        available = ", ".join(sorted(str(role) for role in roles))
        raise UnknownTargetRoleError(
            f"Unknown target role {target_role!r}. Available roles: {available}."
        )

    requirements: dict[str, dict[str, Any]] = {}
    for row in rows:
        role = row.get("career_role")
        raw_skill = row.get("skill")
        skill = normalize_skill(raw_skill) if isinstance(raw_skill, str) else None
        if skill is None:
            raise UnknownSkillError(f"Industry Skill Twin has unknown skill: {raw_skill!r}")
        frequency = row.get("role_frequency_percentage")
        if not isinstance(frequency, (int, float)) or not 0 <= frequency <= 100:
            raise ValueError(f"Invalid role frequency for {role!r}/{skill!r}: {frequency!r}")
        if role != target_role or frequency <= 0:
            # A zero-frequency row is a matrix placeholder, not a requirement.
            continue
        if skill in requirements:
            raise ValueError(f"Duplicate Industry Skill Twin row for {target_role!r}/{skill!r}")
        requirements[skill] = {
            "skill": skill,
            "category": row.get("category"),
            "role_frequency_percentage": float(frequency),
            "role_association_ratio": float(row.get("role_association_ratio") or 0.0),
            "priority": row.get("priority"),
            "role_record_count": row.get("role_record_count"),
            "role_record_total": row.get("role_record_total"),
        }
    return requirements, roles


def _student_evidence_by_skill(
    student_skill_twin: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for record in student_skill_twin:
        if not isinstance(record, Mapping):
            raise InvalidEvidenceError("Each Student Skill Twin record must be a mapping.")
        raw_skill = record.get("skill")
        skill = normalize_skill(raw_skill) if isinstance(raw_skill, str) else None
        if skill is None:
            raise UnknownSkillError(f"Unknown or empty student skill: {raw_skill!r}")
        target = grouped.setdefault(skill, {"sources": set(), "evidence": set()})

        raw_sources = record.get("sources", [])
        if raw_sources is not None:
            if not isinstance(raw_sources, (list, tuple, set)):
                raise InvalidEvidenceError(f"Sources for {skill!r} must be a list.")
            for source in raw_sources:
                if source not in SOURCE_TYPES:
                    raise InvalidEvidenceError(f"Invalid source for {skill!r}: {source!r}")
                target["sources"].add(source)

        evidence_items = record.get("evidence", [])
        if evidence_items is None:
            evidence_items = []
        if not isinstance(evidence_items, (list, tuple)):
            raise InvalidEvidenceError(f"Evidence for {skill!r} must be a list.")
        for item in evidence_items:
            if not isinstance(item, Mapping):
                raise InvalidEvidenceError(f"Evidence item for {skill!r} must be a mapping.")
            source = item.get("source")
            evidence_text = item.get("evidence")
            proficiency = item.get("proficiency", "unknown")
            confidence = item.get("confidence", "low")
            basis = item.get("proficiency_basis", "not_provided")
            if source not in SOURCE_TYPES:
                raise InvalidEvidenceError(f"Invalid evidence source for {skill!r}: {source!r}")
            if not isinstance(evidence_text, str) or not evidence_text.strip():
                raise InvalidEvidenceError(f"Evidence for {skill!r} must be non-empty text.")
            if proficiency not in PROFICIENCY_LEVELS:
                raise InvalidEvidenceError(f"Invalid proficiency for {skill!r}: {proficiency!r}")
            if confidence not in CONFIDENCE_LEVELS:
                raise InvalidEvidenceError(f"Invalid confidence for {skill!r}: {confidence!r}")
            if not isinstance(basis, str):
                raise InvalidEvidenceError(f"Invalid proficiency basis for {skill!r}.")
            evidence = {
                "source": source,
                "evidence": evidence_text.strip(),
                "proficiency": proficiency,
                "proficiency_basis": basis,
                "confidence": confidence,
            }
            # Store evidence as a stable JSON key to merge duplicate student
            # records without duplicating evidence items.
            target["evidence"].add(
                json.dumps(evidence, ensure_ascii=False, sort_keys=True)
            )
            target["sources"].add(source)
    return grouped


def _ordered_evidence(items: set[str]) -> list[dict[str, Any]]:
    parsed = [json.loads(item) for item in items]
    source_order = {source: index for index, source in enumerate(SOURCE_TYPES)}
    return sorted(
        parsed,
        key=lambda item: (
            source_order[item["source"]],
            item["evidence"].casefold(),
            item["evidence"],
            item["proficiency"],
            item["confidence"],
            item["proficiency_basis"],
        ),
    )


def _classify_student_skill(student: dict[str, Any]) -> tuple[str, list[str], list[dict[str, Any]]]:
    evidence = _ordered_evidence(student["evidence"])
    usable = [item for item in evidence if item["evidence"].strip()]
    matched_by = [
        item
        for item in usable
        if item["proficiency"] in _STRONG_PROFICIENCY
        and item["confidence"] in {"medium", "high"}
        and item["proficiency_basis"] != "self_reported"
    ]
    if matched_by:
        return "matched", [], evidence

    reasons: set[str] = set()
    if not usable:
        reasons.add("no_usable_evidence")
    for item in usable:
        if item["proficiency"] in _UNCERTAIN_PROFICIENCY:
            reasons.add(f"proficiency_{item['proficiency']}")
        if item["confidence"] == "low":
            reasons.add("low_confidence")
        if item["proficiency_basis"] == "self_reported":
            reasons.add("self_reported_proficiency")
    return "partial", sorted(reasons), evidence


def analyze_skill_gap(
    student_skill_twin: Iterable[Mapping[str, Any]],
    target_role: str,
    industry_skill_twin: str | Path | Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compare student evidence with observed positive-frequency role skills.

    All positive-frequency skills for the selected role are included, including
    occasional skills. Zero-frequency rows in the complete matrix are ignored.
    A skill is matched only when at least one evidence item has intermediate,
    advanced, or expert proficiency, medium/high association confidence, and
    is not self-reported-only. Present but weaker or uncertain evidence is
    partial; a role skill with no student entry is missing.
    """
    if not isinstance(target_role, str) or not target_role.strip():
        raise UnknownTargetRoleError("Target role must be a non-empty known role name.")
    target_role = target_role.strip()
    industry_rows = _load_industry_rows(industry_skill_twin)
    requirements, _ = _industry_for_role(industry_rows, target_role)
    student_by_skill = _student_evidence_by_skill(student_skill_twin)

    matched: list[dict[str, Any]] = []
    partial: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []

    for skill in sorted(requirements):
        industry = requirements[skill]
        student = student_by_skill.get(skill)
        if student is None:
            missing.append(dict(industry))
            continue

        classification, reasons, evidence = _classify_student_skill(student)
        item = {
            **industry,
            "student_sources": sorted(student["sources"], key=SOURCE_TYPES.index),
            "student_evidence": evidence,
        }
        if classification == "matched":
            matched.append(item)
        else:
            item["partial_reasons"] = reasons
            partial.append(item)

    result = {
        "target_role": target_role,
        "matched_skills": matched,
        "partial_skills": partial,
        "missing_skills": missing,
        "matched_count": len(matched),
        "partial_count": len(partial),
        "missing_count": len(missing),
    }
    return result
