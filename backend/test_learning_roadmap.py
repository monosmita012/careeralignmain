"""Focused tests for CareerAlign's rule-based personalized roadmap."""

import unittest

try:
    from .learning_roadmap import (
        PrerequisiteCycleError,
        UnknownTargetRoleError,
        generate_learning_roadmap,
    )
    from .skill_taxonomy import normalize_skill
    from .student_skill_twin import merge_skill_evidence
except ImportError:  # Support discovery with backend/ as the start directory.
    from learning_roadmap import PrerequisiteCycleError, UnknownTargetRoleError, generate_learning_roadmap
    from skill_taxonomy import normalize_skill
    from student_skill_twin import merge_skill_evidence


ROLE = "Data Engineer"


def industry_rows():
    definitions = [
        ("JavaScript", "Programming Languages", 20.0, "common"),
        ("React", "Frontend", 10.0, "supporting"),
        ("Node.js", "Backend", 18.0, "common"),
        ("Express.js", "Backend", 3.0, "occasional"),
        ("Python", "Programming Languages", 40.0, "core"),
        ("SQL", "Databases", 25.0, "common"),
        ("Apache Spark", "Data Engineering", 10.0, "supporting"),
        ("Linux", "DevOps / Cloud", 10.0, "supporting"),
        ("Docker", "DevOps / Cloud", 30.0, "core"),
        ("Kubernetes", "DevOps / Cloud", 3.0, "occasional"),
    ]
    return [
        {
            "career_role": ROLE,
            "skill": skill,
            "category": category,
            "role_record_count": int(frequency),
            "role_record_total": 100,
            "role_frequency_percentage": frequency,
            "role_association_ratio": 1.0,
            "priority": priority,
        }
        for skill, category, frequency, priority in definitions
    ]


def gap_entry(skill, gap_type="missing", priority_score=None):
    canonical = normalize_skill(skill)
    source = next(row for row in industry_rows() if row["skill"] == canonical)
    return {
        "skill": skill,
        "category": source["category"],
        "role_frequency_percentage": source["role_frequency_percentage"],
        "role_association_ratio": source["role_association_ratio"],
        "priority": source["priority"],
        "priority_score": priority_score,
        "reason": f"{gap_type} evidence for {skill}",
        **({"partial_reasons": ["proficiency_exposure"]} if gap_type == "partial" else {}),
    }


def gap_result(missing=(), partial=(), role=ROLE):
    return {
        "target_role": role,
        "matched_skills": [],
        "partial_skills": [gap_entry(skill, "partial") for skill in partial],
        "missing_skills": [gap_entry(skill, "missing") for skill in missing],
    }


def student_evidence(skill, source="project", proficiency="intermediate", confidence="high"):
    return {
        "skill": skill,
        "source": source,
        "evidence": f"Temporary in-memory {source} evidence for {skill}",
        "proficiency": proficiency,
        "confidence": confidence,
    }


def student_twin(*evidence):
    return merge_skill_evidence(list(evidence))


