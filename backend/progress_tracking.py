"""Serializable in-memory progress tracking for CareerAlign roadmap skills."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

try:
    from .skill_taxonomy import normalize_skill
    from .student_skill_twin import UnknownSkillError
except ImportError:  # Support ``python backend/progress_tracking.py``.
    from skill_taxonomy import normalize_skill
    from student_skill_twin import UnknownSkillError


PROGRESS_STATUSES = ("not_started", "in_progress", "completed")


class InvalidProgressStatusError(ValueError):
    """Raised when a progress status is not supported."""


class ProgressTracker:
    """An in-memory ordered collection of JSON-serializable progress records.

    ``updated_revision`` is a deterministic update marker: it starts at zero
    and increments only when a record's status or notes actually change.
    Completion events describe the student's explicit status update; they do
    not infer proficiency, confidence, or demonstrated skill.
    """

    def __init__(self, progress: Iterable[Mapping[str, Any]] | None = None):
        self._records: dict[str, dict[str, Any]] = {}
        self._completion_events: list[dict[str, Any]] = []
        if progress is None:
            return
        if isinstance(progress, (str, bytes, Mapping)):
            raise ValueError("progress must be an iterable of progress mappings.")
        for item in progress:
            if not isinstance(item, Mapping):
                raise ValueError("Each progress record must be a mapping.")
            skill = self._canonical_skill(item.get("skill"))
            status = self._validate_status(item.get("status"))
            if skill in self._records:
                raise ValueError(f"Duplicate progress record for {skill!r}.")
            notes = item.get("notes")
            if notes is not None and not isinstance(notes, str):
                raise ValueError(f"Notes for {skill!r} must be a string or None.")
            revision = item.get("updated_revision", 0)
            if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
                raise ValueError(f"updated_revision for {skill!r} must be a non-negative integer.")
            self._records[skill] = self._make_record(skill, status, revision, notes)

    @classmethod
    def from_roadmap(cls, roadmap: Mapping[str, Any] | Iterable[Mapping[str, Any]]) -> "ProgressTracker":
        """Create one record per roadmap skill, defaulting to not_started.

        The roadmap may be a mapping with a ``steps`` list or an iterable of
        step mappings. For duplicate skills, the first valid status wins unless
        it is ``not_started`` and a later duplicate has a meaningful status.
        """
        if isinstance(roadmap, Mapping):
            steps = roadmap.get("steps", [])
            if not isinstance(steps, list):
                raise ValueError("roadmap steps must be a list.")
        else:
            if isinstance(roadmap, (str, bytes)):
                raise ValueError("roadmap must be a mapping or iterable of step mappings.")
            steps = list(roadmap)

        records: dict[str, dict[str, Any]] = {}
        for step in steps:
            if not isinstance(step, Mapping):
                raise ValueError("Each roadmap step must be a mapping.")
            skill = cls._canonical_skill(step.get("skill"))
            supplied_status = step.get("status")
            status = "not_started" if supplied_status is None else cls._validate_status(supplied_status)
            notes = step.get("notes")
            if notes is not None and not isinstance(notes, str):
                raise ValueError(f"Notes for {skill!r} must be a string or None.")
            current = records.get(skill)
            if current is None:
                records[skill] = cls._make_record(skill, status, 0, notes)
            elif current["status"] == "not_started" and status != "not_started":
                current["status"] = status
                if notes is not None:
                    current["notes"] = notes
        tracker = cls()
        tracker._records = records
        return tracker

    @staticmethod
    def _canonical_skill(raw_skill: Any) -> str:
        skill = normalize_skill(raw_skill) if isinstance(raw_skill, str) else None
        if skill is None:
            raise UnknownSkillError(f"Unknown or empty progress skill: {raw_skill!r}")
        return skill

    @staticmethod
    def _validate_status(status: Any) -> str:
        if not isinstance(status, str) or status not in PROGRESS_STATUSES:
            raise InvalidProgressStatusError(
                f"Invalid progress status {status!r}; expected one of {PROGRESS_STATUSES}."
            )
        return status

    @staticmethod
    def _make_record(skill: str, status: str, revision: int, notes: str | None) -> dict[str, Any]:
        return {
            "skill": skill,
            "status": status,
            "updated_revision": revision,
            "notes": notes,
        }

    def update_progress(
        self,
        skill: str,
        status: str,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing skill. Unknown skills are never created implicitly."""
        canonical = self._canonical_skill(skill)
        valid_status = self._validate_status(status)
        if notes is not None and not isinstance(notes, str):
            raise ValueError("notes must be a string or None.")
        if canonical not in self._records:
            raise KeyError(f"No progress record exists for {canonical!r}.")

        record = self._records[canonical]
        previous_status = record["status"]
        new_notes = record["notes"] if notes is None else notes
        changed = record["status"] != valid_status or record["notes"] != new_notes
        if changed:
            record["status"] = valid_status
            record["notes"] = new_notes
            record["updated_revision"] += 1
            if valid_status == "completed" and previous_status != "completed":
                self._completion_events.append({
                    "event_type": "roadmap_step_completed",
                    "skill": canonical,
                    "status": "completed",
                    "updated_revision": record["updated_revision"],
                    "statement": "student marked this learning step as completed.",
                    "proficiency": None,
                    "confidence": None,
                })
        return dict(record)

    def get_progress(self, skill: str) -> dict[str, Any] | None:
        canonical = self._canonical_skill(skill)
        record = self._records.get(canonical)
        return dict(record) if record is not None else None

    def get_all_progress(self) -> list[dict[str, Any]]:
        return [dict(record) for record in self._records.values()]

    def summary(self) -> dict[str, Any]:
        counts = {status: 0 for status in PROGRESS_STATUSES}
        for record in self._records.values():
            counts[record["status"]] += 1
        total = len(self._records)
        percentage = (100.0 * counts["completed"] / total) if total else 0.0
        return {
            "total_skills": total,
            "not_started_count": counts["not_started"],
            "in_progress_count": counts["in_progress"],
            "completed_count": counts["completed"],
            "completion_percentage": round(min(100.0, max(0.0, percentage)), 2),
        }

    def newly_completed_skills(self) -> list[dict[str, Any]]:
        """Return neutral completion events accumulated since tracker creation."""
        return [dict(event) for event in self._completion_events]


def create_progress_from_roadmap(
    roadmap: Mapping[str, Any] | Iterable[Mapping[str, Any]],
) -> ProgressTracker:
    """Convenience factory for initializing in-memory progress."""
    return ProgressTracker.from_roadmap(roadmap)


__all__ = [
    "InvalidProgressStatusError",
    "PROGRESS_STATUSES",
    "ProgressTracker",
    "create_progress_from_roadmap",
]
