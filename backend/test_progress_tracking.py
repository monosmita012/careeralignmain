import json
import unittest

from backend.progress_tracking import (
    InvalidProgressStatusError,
    ProgressTracker,
    create_progress_from_roadmap,
)
from backend.student_skill_twin import UnknownSkillError


class ProgressTrackingTests(unittest.TestCase):
    def test_initial_progress_is_created_from_roadmap(self):
        tracker = create_progress_from_roadmap({"target_role": "Data Engineer", "steps": [
            {"skill": "Python"}, {"skill": "SQL"},
        ]})
        self.assertEqual(["Python", "SQL"], [row["skill"] for row in tracker.get_all_progress()])

    def test_initial_status_defaults_to_not_started(self):
        tracker = ProgressTracker.from_roadmap([{"skill": "Python"}])
        self.assertEqual("not_started", tracker.get_progress("Python")["status"])

    def test_valid_existing_roadmap_status_is_preserved(self):
        tracker = ProgressTracker.from_roadmap([
            {"skill": "Python", "status": "not_started"},
            {"skill": "Python", "status": "in_progress", "notes": "Started"},
            {"skill": "SQL", "status": "completed"},
        ])
        self.assertEqual("in_progress", tracker.get_progress("Python")["status"])
        self.assertEqual("completed", tracker.get_progress("SQL")["status"])
        self.assertEqual([], tracker.newly_completed_skills())

    def test_duplicate_roadmap_skills_create_one_record(self):
        tracker = ProgressTracker.from_roadmap([{"skill": "Python"}, {"skill": "py"}])
        self.assertEqual(1, len(tracker.get_all_progress()))
        self.assertEqual("Python", tracker.get_all_progress()[0]["skill"])

    def test_skill_can_be_changed_to_in_progress(self):
        tracker = ProgressTracker.from_roadmap([{"skill": "Python"}])
        updated = tracker.update_progress("Python", "in_progress")
        self.assertEqual("in_progress", updated["status"])
        self.assertEqual(1, updated["updated_revision"])

    def test_skill_can_be_changed_to_completed(self):
        tracker = ProgressTracker.from_roadmap([{"skill": "Python"}])
        self.assertEqual("completed", tracker.update_progress("Python", "completed")["status"])

    def test_invalid_status_raises_clear_error(self):
        tracker = ProgressTracker.from_roadmap([{"skill": "Python"}])
        with self.assertRaises(InvalidProgressStatusError):
            tracker.update_progress("Python", "expert")

    def test_unknown_skill_is_rejected(self):
        with self.assertRaises(UnknownSkillError):
            ProgressTracker.from_roadmap([{"skill": "Imaginary Skill"}])

    def test_retrieving_one_skill_works(self):
        tracker = ProgressTracker.from_roadmap([{"skill": "Python"}])
        self.assertEqual("Python", tracker.get_progress("py")["skill"])
        self.assertIsNone(tracker.get_progress("SQL"))

    def test_retrieving_all_progress_works(self):
        tracker = ProgressTracker.from_roadmap([{"skill": "Python"}, {"skill": "SQL"}])
        self.assertEqual(2, len(tracker.get_all_progress()))

    def test_empty_progress_is_safe(self):
        tracker = ProgressTracker.from_roadmap([])
        self.assertEqual([], tracker.get_all_progress())
        self.assertEqual(0, tracker.summary()["completion_percentage"])

    def test_completion_percentage_is_calculated(self):
        tracker = ProgressTracker.from_roadmap([{"skill": "Python"}, {"skill": "SQL"}, {"skill": "Docker"}])
        tracker.update_progress("Python", "completed")
        tracker.update_progress("SQL", "completed")
        self.assertEqual(66.67, tracker.summary()["completion_percentage"])

    def test_zero_total_returns_zero_without_division_by_zero(self):
        self.assertEqual(0.0, ProgressTracker().summary()["completion_percentage"])

    def test_repeated_updates_are_deterministic(self):
        tracker = ProgressTracker.from_roadmap([{"skill": "Python"}])
        first = tracker.update_progress("Python", "in_progress", notes="Working")
        second = tracker.update_progress("Python", "in_progress", notes="Working")
        self.assertEqual(first, second)
        self.assertEqual(1, tracker.summary()["in_progress_count"])

    def test_completion_does_not_assign_proficiency_or_confidence(self):
        tracker = ProgressTracker.from_roadmap([{"skill": "Python"}])
        result = tracker.update_progress("Python", "completed")
        event = tracker.newly_completed_skills()[0]
        self.assertNotIn("proficiency", result)
        self.assertNotIn("confidence", result)
        self.assertIsNone(event["proficiency"])
        self.assertIsNone(event["confidence"])
        self.assertEqual("student marked this learning step as completed.", event["statement"])

    def test_newly_completed_skills_are_structured_and_not_duplicated_on_repeat(self):
        tracker = ProgressTracker.from_roadmap([{"skill": "Python"}])
        tracker.update_progress("Python", "completed")
        tracker.update_progress("Python", "completed")
        events = tracker.newly_completed_skills()
        self.assertEqual(1, len(events))
        self.assertEqual("roadmap_step_completed", events[0]["event_type"])

    def test_recompletion_after_reopening_is_a_new_event(self):
        tracker = ProgressTracker.from_roadmap([{"skill": "Python"}])
        tracker.update_progress("Python", "completed")
        tracker.update_progress("Python", "in_progress")
        tracker.update_progress("Python", "completed")
        self.assertEqual(2, len(tracker.newly_completed_skills()))

    def test_summary_counts_match_and_are_bounded(self):
        tracker = ProgressTracker.from_roadmap([
            {"skill": "Python"}, {"skill": "SQL", "status": "in_progress"}, {"skill": "Docker", "status": "completed"},
        ])
        summary = tracker.summary()
        self.assertEqual(3, summary["total_skills"])
        self.assertEqual((1, 1, 1), (summary["not_started_count"], summary["in_progress_count"], summary["completed_count"]))
        self.assertGreaterEqual(summary["completion_percentage"], 0)
        self.assertLessEqual(summary["completion_percentage"], 100)

    def test_invalid_input_types_and_duplicate_initial_records_are_rejected(self):
        with self.assertRaises(ValueError):
            ProgressTracker.from_roadmap("Python")
        with self.assertRaises(ValueError):
            ProgressTracker([{"skill": "Python", "status": "not_started"}, {"skill": "py", "status": "completed"}])
        tracker = ProgressTracker.from_roadmap([{"skill": "Python"}])
        with self.assertRaises(ValueError):
            tracker.update_progress("Python", "completed", notes=123)
        self.assertEqual("completed", tracker.update_progress("Python", "completed", notes="done")["status"])
        json.dumps(tracker.get_all_progress())
        json.dumps(tracker.newly_completed_skills())


if __name__ == "__main__":
    unittest.main()
