"""Focused tests for gap prioritization and Career Readiness scoring."""

import unittest

try:
    from .career_alignment import (
        UnknownTargetRoleError,
        calculate_career_readiness,
        prioritize_skill_gaps,
    )
except ImportError:  # Support discovery with backend/ as the start directory.
    from career_alignment import UnknownTargetRoleError, calculate_career_readiness, prioritize_skill_gaps


def industry_rows():
    definitions = [
        ("Python", "Programming Languages", 40.0, 1.5, "core", 40),
        ("SQL", "Databases", 25.0, 1.0, "common", 25),
        ("Docker", "DevOps / Cloud", 10.0, 1.2, "supporting", 10),
        ("React", "Frontend", 4.0, 0.8, "occasional", 4),
        ("Node.js", "Backend", 0.0, 0.0, "occasional", 0),
    ]
    return [
        {
            "career_role": "Data Analyst",
            "skill": skill,
            "category": category,
            "role_record_count": count,
            "role_record_total": 100,
            "role_frequency_percentage": frequency,
            "all_role_record_count": count,
            "all_role_record_total": 100,
            "all_role_frequency_percentage": frequency,
            "role_association_ratio": ratio,
            "priority": priority,
        }
        for skill, category, frequency, ratio, priority, count in definitions
    ]


def gap_result(statuses, role="Data Analyst", extra_zero=False):
    result = {
        "target_role": role,
        "matched_skills": [],
        "partial_skills": [],
        "missing_skills": [],
    }
    for row in industry_rows():
        skill = row["skill"]
        state = statuses.get(skill, "missing")
        if row["role_frequency_percentage"] == 0 and not extra_zero:
            continue
        entry = {
            "skill": skill,
            "category": row["category"],
            "role_frequency_percentage": row["role_frequency_percentage"],
            "role_association_ratio": row["role_association_ratio"],
            "priority": row["priority"],
            "role_record_count": row["role_record_count"],
            "role_record_total": row["role_record_total"],
        }
        if state == "partial":
            entry["partial_reasons"] = ["proficiency_beginner"]
        result[f"{state}_skills"].append(entry)
    for group in ("matched", "partial", "missing"):
        result[f"{group}_count"] = len(result[f"{group}_skills"])
    return result


