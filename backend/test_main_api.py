"""FastAPI integration smoke tests for the active CareerAlign API."""

import unittest
from uuid import uuid4

import pyarrow.parquet as pq
from fastapi.testclient import TestClient
from backend.main import app
from backend.progress_repository import MongoProgressRepository
from backend.skill_gap_analysis import DEFAULT_INDUSTRY_TWIN


class CareerAlignApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()
        rows = pq.read_table(DEFAULT_INDUSTRY_TWIN).to_pylist()
        cls.role = "Data Engineer"
        positive = [row["skill"] for row in rows if row["career_role"] == cls.role and row["role_frequency_percentage"] > 0]
        cls.skill1 = "Python"
        cls.skill2 = next(skill for skill in positive if skill not in {cls.skill1, "JavaScript"})
        cls.missing_skill = next(skill for skill in positive if skill not in {cls.skill1, cls.skill2})
        cls.records = [
            {"skill": cls.skill1, "source": "project", "evidence": "Built and maintained a Python data pipeline.", "proficiency": "intermediate", "confidence": "high"},
            {"skill": cls.skill2, "source": "education", "evidence": f"Studied {cls.skill2} in coursework.", "proficiency": "beginner", "confidence": "low"},
        ]
        cls.progress_student_id = f"api-test-{uuid4().hex}@example.invalid"

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)
        try:
            repository = MongoProgressRepository()
            repository._collection.delete_many({"student_id": cls.progress_student_id})
            repository.close()
        except Exception:
            pass

    def role_payload(self):
        return {"target_role": self.role, "records": self.records}

    def test_health_check(self):
        response = self.client.get("/api/health")
        self.assertEqual(200, response.status_code)
        self.assertEqual({"status": "ok"}, response.json())

    def test_skill_extraction_returns_canonical_skills(self):
        response = self.client.post("/api/skills/extract", json={"text": "Python, SQL, React and Docker"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(["Python", "SQL", "React", "Docker"], response.json()["extracted_skills"])

    def test_student_skill_twin_accepts_valid_evidence(self):
        response = self.client.post("/api/student-skill-twin", json={"records": self.records})
        self.assertEqual(200, response.status_code)
        self.assertEqual({"Python", self.skill2}, {row["skill"] for row in response.json()})

    def test_skill_gap_returns_all_three_groups(self):
        response = self.client.post("/api/skill-gap", json=self.role_payload())
        self.assertEqual(200, response.status_code, response.text)
        payload = response.json()
        self.assertIn(self.skill1, [row["skill"] for row in payload["matched_skills"]])
        self.assertIn(self.skill2, [row["skill"] for row in payload["partial_skills"]])
        self.assertIn(self.missing_skill, [row["skill"] for row in payload["missing_skills"]])

    def test_career_alignment_returns_readiness_and_explanation_data(self):
        response = self.client.post("/api/career-alignment", json=self.role_payload())
        self.assertEqual(200, response.status_code, response.text)
        payload = response.json()
        self.assertIn("career_readiness", payload)
        self.assertIn("prioritized_gaps", payload)
        self.assertIn("matched_skills", payload)
        self.assertIn("partial_skills", payload)
        self.assertIn("missing_skills", payload)

    def test_learning_roadmap_returns_steps(self):
        response = self.client.post("/api/learning-roadmap", json=self.role_payload())
        self.assertEqual(200, response.status_code, response.text)
        self.assertIn("steps", response.json())

    def test_jupyter_notebook_does_not_block_roadmap_generation(self):
        records = [
            *self.records,
            {
                "skill": "Jupyter Notebook",
                "source": "project",
                "evidence": "Used Jupyter Notebook for an exploratory analysis project.",
                "confidence": "high",
            },
        ]
        twin = self.client.post("/api/student-skill-twin", json={"records": records})
        self.assertEqual(200, twin.status_code, twin.text)
        self.assertIn("Jupyter Notebook", [row["skill"] for row in twin.json()])
        self.assertIn("Python", [row["skill"] for row in twin.json()])

        roadmap = self.client.post(
            "/api/learning-roadmap",
            json={"target_role": self.role, "records": records},
        )
        self.assertEqual(200, roadmap.status_code, roadmap.text)
        self.assertEqual(self.role, roadmap.json()["target_role"])
        self.assertTrue(roadmap.json()["steps"])
        self.assertNotIn("Jupyter Notebook", [step["skill"] for step in roadmap.json()["steps"]])

    def test_learning_resources_returns_catalog_recommendations(self):
        response = self.client.post("/api/learning-resources", json=self.role_payload())
        self.assertEqual(200, response.status_code, response.text)
        self.assertIn("recommendations", response.json())

    def test_project_recommendations_return_catalog_projects(self):
        response = self.client.post("/api/project-recommendations", json=self.role_payload())
        self.assertEqual(200, response.status_code, response.text)
        self.assertIn("recommendations", response.json())

    def test_job_matching_returns_ranked_jobs(self):
        response = self.client.post("/api/job-matching", json={
            "student_records": self.records,
            "jobs": [{"job_id": "J1", "title": "Data Engineer", "career_role": self.role, "company": "Example", "skills": [self.skill1, self.skill2, self.missing_skill]}],
        })
        self.assertEqual(200, response.status_code, response.text)
        self.assertEqual("J1", response.json()["matches"][0]["job_id"])

    def test_progress_initialize_update_summary_and_event(self):
        init = self.client.post("/api/progress/initialize", json={"student_id": self.progress_student_id, "roadmap": {"target_role": self.role, "steps": [{"skill": self.skill1}, {"skill": self.skill2}]}})
        self.assertEqual(200, init.status_code, init.text)
        roadmap_id = init.json()["roadmap_id"]
        update = self.client.put("/api/progress/update", json={"student_id": self.progress_student_id, "roadmap_id": roadmap_id, "skill": self.skill1, "status": "completed"})
        self.assertEqual(200, update.status_code, update.text)
        self.assertEqual("completed", update.json()["progress"]["status"])
        params = {"student_id": self.progress_student_id, "roadmap_id": roadmap_id}
        self.assertEqual(50.0, self.client.get("/api/progress/summary", params=params).json()["completion_percentage"])
        self.assertEqual(1, self.client.get("/api/progress/completed-events", params=params).json()["total_events"])
        self.assertEqual(2, self.client.get("/api/progress", params=params).json()["total_skills"])
        self.assertEqual(self.skill1, self.client.get(f"/api/progress/skill/{self.skill1}", params=params).json()["skill"])

    def test_invalid_skill_returns_client_error_without_traceback(self):
        response = self.client.post("/api/student-skill-twin", json={"records": [{"skill": "NotReal", "source": "project", "evidence": "x", "confidence": "high"}]})
        self.assertEqual(422, response.status_code)
        self.assertNotIn("Traceback", response.text)

    def test_invalid_progress_status_returns_client_error_without_traceback(self):
        init = self.client.post("/api/progress/initialize", json={"student_id": self.progress_student_id, "roadmap": {"steps": [{"skill": self.skill1}]}})
        response = self.client.put("/api/progress/update", json={"student_id": self.progress_student_id, "roadmap_id": init.json()["roadmap_id"], "skill": self.skill1, "status": "expert"})
        self.assertEqual(422, response.status_code)
        self.assertNotIn("Traceback", response.text)

    def test_role_alias_is_preserved_and_conflict_is_rejected(self):
        response = self.client.post("/api/skill-gap", json={"role": self.role, "records": self.records})
        self.assertEqual(200, response.status_code, response.text)
        conflict = self.client.post("/api/skill-gap", json={"role": self.role, "target_role": "Project Manager", "records": []})
        self.assertEqual(422, conflict.status_code)

    def test_existing_role_classifier_route_behavior_is_preserved(self):
        roles = self.client.get("/api/roles")
        self.assertEqual(200, roles.status_code, roles.text)
        self.assertEqual(7, len(roles.json()["roles"]))
        self.assertEqual(
            {
                "Data Analyst",
                "Data Engineer",
                "Business Analyst",
                "Project Manager",
                "Product Manager",
                "QA Automation Engineer",
                "System Administrator",
            },
            set(roles.json()["roles"]),
        )

        prediction = self.client.post(
            "/api/predict-role",
            json={"job_description": "Data Engineer building Python and SQL data pipelines."},
        )
        self.assertEqual(200, prediction.status_code, prediction.text)
        self.assertGreaterEqual(len(prediction.json()), 1)
        self.assertTrue(all("role" in result and "confidence" in result for result in prediction.json()))
        self.assertTrue(all(result["role"] in roles.json()["roles"] for result in prediction.json()))

        # Existing clients that send skills remain accepted by the same TF-IDF pipeline.
        legacy_input = self.client.post("/api/predict-role", json={"skills": ["Python", "SQL"]})
        self.assertEqual(200, legacy_input.status_code, legacy_input.text)

    def test_legacy_skill_gap_fields_remain_accepted(self):
        self.assertIn("/api/skill-gap", {route.path for route in app.routes})
        # If the legacy raw dataset is absent, its established structured 503
        # is expected; if present, the route continues returning its result.
        response = self.client.post("/api/skill-gap", json={"skills": ["Python"], "role": self.role})
        self.assertIn(response.status_code, {200, 503})
        if response.status_code == 503:
            self.assertFalse(response.json()["detail"]["available"])


if __name__ == "__main__":
    unittest.main()
