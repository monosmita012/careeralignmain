"""MongoDB persistence for user-scoped learning-roadmap progress."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from backend.progress_tracking import ProgressTracker
from backend.skill_taxonomy import normalize_skill
from backend.student_skill_twin import UnknownSkillError


class ProgressNotFoundError(KeyError):
    """Raised when a student, roadmap, or step has no stored progress."""


class ProgressStorageError(RuntimeError):
    """Raised when MongoDB cannot serve a progress operation."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_student_id(student_id: str) -> str:
    if not isinstance(student_id, str) or not student_id.strip():
        raise ValueError("student_id must be a non-empty profile identifier.")
    return student_id.strip().casefold()


def _roadmap_metadata(roadmap: Any) -> tuple[str, str, list[dict[str, Any]]]:
    if not isinstance(roadmap, dict):
        raise ValueError("roadmap must be an object.")
    target_role = roadmap.get("target_role")
    if target_role is not None and not isinstance(target_role, str):
        raise ValueError("roadmap target_role must be a string.")
    target_role = (target_role or "Unspecified role").strip() or "Unspecified role"
    steps = roadmap.get("steps", [])
    if not isinstance(steps, list):
        raise ValueError("roadmap steps must be a list.")

    tracker = ProgressTracker.from_roadmap(roadmap)
    tracker_records = tracker.get_all_progress()
    supplied_steps: dict[str, dict[str, Any]] = {}
    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            raise ValueError("Each roadmap step must be an object.")
        skill = normalize_skill(step.get("skill")) if isinstance(step.get("skill"), str) else None
        if skill is None:
            raise UnknownSkillError(f"Unknown or empty progress skill: {step.get('skill')!r}")
        supplied_steps.setdefault(skill, {
            "step_id": str(step.get("id", step.get("step", index))),
            "status": step.get("status", "not_started"),
        })

    records: list[dict[str, Any]] = []
    for record in tracker_records:
        source = supplied_steps.get(record["skill"], {})
        records.append({
            **record,
            "step_id": source.get("step_id", str(len(records) + 1)),
            "completed_at": None,
            "created_at": None,
            "updated_at": None,
        })
    # A role-scoped key remains stable when the same target role's generated
    # steps change after a profile refresh. Initialization reconciles steps by
    # canonical skill and preserves progress for those that remain.
    roadmap_id = "role:" + target_role.casefold()
    return target_role, roadmap_id, records


def _json_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value.isoformat() if isinstance(value, datetime) else value
        for key, value in record.items()
    }


