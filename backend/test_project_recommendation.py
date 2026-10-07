import unittest

from backend.project_recommendation import PROJECT_CATALOG, recommend_projects
from backend.skill_gap_analysis import UnknownTargetRoleError
from backend.student_skill_twin import UnknownSkillError, merge_skill_evidence


def gap_result(role="Data Engineer", missing=(), partial=()):
    return {
        "target_role": role,
        "missing_skills": [dict(item) if isinstance(item, dict) else {"skill": item} for item in missing],
        "partial_skills": [dict(item) if isinstance(item, dict) else {"skill": item} for item in partial],
    }


class ProjectRecommendationTests(unittest.TestCase):
    def test_project_for_missing_skill_is_recommended(self):
        result = recommend_projects("Data Engineer", gap_result(missing=["Apache Spark"]))
        self.assertTrue(result["recommendations"])
        self.assertTrue(any("Apache Spark" in row["addressed_missing_skills"] for row in result["recommendations"]))

    def test_multi_missing_project_ranks_above_single_gap_project(self):
        result = recommend_projects("Data Engineer", gap_result(missing=["Python", "SQL", "Apache Spark", "Docker"]))
        by_id = {row["project_id"]: row for row in result["recommendations"]}
        self.assertGreater(by_id["big-data-processing"]["score"], by_id["linux-server-monitoring"]["score"])

    def test_high_priority_missing_skills_influence_ranking(self):
        gaps = gap_result(missing=[
            {"skill": "Apache Spark", "priority": "core"},
            {"skill": "Python", "priority": "occasional"},
            {"skill": "SQL", "priority": "occasional"},
            {"skill": "Docker", "priority": "occasional"},
        ])
        result = recommend_projects("Data Engineer", gaps)
        by_id = {row["project_id"]: row for row in result["recommendations"]}
        self.assertGreater(by_id["big-data-processing"]["score"], by_id["etl-data-pipeline"]["score"])

    def test_partial_skills_contribute(self):
        result = recommend_projects("Data Engineer", gap_result(partial=["Apache Airflow"]))
        self.assertTrue(any("Apache Airflow" in row["addressed_partial_skills"] for row in result["recommendations"]))

    def test_strongly_present_skills_alone_do_not_trigger_projects(self):
        twin = merge_skill_evidence([{
            "skill": "Python", "source": "project", "evidence": "Built and maintained a Python data pipeline.",
            "proficiency": "intermediate", "confidence": "high",
        }])
        result = recommend_projects("Data Engineer", gap_result(missing=["Python"]), student_skill_twin=twin)
        self.assertEqual([], result["recommendations"])

    def test_project_unrelated_to_gaps_is_excluded(self):
        result = recommend_projects("Data Engineer", gap_result(missing=["Power BI"]))
        self.assertNotIn("linux-server-monitoring", [row["project_id"] for row in result["recommendations"]])

    def test_multiple_projects_can_be_returned(self):
        result = recommend_projects("Data Engineer", gap_result(missing=["Python"]))
        self.assertGreater(result["total_recommendations"], 1)

    def test_duplicate_projects_are_not_returned(self):
        result = recommend_projects("Data Engineer", gap_result(missing=["Python", "SQL", "Docker"]))
        ids = [row["project_id"] for row in result["recommendations"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_duplicate_gap_skills_do_not_distort_score(self):
        once = recommend_projects("Data Engineer", gap_result(missing=["Python", "SQL"]))
        repeated = recommend_projects("Data Engineer", gap_result(missing=["Python", "Python", "SQL"]))
        self.assertEqual(once, repeated)

    def test_empty_gap_result_returns_empty_list(self):
        result = recommend_projects("Data Engineer", gap_result())
        self.assertEqual([], result["recommendations"])
        self.assertEqual(0, result["total_recommendations"])

    def test_unknown_role_raises_clear_error(self):
        with self.assertRaises(UnknownTargetRoleError):
            recommend_projects("Imaginary Role", gap_result("Imaginary Role", missing=["Python"]))

    def test_unknown_skill_raises_clear_error(self):
        with self.assertRaisesRegex(UnknownSkillError, "Unknown or empty gap skill"):
            recommend_projects("Data Engineer", gap_result(missing=["Not A Real Skill"]))

    def test_equal_score_projects_keep_deterministic_catalog_order(self):
        result = recommend_projects("Data Engineer", gap_result(missing=["Docker"]))
        selected_ids = [row["project_id"] for row in result["recommendations"]]
        expected = [project.project_id for project in PROJECT_CATALOG if "Docker" in project.skills]
        self.assertEqual(expected, selected_ids)

    def test_recommendations_explain_addressed_skills(self):
        result = recommend_projects("Data Engineer", gap_result(missing=["Apache Spark"], partial=["Docker"]))
        self.assertTrue(result["recommendations"])
        for row in result["recommendations"]:
            self.assertIn("addressed_missing_skills", row)
            self.assertIn("addressed_partial_skills", row)
            self.assertTrue(row["reason"])
            self.assertIn("Data Engineer", row["reason"])
            self.assertIn("Score:", row["reason"])

    def test_scores_are_deterministic(self):
        gaps = gap_result(missing=[{"skill": "Apache Spark", "priority": "core"}], partial=["Docker"])
        self.assertEqual(
            recommend_projects("Data Engineer", gaps),
            recommend_projects("Data Engineer", gaps),
        )

    def test_every_recommendation_is_from_the_explicit_catalog(self):
        ids = {project.project_id for project in PROJECT_CATALOG}
        result = recommend_projects("Data Engineer", gap_result(missing=["Python", "SQL", "Docker"]))
        self.assertTrue(all(row["project_id"] in ids for row in result["recommendations"]))

    def test_priority_wrapper_and_aliases_are_accepted(self):
        result = recommend_projects("Data Engineer", prioritized_gaps={
            "target_role": "Data Engineer",
            "prioritized_gaps": [{"skill": "py", "gap_type": "missing", "industry_priority": "core"}],
        })
        python_rows = [row for row in result["recommendations"] if "Python" in row["addressed_missing_skills"]]
        self.assertTrue(python_rows)
        self.assertIn("core priority", python_rows[0]["reason"])


if __name__ == "__main__":
    unittest.main()
