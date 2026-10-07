"""Focused tests for CareerAlign's explainable Skill Gap Analysis."""

import unittest

try:
    from .skill_gap_analysis import (
        UnknownTargetRoleError,
        analyze_skill_gap,
    )
    from .student_skill_twin import merge_skill_evidence
except ImportError:  # Support discovery with backend/ as the start directory.
    from skill_gap_analysis import UnknownTargetRoleError, analyze_skill_gap
    from student_skill_twin import merge_skill_evidence


def industry_rows():
    return [
        {
            "career_role": "Data Analyst",
            "skill": "Python",
            "category": "Programming Languages",
            "role_record_count": 40,
            "role_record_total": 100,
            "role_frequency_percentage": 40.0,
            "role_association_ratio": 2.0,
            "priority": "core",
        },
        {
            "career_role": "Data Analyst",
            "skill": "SQL",
            "category": "Databases",
            "role_record_count": 20,
            "role_record_total": 100,
            "role_frequency_percentage": 20.0,
            "role_association_ratio": 0.8,
            "priority": "common",
        },
        {
            "career_role": "Data Analyst",
            "skill": "React",
            "category": "Frontend",
            "role_record_count": 0,
            "role_record_total": 100,
            "role_frequency_percentage": 0.0,
            "role_association_ratio": 0.0,
            "priority": "occasional",
        },
        {
            "career_role": "Data Analyst",
            "skill": "Docker",
            "category": "DevOps / Cloud",
            "role_record_count": 5,
            "role_record_total": 100,
            "role_frequency_percentage": 5.0,
            "role_association_ratio": 1.1,
            "priority": "supporting",
        },
        {
            "career_role": "Project Manager",
            "skill": "Jira",
            "category": "Tools / Version Control",
            "role_record_count": 30,
            "role_record_total": 100,
            "role_frequency_percentage": 30.0,
            "role_association_ratio": 1.5,
            "priority": "core",
        },
    ]


def student(records):
    return merge_skill_evidence(records)


def evidence(skill, source="project", proficiency="intermediate", confidence="high", text=None):
    return {
        "skill": skill,
        "source": source,
        "evidence": text or f"Supplied {source} evidence for {skill}",
        "proficiency": proficiency,
        "confidence": confidence,
    }