class LearningRoadmapTests(unittest.TestCase):
    def build(self, gaps, student=(), **kwargs):
        return generate_learning_roadmap(
            ROLE,
            student,
            gaps,
            industry_skill_twin=industry_rows(),
            **kwargs,
        )

    def test_simple_missing_skill_becomes_step(self):
        result = self.build(gap_result(missing=["SQL"]), prerequisite_map={})
        self.assertEqual([step["skill"] for step in result["steps"]], ["SQL"])
        self.assertEqual(result["steps"][0]["gap_type"], "missing")

    def test_prerequisite_is_ordered_before_dependent(self):
        result = self.build(gap_result(missing=["React", "JavaScript"]))
        skills = [step["skill"] for step in result["steps"]]
        self.assertLess(skills.index("JavaScript"), skills.index("React"))

    def test_strong_existing_prerequisite_is_not_added(self):
        existing = student_twin(student_evidence("JavaScript"))
        result = self.build(gap_result(missing=["React"]), student=existing)
        self.assertEqual([step["skill"] for step in result["steps"]], ["React"])
        self.assertEqual(result["steps"][0]["satisfied_prerequisites"], ["JavaScript"])

    def test_missing_prerequisite_is_inserted(self):
        result = self.build(gap_result(missing=["React"]))
        by_skill = {step["skill"]: step for step in result["steps"]}
        self.assertIn("JavaScript", by_skill)
        self.assertTrue(by_skill["JavaScript"]["added_as_prerequisite"])
        self.assertIsNone(by_skill["JavaScript"]["gap_type"])
        self.assertLess(by_skill["JavaScript"]["step"], by_skill["React"]["step"])
        self.assertIn("prerequisite", by_skill["JavaScript"]["reason"])

    def test_multiple_prerequisites_are_handled(self):
        result = self.build(gap_result(missing=["Apache Spark"]))
        skills = [step["skill"] for step in result["steps"]]
        self.assertIn("Python", skills)
        self.assertIn("SQL", skills)
        self.assertLess(skills.index("Python"), skills.index("Apache Spark"))
        self.assertLess(skills.index("SQL"), skills.index("Apache Spark"))
        spark = next(step for step in result["steps"] if step["skill"] == "Apache Spark")
        self.assertEqual(spark["prerequisites"], ["Python", "SQL"])

    def test_duplicate_gap_skills_do_not_duplicate_steps(self):
        gaps = gap_result(missing=["React", "React.js"])
        result = self.build(gaps)
        names = [step["skill"] for step in result["steps"]]
        self.assertEqual(names.count("React"), 1)
        self.assertEqual(names.count("JavaScript"), 1)

    def test_partial_skill_is_an_in_progress_step(self):
        result = self.build(gap_result(partial=["SQL"]), prerequisite_map={})
        self.assertEqual(result["steps"][0]["gap_type"], "partial")
        self.assertEqual(result["steps"][0]["status"], "in_progress")

    def test_priority_is_preserved_when_no_prerequisite_orders_steps(self):
        gaps = gap_result(missing=["React", "Express.js"])
        alignment = {
            "target_role": ROLE,
            "prioritized_gaps": [
                {"skill": "React", "gap_type": "missing", "priority_score": 50.0, "reason": "lower"},
                {"skill": "Express.js", "gap_type": "missing", "priority_score": 90.0, "reason": "higher"},
            ],
        }
        result = self.build(gaps, career_alignment=alignment, prerequisite_map={})
        skills = [step["skill"] for step in result["steps"]]
        self.assertLess(skills.index("Express.js"), skills.index("React"))

    def test_empty_gap_result_returns_empty_roadmap(self):
        result = self.build(gap_result(), student=())
        self.assertEqual(result["steps"], [])
        self.assertEqual(result["total_steps"], 0)

    def test_unknown_role_is_handled_clearly(self):
        with self.assertRaisesRegex(UnknownTargetRoleError, "Unknown target role"):
            generate_learning_roadmap(
                "Unknown Role", (), gap_result(role="Unknown Role"), industry_skill_twin=industry_rows()
            )

    def test_cycle_in_prerequisite_map_is_rejected(self):
        with self.assertRaisesRegex(PrerequisiteCycleError, "cycle"):
            self.build(
                gap_result(missing=["React"]),
                prerequisite_map={"React": ("JavaScript",), "JavaScript": ("React",)},
            )

    def test_repeated_execution_is_deterministic(self):
        gaps = gap_result(missing=["Apache Spark", "React"], partial=["Docker"])
        student = student_twin(student_evidence("Python"))
        first = self.build(gaps, student=student)
        second = self.build(gaps, student=student)
        self.assertEqual(first, second)

    def test_steps_originate_from_gaps_or_explicit_prerequisites(self):
        gaps = gap_result(missing=["React", "Apache Spark"])
        result = self.build(gaps)
        original = {"React", "Apache Spark"}
        allowed_prerequisites = {"JavaScript", "Python", "SQL"}
        self.assertTrue({step["skill"] for step in result["steps"]}.issubset(original | allowed_prerequisites))

    def test_every_step_has_an_explanation(self):
        result = self.build(gap_result(missing=["React"]))
        self.assertTrue(all(step["reason"].strip() for step in result["steps"]))

    def test_multiple_sources_make_prerequisite_strongly_present(self):
        student = student_twin(
            student_evidence("JavaScript", source="education", proficiency="exposure", confidence="medium"),
            student_evidence("JavaScript", source="project", proficiency="intermediate", confidence="high"),
        )
        result = self.build(gap_result(missing=["React"]), student=student)
        self.assertNotIn("JavaScript", {step["skill"] for step in result["steps"]})

    def test_weak_prerequisite_is_added_as_in_progress(self):
        student = student_twin(student_evidence("JavaScript", source="education", proficiency="exposure"))
        result = self.build(gap_result(missing=["React"]), student=student)
        javascript = next(step for step in result["steps"] if step["skill"] == "JavaScript")
        self.assertEqual(javascript["status"], "in_progress")
        self.assertTrue(javascript["added_as_prerequisite"])

    def test_occasional_gap_is_marked_optional(self):
        result = self.build(gap_result(missing=["Express.js"]))
        express = next(step for step in result["steps"] if step["skill"] == "Express.js")
        self.assertTrue(express["optional"])
        self.assertIn("Optional", express["reason"])

    def test_gap_and_career_alignment_target_must_agree(self):
        alignment = {"target_role": "Different Role", "prioritized_gaps": []}
        with self.assertRaisesRegex(ValueError, "Target role mismatch"):
            self.build(gap_result(missing=["SQL"]), career_alignment=alignment)


if __name__ == "__main__":
    unittest.main()
