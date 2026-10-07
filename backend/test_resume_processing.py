"""Focused resume parsing and CareerAlign pipeline integration tests."""

from __future__ import annotations

from io import BytesIO
import unittest
import xml.etree.ElementTree as ET
import zipfile

import fitz
from fastapi.testclient import TestClient

from backend.main import app
from backend.resume_processing import ResumeProcessingError, extract_resume_text, process_resume


def make_docx(paragraphs: list[str]) -> bytes:
    namespace = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    root = ET.Element(f"{{{namespace}}}document")
    body = ET.SubElement(root, f"{{{namespace}}}body")
    for text in paragraphs:
        paragraph = ET.SubElement(body, f"{{{namespace}}}p")
        run = ET.SubElement(paragraph, f"{{{namespace}}}r")
        ET.SubElement(run, f"{{{namespace}}}t").text = text
    xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    output = BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", xml)
    return output.getvalue()


def make_pdf(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    content = document.tobytes()
    document.close()
    return content


class ResumeProcessingTests(unittest.TestCase):
    def test_extracts_text_from_valid_pdf(self):
        text = extract_resume_text("candidate.pdf", make_pdf("Python SQL React"))
        self.assertIn("Python", text)
        result = process_resume("candidate.pdf", make_pdf("Python SQL React"))
        self.assertEqual(["Python", "SQL", "React"], result["extracted_skills"])

    def test_extracts_paragraphs_from_docx(self):
        text = extract_resume_text("candidate.docx", make_docx(["Python developer", "SQL reporting"]))
        self.assertIn("Python developer\nSQL reporting", text)

    def test_empty_and_malformed_documents_return_clear_errors(self):
        for filename, content in (("empty.txt", b"  \n"), ("broken.pdf", b"not a PDF"), ("broken.docx", b"not a zip")):
            with self.subTest(filename=filename), self.assertRaises(ResumeProcessingError):
                process_resume(filename, content)

    def test_canonical_skill_extraction_and_evidence_metadata(self):
        result = process_resume("candidate.txt", b"Built Python services with JS, React.js and Postgres.")
        self.assertEqual(["Python", "JavaScript", "React", "PostgreSQL"], result["extracted_skills"])
        self.assertEqual("resume", result["skill_evidence"][0]["source"])
        self.assertIn("Built Python services", result["skill_evidence"][0]["evidence"])
        self.assertEqual("unknown", result["skill_evidence"][0]["proficiency"])
        self.assertEqual("medium", result["skill_evidence"][0]["confidence"])
        self.assertNotIn("text", result)  # Raw resume text is not returned.

    def test_legacy_doc_and_unsupported_files_are_not_claimed_as_processed(self):
        with self.assertRaises(ResumeProcessingError) as legacy:
            process_resume("candidate.doc", b"binary")
        self.assertEqual(415, legacy.exception.status_code)
        with self.assertRaises(ResumeProcessingError) as unsupported:
            process_resume("candidate.rtf", b"text")
        self.assertEqual(415, unsupported.exception.status_code)


class ResumeApiEndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)

    def test_resume_upload_to_student_twin_gap_and_alignment(self):
        content = (
            b"Data Engineer resume. Built Python and SQL data pipelines. "
            b"Used Jupyter Notebook for exploratory analysis."
        )
        uploaded = self.client.post(
            "/api/resume/process",
            files={"file": ("candidate.txt", content, "text/plain")},
        )
        self.assertEqual(200, uploaded.status_code, uploaded.text)
        processed = uploaded.json()
        self.assertEqual("processed", processed["status"])
        self.assertEqual({"Python", "SQL"}, set(processed["extracted_skills"]))
        # Jupyter Notebook is intentionally informational: the existing free-text
        # extractor does not classify it as an industry requirement skill.

        # Resume evidence is combined with, not substituted for, manual evidence.
        records = processed["skill_evidence"] + [
            {
                "skill": "Jupyter Notebook",
                "source": "project",
                "evidence": "Used Jupyter Notebook for an exploratory analysis project.",
                "confidence": "high",
            },
            {
                "skill": "Python",
                "source": "self_declared",
                "evidence": "User-provided skill: Python",
                "confidence": "low",
            },
            {
                "skill": "React",
                "source": "self_declared",
                "evidence": "User-provided skill: React",
                "confidence": "low",
            }
        ]
        twin_response = self.client.post("/api/student-skill-twin", json={"records": records})
        self.assertEqual(200, twin_response.status_code, twin_response.text)
        twin = {row["skill"]: row for row in twin_response.json()}
        self.assertEqual({"Python", "SQL", "Jupyter Notebook", "React"}, set(twin))
        self.assertIn("resume", twin["Python"]["sources"])
        self.assertIn("self_declared", twin["Python"]["sources"])
        self.assertIn("self_declared", twin["React"]["sources"])
        self.assertIn("project", twin["Jupyter Notebook"]["sources"])

        payload = {"target_role": "Data Engineer", "records": records}
        gap = self.client.post("/api/skill-gap", json=payload)
        alignment = self.client.post("/api/career-alignment", json=payload)
        roadmap = self.client.post("/api/learning-roadmap", json=payload)
        self.assertEqual(200, gap.status_code, gap.text)
        self.assertEqual(200, alignment.status_code, alignment.text)
        self.assertEqual(200, roadmap.status_code, roadmap.text)
        self.assertEqual("Data Engineer", alignment.json()["career_readiness"]["target_role"])
        self.assertTrue(roadmap.json()["steps"])

    def test_upload_rejects_malformed_pdf_and_legacy_doc(self):
        malformed = self.client.post("/api/resume/process", files={"file": ("bad.pdf", b"bad", "application/pdf")})
        legacy = self.client.post("/api/resume/process", files={"file": ("old.doc", b"binary", "application/msword")})
        self.assertEqual(422, malformed.status_code)
        self.assertIn("Could not read", malformed.json()["detail"])
        self.assertEqual(415, legacy.status_code)
        self.assertIn("Legacy .doc", legacy.json()["detail"])


if __name__ == "__main__":
    unittest.main()
