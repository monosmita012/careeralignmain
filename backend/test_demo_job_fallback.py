"""Tests for the small, explicitly marked job-search demo fallback."""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import DEMO_JOBS_PATH, _load_demo_jobs, app
from backend.skill_taxonomy import SKILL_TAXONOMY, normalize_skill


class DemoJobFallbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)

    def test_demo_dataset_loads_with_required_fields_and_canonical_skills(self):
        self.assertTrue(DEMO_JOBS_PATH.is_file())
        jobs = _load_demo_jobs()
        self.assertGreaterEqual(len(jobs), 10)
        self.assertLessEqual(len(jobs), 15)

        required = {"job_id", "title", "career_role", "company", "skills"}
        taxonomy = {definition.canonical_name for definition in SKILL_TAXONOMY}
        for job in jobs:
            self.assertTrue(required.issubset(job))
            self.assertTrue(job["company"].startswith((
                "CareerAlign Demo", "SkillTwin", "FuturePath"
            )))
            self.assertIsInstance(job["skills"], list)
            self.assertTrue(job["skills"])
            self.assertTrue(all(normalize_skill(skill) == skill for skill in job["skills"]))
            self.assertTrue(set(job["skills"]).issubset(taxonomy))

    def test_demo_job_ids_are_unique_and_all_approved_roles_are_represented(self):
        jobs = _load_demo_jobs()
        ids = [job["job_id"] for job in jobs]
        self.assertEqual(len(ids), len(set(ids)))
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
            {job["career_role"] for job in jobs},
        )

    def test_existing_remote_results_are_preferred(self):
        real_job = {
            "job_id": "REMOTE-001",
            "title": "Data Analyst",
            "career_role": "Data Analyst",
            "company": "Remote Provider",
            "description": "",
            "tags": ["Python"],
            "location": "Remote",
            "url": "https://jobs.example.test/1",
            "source": "Remotive",
        }
        with patch("backend.main._fetch_remote_jobs", side_effect=[[real_job], []]):
            response = self.client.post("/api/jobs/search", json={"skills": ["Python"]})

        self.assertEqual(200, response.status_code, response.text)
        payload = response.json()
        self.assertFalse(payload["is_demo_fallback"])
        self.assertEqual("live_results", payload["source"])
        self.assertEqual(["REMOTE-001"], [job["job_id"] for job in payload["jobs"]])

    def test_demo_jobs_are_used_when_real_search_has_no_usable_results(self):
        with patch("backend.main._fetch_remote_jobs", return_value=[]):
            response = self.client.post("/api/jobs/search", json={"skills": [], "limit": 30})

        self.assertEqual(200, response.status_code, response.text)
        payload = response.json()
        self.assertTrue(payload["is_demo_fallback"])
        self.assertEqual("demo_fallback", payload["source"])
        self.assertEqual(len(_load_demo_jobs()), payload["total_found"])
        self.assertTrue(all(job["source"] == "CareerAlign demo dataset" for job in payload["jobs"]))
        self.assertTrue(all(job["url"] == "" for job in payload["jobs"]))

    def test_demo_jobs_are_used_when_real_rows_do_not_match_search_skills(self):
        unrelated_job = {
            "title": "Unrelated role",
            "company": "Remote Provider",
            "description": "",
            "tags": ["Tableau"],
            "location": "Remote",
            "url": "https://jobs.example.test/2",
            "source": "Remotive",
        }
        with patch("backend.main._fetch_remote_jobs", side_effect=[[unrelated_job], []]):
            response = self.client.post("/api/jobs/search", json={"skills": ["Python"]})

        self.assertEqual(200, response.status_code, response.text)
        self.assertTrue(response.json()["is_demo_fallback"])
        self.assertGreater(response.json()["total_found"], 0)

    def test_job_matching_api_accepts_and_ranks_demo_job_records(self):
        jobs = _load_demo_jobs()
        student_records = [{
            "skill": "Python",
            "source": "project",
            "evidence": "Temporary unit-test evidence for ranking.",
            "proficiency": "intermediate",
            "confidence": "high",
        }]
        response = self.client.post("/api/job-matching", json={
            "student_records": student_records,
            "jobs": jobs,
        })

        self.assertEqual(200, response.status_code, response.text)
        payload = response.json()
        self.assertEqual(len(jobs), payload["total_jobs"])
        self.assertEqual("DEMO-DE-001", payload["matches"][0]["job_id"])
        top = payload["matches"][0]
        self.assertEqual("Data Engineer", top["career_role"])
        self.assertEqual("FuturePath Systems", top["company"])
        self.assertIn("Python", top["matched_skills"])
        self.assertTrue(top["missing_skills"])
        self.assertGreater(top["score"], payload["matches"][-1]["score"])


if __name__ == "__main__":
    unittest.main()