class CareerAlignmentTests(unittest.TestCase):
    def test_fully_matched_profile_scores_maximum(self):
        gap = gap_result({skill: "matched" for skill in ("Python", "SQL", "Docker", "React")})
        result = calculate_career_readiness(gap, industry_rows())
        self.assertEqual(result["career_readiness_score"], 100.0)

    def test_completely_missing_profile_scores_minimum(self):
        result = calculate_career_readiness(gap_result({}), industry_rows())
        self.assertEqual(result["career_readiness_score"], 0.0)

    def test_partial_skills_receive_half_credit(self):
        gap = gap_result({"Python": "partial"})
        result = calculate_career_readiness(gap, industry_rows())
        self.assertEqual(result["earned_weight_points"], 2.0)
        self.assertEqual(result["career_readiness_score"], 20.0)

    def test_core_has_more_score_effect_than_occasional(self):
        core_missing = calculate_career_readiness(
            gap_result({"Python": "missing", "SQL": "matched", "Docker": "matched", "React": "matched"}),
            industry_rows(),
        )["career_readiness_score"]
        occasional_missing = calculate_career_readiness(
            gap_result({"Python": "matched", "SQL": "matched", "Docker": "matched", "React": "missing"}),
            industry_rows(),
        )["career_readiness_score"]
        self.assertLess(core_missing, occasional_missing)

    def test_common_has_more_score_effect_than_supporting(self):
        common_missing = calculate_career_readiness(
            gap_result({"Python": "matched", "SQL": "missing", "Docker": "matched", "React": "matched"}),
            industry_rows(),
        )["career_readiness_score"]
        supporting_missing = calculate_career_readiness(
            gap_result({"Python": "matched", "SQL": "matched", "Docker": "missing", "React": "matched"}),
            industry_rows(),
        )["career_readiness_score"]
        self.assertLess(common_missing, supporting_missing)

    def test_missing_core_has_higher_priority_than_missing_occasional(self):
        result = prioritize_skill_gaps(gap_result({}), industry_rows())
        scores = {item["skill"]: item["priority_score"] for item in result["prioritized_gaps"]}
        self.assertGreater(scores["Python"], scores["React"])

    def test_prioritization_contains_only_partial_and_missing_gaps(self):
        gap = gap_result({"Python": "matched", "SQL": "partial"})
        result = prioritize_skill_gaps(gap, industry_rows())
        self.assertNotIn("Python", {item["skill"] for item in result["prioritized_gaps"]})
        self.assertIn("SQL", {item["skill"] for item in result["prioritized_gaps"]})
        self.assertEqual(result["partial_count"], 1)

    def test_partial_core_retains_core_priority_and_partial_gap_type(self):
        result = prioritize_skill_gaps(gap_result({"Python": "partial"}), industry_rows())
        python = next(item for item in result["prioritized_gaps"] if item["skill"] == "Python")
        react = next(item for item in result["prioritized_gaps"] if item["skill"] == "React")
        self.assertEqual(python["gap_type"], "partial")
        self.assertEqual(python["priority_label"], "core")
        self.assertGreater(python["priority_score"], react["priority_score"])

    def test_zero_frequency_rows_do_not_affect_score(self):
        statuses = {skill: "matched" for skill in ("Python", "SQL", "Docker", "React")}
        ordinary = calculate_career_readiness(gap_result(statuses), industry_rows())
        with_zero_row = calculate_career_readiness(gap_result(statuses, extra_zero=True), industry_rows())
        self.assertEqual(ordinary["career_readiness_score"], with_zero_row["career_readiness_score"])
        self.assertEqual(ordinary["total_positive_frequency_skills"], with_zero_row["total_positive_frequency_skills"])
        self.assertNotIn("Node.js", {item["skill"] for item in with_zero_row["components"]})

    def test_empty_student_skill_twin_is_safe(self):
        result = calculate_career_readiness(gap_result({}), industry_rows())
        self.assertEqual(result["career_readiness_score"], 0.0)
        self.assertEqual(result["matched_count"], 0)
        self.assertEqual(result["partial_count"], 0)
        self.assertEqual(result["missing_count"], 4)

    def test_unknown_target_role_has_clear_error(self):
        gap = gap_result({}, role="Unknown Role")
        with self.assertRaisesRegex(UnknownTargetRoleError, "Unknown target role"):
            calculate_career_readiness(gap, industry_rows())

    def test_repeated_calculation_is_deterministic(self):
        gap = gap_result({"Python": "matched", "SQL": "partial"})
        self.assertEqual(
            calculate_career_readiness(gap, industry_rows()),
            calculate_career_readiness(gap, industry_rows()),
        )
        self.assertEqual(
            prioritize_skill_gaps(gap, industry_rows()),
            prioritize_skill_gaps(gap, industry_rows()),
        )

    def test_output_contains_explainable_breakdown(self):
        result = calculate_career_readiness(gap_result({"Python": "partial"}), industry_rows())
        self.assertIn("score_formula", result)
        self.assertIn("priority_weights", result)
        self.assertIn("earned_weight_points", result)
        self.assertEqual(len(result["components"]), 4)
        self.assertEqual(result["components"][0]["skill"], "Docker")

    def test_counts_match_skill_gap_analysis(self):
        gap = gap_result({"Python": "matched", "SQL": "partial"})
        result = calculate_career_readiness(gap, industry_rows())
        self.assertEqual(result["matched_count"], gap["matched_count"])
        self.assertEqual(result["partial_count"], gap["partial_count"])
        self.assertEqual(result["missing_count"], gap["missing_count"])

    def test_score_is_within_zero_and_one_hundred(self):
        statuses = [
            {},
            {"Python": "partial"},
            {skill: "matched" for skill in ("Python", "SQL", "Docker", "React")},
            {"Python": "matched", "SQL": "partial", "Docker": "missing", "React": "matched"},
        ]
        for state in statuses:
            with self.subTest(state=state):
                score = calculate_career_readiness(gap_result(state), industry_rows())["career_readiness_score"]
                self.assertGreaterEqual(score, 0.0)
                self.assertLessEqual(score, 100.0)

    def test_role_with_no_positive_frequency_skills_has_unavailable_score(self):
        only_zero = [row for row in industry_rows() if row["skill"] == "Node.js"]
        gap = {"target_role": "Data Analyst", "matched_skills": [], "partial_skills": [], "missing_skills": []}
        result = calculate_career_readiness(gap, only_zero)
        self.assertIsNone(result["career_readiness_score"])
        self.assertFalse(result["score_available"])
        self.assertEqual(result["score_status"], "no_positive_frequency_role_skills")

    def test_priority_output_preserves_industry_fields_and_reasons(self):
        result = prioritize_skill_gaps(gap_result({}), industry_rows())
        python = next(item for item in result["prioritized_gaps"] if item["skill"] == "Python")
        self.assertEqual(python["category"], "Programming Languages")
        self.assertEqual(python["industry_frequency_percentage"], 40.0)
        self.assertEqual(python["industry_priority"], "core")
        self.assertIn("40.00%", python["reason"])
        self.assertIn("association ratio", python["reason"])


if __name__ == "__main__":
    unittest.main()
