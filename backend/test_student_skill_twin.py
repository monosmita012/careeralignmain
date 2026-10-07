"""Focused unit tests for the source-aware Student Skill Twin foundation."""

import unittest

try:
    from .skill_taxonomy import SKILL_TAXONOMY
    from .student_skill_twin import (
        CONFIDENCE_LEVELS,
        PROFICIENCY_LEVELS,
        SOURCE_TYPES,
        InvalidEvidenceError,
        UnknownSkillError,
        merge_skill_evidence,
    )
except ImportError:  # Support discovery with backend/ as the start directory.
    from skill_taxonomy import SKILL_TAXONOMY
    from student_skill_twin import (
        CONFIDENCE_LEVELS,
        PROFICIENCY_LEVELS,
        SOURCE_TYPES,
        InvalidEvidenceError,
        UnknownSkillError,
        merge_skill_evidence,
    )


class StudentSkillTwinTests(unittest.TestCase):
    def test_canonical_skill_normalization(self) -> None:
        result = merge_skill_evidence([
            {
                "skill": " js ",
                "source": "resume",
                "evidence": "JavaScript listed in supplied resume text",
                "confidence": "medium",
            }
        ])
        self.assertEqual(result[0]["skill"], "JavaScript")

    def test_jupyter_notebook_is_preserved_as_its_own_skill(self) -> None:
        result = merge_skill_evidence([
            {
                "skill": " JUPYTER NOTEBOOK ",
                "source": "project",
                "evidence": "Used Jupyter Notebook for exploratory analysis",
                "confidence": "high",
            }
        ])
        self.assertEqual(result[0]["skill"], "Jupyter Notebook")
        self.assertEqual(result[0]["category"], "Data Analysis / BI")
        self.assertNotEqual(result[0]["skill"], "Python")
        self.assertEqual(len(SKILL_TAXONOMY), 93)
        self.assertNotIn("Jupyter Notebook", {item.canonical_name for item in SKILL_TAXONOMY})

    def test_unknown_skill_is_rejected(self) -> None:
        with self.assertRaises(UnknownSkillError):
            merge_skill_evidence([
                {
                    "skill": "Invented Framework",
                    "source": "resume",
                    "evidence": "Provided text",
                    "confidence": "low",
                }
            ])

    def test_single_source_skill_creation(self) -> None:
        result = merge_skill_evidence([
            {
                "skill": "Python",
                "source": "project",
                "evidence": "Used Python for data preparation",
                "confidence": "high",
            }
        ])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["sources"], ["project"])
        self.assertEqual(result[0]["proficiency"][0]["level"], "unknown")

    def test_multiple_sources_merge_to_one_skill(self) -> None:
        result = merge_skill_evidence([
            {"skill": "Python", "source": "education", "evidence": "Coursework mention", "confidence": "medium"},
            {"skill": "py", "source": "project", "evidence": "Project implementation mention", "confidence": "high"},
        ])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["skill"], "Python")
        self.assertEqual(result[0]["sources"], ["education", "project"])

    def test_multiple_evidence_items_are_retained(self) -> None:
        result = merge_skill_evidence([
            {"skill": "Python", "source": "resume", "evidence": "Resume phrase", "confidence": "medium"},
            {"skill": "Python", "source": "project", "evidence": "Project phrase", "confidence": "high"},
        ])
        self.assertEqual(len(result[0]["evidence"]), 2)
        self.assertEqual(
            {item["evidence"] for item in result[0]["evidence"]},
            {"Resume phrase", "Project phrase"},
        )

    def test_no_duplicate_canonical_skills_in_output(self) -> None:
        result = merge_skill_evidence([
            {"skill": "Python", "source": "resume", "evidence": "First phrase", "confidence": "medium"},
            {"skill": "python 3", "source": "project", "evidence": "Second phrase", "confidence": "high"},
        ])
        names = [item["skill"] for item in result]
        self.assertEqual(names, ["Python"])
        self.assertEqual(len(names), len(set(names)))

    def test_proficiency_is_separate_from_confidence(self) -> None:
        result = merge_skill_evidence([
            {
                "skill": "Python",
                "source": "self_declared",
                "evidence": "User supplied an explicit self-rating",
                "proficiency": "beginner",
                "confidence": "low",
            },
            {
                "skill": "Python",
                "source": "project",
                "evidence": "Project record names Python usage",
                "confidence": "high",
            },
        ])[0]
        self.assertIn("beginner", {item["level"] for item in result["proficiency"]})
        self.assertIn("unknown", {item["level"] for item in result["proficiency"]})
        self.assertEqual({item["level"] for item in result["confidence"]}, {"low", "high"})
        self_report = next(item for item in result["proficiency"] if item["source"] == "self_declared")
        self.assertEqual(self_report["basis"], "self_reported")

    def test_source_type_validation(self) -> None:
        self.assertEqual(len(SOURCE_TYPES), 8)
        with self.assertRaises(InvalidEvidenceError):
            merge_skill_evidence([
                {"skill": "Python", "source": "unknown_source", "evidence": "Text", "confidence": "low"}
            ])

    def test_invalid_proficiency_is_rejected(self) -> None:
        self.assertIn("exposure", PROFICIENCY_LEVELS)
        with self.assertRaises(InvalidEvidenceError):
            merge_skill_evidence([
                {
                    "skill": "Python",
                    "source": "project",
                    "evidence": "Supplied project evidence",
                    "proficiency": "guru",
                    "confidence": "medium",
                }
            ])

    def test_invalid_confidence_is_rejected(self) -> None:
        self.assertEqual(set(CONFIDENCE_LEVELS), {"low", "medium", "high"})
        with self.assertRaises(InvalidEvidenceError):
            merge_skill_evidence([
                {"skill": "Python", "source": "project", "evidence": "Supplied project evidence", "confidence": "certain"}
            ])

    def test_output_is_deterministic(self) -> None:
        records = [
            {"skill": "Python", "source": "project", "evidence": "B evidence", "confidence": "high"},
            {"skill": "js", "source": "resume", "evidence": "A evidence", "confidence": "medium"},
            {"skill": "Python", "source": "education", "evidence": "C evidence", "confidence": "low"},
        ]
        self.assertEqual(merge_skill_evidence(records), merge_skill_evidence(records))
        self.assertEqual(
            merge_skill_evidence(records),
            merge_skill_evidence(list(reversed(records))),
        )

    def test_taxonomy_supplies_canonical_names_and_categories(self) -> None:
        taxonomy = {item.canonical_name: item.category for item in SKILL_TAXONOMY}
        result = merge_skill_evidence([
            {"skill": "Postgres", "source": "resume", "evidence": "Postgres supplied phrase", "confidence": "medium"}
        ])[0]
        self.assertEqual(result["skill"], "PostgreSQL")
        self.assertEqual(result["category"], taxonomy["PostgreSQL"])
        self.assertNotIn("Invented Framework", taxonomy)

    def test_coursework_defaults_to_exposure_not_practical_proficiency(self) -> None:
        result = merge_skill_evidence([
            {"skill": "Python", "source": "education", "evidence": "Coursework supplied phrase", "confidence": "medium"}
        ])[0]
        self.assertEqual(result["proficiency"][0]["level"], "exposure")
        self.assertEqual(result["proficiency"][0]["basis"], "source_default")

    def test_identical_evidence_is_not_duplicated(self) -> None:
        item = {"skill": "Python", "source": "resume", "evidence": "Same supplied phrase", "confidence": "medium"}
        result = merge_skill_evidence([item, item])
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]["evidence"]), 1)


if __name__ == "__main__":
    unittest.main()