class MongoProgressRepository:
    """One MongoDB document per student and deterministic roadmap version."""

    def __init__(
        self,
        uri: str | None = None,
        database_name: str | None = None,
        collection_name: str = "roadmap_progress",
        collection: Collection | None = None,
    ):
        self._client: MongoClient | None = None
        if collection is None:
            selected_uri = uri or os.getenv("CAREERALIGN_MONGODB_URI", "mongodb://127.0.0.1:27017")
            selected_database = database_name or os.getenv("CAREERALIGN_MONGODB_DATABASE", "careerAlign")
            try:
                self._client = MongoClient(selected_uri, serverSelectionTimeoutMS=3000)
                self._client.admin.command("ping")
                collection = self._client[selected_database][collection_name]
                collection.create_index(
                    [("student_id", 1), ("roadmap_id", 1)], unique=True,
                    name="uniq_student_roadmap",
                )
            except PyMongoError as exc:
                if self._client is not None:
                    self._client.close()
                raise ProgressStorageError("Progress storage is unavailable; MongoDB could not be reached.") from exc
        self._collection = collection

    def close(self) -> None:
        if self._client is not None:
            self._client.close()

    def initialize(self, student_id: str, roadmap: Any) -> dict[str, Any]:
        normalized_id = _normalize_student_id(student_id)
        target_role, roadmap_id, records = _roadmap_metadata(roadmap)
        now = _now()
        try:
            existing = self._collection.find_one(
                {"student_id": normalized_id, "roadmap_id": roadmap_id}, {"_id": 0}
            )
            old_by_skill = {row["skill"]: row for row in (existing or {}).get("progress", [])}
            for row in records:
                old = old_by_skill.get(row["skill"])
                if old:
                    row.update({
                        key: old.get(key)
                        for key in ("status", "updated_revision", "notes", "completed_at", "created_at", "updated_at")
                    })
                    row["updated_at"] = now
                else:
                    row["created_at"] = now
                    row["updated_at"] = now
                    if row["status"] == "completed":
                        row["completed_at"] = now
            document = {
                "student_id": normalized_id,
                "roadmap_id": roadmap_id,
                "target_role": target_role,
                "progress": records,
                "completion_events": (existing or {}).get("completion_events", []),
                "created_at": (existing or {}).get("created_at", now),
                "updated_at": now,
            }
            self._collection.update_one(
                {"student_id": normalized_id, "roadmap_id": roadmap_id},
                {
                    "$set": {key: value for key, value in document.items() if key != "created_at"},
                    "$setOnInsert": {"created_at": document["created_at"]},
                },
                upsert=True,
            )
            stored = self._collection.find_one(
                {"student_id": normalized_id, "roadmap_id": roadmap_id},
                {"_id": 0},
            )
        except PyMongoError as exc:
            raise ProgressStorageError("Could not initialize progress in MongoDB.") from exc
        if stored is None:
            raise ProgressStorageError("MongoDB did not return the initialized progress record.")
        return self._response(stored)

    def update(
        self,
        student_id: str,
        roadmap_id: str,
        skill: str,
        status: str,
        notes: str | None = None,
    ) -> dict[str, Any]:
        normalized_id = _normalize_student_id(student_id)
        canonical = normalize_skill(skill) if isinstance(skill, str) else None
        if canonical is None:
            raise UnknownSkillError(f"Unknown or empty progress skill: {skill!r}")
        try:
            stored = self._collection.find_one(
                {"student_id": normalized_id, "roadmap_id": roadmap_id},
                {"_id": 0},
            )
        except PyMongoError as exc:
            raise ProgressStorageError("Could not retrieve progress from MongoDB.") from exc
        if stored is None:
            raise ProgressNotFoundError("No progress record exists for this student and roadmap.")

        tracker = ProgressTracker(stored.get("progress", []))
        previous = tracker.get_progress(canonical)
        if previous is None:
            raise ProgressNotFoundError(f"No progress record exists for {canonical!r}.")
        updated = tracker.update_progress(canonical, status, notes)
        newly_completed = tracker.newly_completed_skills()
        now = _now()
        rows = stored.get("progress", [])
        target = next(row for row in rows if row["skill"] == canonical)
        target.update(updated)
        target["updated_at"] = now
        if newly_completed:
            target["completed_at"] = now
            stored.setdefault("completion_events", []).extend({**event, "completed_at": now} for event in newly_completed)
        elif status != "completed":
            target["completed_at"] = None
        stored["updated_at"] = now
        try:
            result = self._collection.replace_one(
                {"student_id": normalized_id, "roadmap_id": roadmap_id}, stored
            )
        except PyMongoError as exc:
            raise ProgressStorageError("Could not save progress to MongoDB.") from exc
        if result.matched_count != 1:
            raise ProgressNotFoundError("No progress record exists for this student and roadmap.")
        return self._response(stored, response_events=newly_completed)

    def get_all(self, student_id: str, roadmap_id: str) -> dict[str, Any]:
        normalized_id = _normalize_student_id(student_id)
        try:
            stored = self._collection.find_one(
                {"student_id": normalized_id, "roadmap_id": roadmap_id}, {"_id": 0}
            )
        except PyMongoError as exc:
            raise ProgressStorageError("Could not retrieve progress from MongoDB.") from exc
        if stored is None:
            raise ProgressNotFoundError("No progress record exists for this student and roadmap.")
        return self._response(stored)

    def _response(
        self,
        document: dict[str, Any],
        response_events: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        rows = [_json_record(row) for row in document.get("progress", [])]
        tracker = ProgressTracker(rows)
        event_source = document.get("completion_events", []) if response_events is None else response_events
        events = [_json_record(event) for event in event_source]
        return {
            "student_id": document["student_id"],
            "roadmap_id": document["roadmap_id"],
            "target_role": document["target_role"],
            "progress": rows,
            "summary": tracker.summary(),
            "newly_completed_skills": events,
            "created_at": document["created_at"].isoformat() if isinstance(document.get("created_at"), datetime) else document.get("created_at"),
            "updated_at": document["updated_at"].isoformat() if isinstance(document.get("updated_at"), datetime) else document.get("updated_at"),
        }


__all__ = ["MongoProgressRepository", "ProgressNotFoundError", "ProgressStorageError"]
