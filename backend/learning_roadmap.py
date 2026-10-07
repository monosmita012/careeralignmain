"""Rule-based personalized learning roadmap from CareerAlign evidence.

Prerequisite edges are explicit CareerAlign project rules, not universal
industry standards. The map is deliberately small and can be extended after
human review. Keys are dependent skills and values are their prerequisites.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import heapq
import math
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

try:
    from .skill_gap_analysis import UnknownTargetRoleError
    from .skill_taxonomy import SKILL_TAXONOMY, normalize_skill
    from .student_skill_twin import (
        CONFIDENCE_LEVELS,
        PROFICIENCY_LEVELS,
        SOURCE_TYPES,
        InvalidEvidenceError,
        UnknownSkillError,
    )
except ImportError:  # Support ``python backend/learning_roadmap.py``.
    from skill_gap_analysis import UnknownTargetRoleError
    from skill_taxonomy import SKILL_TAXONOMY, normalize_skill
    from student_skill_twin import (
        CONFIDENCE_LEVELS,
        PROFICIENCY_LEVELS,
        SOURCE_TYPES,
        InvalidEvidenceError,
        UnknownSkillError,
    )


DEFAULT_INDUSTRY_TWIN = (
    Path(__file__).resolve().parent
    / "data/processed/careeralign_industry_skill_twin.parquet"
)

# Explicit, limited rules: dependent skill -> prerequisites.
PREREQUISITE_MAP: dict[str, tuple[str, ...]] = {
    "React": ("JavaScript",),
    "Node.js": ("JavaScript",),
    "Express.js": ("Node.js",),
    "Apache Spark": ("Python", "SQL"),
    "Apache Airflow": ("Python",),
    "Docker": ("Linux",),
    "Kubernetes": ("Docker",),
}

_SKILL_ORDER = {item.canonical_name: index for index, item in enumerate(SKILL_TAXONOMY)}
_CATEGORY = {item.canonical_name: item.category for item in SKILL_TAXONOMY}
_PRIORITY_ORDER = {"core": 4, "common": 3, "supporting": 2, "occasional": 1}
_STRONG_PROFICIENCY = {"intermediate", "advanced", "expert"}


class PrerequisiteCycleError(ValueError):
    """Raised when the configured prerequisite rules contain a cycle."""


def _load_industry_rows(
    industry_skill_twin: str | Path | Iterable[Mapping[str, Any]] | None,
) -> list[dict[str, Any]]:
    if industry_skill_twin is None:
        path = DEFAULT_INDUSTRY_TWIN
        if not path.is_file():
            raise FileNotFoundError(f"Industry Skill Twin not found: {path}")
        return pq.read_table(path, columns=["career_role", "skill", "category", "role_frequency_percentage", "priority"]).to_pylist()
    if isinstance(industry_skill_twin, (str, Path)):
        path = Path(industry_skill_twin)
        if not path.is_file():
            raise FileNotFoundError(f"Industry Skill Twin not found: {path}")
        return pq.read_table(path, columns=["career_role", "skill", "category", "role_frequency_percentage", "priority"]).to_pylist()
    rows = list(industry_skill_twin)
    if any(not isinstance(row, Mapping) for row in rows):
        raise ValueError("Industry Skill Twin rows must be mappings.")
    return [dict(row) for row in rows]


def _normalize_prerequisite_map(
    prerequisite_map: Mapping[str, Iterable[str]] | None,
) -> dict[str, tuple[str, ...]]:
    raw = PREREQUISITE_MAP if prerequisite_map is None else prerequisite_map
    result: dict[str, tuple[str, ...]] = {}
    for dependent_raw, prerequisite_values in raw.items():
        dependent = normalize_skill(dependent_raw) if isinstance(dependent_raw, str) else None
        if dependent is None:
            raise UnknownSkillError(f"Unknown dependent skill in prerequisite map: {dependent_raw!r}")
        if isinstance(prerequisite_values, str):
            prerequisite_values = (prerequisite_values,)
        prerequisites = []
        for prerequisite_raw in prerequisite_values:
            prerequisite = normalize_skill(prerequisite_raw) if isinstance(prerequisite_raw, str) else None
            if prerequisite is None:
                raise UnknownSkillError(f"Unknown prerequisite skill: {prerequisite_raw!r}")
            if prerequisite not in prerequisites:
                prerequisites.append(prerequisite)
        result[dependent] = tuple(sorted(prerequisites, key=lambda skill: _SKILL_ORDER[skill]))
    return result


def _assert_acyclic(prerequisites: Mapping[str, tuple[str, ...]]) -> None:
    state: dict[str, int] = {}

    def visit(skill: str, chain: list[str]) -> None:
        mark = state.get(skill, 0)
        if mark == 1:
            cycle_start = chain.index(skill) if skill in chain else 0
            cycle = chain[cycle_start:] + [skill]
            raise PrerequisiteCycleError("Prerequisite cycle detected: " + " -> ".join(cycle))
        if mark == 2:
            return
        state[skill] = 1
        chain.append(skill)
        for prerequisite in prerequisites.get(skill, ()):
            visit(prerequisite, chain)
        chain.pop()
        state[skill] = 2

    for skill in sorted(set(prerequisites) | {item for values in prerequisites.values() for item in values}, key=lambda value: _SKILL_ORDER[value]):
        visit(skill, [])


def _industry_requirements(
    target_role: str,
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    roles = {row.get("career_role") for row in rows if row.get("career_role")}
    if target_role not in roles:
        available = ", ".join(sorted(str(role) for role in roles))
        raise UnknownTargetRoleError(f"Unknown target role {target_role!r}. Available roles: {available}.")
    requirements: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("career_role") != target_role:
            continue
        raw_skill = row.get("skill")
        skill = normalize_skill(raw_skill) if isinstance(raw_skill, str) else None
        if skill is None:
            raise UnknownSkillError(f"Unknown Industry Skill Twin skill: {raw_skill!r}")
        frequency = row.get("role_frequency_percentage")
        if not isinstance(frequency, (int, float)) or not math.isfinite(float(frequency)) or not 0 <= frequency <= 100:
            raise ValueError(f"Invalid role frequency for {target_role}/{skill}: {frequency!r}")
        if frequency <= 0:
            continue
        if skill in requirements:
            raise ValueError(f"Duplicate Industry Skill Twin role/skill row: {target_role}/{skill}")
        priority = row.get("priority")
        if priority not in _PRIORITY_ORDER:
            raise ValueError(f"Invalid Industry Skill Twin priority for {skill}: {priority!r}")
        requirements[skill] = {
            "skill": skill,
            "category": row.get("category", _CATEGORY[skill]),
            "role_frequency_percentage": float(frequency),
            "priority": priority,
        }
    return requirements


def _student_strength(student_skill_twin: Iterable[Mapping[str, Any]]) -> tuple[set[str], set[str]]:
    present: set[str] = set()
    strongly_present: set[str] = set()
    for record in student_skill_twin:
        if not isinstance(record, Mapping):
            raise InvalidEvidenceError("Each Student Skill Twin record must be a mapping.")
        raw_skill = record.get("skill")
        skill = normalize_skill(raw_skill) if isinstance(raw_skill, str) else None
        if skill is None:
            raise UnknownSkillError(f"Unknown or empty student skill: {raw_skill!r}")
        present.add(skill)
        evidence_items = record.get("evidence") or []
        if not isinstance(evidence_items, (list, tuple)):
            raise InvalidEvidenceError(f"Evidence for {skill} must be a list.")
        for item in evidence_items:
            if not isinstance(item, Mapping):
                raise InvalidEvidenceError(f"Evidence item for {skill} must be a mapping.")
            source = item.get("source")
            text = item.get("evidence")
            proficiency = item.get("proficiency", "unknown")
            confidence = item.get("confidence", "low")
            basis = item.get("proficiency_basis", "not_provided")
            if source not in SOURCE_TYPES:
                raise InvalidEvidenceError(f"Invalid evidence source for {skill}: {source!r}")
            if not isinstance(text, str) or not text.strip():
                raise InvalidEvidenceError(f"Evidence for {skill} must be non-empty text.")
            if proficiency not in PROFICIENCY_LEVELS:
                raise InvalidEvidenceError(f"Invalid proficiency for {skill}: {proficiency!r}")
            if confidence not in CONFIDENCE_LEVELS:
                raise InvalidEvidenceError(f"Invalid confidence for {skill}: {confidence!r}")
            if (
                proficiency in _STRONG_PROFICIENCY
                and confidence in {"medium", "high"}
                and basis != "self_reported"
            ):
                strongly_present.add(skill)
    return present, strongly_present


def _collect_gap_entries(
    target_role: str,
    skill_gap_result: Mapping[str, Any],
    career_alignment: Mapping[str, Any] | None,
    requirements: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    if not isinstance(skill_gap_result, Mapping):
        raise ValueError("Skill Gap Analysis result must be a mapping.")
    gap_role = skill_gap_result.get("target_role")
    if gap_role is not None and gap_role != target_role:
        raise ValueError(f"Target role mismatch: requested {target_role!r}, Skill Gap Analysis has {gap_role!r}.")
    if career_alignment is not None:
        alignment_role = career_alignment.get("target_role")
        if alignment_role is not None and alignment_role != target_role:
            raise ValueError(f"Target role mismatch: requested {target_role!r}, Career Alignment has {alignment_role!r}.")

    aligned_by_skill: dict[str, dict[str, Any]] = {}
    if career_alignment is not None:
        for item in career_alignment.get("prioritized_gaps", []):
            if not isinstance(item, Mapping):
                raise ValueError("Career Alignment prioritized gaps must contain mappings.")
            raw_skill = item.get("skill")
            skill = normalize_skill(raw_skill) if isinstance(raw_skill, str) else None
            if skill is None:
                raise UnknownSkillError(f"Unknown skill in Career Alignment: {raw_skill!r}")
            if skill in requirements and item.get("gap_type") in {"missing", "partial"}:
                current = aligned_by_skill.get(skill)
                candidate = dict(item)
                if current is None or float(candidate.get("priority_score") or 0) > float(current.get("priority_score") or 0):
                    aligned_by_skill[skill] = candidate

    result: dict[str, dict[str, Any]] = {}
    for group, gap_type in (("missing_skills", "missing"), ("partial_skills", "partial")):
        entries = skill_gap_result.get(group, [])
        if not isinstance(entries, list):
            raise ValueError(f"{group} must be a list.")
        for item in entries:
            if not isinstance(item, Mapping):
                raise ValueError(f"Invalid item in {group}.")
            raw_skill = item.get("skill")
            skill = normalize_skill(raw_skill) if isinstance(raw_skill, str) else None
            if skill is None:
                raise UnknownSkillError(f"Unknown skill in Skill Gap Analysis: {raw_skill!r}")
            # Do not turn zero-frequency matrix rows or unrelated skills into steps.
            if skill not in requirements:
                continue
            merged = dict(requirements[skill])
            merged.update(dict(item))
            merged["skill"] = skill
            merged["gap_type"] = gap_type
            aligned = aligned_by_skill.get(skill, {})
            merged["priority_score"] = aligned.get("priority_score", merged.get("priority_score"))
            merged["reason"] = aligned.get("reason", merged.get("reason"))
            merged["priority_source"] = "career_alignment" if aligned else "industry_skill_twin"

            previous = result.get(skill)
            if previous is None:
                result[skill] = merged
            else:
                # Keep one canonical step. Partial wins a contradictory
                # duplicate because it carries actual student-side evidence.
                if gap_type == "partial":
                    merged["partial_reasons"] = item.get("partial_reasons", [])
                    result[skill] = merged
                elif previous.get("gap_type") == "partial":
                    continue
    # Alignment output may be provided without a corresponding grouped entry.
    for skill, aligned in aligned_by_skill.items():
        if skill in result:
            continue
        merged = dict(requirements[skill])
        merged.update({
            "skill": skill,
            "gap_type": aligned["gap_type"],
            "priority_score": aligned.get("priority_score"),
            "reason": aligned.get("reason"),
            "priority_source": "career_alignment",
        })
        result[skill] = merged
    return result


def generate_learning_roadmap(
    target_role: str,
    student_skill_twin: Iterable[Mapping[str, Any]],
    skill_gap_result: Mapping[str, Any],
    career_alignment: Mapping[str, Any] | None = None,
    industry_skill_twin: str | Path | Iterable[Mapping[str, Any]] | None = None,
    prerequisite_map: Mapping[str, Iterable[str]] | None = None,
) -> dict[str, Any]:
    """Create an ordered roadmap from role gaps and explicit prerequisites.

    Occasional industry gaps remain visible as optional steps. Their observed
    lower frequency does not make them mandatory. Strongly evidenced student
    prerequisites are listed as satisfied dependencies but do not become steps.
    """
    if not isinstance(target_role, str) or not target_role.strip():
        raise UnknownTargetRoleError("Target role must be a non-empty known role name.")
    target_role = target_role.strip()
    prerequisites = _normalize_prerequisite_map(prerequisite_map)
    _assert_acyclic(prerequisites)
    industry_rows = _load_industry_rows(industry_skill_twin)
    requirements = _industry_requirements(target_role, industry_rows)
    present, strongly_present = _student_strength(student_skill_twin)
    direct_gaps = _collect_gap_entries(target_role, skill_gap_result, career_alignment, requirements)

    # A clear conflict would otherwise create a contradictory roadmap.
    contradictory = sorted(set(direct_gaps) & strongly_present)
    if contradictory:
        raise ValueError(f"Skill Gap Analysis marks strongly evidenced skills as gaps: {contradictory}")

    nodes: dict[str, dict[str, Any]] = {}
    edges: set[tuple[str, str]] = set()  # prerequisite node -> dependent node
    expanded: set[str] = set()

    for skill, gap in direct_gaps.items():
        priority = gap["priority"]
        if priority not in _PRIORITY_ORDER:
            raise ValueError(f"Invalid priority for {skill}: {priority!r}")
        priority_score = gap.get("priority_score")
        if not isinstance(priority_score, (int, float)) or not math.isfinite(float(priority_score)):
            priority_score = float(_PRIORITY_ORDER[priority] * 100)
        reason = gap.get("reason") or (
            f"{gap['gap_type'].capitalize()} {priority} skill observed in "
            f"{gap['role_frequency_percentage']:.2f}% of {target_role} descriptions."
        )
        if priority == "occasional":
            reason += " Optional step because it is an occasional, lower-frequency observed skill."
        nodes[skill] = {
            "skill": skill,
            "skill_category": _CATEGORY[skill],
            "gap_type": gap["gap_type"],
            "priority": priority,
            "priority_score": float(priority_score),
            "priority_source": gap["priority_source"],
            "reason": reason,
            "prerequisites": [],
            "satisfied_prerequisites": [],
            "status": "in_progress" if gap["gap_type"] == "partial" else "not_started",
            "added_as_prerequisite": False,
            "optional": priority == "occasional",
            "industry_frequency_percentage": float(gap["role_frequency_percentage"]),
            "required_for": set(),
        }

    def ensure_prerequisites(skill: str, parent_priority: str, parent_score: float, parent_optional: bool) -> None:
        if skill in expanded:
            return
        expanded.add(skill)
        node = nodes[skill]
        direct_prerequisites = prerequisites.get(skill, ())
        node["prerequisites"] = list(direct_prerequisites)
        for prerequisite in direct_prerequisites:
            if prerequisite in strongly_present:
                node["satisfied_prerequisites"].append(prerequisite)
                continue
            if prerequisite not in nodes:
                nodes[prerequisite] = {
                    "skill": prerequisite,
                    "skill_category": _CATEGORY[prerequisite],
                    "gap_type": "partial" if prerequisite in present else None,
                    "priority": parent_priority,
                    "priority_score": parent_score,
                    "priority_source": "inherited_from_dependent",
                    "reason": (
                        f"Added as a prerequisite of {skill}; this dependency is an explicit "
                        "CareerAlign project rule, not a universal industry standard."
                    ),
                    "prerequisites": [],
                    "satisfied_prerequisites": [],
                    "status": "in_progress" if prerequisite in present else "not_started",
                    "added_as_prerequisite": True,
                    "optional": parent_optional,
                    "industry_frequency_percentage": None,
                    "required_for": set(),
                }
            prereq_node = nodes[prerequisite]
            prereq_node["required_for"].add(skill)
            if prereq_node["added_as_prerequisite"] and (
                _PRIORITY_ORDER[parent_priority] > _PRIORITY_ORDER[prereq_node["priority"]]
                or (
                    _PRIORITY_ORDER[parent_priority] == _PRIORITY_ORDER[prereq_node["priority"]]
                    and parent_score > prereq_node["priority_score"]
                )
            ):
                prereq_node["priority"] = parent_priority
                prereq_node["priority_score"] = parent_score
            if not parent_optional:
                prereq_node["optional"] = False
                optional_note = " Optional step because it is an occasional, lower-frequency observed skill."
                if prereq_node["reason"].endswith(optional_note):
                    prereq_node["reason"] = prereq_node["reason"][:-len(optional_note)] + (
                        " Required before a higher-priority dependent as an explicit project prerequisite."
                    )
            edges.add((prerequisite, skill))
            ensure_prerequisites(prerequisite, prereq_node["priority"], prereq_node["priority_score"], prereq_node["optional"])

    for skill in sorted(direct_gaps, key=lambda name: _SKILL_ORDER[name]):
        node = nodes[skill]
        ensure_prerequisites(skill, node["priority"], node["priority_score"], node["optional"])

    # If a generated prerequisite supports several dependents, inherit the
    # strongest dependent priority and make it mandatory if any dependent is.
    changed = True
    while changed:
        changed = False
        for prerequisite, dependent in sorted(edges):
            prerequisite_node = nodes[prerequisite]
            dependent_node = nodes[dependent]
            if not prerequisite_node["added_as_prerequisite"]:
                continue
            if (
                _PRIORITY_ORDER[dependent_node["priority"]] > _PRIORITY_ORDER[prerequisite_node["priority"]]
                or (
                    _PRIORITY_ORDER[dependent_node["priority"]] == _PRIORITY_ORDER[prerequisite_node["priority"]]
                    and dependent_node["priority_score"] > prerequisite_node["priority_score"]
                )
            ):
                prerequisite_node["priority"] = dependent_node["priority"]
                prerequisite_node["priority_score"] = dependent_node["priority_score"]
                changed = True
            if prerequisite_node["optional"] and not dependent_node["optional"]:
                prerequisite_node["optional"] = False
                changed = True

    # Stable Kahn ordering: satisfy prerequisite edges first; among currently
    # available steps, use priority score, then role frequency, then skill name.
    indegree = {skill: 0 for skill in nodes}
    children: dict[str, set[str]] = {skill: set() for skill in nodes}
    for prerequisite, dependent in edges:
        if dependent not in children[prerequisite]:
            children[prerequisite].add(dependent)
            indegree[dependent] += 1

    def ready_key(skill: str) -> tuple[float, float, int, str]:
        node = nodes[skill]
        frequency = node["industry_frequency_percentage"]
        return (
            -node["priority_score"],
            -(frequency if frequency is not None else 0.0),
            _SKILL_ORDER[skill],
            skill,
        )

    ready = [(ready_key(skill), skill) for skill, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    ordered: list[str] = []
    while ready:
        _, skill = heapq.heappop(ready)
        ordered.append(skill)
        for child in sorted(children[skill], key=lambda name: _SKILL_ORDER[name]):
            indegree[child] -= 1
            if indegree[child] == 0:
                heapq.heappush(ready, (ready_key(child), child))
    if len(ordered) != len(nodes):
        raise PrerequisiteCycleError("Prerequisite cycle detected while ordering roadmap steps.")

    steps = []
    for index, skill in enumerate(ordered, start=1):
        node = nodes[skill]
        reason = node["reason"]
        if node["added_as_prerequisite"] and node["optional"]:
            reason += " It is optional because it only supports occasional, lower-frequency gap steps."
        steps.append({
            "step": index,
            "skill": skill,
            "skill_category": node["skill_category"],
            "gap_type": node["gap_type"],
            "priority": node["priority"],
            "priority_score": round(node["priority_score"], 2),
            "priority_source": node["priority_source"],
            "industry_frequency_percentage": node["industry_frequency_percentage"],
            "reason": reason,
            "prerequisites": list(node["prerequisites"]),
            "satisfied_prerequisites": list(node["satisfied_prerequisites"]),
            "required_for": sorted(node["required_for"], key=lambda name: _SKILL_ORDER[name]),
            "added_as_prerequisite": node["added_as_prerequisite"],
            "optional": node["optional"],
            "status": node["status"],
        })

    return {
        "target_role": target_role,
        "steps": steps,
        "total_steps": len(steps),
        "optional_step_count": sum(step["optional"] for step in steps),
        "prerequisite_rule_note": "Prerequisites are explicit CareerAlign project rules and are not universal industry standards.",
        "employability_note": "This roadmap organizes skill-alignment work and does not guarantee employability.",
    }
