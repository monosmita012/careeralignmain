"""Persistence and profile-isolation checks against the local MongoDB service."""

from __future__ import annotations

import unittest
from uuid import uuid4

from backend.progress_repository import (
    MongoProgressRepository,
    ProgressNotFoundError,
    ProgressStorageError,
)


class MongoProgressRepositoryTests(unittest.TestCase):
    def setUp(self):
        try:
            self.repository = MongoProgressRepository()
        except ProgressStorageError as exc:
            self.skipTest(str(exc))
        self.student_ids = [f"progress-test-{uuid4().hex}@example.invalid"]
        self.roadmap = {
            "target_role": "Data Engineer",
            "steps": [
                {"step": 1, "skill": "Python", "status": "not_started"},
                {"step": 2, "skill": "SQL", "status": "not_started"},
            ],
        }

    def tearDown(self):
        if hasattr(self, "repository"):
            try:
                self.repository._collection.delete_many({"student_id": {"$in": self.student_ids}})
            finally:
                self.repository.close()

    def _student(self):
        student_id = self.student_ids[0]
        return student_id

    def test_initialize_retrieve_and_update_progress(self):
        initialized = self.repository.initialize(self._student(), self.roadmap)
        self.assertEqual(2, len(initialized["progress"]))
        self.assertEqual("not_started", initialized["progress"][0]["status"])
        updated = self.repository.update(self._student(), initialized["roadmap_id"], "Python", "completed")
        self.assertEqual("completed", next(row for row in updated["progress"] if row["skill"] == "Python")["status"])
        self.assertIsNotNone(next(row for row in updated["progress"] if row["skill"] == "Python")["completed_at"])
        readback = self.repository.get_all(self._student(), initialized["roadmap_id"])
        self.assertEqual(1, readback["summary"]["completed_count"])

    def test_progress_survives_repository_recreation_and_reinitialization(self):
        initialized = self.repository.initialize(self._student(), self.roadmap)
        roadmap_id = initialized["roadmap_id"]
        self.repository.update(self._student(), roadmap_id, "Python", "completed")
        self.repository.close()
        self.repository = MongoProgressRepository()
        reinitialized = self.repository.initialize(self._student(), self.roadmap)
        self.assertEqual(roadmap_id, reinitialized["roadmap_id"])
        self.assertEqual("completed", reinitialized["progress"][0]["status"])

    def test_progress_is_isolated_by_student_identifier(self):
        student_a = self._student()
        student_b = f"progress-test-{uuid4().hex}@example.invalid"
        self.student_ids.append(student_b)
        roadmap_a = self.repository.initialize(student_a, self.roadmap)
        roadmap_b = self.repository.initialize(student_b, self.roadmap)
        self.repository.update(student_a, roadmap_a["roadmap_id"], "Python", "completed")
        self.assertEqual("completed", self.repository.get_all(student_a, roadmap_a["roadmap_id"])["progress"][0]["status"])
        self.assertEqual("not_started", self.repository.get_all(student_b, roadmap_b["roadmap_id"])["progress"][0]["status"])

    def test_duplicate_completion_does_not_duplicate_event(self):
        initialized = self.repository.initialize(self._student(), self.roadmap)
        roadmap_id = initialized["roadmap_id"]
        first = self.repository.update(self._student(), roadmap_id, "Python", "completed")
        duplicate = self.repository.update(self._student(), roadmap_id, "Python", "completed")
        self.assertEqual(1, len(first["newly_completed_skills"]))
        self.assertEqual([], duplicate["newly_completed_skills"])
        self.assertEqual(1, len(self.repository.get_all(self._student(), roadmap_id)["newly_completed_skills"]))

    def test_nonexistent_roadmap_or_step_is_reported(self):
        with self.assertRaises(ProgressNotFoundError):
            self.repository.get_all(self._student(), "role:Data Engineer")
        initialized = self.repository.initialize(self._student(), self.roadmap)
        with self.assertRaises(ProgressNotFoundError):
            self.repository.update(self._student(), initialized["roadmap_id"], "Docker", "completed")

    def test_reinitializing_changed_steps_preserves_matching_completed_skill(self):
        initialized = self.repository.initialize(self._student(), self.roadmap)
        self.repository.update(self._student(), initialized["roadmap_id"], "Python", "completed")
        updated_plan = {
            "target_role": "Data Engineer",
            "steps": [
                {"step": 1, "skill": "Python", "status": "not_started"},
                {"step": 2, "skill": "Docker", "status": "not_started"},
            ],
        }
        refreshed = self.repository.initialize(self._student(), updated_plan)
        self.assertEqual(initialized["roadmap_id"], refreshed["roadmap_id"])
        self.assertEqual(["Python", "Docker"], [row["skill"] for row in refreshed["progress"]])
        self.assertEqual("completed", refreshed["progress"][0]["status"])
        self.assertEqual("not_started", refreshed["progress"][1]["status"])


if __name__ == "__main__":
    unittest.main()
