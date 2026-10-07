"""Explainable deterministic matching of Student Skill Twin evidence to jobs."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

try:
    from .skill_gap_analysis import _classify_student_skill, _student_evidence_by_skill
    from .skill_taxonomy import normalize_skill
    from .student_skill_twin import InvalidEvidenceError, UnknownSkillError
except ImportError:  # Support ``python backend/job_matching.py``.
    from skill_gap_analysis import _classify_student_skill, _student_evidence_by_skill
    from skill_taxonomy import normalize_skill
    from student_skill_twin import InvalidEvidenceError, UnknownSkillError


_MATCHED_CREDIT = 1.0
_PARTIAL_CREDIT = 0.5


def _prepare_student(
    student_skill_twin: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    if isinstance(student_skill_twin, (str, bytes, Mapping)):
        raise InvalidEvidenceError("Student Skill Twin must be an iterable of skill records.")
    return _student_evidence_by_skill(student_skill_twin)


def _prepare_job(job: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(job, Mapping):
        raise ValueError("Each job record must be a mapping.")
    job_id = job.get("job_id")
    title = job.get("title")
    skills = job.get("skills")
    if not isinstance(job_id, str) or not job_id.strip():
        raise ValueError("Job record requires a non-empty string job_id.")
    if not isinstance(title, str) or not title.strip():
        raise ValueError(f"Job {job_id!r} requires a non-empty string title.")
    if not isinstance(skills, (list, tuple)):
        raise ValueError(f"Job {job_id!r} skills must be a list or tuple.")

    canonical_skills: list[str] = []
    for raw_skill in skills:
        skill = normalize_skill(raw_skill) if isinstance(raw_skill, str) else None
        if skill is None:
            raise UnknownSkillError(f"Unknown or empty job skill for {job_id!r}: {raw_skill!r}")
        if skill not in canonical_skills:
            canonical_skills.append(skill)

    prepared = {"job_id": job_id.strip(), "title": title.strip(), "skills": canonical_skills}
    for optional_field in ("career_role", "company"):
        value = job.get(optional_field)
        if value is not None:
            if not isinstance(value, str):
                raise ValueError(f"Job {job_id!r} {optional_field} must be a string when supplied.")
            if value.strip():
                prepared[optional_field] = value.strip()
    return prepared


def _explanation(matched: list[str], partial: list[str], missing: list[str]) -> str:
    parts = []
    parts.append("Strongest alignment: " + (", ".join(matched) if matched else "none"))
    parts.append("Partial alignment: " + (", ".join(partial) if partial else "none"))
    parts.append("Missing: " + (", ".join(missing) if missing else "none"))
    return ". ".join(parts) + "."


def match_jobs(
    student_skill_twin: Iterable[Mapping[str, Any]],
    jobs: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Score and rank jobs by current skill alignment with their listed skills.

    Per unique job skill, matched evidence earns 1.0, partial evidence 0.5,
    and absent evidence 0.0. The percentage is earned points divided by the
    number of unique listed skills; a job with no skills scores zero. Ties are
    resolved by matched count, partial count, then ascending job_id.
    """
    student = _prepare_student(student_skill_twin)
    if isinstance(jobs, (str, bytes, Mapping)):
        raise ValueError("jobs must be an iterable of job mappings.")
    prepared_jobs = [_prepare_job(job) for job in jobs]
    ids = [job["job_id"] for job in prepared_jobs]
    if len(ids) != len(set(ids)):
        raise ValueError("Job records must have unique job_id values.")

    ranked = []
    for job in prepared_jobs:
        matched: list[str] = []
        partial: list[str] = []
        missing: list[str] = []
        for skill in job["skills"]:
            evidence = student.get(skill)
            if evidence is None:
                missing.append(skill)
            elif _classify_student_skill(evidence)[0] == "matched":
                matched.append(skill)
            else:
                # The established Skill Gap Analysis rules classify any
                # present but non-strong evidence as partial.
                partial.append(skill)

        total = len(job["skills"])
        score = round(
            100.0 * (_MATCHED_CREDIT * len(matched) + _PARTIAL_CREDIT * len(partial)) / total,
            2,
        ) if total else 0.0
        result = {
            "job_id": job["job_id"],
            "title": job["title"],
        }
        for optional_field in ("career_role", "company"):
            if optional_field in job:
                result[optional_field] = job[optional_field]
        result.update({
            "score": score,
            "matched_skills": matched,
            "partial_skills": partial,
            "missing_skills": missing,
            "matched_count": len(matched),
            "partial_count": len(partial),
            "missing_count": len(missing),
            "total_skill_count": total,
            "explanation": _explanation(matched, partial, missing),
        })
        ranked.append(result)

    ranked.sort(key=lambda item: (
        -item["score"],
        -item["matched_count"],
        -item["partial_count"],
        item["job_id"],
    ))
    return {
        "matches": ranked,
        "total_jobs": len(ranked),
        "score_interpretation": "Current skill alignment with the listed job skills; not a hiring, placement, or employment probability.",
    }


__all__ = ["match_jobs"]
