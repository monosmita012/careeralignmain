"""Tests for rule-based resume feedback and its existing pipeline integrations."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from backend.main import app
from backend.resume_enhancement import UnknownResumeTargetRoleError, enhance_resume_text


COMPLETE_RESUME = """Alex Example
alex@example.com | +1 555 123 4567

Professional Summary
Data analyst using Python and SQL to turn operational data into reports.

Education
BSc in Information Systems, Example University

Skills
Python, SQL, Excel, Power BI

Projects
- Built a sales dashboard with Python and Power BI, reducing report time by 35%.

Experience
- Automated SQL reporting for 20 users and cut weekly processing by 4 hours.

Certifications
Power BI Data Analyst Associate

Achievements
Recognized for improving monthly reporting accuracy by 15 percent.
"""


class ResumeEnhancementServiceTests(unittest.TestCase):
    def test_valid_resume_returns_structured_feedback_and_strengths(self):
        result = enhance_resume_text(COMPLETE_RESUME)
        self.assertIn("summary", result)
        self.assertTrue(result["strengths"])
        self.assertEqual([], result["section_completeness"]["missing_sections"])
        self.assertIsNone(result["target_role_coverage"])
        self.assertIn("suggestions", result)
        self.assertNotIn("text", result)

    def test_common_sections_are_detected(self):
        result = enhance_resume_text(COMPLETE_RESUME)
        present = set(result["section_completeness"]["present"])
        self.assertEqual(
            {"contact", "professional_summary", "education", "skills", "projects", "experience", "certifications", "achievements"},
            present,
        )

    def test_missing_sections_are_reported_without_defect_score(self):
        result = enhance_resume_text("Jamie\nPython developer with two years of experience.")
        self.assertIn("education", result["section_completeness"]["missing_sections"])
        self.assertIn("relevant", result["section_completeness"]["applicability_note"])
        suggestion = next(item for item in result["suggestions"] if item["topic"] == "completeness")
        self.assertIn("if they apply", suggestion["suggestion"])

    def test_target_role_coverage_uses_existing_industry_twin(self):
        result = enhance_resume_text(COMPLETE_RESUME, target_role="Data Analyst")
        coverage = result["target_role_coverage"]
        self.assertEqual("Data Analyst", coverage["target_role"])
        represented = {item["skill"] for item in coverage["represented_skills"]}
        not_represented = {item["skill"] for item in coverage["not_represented_skills"]}
        self.assertIn("Python", represented)
        self.assertTrue(not_represented)
        self.assertTrue(all(item["role_frequency_percentage"] > 0 for item in coverage["not_represented_skills"]))
        self.assertIn("does not establish that you lack", coverage["note"])

    def test_no_target_role_returns_general_feedback_only(self):
        result = enhance_resume_text(COMPLETE_RESUME)
        self.assertIsNone(result["target_role_coverage"])

    def test_empty_invalid_resume_and_unknown_role_are_clear(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            enhance_resume_text(" \n ")
        with self.assertRaises(UnknownResumeTargetRoleError):
            enhance_resume_text(COMPLETE_RESUME, target_role="Invented Role")

    def test_content_checks_are_explicit_heuristics(self):
        result = enhance_resume_text("Skills\nPython\nExperience\n- Worked on Python tasks throughout the project team.\n- Worked on Python tasks throughout the project team.")
        checks = result["content_checks"]
        self.assertGreater(checks["vague_phrase_count"], 0)
        self.assertGreater(checks["weak_opening_count"], 0)
        self.assertGreater(checks["repeated_sentence_count"], 0)
        self.assertTrue(any(item["topic"] == "measurable_outcomes" for item in result["suggestions"]))


class ResumeEnhancementApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)

    def test_processing_student_twin_and_enhancement_api_still_work(self):
        content = COMPLETE_RESUME.encode("utf-8")
        processed_response = self.client.post(
            "/api/resume/process",
            files={"file": ("alex_resume.txt", content, "text/plain")},
        )
        self.assertEqual(200, processed_response.status_code, processed_response.text)
        processed = processed_response.json()
        self.assertIn("Python", processed["extracted_skills"])
        self.assertTrue(processed["skill_evidence"])

        twin_response = self.client.post(
            "/api/student-skill-twin", json={"records": processed["skill_evidence"]}
        )
        self.assertEqual(200, twin_response.status_code, twin_response.text)
        self.assertIn("Python", {row["skill"] for row in twin_response.json()})

        enhancement_response = self.client.post(
            "/api/resume/enhance",
            data={"target_role": "Data Analyst"},
            files={"file": ("alex_resume.txt", content, "text/plain")},
        )
        self.assertEqual(200, enhancement_response.status_code, enhancement_response.text)
        result = enhancement_response.json()
        self.assertEqual("alex_resume.txt", result["filename"])
        self.assertEqual("Data Analyst", result["target_role_coverage"]["target_role"])
        self.assertTrue(result["strengths"])
        self.assertTrue(result["suggestions"])
        self.assertNotIn("resume_text", result)

    def test_enhancement_without_role_and_invalid_payload(self):
        general = self.client.post(
            "/api/resume/enhance",
            files={"file": ("general.txt", b"Python developer.", "text/plain")},
        )
        self.assertEqual(200, general.status_code, general.text)
        self.assertIsNone(general.json()["target_role_coverage"])

        empty = self.client.post(
            "/api/resume/enhance",
            files={"file": ("empty.txt", b" \n", "text/plain")},
        )
        self.assertEqual(422, empty.status_code)
        unknown = self.client.post(
            "/api/resume/enhance",
            data={"target_role": "Invented Role"},
            files={"file": ("resume.txt", b"Python developer", "text/plain")},
        )
        self.assertEqual(422, unknown.status_code)


if __name__ == "__main__":
    unittest.main()
