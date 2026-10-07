"""Deterministic, explainable resume feedback using CareerAlign's existing data."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
import re
from typing import Any

import pyarrow.parquet as pq

try:
    from .resume_processing import extract_resume_text
    from .skill_extractor import extract_skills
    from .skill_gap_analysis import DEFAULT_INDUSTRY_TWIN
except ImportError:  # Support direct execution from the backend directory.
    from resume_processing import extract_resume_text
    from skill_extractor import extract_skills
    from skill_gap_analysis import DEFAULT_INDUSTRY_TWIN


class UnknownResumeTargetRoleError(ValueError):
    """Raised when a requested role is not in the existing Industry Skill Twin."""


SECTION_PATTERNS: dict[str, re.Pattern[str]] = {
    "professional_summary": re.compile(r"^(?:professional\s+)?(?:summary|profile|objective|career\s+objective)$", re.I),
    "education": re.compile(r"^(?:education|academic\s+(?:background|history)|qualifications?)$", re.I),
    "skills": re.compile(r"^(?:(?:technical\s+)?skills|core\s+competencies)$", re.I),
    "projects": re.compile(r"^(?:selected\s+)?projects?|personal\s+projects?$", re.I),
    "experience": re.compile(r"^(?:(?:(?:professional|work|employment)\s+)?experience|internships?)$", re.I),
    "certifications": re.compile(r"^(?:certifications?|licenses?)$", re.I),
    "achievements": re.compile(r"^(?:achievements?|awards?|honors?)$", re.I),
}
_HEADING_DECORATION = re.compile(r"^[\s#*\-•|]+|[\s:#*|]+$")
_VAGUE_PHRASES = re.compile(
    r"\b(?:responsible for|worked on|helped with|assisted with|participated in|various tasks|etc\.)\b",
    re.IGNORECASE,
)
_WEAK_OPENING = re.compile(r"^\s*(?:was\s+)?(?:responsible for|worked on|helped|assisted|participated in|handled)\b", re.I)
_CONTACT_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_CONTACT_PHONE = re.compile(r"(?<!\w)\+?\d[\d()\s.-]{7,}\d(?!\w)")
_METRIC = re.compile(r"(?:\b\d+(?:\.\d+)?\s*(?:%|percent|x|users|customers|hours|days|weeks|months|years|records|rows|requests)(?=\W|$)|[$€£]\s*\d+|\bby\s+\d+\b)", re.I)
_BULLET = re.compile(r"^\s*(?:[-*•▪◦]|\d+[.)])\s+")
_ROLE_ORDER = {"core": 0, "common": 1, "supporting": 2, "occasional": 3}


def _heading(line: str) -> str | None:
    normalized = _HEADING_DECORATION.sub("", line).strip()
    normalized = re.sub(r"\s+", " ", normalized)
    for name, pattern in SECTION_PATTERNS.items():
        if pattern.fullmatch(normalized):
            return name
    return None


def _sections(text: str) -> tuple[dict[str, str], dict[str, bool]]:
    content: dict[str, list[str]] = {name: [] for name in SECTION_PATTERNS}
    found = {name: False for name in SECTION_PATTERNS}
    current: str | None = None
    for line in text.splitlines():
        heading = _heading(line)
        if heading is not None:
            current = heading
            found[heading] = True
            continue
        if current is not None:
            content[current].append(line)

    has_contact = bool(_CONTACT_EMAIL.search(text) or _CONTACT_PHONE.search(text) or re.search(r"\b(?:linkedin\.com|github\.com)\b", text, re.I))
    found["contact"] = has_contact
    sections = {name: "\n".join(lines).strip() for name, lines in content.items()}
    sections["contact"] = text if has_contact else ""
    return sections, found


def _industry_rows(rows: Iterable[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    if rows is not None:
        return [dict(row) for row in rows]
    if not DEFAULT_INDUSTRY_TWIN.is_file():
        raise FileNotFoundError(f"Industry Skill Twin not found: {DEFAULT_INDUSTRY_TWIN}")
    return pq.read_table(
        DEFAULT_INDUSTRY_TWIN,
        columns=["career_role", "skill", "role_frequency_percentage", "priority"],
    ).to_pylist()


def enhance_resume_text(
    text: str,
    target_role: str | None = None,
    industry_skill_twin: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return heuristic feedback; no ATS score or possession inference is made."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Processed resume text is empty.")

    resume_skills = extract_skills(text)
    sections, present = _sections(text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    lowered_sentences = [
        re.sub(r"[^a-z0-9]+", " ", sentence.casefold()).strip()
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", text)
    ]
    repeated_sentences = sum(count - 1 for count in Counter(s for s in lowered_sentences if len(s) >= 30).values() if count > 1)
    vague_count = sum(len(_VAGUE_PHRASES.findall(line)) for line in lines)
    weak_count = sum(bool(_WEAK_OPENING.search(_BULLET.sub("", line))) for line in lines)
    project_experience_text = "\n".join((sections.get("projects", ""), sections.get("experience", "")))
    support_text = "\n".join((project_experience_text, sections.get("certifications", "")))
    project_experience_skills = set(extract_skills(support_text)) if support_text.strip() else set()
    skills_needing_evidence = [skill for skill in resume_skills if skill not in project_experience_skills]

    evidence_lines = [line for line in lines if _BULLET.match(line) or len(line) >= 45]
    measurable_lines = [line for line in evidence_lines if _METRIC.search(line)]
    long_lines = [len(line) for line in lines if len(line) > 1200]

    strengths: list[str] = []
    if present["contact"]:
        strengths.append("Contact information appears to be present.")
    if present["professional_summary"]:
        strengths.append("A summary or objective section is present.")
    if present["education"]:
        strengths.append("An education section is present.")
    if present["experience"]:
        strengths.append("An experience or internship section is present.")
    if present["projects"]:
        strengths.append("A projects section is present.")
    if resume_skills:
        strengths.append(f"The existing CareerAlign extractor detected {len(resume_skills)} canonical skills.")
    if measurable_lines:
        strengths.append(f"{len(measurable_lines)} content line(s) include a detectable quantity or outcome measure.")

    suggestions: list[dict[str, str]] = []

    def suggest(priority: str, topic: str, message: str) -> None:
        suggestions.append({"priority": priority, "topic": topic, "suggestion": message})

    missing_sections = [name for name, exists in present.items() if not exists]
    if missing_sections:
        labels = {
            "contact": "contact information", "professional_summary": "summary/objective",
            "education": "education", "skills": "skills", "projects": "projects",
            "experience": "experience/internship", "certifications": "certifications",
            "achievements": "achievements",
        }
        suggest("review", "completeness", "Consider adding or confirming these sections if they apply to your background: " + ", ".join(labels[item] for item in missing_sections) + ".")
    if vague_count:
        suggest("high", "specificity", f"Replace or clarify {vague_count} vague phrase(s) such as 'worked on' or 'responsible for' with the action, context, and result.")
    if weak_count:
        suggest("high", "action_verbs", f"Review {weak_count} line(s) that begin with a weak or responsibility-focused phrase; lead with the action you took.")
    if evidence_lines and not measurable_lines:
        suggest("high", "measurable_outcomes", "Add a measurable result to a project or experience bullet where you can support it with accurate figures.")
    elif evidence_lines and len(measurable_lines) < len(evidence_lines):
        suggest("medium", "measurable_outcomes", "Add measurable outcomes to additional project or experience bullets where accurate figures are available.")
    if present["projects"] and not extract_skills(sections.get("projects", "")):
        suggest("medium", "project_context", "Mention the technologies and your specific contribution in project descriptions, when applicable.")
    if skills_needing_evidence:
        suggest("medium", "skill_evidence", "The resume lists " + ", ".join(skills_needing_evidence[:8]) + " but those skills were not detected in project, experience, or certification sections. Add genuine supporting examples if available.")
    if repeated_sentences:
        suggest("medium", "repetition", f"Review {repeated_sentences} repeated sentence(s) and keep the clearest version.")
    if long_lines:
        suggest("low", "readability", f"Review {len(long_lines)} unusually long line(s) (over 1,200 characters) for readability.")

    target_coverage: dict[str, Any] | None = None
    role_name = target_role.strip() if isinstance(target_role, str) and target_role.strip() else None
    if role_name:
        rows = _industry_rows(industry_skill_twin)
        available_roles = {row.get("career_role") for row in rows if row.get("career_role")}
        if role_name not in available_roles:
            raise UnknownResumeTargetRoleError(
                f"Unknown target role {role_name!r}. Available roles: {', '.join(sorted(str(role) for role in available_roles))}."
            )
        requirements = [
            row for row in rows
            if row.get("career_role") == role_name
            and isinstance(row.get("role_frequency_percentage"), (int, float))
            and row["role_frequency_percentage"] > 0
        ]
        requirements.sort(key=lambda row: (
            _ROLE_ORDER.get(str(row.get("priority", "occasional")).casefold(), 4),
            -float(row["role_frequency_percentage"]),
            str(row.get("skill", "")).casefold(),
        ))
        represented = [row for row in requirements if row.get("skill") in resume_skills]
        not_represented = [row for row in requirements if row.get("skill") not in resume_skills]
        represented_needing_evidence = [row for row in represented if row.get("skill") not in project_experience_skills]
        coverage_note = "Not represented in this resume does not establish that you lack the skill. Add it only if you genuinely have the experience."
        target_coverage = {
            "target_role": role_name,
            "represented_skills": [
                {"skill": row["skill"], "priority": row.get("priority"), "role_frequency_percentage": row["role_frequency_percentage"]}
                for row in represented
            ],
            "not_represented_skills": [
                {"skill": row["skill"], "priority": row.get("priority"), "role_frequency_percentage": row["role_frequency_percentage"]}
                for row in not_represented
            ],
            "skills_needing_stronger_evidence": [row["skill"] for row in represented_needing_evidence],
            "note": coverage_note,
        }
        if not_represented:
            top = not_represented[:8]
            suggest("role", "target_role_coverage", f"For {role_name}, the resume does not represent " + ", ".join(row["skill"] for row in top) + ". If you genuinely have experience with these skills, add concrete evidence; this is not a claim that you lack them.")
        if represented_needing_evidence:
            suggest("role", "target_role_evidence", "For the selected role, add project or experience examples for represented skills where available: " + ", ".join(row["skill"] for row in represented_needing_evidence[:8]) + ".")

    if not suggestions:
        suggest("low", "review", "No specific heuristic issues were detected. Review the resume for accuracy and relevance before sharing it.")
    priority_order = {"high": 0, "role": 1, "medium": 2, "review": 3, "low": 4}
    suggestions.sort(key=lambda item: (priority_order.get(item["priority"], 9), item["topic"], item["suggestion"]))
    return {
        "summary": f"Found {len(strengths)} resume strength(s) and {len(suggestions)} improvement suggestion(s). This is a content review, not an ATS score.",
        "strengths": strengths,
        "section_completeness": {
            "present": [name for name, exists in present.items() if exists],
            "missing_sections": missing_sections,
            "applicability_note": "A missing section is a prompt for review, not an automatic defect; include it only when relevant to your experience.",
        },
        "skill_coverage": {
            "resume_skills": resume_skills,
            "skills_needing_stronger_evidence": skills_needing_evidence,
        },
        "target_role_coverage": target_coverage,
        "content_checks": {
            "vague_phrase_count": vague_count,
            "weak_opening_count": weak_count,
            "measurable_line_count": len(measurable_lines),
            "candidate_content_line_count": len(evidence_lines),
            "repeated_sentence_count": repeated_sentences,
            "very_long_line_count": len(long_lines),
        },
        "suggestions": suggestions[:20],
        "improvement_priorities": list(dict.fromkeys(item["topic"] for item in suggestions[:20])),
    }


def enhance_resume_file(
    filename: str,
    content: bytes,
    target_role: str | None = None,
) -> dict[str, Any]:
    """Run enhancement over text from the shared resume parser."""
    text = extract_resume_text(filename, content)
    result = enhance_resume_text(text, target_role=target_role)
    result["filename"] = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    return result
