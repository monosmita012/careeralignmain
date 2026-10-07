"""Deterministic project recommendations for prioritized CareerAlign skill gaps."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

try:
    from .skill_gap_analysis import (
        DEFAULT_INDUSTRY_TWIN,
        UnknownTargetRoleError,
        _classify_student_skill,
        _student_evidence_by_skill,
    )
    from .skill_taxonomy import normalize_skill
    from .student_skill_twin import UnknownSkillError
except ImportError:  # Support ``python backend/project_recommendation.py``.
    from skill_gap_analysis import (
        DEFAULT_INDUSTRY_TWIN,
        UnknownTargetRoleError,
        _classify_student_skill,
        _student_evidence_by_skill,
    )
    from skill_taxonomy import normalize_skill
    from student_skill_twin import UnknownSkillError


@dataclass(frozen=True)
class LearningProject:
    project_id: str
    title: str
    description: str
    difficulty: str
    skills: tuple[str, ...]
    project_type: str
    reason_template: str


# A deliberately compact, static catalog; it does not create assignments or
# contact external services.
PROJECT_CATALOG: tuple[LearningProject, ...] = (
    LearningProject("data-analysis-dashboard", "Data Analysis Dashboard", "Analyze a well-structured dataset, write SQL queries, and present findings in a dashboard.", "beginner", ("Python", "SQL", "Power BI", "Tableau"), "analytics_dashboard", "Builds {skills} through a practical data-analysis dashboard."),
    LearningProject("etl-data-pipeline", "ETL Data Pipeline", "Build a repeatable pipeline that extracts, transforms, and loads data, with scheduled workflow runs.", "intermediate", ("Python", "SQL", "Apache Airflow"), "data_pipeline", "Builds {skills} by implementing and scheduling an ETL pipeline."),
    LearningProject("big-data-processing", "Big Data Processing Pipeline", "Process structured data with a distributed Spark job and package the workflow in containers.", "intermediate", ("Python", "SQL", "Apache Spark", "Docker"), "data_pipeline", "Builds {skills} through distributed data processing and containerization."),
    LearningProject("cloud-data-engineering", "Cloud Data Engineering Pipeline", "Design a small cloud-hosted data workflow with scheduled orchestration and containerized components.", "advanced", ("Python", "SQL", "AWS", "Apache Airflow", "Docker"), "cloud_data_pipeline", "Builds {skills} by implementing a cloud-based data engineering workflow."),
    LearningProject("full-stack-web-app", "Full Stack Web Application", "Create a small web application with a React interface, Node.js API, persistent storage, and version control.", "intermediate", ("JavaScript", "React", "Node.js", "Express.js", "MongoDB", "Git"), "web_application", "Builds {skills} across a complete web application."),
    LearningProject("containerized-web-app", "Containerized Web Application", "Package a simple service in containers and deploy it to a local Kubernetes environment using Git.", "intermediate", ("Docker", "Kubernetes", "Git"), "cloud_native_application", "Builds {skills} through containerization and orchestration."),
    LearningProject("automated-web-testing", "Automated Web Testing Framework", "Create browser-based regression tests and organize the test code in a version-controlled project.", "intermediate", ("Java", "Selenium", "Test Automation", "Git"), "test_automation", "Builds {skills} by implementing a maintainable automated testing framework."),
    LearningProject("linux-server-monitoring", "Linux Server Monitoring Project", "Write a small monitoring utility for Linux hosts and run it in a basic cloud environment.", "intermediate", ("Linux", "Python", "AWS"), "systems_monitoring", "Builds {skills} by creating and operating a server-monitoring utility."),
)

_PRIORITY_POINTS = {"core": 4, "common": 3, "supporting": 2, "occasional": 1}
_DEFAULT_ROLE_PATH = Path(DEFAULT_INDUSTRY_TWIN)


def _known_roles() -> set[str]:
    if not _DEFAULT_ROLE_PATH.is_file():
        raise FileNotFoundError(f"Industry Skill Twin not found: {_DEFAULT_ROLE_PATH}")
    return {
        role for role in pq.read_table(_DEFAULT_ROLE_PATH, columns=["career_role"])
        .column("career_role").to_pylist() if role
    }


def _normalize_gap_items(
    target_role: str,
    skill_gap_result: Mapping[str, Any] | None,
    prioritized_gaps: Mapping[str, Any] | Iterable[Mapping[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    gaps: dict[str, dict[str, Any]] = {}

    def add(items: Any, inferred_type: str | None = None) -> None:
        if items is None:
            return
        if not isinstance(items, list):
            raise ValueError("Skill gap groups must be lists of mappings.")
        for item in items:
            if not isinstance(item, Mapping):
                raise ValueError("Each skill gap must be a mapping.")
            raw_skill = item.get("skill")
            skill = normalize_skill(raw_skill) if isinstance(raw_skill, str) else None
            if skill is None:
                raise UnknownSkillError(f"Unknown or empty gap skill: {raw_skill!r}")
            gap_type = item.get("gap_type") or inferred_type
            if gap_type not in {"missing", "partial"}:
                continue
            record = gaps.setdefault(skill, {"skill": skill, "gap_type": gap_type})
            # If duplicate entries disagree, partial is the cautious state.
            if gap_type == "partial":
                record["gap_type"] = "partial"
            labels = [item.get("industry_priority"), item.get("priority_label"), item.get("priority")]
            valid_labels = [label for label in labels if label in _PRIORITY_POINTS]
            if valid_labels:
                record["priority"] = max(valid_labels, key=lambda label: _PRIORITY_POINTS[label])
            score = item.get("priority_score")
            if isinstance(score, (int, float)):
                record["priority_score"] = max(float(score), float(record.get("priority_score", score)))

    if skill_gap_result is not None:
        if not isinstance(skill_gap_result, Mapping):
            raise ValueError("Skill Gap Analysis result must be a mapping.")
        input_role = skill_gap_result.get("target_role")
        if input_role is not None and input_role != target_role:
            raise ValueError(f"Target role mismatch: requested {target_role!r}, input has {input_role!r}.")
        add(skill_gap_result.get("missing_skills", []), "missing")
        add(skill_gap_result.get("partial_skills", []), "partial")

    if prioritized_gaps is not None:
        if isinstance(prioritized_gaps, Mapping):
            input_role = prioritized_gaps.get("target_role")
            if input_role is not None and input_role != target_role:
                raise ValueError(f"Target role mismatch: requested {target_role!r}, input has {input_role!r}.")
            items = prioritized_gaps.get("prioritized_gaps", [])
        else:
            items = list(prioritized_gaps)
        add(items)

    return gaps


def _strong_student_skills(student_skill_twin: Iterable[Mapping[str, Any]] | None) -> set[str]:
    if student_skill_twin is None:
        return set()
    # Reuse the same evidence validation and possession definition as Skill Gap Analysis.
    grouped = _student_evidence_by_skill(student_skill_twin)
    return {
        skill for skill, student in grouped.items()
        if _classify_student_skill(student)[0] == "matched"
    }


def _validate_catalog() -> None:
    ids: set[str] = set()
    for project in PROJECT_CATALOG:
        if project.project_id in ids:
            raise ValueError(f"Duplicate project id: {project.project_id}")
        ids.add(project.project_id)
        if project.difficulty not in {"beginner", "intermediate", "advanced"}:
            raise ValueError(f"Invalid project difficulty: {project.difficulty}")
        if not project.skills or len(project.skills) != len(set(project.skills)):
            raise ValueError(f"Project skills must be non-empty and unique: {project.project_id}")
        if any(normalize_skill(skill) != skill for skill in project.skills):
            raise ValueError(f"Project has a non-canonical skill: {project.project_id}")


_validate_catalog()


def recommend_projects(
    target_role: str,
    skill_gap_result: Mapping[str, Any] | None = None,
    prioritized_gaps: Mapping[str, Any] | Iterable[Mapping[str, Any]] | None = None,
    student_skill_twin: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Rank catalog projects using 2× priority points for missing and 1× for partial.

    Priority tier points are core=4, common=3, supporting=2, occasional=1.
    A gap without a supplied tier gets 1 point, so absent evidence does not
    silently become high priority. This is a transparent project heuristic,
    not an industry-standard score. Ties retain catalog order.
    """
    if not isinstance(target_role, str) or not target_role.strip():
        raise UnknownTargetRoleError("Target role must be a non-empty known role name.")
    target_role = target_role.strip()
    roles = _known_roles()
    if target_role not in roles:
        raise UnknownTargetRoleError(
            f"Unknown target role {target_role!r}. Available roles: {', '.join(sorted(roles))}."
        )

    gaps = _normalize_gap_items(target_role, skill_gap_result, prioritized_gaps)
    strongly_present = _strong_student_skills(student_skill_twin)
    for skill in strongly_present:
        gaps.pop(skill, None)

    results = []
    for catalog_index, project in enumerate(PROJECT_CATALOG):
        addressed_missing = [skill for skill in project.skills if gaps.get(skill, {}).get("gap_type") == "missing"]
        addressed_partial = [skill for skill in project.skills if gaps.get(skill, {}).get("gap_type") == "partial"]
        if not addressed_missing and not addressed_partial:
            continue
        # Per-skill weighted points reward both breadth and higher-priority gaps;
        # missing gaps count twice as much as partial gaps of the same tier.
        score = sum(2 * _PRIORITY_POINTS.get(gaps[skill].get("priority"), 1) for skill in addressed_missing)
        score += sum(_PRIORITY_POINTS.get(gaps[skill].get("priority"), 1) for skill in addressed_partial)
        addressed_skills = addressed_missing + addressed_partial
        names = ", ".join(addressed_skills)
        priority_words = sorted({gaps[skill].get("priority", "unspecified-priority") for skill in addressed_skills})
        priority_note = f" ({', '.join(priority_words)} priority)" if priority_words != ["unspecified-priority"] else ""
        if addressed_missing and addressed_partial:
            gap_note = "missing and partial"
        elif addressed_missing:
            gap_note = "missing"
        else:
            gap_note = "partial"
        reason = (
            f"Recommended for {target_role} because this project develops {names}, "
            f"which are {gap_note} roadmap skills{priority_note}. "
            f"Score: {score} weighted gap points (missing=2×, partial=1×)."
        )
        results.append({
            "project_id": project.project_id,
            "title": project.title,
            "description": project.description,
            "difficulty": project.difficulty,
            "project_type": project.project_type,
            "addressed_missing_skills": addressed_missing,
            "addressed_partial_skills": addressed_partial,
            "score": score,
            "reason": reason,
            "_catalog_order": catalog_index,
        })

    results.sort(key=lambda item: (-item["score"], item["_catalog_order"]))
    for item in results:
        item.pop("_catalog_order")
    return {
        "target_role": target_role,
        "recommendations": results,
        "total_recommendations": len(results),
    }


__all__ = ["LearningProject", "PROJECT_CATALOG", "recommend_projects"]
