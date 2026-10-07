import unittest

from backend.resource_recommendation import (
    RESOURCE_CATALOG,
    UnknownSkillError,
    recommend_learning_resources,
)


def evidence(skill, proficiency="beginner", confidence="high", basis="coursework"):
    return {
        "skill": skill,
        "evidence": [{
            "source": "project",
            "evidence": f"Used {skill} in a small practice project.",
            "proficiency": proficiency,
            "confidence": confidence,
            "proficiency_basis": basis,
        }],
    }


class ResourceRecommendationTests(unittest.TestCase):
    def test_missing_skill_gets_recommendation(self):
        result = recommend_learning_resources("Data Engineer", [{"skill": "Python", "gap_type": "missing"}])
        self.assertGreater(result["total_recommendations"], 0)
        self.assertTrue(all(row["skill"] == "Python" for row in result["recommendations"]))

    def test_partial_skill_gets_recommendation(self):
        result = recommend_learning_resources("Data Engineer", [{"skill": "Python", "gap_type": "partial"}])
        self.assertGreater(result["total_recommendations"], 0)
        self.assertIn("partial", result["recommendations"][0]["reason"])

    def test_strongly_present_skill_is_skipped(self):
        twin = [evidence("Python", "intermediate", "high")]
        result = recommend_learning_resources("Data Engineer", [{"skill": "Python", "gap_type": "missing"}], twin)
        self.assertEqual([], result["recommendations"])

    def test_missing_skill_prefers_beginner_resources_first(self):
        result = recommend_learning_resources("Data Engineer", [{"skill": "Python", "gap_type": "missing"}])
        levels = [row["level"] for row in result["recommendations"]]
        self.assertEqual("beginner", levels[0])

    def test_partial_skill_selects_level_from_evidence(self):
        twin = [evidence("Python", "intermediate", "low")]
        result = recommend_learning_resources("Data Engineer", [{"skill": "Python", "gap_type": "partial"}], twin)
        self.assertEqual("intermediate", result["recommendations"][0]["level"])

    def test_multiple_resources_can_be_returned_for_one_skill(self):
        result = recommend_learning_resources("Data Engineer", [{"skill": "Python", "gap_type": "missing"}])
        self.assertEqual(2, result["total_recommendations"])

    def test_roadmap_order_is_preserved(self):
        result = recommend_learning_resources("Data Engineer", [
            {"skill": "Docker", "gap_type": "missing"},
            {"skill": "Python", "gap_type": "missing"},
        ])
        self.assertEqual(["Docker", "Python"], list(dict.fromkeys(row["skill"] for row in result["recommendations"])))

    def test_duplicate_skills_and_resources_are_not_duplicated(self):
        result = recommend_learning_resources("Data Engineer", [
            {"skill": "Python", "gap_type": "missing"},
            {"skill": "py", "gap_type": "partial"},
        ])
        ids = [row["resource_id"] for row in result["recommendations"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(2, len(ids))

    def test_known_skill_without_catalog_is_skipped(self):
        result = recommend_learning_resources("Data Engineer", [{"skill": "Ruby", "gap_type": "missing"}])
        self.assertEqual([], result["recommendations"])

    def test_empty_roadmap_returns_empty_result(self):
        self.assertEqual(
            {"target_role": "Data Engineer", "recommendations": [], "total_recommendations": 0},
            recommend_learning_resources("Data Engineer", {"target_role": "Data Engineer", "steps": []}),
        )

    def test_unknown_skill_raises_clear_error(self):
        with self.assertRaisesRegex(UnknownSkillError, "Unknown or empty learning skill"):
            recommend_learning_resources("Data Engineer", [{"skill": "MadeUpSkill", "gap_type": "missing"}])

    def test_output_is_deterministic(self):
        roadmap = [{"skill": "Python", "gap_type": "missing", "priority": "core"}]
        self.assertEqual(
            recommend_learning_resources("Data Engineer", roadmap),
            recommend_learning_resources("Data Engineer", roadmap),
        )

    def test_every_result_is_from_explicit_catalog(self):
        catalog_ids = {resource.resource_id for resource in RESOURCE_CATALOG}
        result = recommend_learning_resources("Data Engineer", [{"skill": "Python", "gap_type": "missing"}])
        self.assertTrue(all(row["resource_id"] in catalog_ids for row in result["recommendations"]))

    def test_each_recommendation_has_explainable_reason_and_required_fields(self):
        result = recommend_learning_resources("Data Engineer", [{"skill": "Apache Spark", "gap_type": "missing", "priority": "core"}])
        required = {"skill", "resource_id", "title", "resource_type", "level", "provider", "description", "url", "reason"}
        self.assertTrue(result["recommendations"])
        for row in result["recommendations"]:
            self.assertTrue(required.issubset(row))
            self.assertIn("Apache Spark", row["reason"])
            self.assertIn("Data Engineer", row["reason"])

    def test_explicitly_included_strong_skill_can_be_recommended(self):
        twin = [evidence("Python", "advanced", "high")]
        result = recommend_learning_resources(
            "Data Engineer", [{"skill": "Python", "gap_type": "partial"}], twin, include_strongly_present=True
        )
        self.assertTrue(result["recommendations"])

    def test_prioritized_gap_input_and_alias_are_supported(self):
        result = recommend_learning_resources("Data Engineer", {
            "target_role": "Data Engineer",
            "prioritized_gaps": [{"skill": "py", "gap_type": "missing", "priority_label": "common"}],
        })
        self.assertEqual("Python", result["recommendations"][0]["skill"])
        self.assertIn("common", result["recommendations"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
