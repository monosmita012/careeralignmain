"""Source-aware Student Skill Twin records built from supplied skill evidence.

This module does not parse documents or infer a student's proficiency. Its
confidence values describe the supplied skill/evidence association only.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

try:
    from .skill_taxonomy import INFORMATIONAL_SKILLS, SKILL_TAXONOMY, normalize_skill
except ImportError:  # Support ``python backend/student_skill_twin.py``.
    from skill_taxonomy import INFORMATIONAL_SKILLS, SKILL_TAXONOMY, normalize_skill


SOURCE_TYPES = (
    "resume",
    "education",
    "syllabus",
    "project",
    "certification",
    "internship",
    "self_declared",
    "github",
)
PROFICIENCY_LEVELS = (
    "exposure",
    "beginner",
    "intermediate",
    "advanced",
    "expert",
    "unknown",
)
CONFIDENCE_LEVELS = ("low", "medium", "high")

_SOURCE_ORDER = {source: index for index, source in enumerate(SOURCE_TYPES)}
_SKILL_ORDER = {
    definition.canonical_name: index
    for index, definition in enumerate((*SKILL_TAXONOMY, *INFORMATIONAL_SKILLS))
}
_CATEGORY_BY_SKILL = {
    definition.canonical_name: definition.category
    for definition in (*SKILL_TAXONOMY, *INFORMATIONAL_SKILLS)
}


class UnknownSkillError(ValueError):
    """Raised when a skill is not an exact taxonomy name or alias."""


class InvalidEvidenceError(ValueError):
    """Raised when supplied evidence fields are invalid or incomplete."""


@dataclass(frozen=True)
class EvidenceItem:
    """One supplied piece of skill evidence with source-specific attributes."""

    source: str
    evidence: str
    proficiency: str
    proficiency_basis: str
    confidence: str

    def as_dict(self) -> dict[str, str]:
        return {
            "source": self.source,
            "evidence": self.evidence,
            "proficiency": self.proficiency,
            "proficiency_basis": self.proficiency_basis,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class StudentSkillRecord:
    """Merged evidence for one canonical skill.

    Proficiency and confidence are retained per evidence item rather than
    collapsed into one score. This preserves disagreement and provenance.
    """

    skill: str
    category: str
    sources: tuple[str, ...]
    evidence: tuple[EvidenceItem, ...]

    def as_dict(self) -> dict[str, Any]:
        evidence_items = [item.as_dict() for item in self.evidence]
        return {
            "skill": self.skill,
            "category": self.category,
            "sources": list(self.sources),
            "evidence": evidence_items,
            # These remain source-bound lists. No overall proficiency or
            # confidence is inferred when evidence differs across sources.
            "proficiency": [
                {
                    "source": item.source,
                    "level": item.proficiency,
                    "basis": item.proficiency_basis,
                }
                for item in self.evidence
            ],
            "confidence": [
                {"source": item.source, "level": item.confidence}
                for item in self.evidence
            ],
        }


def _validate_input(record: Mapping[str, Any]) -> tuple[str, EvidenceItem]:
    if not isinstance(record, Mapping):
        raise InvalidEvidenceError("Each evidence record must be a mapping.")

    raw_skill = record.get("skill")
    canonical = normalize_skill(raw_skill) if isinstance(raw_skill, str) else None
    if canonical is None:
        raise UnknownSkillError(f"Unknown or empty skill: {raw_skill!r}")

    source = record.get("source")
    if not isinstance(source, str) or source not in SOURCE_TYPES:
        raise InvalidEvidenceError(
            f"Invalid source {source!r}; expected one of {SOURCE_TYPES}."
        )

    evidence = record.get("evidence")
    if not isinstance(evidence, str) or not evidence.strip():
        raise InvalidEvidenceError("Evidence must be a non-empty supplied string.")

    if "proficiency" in record and record["proficiency"] is not None:
        proficiency = record["proficiency"]
        if not isinstance(proficiency, str) or proficiency not in PROFICIENCY_LEVELS:
            raise InvalidEvidenceError(
                f"Invalid proficiency {proficiency!r}; expected one of {PROFICIENCY_LEVELS}."
            )
        proficiency_basis = "self_reported" if source == "self_declared" else "provided_evidence"
    elif source in ("education", "syllabus"):
        # Coursework indicates exposure; it does not demonstrate practical skill.
        proficiency = "exposure"
        proficiency_basis = "source_default"
    else:
        # A bare mention or source association does not prove proficiency.
        proficiency = "unknown"
        proficiency_basis = "not_provided"

    confidence = record.get("confidence")
    if not isinstance(confidence, str) or confidence not in CONFIDENCE_LEVELS:
        raise InvalidEvidenceError(
            f"Invalid confidence {confidence!r}; expected one of {CONFIDENCE_LEVELS}."
        )

    return canonical, EvidenceItem(
        source=source,
        evidence=evidence.strip(),
        proficiency=proficiency,
        proficiency_basis=proficiency_basis,
        confidence=confidence,
    )


def merge_skill_evidence(
    records: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize and merge supplied evidence into one record per skill.

    Expected input fields are ``skill``, ``source``, ``evidence`` and
    ``confidence``. ``proficiency`` is optional. Unknown skills and invalid
    values raise explicit exceptions instead of creating arbitrary taxonomy
    entries. Exact duplicate evidence records are de-duplicated.
    """
    grouped: dict[str, set[EvidenceItem]] = {}
    for record in records:
        skill, evidence_item = _validate_input(record)
        grouped.setdefault(skill, set()).add(evidence_item)

    result: list[dict[str, Any]] = []
    for skill in sorted(grouped, key=lambda value: _SKILL_ORDER[value]):
        items = sorted(
            grouped[skill],
            key=lambda item: (
                _SOURCE_ORDER[item.source],
                item.evidence.casefold(),
                item.evidence,
                item.proficiency,
                item.proficiency_basis,
                item.confidence,
            ),
        )
        sources = tuple(sorted({item.source for item in items}, key=_SOURCE_ORDER.get))
        result.append(
            StudentSkillRecord(
                skill=skill,
                category=_CATEGORY_BY_SKILL[skill],
                sources=sources,
                evidence=tuple(items),
            ).as_dict()
        )
    return result
