"""Deterministic, catalog-based learning resource recommendations."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from typing import Any

try:
    from .skill_taxonomy import normalize_skill
    from .student_skill_twin import (
        CONFIDENCE_LEVELS,
        PROFICIENCY_LEVELS,
        SOURCE_TYPES,
        InvalidEvidenceError,
        UnknownSkillError,
    )
except ImportError:  # Support ``python backend/resource_recommendation.py``.
    from skill_taxonomy import normalize_skill
    from student_skill_twin import (
        CONFIDENCE_LEVELS,
        PROFICIENCY_LEVELS,
        SOURCE_TYPES,
        InvalidEvidenceError,
        UnknownSkillError,
    )


@dataclass(frozen=True)
class LearningResource:
    resource_id: str
    skill: str
    title: str
    resource_type: str
    level: str
    description: str
    url: str
    provider: str


# Small, curated catalog. URLs point to well-known public documentation or
# training pages; no network access or resource discovery occurs at runtime.
RESOURCE_CATALOG: tuple[LearningResource, ...] = (
    LearningResource("python-tutorial", "Python", "The Python Tutorial", "tutorial", "beginner", "An introduction to Python syntax and core language features.", "https://docs.python.org/3/tutorial/", "Python Documentation"),
    LearningResource("python-library-reference", "Python", "Python Standard Library", "documentation", "intermediate", "Reference material for Python's standard library.", "https://docs.python.org/3/library/", "Python Documentation"),
    LearningResource("sql-postgresql-tutorial", "SQL", "PostgreSQL Tutorial", "tutorial", "beginner", "A guided introduction to relational database concepts and SQL queries.", "https://www.postgresql.org/docs/current/tutorial.html", "PostgreSQL"),
    LearningResource("sql-postgresql-queries", "SQL", "Queries in PostgreSQL", "documentation", "intermediate", "Reference for writing and combining SQL queries.", "https://www.postgresql.org/docs/current/queries.html", "PostgreSQL"),
    LearningResource("javascript-mdn-guide", "JavaScript", "JavaScript Guide", "guide", "beginner", "A structured guide to JavaScript language fundamentals.", "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide", "MDN Web Docs"),
    LearningResource("javascript-mdn-reference", "JavaScript", "JavaScript Reference", "documentation", "intermediate", "A reference for JavaScript statements, operators, and objects.", "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference", "MDN Web Docs"),
    LearningResource("react-learn", "React", "Learn React", "tutorial", "beginner", "Official React lessons covering components, state, and composition.", "https://react.dev/learn", "React"),
    LearningResource("react-reference", "React", "React Reference", "documentation", "intermediate", "Reference pages for React APIs and built-in components.", "https://react.dev/reference/react", "React"),
    LearningResource("nodejs-learn", "Node.js", "Introduction to Node.js", "tutorial", "beginner", "An introduction to running JavaScript on the server with Node.js.", "https://nodejs.org/en/learn/getting-started/introduction-to-nodejs", "Node.js"),
    LearningResource("nodejs-api", "Node.js", "Node.js API Documentation", "documentation", "intermediate", "API reference for Node.js runtime modules.", "https://nodejs.org/api/", "Node.js"),
    LearningResource("express-start", "Express.js", "Express Installing and Getting Started", "tutorial", "beginner", "A quick start for creating an Express application.", "https://expressjs.com/en/starter/installing.html", "Express"),
    LearningResource("express-routing", "Express.js", "Express Routing Guide", "guide", "intermediate", "Learn how Express routes handle application requests.", "https://expressjs.com/en/guide/routing.html", "Express"),
    LearningResource("mongodb-manual-tutorial", "MongoDB", "MongoDB Manual Tutorials", "tutorial", "beginner", "Official tutorials for common MongoDB operations.", "https://www.mongodb.com/docs/manual/tutorial/", "MongoDB"),
    LearningResource("git-pro-book", "Git", "Pro Git Book", "guide", "beginner", "A free book introducing Git concepts and everyday workflows.", "https://git-scm.com/book/en/v2", "Git"),
    LearningResource("git-reference", "Git", "Git Reference", "documentation", "intermediate", "Reference documentation for Git commands and options.", "https://git-scm.com/docs", "Git"),
    LearningResource("docker-get-started", "Docker", "Docker Get Started", "tutorial", "beginner", "A guided introduction to container images and containers.", "https://docs.docker.com/get-started/", "Docker"),
    LearningResource("docker-build", "Docker", "Docker Build Documentation", "documentation", "intermediate", "Learn to build images and manage build processes with Docker.", "https://docs.docker.com/build/", "Docker"),
    LearningResource("kubernetes-tutorials", "Kubernetes", "Kubernetes Tutorials", "tutorial", "beginner", "Hands-on tutorials for deploying and managing applications.", "https://kubernetes.io/docs/tutorials/", "Kubernetes"),
    LearningResource("kubernetes-concepts", "Kubernetes", "Kubernetes Concepts", "documentation", "intermediate", "Core concepts for Kubernetes workloads and cluster resources.", "https://kubernetes.io/docs/concepts/", "Kubernetes"),
    LearningResource("spark-quick-start", "Apache Spark", "Spark Quick Start", "tutorial", "beginner", "A concise introduction to using Apache Spark.", "https://spark.apache.org/docs/latest/quick-start.html", "Apache Spark"),
    LearningResource("spark-sql-guide", "Apache Spark", "Spark SQL Guide", "documentation", "intermediate", "Guide to working with structured data using Spark SQL.", "https://spark.apache.org/docs/latest/sql-programming-guide.html", "Apache Spark"),
    LearningResource("airflow-quick-start", "Apache Airflow", "Airflow Quick Start", "tutorial", "beginner", "An introduction to creating and running Airflow DAGs.", "https://airflow.apache.org/docs/apache-airflow/stable/start.html", "Apache Airflow"),
    LearningResource("airflow-tutorial", "Apache Airflow", "Airflow Tutorial", "tutorial", "intermediate", "A practical tutorial for defining and scheduling workflows.", "https://airflow.apache.org/docs/apache-airflow/stable/tutorial/index.html", "Apache Airflow"),
    LearningResource("aws-skill-builder", "AWS", "AWS Skill Builder", "course", "beginner", "Self-paced learning paths and introductory courses for AWS services.", "https://skillbuilder.aws/", "Amazon Web Services"),
    LearningResource("aws-getting-started", "AWS", "Getting Started with AWS", "guide", "beginner", "Official entry points for learning AWS and starting with its services.", "https://aws.amazon.com/getting-started/", "Amazon Web Services"),
    LearningResource("linux-journey", "Linux", "Linux Journey", "tutorial", "beginner", "A free guided introduction to Linux command-line and system concepts.", "https://linuxjourney.com/", "Linux Journey"),
    LearningResource("selenium-webdriver-start", "Selenium", "Getting Started with WebDriver", "tutorial", "beginner", "Official setup guidance for browser automation using WebDriver.", "https://www.selenium.dev/documentation/webdriver/getting_started/", "Selenium"),
    LearningResource("selenium-test-practices", "Selenium", "Test Practices", "guide", "intermediate", "Guidance for maintainable automated browser tests.", "https://www.selenium.dev/documentation/test_practices/", "Selenium"),
    LearningResource("test-automation-playwright", "Test Automation", "Playwright Getting Started", "tutorial", "beginner", "An official introduction to browser test automation with Playwright.", "https://playwright.dev/docs/intro", "Playwright"),
    LearningResource("power-bi-start", "Power BI", "Get Started with Power BI Desktop", "tutorial", "beginner", "Microsoft's introduction to creating reports in Power BI Desktop.", "https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-getting-started", "Microsoft Learn"),
    LearningResource("tableau-training", "Tableau", "Tableau Training", "course", "beginner", "Official Tableau training resources and learning paths.", "https://www.tableau.com/learn/training", "Tableau"),
)

_VALID_TYPES = {"documentation", "tutorial", "course", "practice", "guide"}
_VALID_LEVELS = {"beginner", "intermediate", "advanced"}
_LEVEL_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2}
_PROFICIENCY_LEVEL_ORDER = {"unknown": -1, "exposure": 0, "beginner": 1, "intermediate": 2, "advanced": 3, "expert": 4}
_STRONG_PROFICIENCY = {"intermediate", "advanced", "expert"}
_CATALOG_BY_SKILL: dict[str, tuple[LearningResource, ...]] = {}
_catalog_lists: dict[str, list[LearningResource]] = {}
for _resource in RESOURCE_CATALOG:
    _catalog_lists.setdefault(_resource.skill, []).append(_resource)
_CATALOG_BY_SKILL = {skill: tuple(items) for skill, items in _catalog_lists.items()}


def _validate_catalog() -> None:
    ids = set()
    for resource in RESOURCE_CATALOG:
        if resource.resource_id in ids:
            raise ValueError(f"Duplicate resource id: {resource.resource_id}")
        ids.add(resource.resource_id)
        if normalize_skill(resource.skill) != resource.skill:
            raise ValueError(f"Resource skill is not canonical: {resource.skill}")
        if resource.resource_type not in _VALID_TYPES or resource.level not in _VALID_LEVELS:
            raise ValueError(f"Invalid resource type or level for {resource.resource_id}")
        if not all((resource.title, resource.provider, resource.description)):
            raise ValueError(f"Missing required resource fields for {resource.resource_id}")


_validate_catalog()


def _student_state(
    student_skill_twin: Iterable[Mapping[str, Any]] | None,
) -> tuple[set[str], dict[str, str]]:
    strong: set[str] = set()
    levels: dict[str, list[str]] = {}
    for record in student_skill_twin or ():
        if not isinstance(record, Mapping):
            raise InvalidEvidenceError("Each Student Skill Twin record must be a mapping.")
        raw_skill = record.get("skill")
        skill = normalize_skill(raw_skill) if isinstance(raw_skill, str) else None
        if skill is None:
            raise UnknownSkillError(f"Unknown or empty student skill: {raw_skill!r}")
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
            if proficiency not in {"unknown", "exposure"}:
                levels.setdefault(skill, []).append(proficiency)
            if (
                proficiency in _STRONG_PROFICIENCY
                and confidence in {"medium", "high"}
                and basis != "self_reported"
            ):
                strong.add(skill)
    best_level = {
        skill: max(values, key=lambda level: _PROFICIENCY_LEVEL_ORDER[level])
        for skill, values in levels.items()
    }
    return strong, best_level


def _extract_learning_items(
    target_role: str,
    learning_input: Mapping[str, Any] | Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if isinstance(learning_input, Mapping):
        input_role = learning_input.get("target_role")
        if input_role is not None and input_role != target_role:
            raise ValueError(f"Target role mismatch: requested {target_role!r}, input has {input_role!r}.")
        if isinstance(learning_input.get("steps"), list):
            items = learning_input["steps"]
        elif isinstance(learning_input.get("prioritized_gaps"), list):
            items = learning_input["prioritized_gaps"]
        else:
            items = []
    else:
        items = list(learning_input)

    ordered: list[dict[str, Any]] = []
    positions: dict[str, int] = {}
    for item in items:
        if not isinstance(item, Mapping):
            raise ValueError("Learning roadmap/gap entries must be mappings.")
        raw_skill = item.get("skill")
        skill = normalize_skill(raw_skill) if isinstance(raw_skill, str) else None
        if skill is None:
            raise UnknownSkillError(f"Unknown or empty learning skill: {raw_skill!r}")
        gap_type = item.get("gap_type")
        if gap_type not in {"missing", "partial"}:
            if item.get("added_as_prerequisite"):
                gap_type = "missing"
            else:
                # Matched or completed steps are not learning needs.
                continue
        if item.get("status") == "completed":
            continue
        normalized = dict(item)
        normalized["skill"] = skill
        normalized["gap_type"] = gap_type
        if skill not in positions:
            positions[skill] = len(ordered)
            ordered.append(normalized)
        else:
            old = ordered[positions[skill]]
            # Preserve first-seen order but retain the more cautious partial
            # classification and the highest supplied priority score.
            if gap_type == "partial":
                old["gap_type"] = "partial"
            new_score = normalized.get("priority_score")
            old_score = old.get("priority_score")
            if isinstance(new_score, (int, float)) and (not isinstance(old_score, (int, float)) or new_score > old_score):
                old["priority_score"] = new_score
            if old.get("priority") is None:
                old["priority"] = normalized.get("priority") or normalized.get("priority_label")
    return ordered


def _resource_order(resource: LearningResource, gap: Mapping[str, Any], student_level: str | None) -> tuple[int, int]:
    if gap["gap_type"] == "missing" or not student_level:
        desired = ("beginner", "intermediate", "advanced")
    elif student_level in {"unknown", "exposure", "beginner"}:
        desired = ("beginner", "intermediate", "advanced")
    elif student_level == "intermediate":
        desired = ("intermediate", "advanced", "beginner")
    else:  # advanced/expert: challenge first, with review resources afterward.
        desired = ("advanced", "intermediate", "beginner")
    catalog_order = next(index for index, item in enumerate(RESOURCE_CATALOG) if item.resource_id == resource.resource_id)
    return desired.index(resource.level), catalog_order


def recommend_learning_resources(
    target_role: str,
    learning_input: Mapping[str, Any] | Iterable[Mapping[str, Any]],
    student_skill_twin: Iterable[Mapping[str, Any]] | None = None,
    include_strongly_present: bool = False,
) -> dict[str, Any]:
    """Recommend catalog resources for roadmap steps or prioritized gaps.

    Roadmap order is retained. Missing skills prefer beginner resources;
    partial skills use the strongest recorded non-unknown proficiency to select
    an appropriate level. Strongly evidenced skills are omitted by default.
    """
    if not isinstance(target_role, str) or not target_role.strip():
        raise ValueError("target_role must be a non-empty string.")
    target_role = target_role.strip()
    learning_items = _extract_learning_items(target_role, learning_input)
    strong_skills, student_levels = _student_state(student_skill_twin)

    recommendations = []
    used_resource_ids: set[str] = set()
    for gap in learning_items:
        skill = gap["skill"]
        if skill in strong_skills and not include_strongly_present:
            continue
        resources = _CATALOG_BY_SKILL.get(skill, ())
        if not resources:
            continue
        current_level = student_levels.get(skill)
        ordered_resources = sorted(resources, key=lambda resource: _resource_order(resource, gap, current_level))
        priority = gap.get("priority") or gap.get("priority_label") or gap.get("industry_priority")
        if gap["gap_type"] == "partial":
            reason = (
                f"Recommended because {skill} is a partial skill for the {target_role} role; "
                f"the {ordered_resources[0].level} resource level is selected from the available student evidence."
            )
        elif gap.get("added_as_prerequisite"):
            reason = f"Recommended because {skill} is an explicit prerequisite step in the {target_role} roadmap."
        else:
            priority_text = f" {priority}" if priority else ""
            reason = f"Recommended because {skill} is a{priority_text} missing skill in the {target_role} roadmap."

        for resource in ordered_resources:
            if resource.resource_id in used_resource_ids:
                continue
            used_resource_ids.add(resource.resource_id)
            recommendations.append({
                "skill": skill,
                **asdict(resource),
                "reason": reason,
            })

    return {
        "target_role": target_role,
        "recommendations": recommendations,
        "total_recommendations": len(recommendations),
    }
