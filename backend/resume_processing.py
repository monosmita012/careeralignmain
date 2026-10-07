"""Parse supported resume documents and extract CareerAlign skill evidence."""

from __future__ import annotations

from io import BytesIO
from pathlib import PurePath
import re
import xml.etree.ElementTree as ET
import zipfile

import fitz

try:
    from .skill_extractor import extract_skills
except ImportError:  # Support direct execution from the backend directory.
    from skill_extractor import extract_skills


MAX_RESUME_BYTES = 10 * 1024 * 1024
MAX_DOCX_XML_BYTES = 20 * 1024 * 1024


class ResumeProcessingError(ValueError):
    """An upload could not be safely parsed as a supported resume document."""

    def __init__(self, message: str, status_code: int = 422) -> None:
        super().__init__(message)
        self.status_code = status_code


def extract_resume_text(filename: str, content: bytes) -> str:
    """Extract text from UTF-8 TXT, PDF, or DOCX bytes without saving the file."""
    extension = PurePath(filename or "").suffix.casefold()
    if not filename or not extension:
        raise ResumeProcessingError("The uploaded resume must have a file extension.")
    if not isinstance(content, bytes) or not content:
        raise ResumeProcessingError("The uploaded resume is empty.")
    if len(content) > MAX_RESUME_BYTES:
        raise ResumeProcessingError("Resume files must be 10 MB or smaller.", 413)

    try:
        if extension == ".txt":
            text = content.decode("utf-8-sig")
        elif extension == ".pdf":
            with fitz.open(stream=content, filetype="pdf") as document:
                if document.is_encrypted:
                    raise ResumeProcessingError("Password-protected PDFs are not supported.")
                text = "\n".join(page.get_text("text") for page in document)
        elif extension == ".docx":
            text = _extract_docx_text(content)
        elif extension == ".doc":
            raise ResumeProcessingError(
                "Legacy .doc files cannot be parsed by the installed readers. Save the resume as .docx, .pdf, or .txt and upload it again.",
                415,
            )
        else:
            raise ResumeProcessingError(
                "Unsupported resume format. Upload a UTF-8 .txt, .pdf, or .docx file.", 415
            )
    except ResumeProcessingError:
        raise
    except Exception as exc:
        raise ResumeProcessingError(f"Could not read the uploaded {extension[1:].upper()} resume.") from exc

    if not text.strip():
        raise ResumeProcessingError(
            "No selectable text was found in the resume. Scanned image-only PDFs are not supported."
        )
    return text


def _extract_docx_text(content: bytes) -> str:
    with zipfile.ZipFile(BytesIO(content)) as archive:
        try:
            info = archive.getinfo("word/document.xml")
        except KeyError as exc:
            raise ResumeProcessingError("The DOCX file does not contain a Word document body.") from exc
        if info.file_size > MAX_DOCX_XML_BYTES:
            raise ResumeProcessingError("The DOCX document body is too large to process safely.")
        document_xml = archive.read(info)

    root = ET.fromstring(document_xml)
    word_namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraphs: list[str] = []
    for paragraph in root.iter(f"{word_namespace}p"):
        fragments: list[str] = []
        for node in paragraph.iter():
            if node.tag == f"{word_namespace}t" and node.text:
                fragments.append(node.text)
            elif node.tag == f"{word_namespace}tab":
                fragments.append("\t")
            elif node.tag == f"{word_namespace}br":
                fragments.append("\n")
        paragraphs.append("".join(fragments))
    return "\n".join(paragraphs)


def process_resume(filename: str, content: bytes) -> dict[str, object]:
    """Return safe text metadata and evidence for canonical skill mentions."""
    text = extract_resume_text(filename, content)
    skills = extract_skills(text)
    evidence_by_skill: dict[str, str] = {}
    for segment in re.split(r"(?<=[.!?])\s+|\n+", text):
        snippet = segment.strip()
        if not snippet:
            continue
        for skill in extract_skills(snippet):
            evidence_by_skill.setdefault(skill, snippet[:240])
    evidence = [
        {
            "skill": skill,
            "source": "resume",
            "evidence": evidence_by_skill.get(
                skill,
                f"CareerAlign's canonical skill extractor matched {skill} in the uploaded resume text.",
            ),
            "proficiency": "unknown",
            "confidence": "medium",
        }
        for skill in skills
    ]
    return {
        "status": "processed",
        "filename": PurePath(filename).name,
        "text_character_count": len(text),
        "extracted_skills": skills,
        "skill_evidence": evidence,
    }