class SkillGapAnalysisTests(unittest.TestCase):
    def test_fully_matched_student_profile(self):
        profile = student([
            evidence("Python", proficiency="advanced"),
            evidence("SQL", proficiency="intermediate", confidence="medium"),
            evidence("Docker"),
        ])
        result = analyze_skill_gap(profile, "Data Analyst", industry_rows())
        self.assertEqual(result["matched_count"], 3)
        self.assertEqual(result["partial_count"], 0)
        self.assertEqual(result["missing_count"], 0)

    def test_completely_missing_student_profile(self):
        result = analyze_skill_gap([], "Data Analyst", industry_rows())
        self.assertEqual(result["matched_count"], 0)
        self.assertEqual(result["partial_count"], 0)
        self.assertEqual(result["missing_count"], 3)
        self.assertEqual({item["skill"] for item in result["missing_skills"]}, {"Python", "SQL", "Docker"})

    def test_beginner_or_exposure_is_partial(self):
        for level in ("beginner", "exposure"):
            with self.subTest(level=level):
                result = analyze_skill_gap(
                    student([evidence("Python", proficiency=level)]),
                    "Data Analyst",
                    industry_rows(),
                )
                self.assertEqual(result["partial_count"], 1)
                self.assertIn(f"proficiency_{level}", result["partial_skills"][0]["partial_reasons"])

    def test_low_confidence_is_partial_not_missing(self):
        result = analyze_skill_gap(
            student([evidence("Python", proficiency="advanced", confidence="low")]),
            "Data Analyst",
            industry_rows(),
        )
        self.assertEqual(result["partial_count"], 1)
        self.assertIn("low_confidence", result["partial_skills"][0]["partial_reasons"])
        self.assertNotIn("Python", {item["skill"] for item in result["missing_skills"]})

    def test_multiple_sources_for_same_skill_remain_one_skill(self):
        profile = student([
            evidence("Python", source="education", proficiency="exposure", confidence="medium"),
            evidence("py", source="project", proficiency="intermediate", confidence="high"),
        ])
        result = analyze_skill_gap(profile, "Data Analyst", industry_rows())
        python_matches = [item for item in result["matched_skills"] if item["skill"] == "Python"]
        self.assertEqual(len(python_matches), 1)
        self.assertEqual(python_matches[0]["student_sources"], ["education", "project"])
        self.assertEqual(len(python_matches[0]["student_evidence"]), 2)

    def test_unknown_target_role_raises_clear_error(self):
        with self.assertRaisesRegex(UnknownTargetRoleError, "Unknown target role"):
            analyze_skill_gap([], "Astronaut", industry_rows())

    def test_zero_frequency_industry_rows_are_not_requirements(self):
        result = analyze_skill_gap([], "Data Analyst", industry_rows())
        all_skills = {
            item["skill"]
            for group in ("matched_skills", "partial_skills", "missing_skills")
            for item in result[group]
        }
        self.assertNotIn("React", all_skills)
        self.assertEqual(result["missing_count"], 3)

    def test_no_duplicate_skills_in_any_output_group(self):
        profile = student([
            evidence("Python", text="Same evidence"),
            evidence("py", source="resume", text="Another evidence"),
            evidence("SQL"),
        ])
        result = analyze_skill_gap(profile, "Data Analyst", industry_rows())
        for group in ("matched_skills", "partial_skills", "missing_skills"):
            names = [item["skill"] for item in result[group]]
            self.assertEqual(len(names), len(set(names)))

    def test_group_counts_match_output_lists(self):
        profile = student([
            evidence("Python"),
            evidence("SQL", proficiency="beginner"),
        ])
        result = analyze_skill_gap(profile, "Data Analyst", industry_rows())
        self.assertEqual(result["matched_count"], len(result["matched_skills"]))
        self.assertEqual(result["partial_count"], len(result["partial_skills"]))
        self.assertEqual(result["missing_count"], len(result["missing_skills"]))
        self.assertEqual((result["matched_count"], result["partial_count"], result["missing_count"]), (1, 1, 1))

    def test_repeated_analysis_is_deterministic(self):
        profile = student([
            evidence("SQL", proficiency="exposure"),
            evidence("Python", proficiency="advanced"),
        ])
        first = analyze_skill_gap(profile, "Data Analyst", industry_rows())
        second = analyze_skill_gap(profile, "Data Analyst", industry_rows())
        self.assertEqual(first, second)

    def test_student_skills_not_required_by_role_are_not_reported_as_missing(self):
        profile = student([evidence("Java", source="project")])
        result = analyze_skill_gap(profile, "Data Analyst", industry_rows())
        self.assertNotIn("Java", {item["skill"] for item in result["missing_skills"]})
        self.assertNotIn("Java", {item["skill"] for item in result["matched_skills"] + result["partial_skills"]})

    def test_industry_evidence_is_preserved(self):
        result = analyze_skill_gap([], "Data Analyst", industry_rows())
        python = next(item for item in result["missing_skills"] if item["skill"] == "Python")
        self.assertEqual(python["category"], "Programming Languages")
        self.assertEqual(python["role_frequency_percentage"], 40.0)
        self.assertEqual(python["role_association_ratio"], 2.0)
        self.assertEqual(python["priority"], "core")

    def test_unknown_student_skill_uses_taxonomy_validation(self):
        with self.assertRaises(ValueError):
            analyze_skill_gap(
                [{"skill": "Unlisted Skill", "sources": [], "evidence": []}],
                "Data Analyst",
                industry_rows(),
            )


if __name__ == "__main__":
    unittest.main()
