"""CareerAlign's active FastAPI application.

Run from the repository root with ``uvicorn backend.main:app --reload``.
Dataset and model resources are loaded only when available; their absence does
not prevent the API from starting.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
from urllib.parse import quote

import joblib
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.data_loader import load_candidates, load_dma, load_jobs
from backend.server import (
    _filter_by_location,
    _lower_text,
    _score_job,
    _fetch_remote_jobs,
    analyze_github_profile,
)
from backend.skill_gap import skill_gap
from backend.career_alignment import build_career_alignment
from backend.job_matching import match_jobs
from backend.learning_roadmap import generate_learning_roadmap
from backend.progress_repository import MongoProgressRepository, ProgressNotFoundError, ProgressStorageError
from backend.project_recommendation import recommend_projects
from backend.resource_recommendation import recommend_learning_resources
from backend.resume_processing import MAX_RESUME_BYTES, ResumeProcessingError, process_resume
from backend.resume_enhancement import UnknownResumeTargetRoleError, enhance_resume_file
from backend.skill_extractor import extract_skills
from backend.skill_taxonomy import normalize_skill
from backend.skill_gap_analysis import UnknownTargetRoleError, analyze_skill_gap as run_skill_gap_analysis
from backend.student_skill_twin import InvalidEvidenceError, UnknownSkillError, merge_skill_evidence
from backend.youtube_learning_videos import (
    YouTubeAPIError,
    YouTubeConfigurationError,
    search_learning_videos,
)


BASE_DIR = Path(__file__).parent
VECTORIZER_PATH = BASE_DIR / "models" / "tfidf_vectorizer.joblib"
CLASSIFIER_PATH = BASE_DIR / "models" / "role_classifier.joblib"
DEMO_JOBS_PATH = BASE_DIR / "data" / "processed" / "careeralign_demo_jobs.json"
store: dict[str, Any] = {
    "jobs": None,
    "candidates": None,
    "dma": None,
    "vectorizer": None,
    "model": None,
}
logger = logging.getLogger("careeralign")

app = FastAPI(title="CareerAlign API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Content-Type"],
)


class SkillGapRequest(BaseModel):
    skills: list[str] | None = None
    role: str | None = None
    target_role: str | None = None
    records: list[dict[str, Any]] | None = None
    student_records: list[dict[str, Any]] | None = None


class SkillExtractionRequest(BaseModel):
    text: str


class StudentSkillTwinRequest(BaseModel):
    records: list[dict[str, Any]]


class StudentRoleRequest(BaseModel):
    records: list[dict[str, Any]] | None = None
    student_records: list[dict[str, Any]] | None = None
    role: str | None = None
    target_role: str | None = None


class JobMatchingRequest(BaseModel):
    student_records: list[dict[str, Any]]
    jobs: list[dict[str, Any]]


class ProgressInitializeRequest(BaseModel):
    student_id: str
    roadmap: Any


class ProgressUpdateRequest(BaseModel):
    student_id: str
    roadmap_id: str
    skill: str
    status: str
    notes: str | None = None


class JobSearchRequest(BaseModel):
    skills: list[str] = Field(default_factory=list)
    syllabus_data_url: str | None = None
    location: str | None = None
    limit: int = Field(default=30, ge=1, le=100)


class GitHubRequest(BaseModel):
    username: str = ""


_progress_repository: MongoProgressRepository | None = None


def _client_error(exc: Exception) -> HTTPException:
    status_code = 404 if isinstance(exc, KeyError) else 422
    detail = str(exc) or "Invalid request."
    return HTTPException(status_code=status_code, detail=detail)


def _request_records(payload: StudentRoleRequest | SkillGapRequest) -> list[dict[str, Any]]:
    records = getattr(payload, "records", None)
    student_records = getattr(payload, "student_records", None)
    if records is not None and student_records is not None and records != student_records:
        raise HTTPException(status_code=422, detail="Provide either records or student_records, not conflicting values.")
    selected = records if records is not None else student_records
    if selected is None:
        raise HTTPException(status_code=422, detail="A records or student_records list is required.")
    return selected


def _request_role(payload: StudentRoleRequest) -> str:
    role = (payload.target_role or payload.role or "").strip()
    if payload.role and payload.target_role and payload.role.strip() != payload.target_role.strip():
        raise HTTPException(status_code=422, detail="role and target_role must identify the same career role.")
    if not role:
        raise HTTPException(status_code=422, detail="target_role (or role) is required.")
    return role


def _build_student_twin(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    try:
        return merge_skill_evidence(records)
    except (UnknownSkillError, InvalidEvidenceError, ValueError) as exc:
        raise _client_error(exc) from exc


def _analyze_request(payload: StudentRoleRequest) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    role = _request_role(payload)
    twin = _build_student_twin(_request_records(payload))
    try:
        gaps = run_skill_gap_analysis(twin, role)
    except (UnknownSkillError, UnknownTargetRoleError, InvalidEvidenceError, ValueError, FileNotFoundError) as exc:
        raise _client_error(exc) from exc
    return role, twin, gaps


def _unavailable(resource: str, paths: list[Path]) -> dict[str, Any]:
    missing = [str(path) for path in paths if not path.exists()]
    return {
        "available": False,
        "error": f"{resource} is unavailable because required project data or model files are missing.",
        "missing_files": missing,
    }


def _load_demo_jobs() -> list[dict[str, Any]]:
    """Read the small, explicit development-only fallback job catalog."""
    with DEMO_JOBS_PATH.open("r", encoding="utf-8") as demo_file:
        jobs = json.load(demo_file)
    if not isinstance(jobs, list) or any(not isinstance(job, dict) for job in jobs):
        raise ValueError(f"Demo jobs must be a JSON list of objects: {DEMO_JOBS_PATH}")
    return jobs


@app.on_event("startup")
def load_available_resources() -> None:
    """Load resources independently so missing optional assets never block startup."""
    resources = (
        ("jobs", load_jobs),
        ("candidates", load_candidates),
        ("dma", load_dma),
    )
    for key, loader in resources:
        try:
            store[key] = loader()
        except (FileNotFoundError, OSError, KeyError, ValueError) as exc:
            store[key] = None
            logger.warning("CareerAlign resource %s unavailable: %s", key, exc)

    if VECTORIZER_PATH.is_file() and CLASSIFIER_PATH.is_file():
        try:
            vectorizer = joblib.load(VECTORIZER_PATH)
            model = joblib.load(CLASSIFIER_PATH)
            if getattr(model, "n_features_in_", None) != len(vectorizer.vocabulary_):
                raise ValueError("Saved classifier and TF-IDF vectorizer have incompatible feature sizes.")
            store["vectorizer"] = vectorizer
            store["model"] = model
        except Exception as exc:
            store["vectorizer"] = None
            store["model"] = None
            logger.warning("CareerAlign classifier artifacts unavailable: %s", exc)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/roles")
@app.get("/api/skill-gap/roles")
def roles() -> dict[str, Any]:
    model = store.get("model")
    if model is None:
        raise HTTPException(
            status_code=503,
            detail=_unavailable("Role list", [CLASSIFIER_PATH]),
        )
    return {"roles": sorted(model.classes_.tolist())}


@app.post("/api/predict-role")
def predict_role(payload: dict[str, Any]) -> list[dict[str, Any]]:
    model = store.get("model")
    vectorizer = store.get("vectorizer")
    if model is None or vectorizer is None:
        raise HTTPException(
            status_code=503,
            detail=_unavailable("Role prediction", [VECTORIZER_PATH, CLASSIFIER_PATH]),
        )

    # The approved classifier is trained on job-description text. Keep the
    # legacy skills-list input accepted, while preferring explicit text input.
    text = payload.get("job_description", payload.get("text"))
    if text is None and "skills" in payload:
        skills = payload["skills"]
        if not isinstance(skills, list) or any(not isinstance(skill, str) for skill in skills):
            raise HTTPException(status_code=422, detail="'skills' must be a list of strings")
        text = ", ".join(skills)
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(status_code=422, detail="Provide non-empty job_description text (or a skills list).")

    probabilities = model.predict_proba(vectorizer.transform([text]))[0]
    top = probabilities.argsort()[::-1][:3]
    return [
        {"role": model.classes_[i], "confidence": round(float(probabilities[i]) * 100, 1)}
        for i in top
    ]


@app.post("/api/skill-gap")
def analyze_skill_gap(payload: SkillGapRequest) -> dict[str, Any]:
    if payload.records is not None or payload.student_records is not None:
        role = (payload.target_role or payload.role or "").strip()
        if payload.role and payload.target_role and payload.role.strip() != payload.target_role.strip():
            raise HTTPException(status_code=422, detail="role and target_role must identify the same career role.")
        if not role:
            raise HTTPException(status_code=422, detail="target_role (or role) is required.")
        records = _request_records(payload)
        twin = _build_student_twin(records)
        try:
            return run_skill_gap_analysis(twin, role)
        except (UnknownSkillError, UnknownTargetRoleError, InvalidEvidenceError, ValueError) as exc:
            raise _client_error(exc) from exc

    jobs = store.get("jobs")
    if jobs is None:
        paths = [BASE_DIR / "data" / "raw" / "all_job_post.csv"]
        raise HTTPException(status_code=503, detail=_unavailable("Skill-gap analysis", paths))
    selected_role = (payload.role or payload.target_role or "").strip()
    return skill_gap(payload.skills or [], selected_role, jobs, store.get("candidates"))


@app.post("/api/skills/extract")
def skills_extract(payload: SkillExtractionRequest) -> dict[str, Any]:
    return {"extracted_skills": extract_skills(payload.text)}


@app.post("/api/resume/process")
async def resume_process(file: UploadFile = File(...)) -> dict[str, Any]:
    """Parse an uploaded resume and return canonical skill evidence only."""
    try:
        contents = await file.read(MAX_RESUME_BYTES + 1)
        return process_resume(file.filename or "", contents)
    except ResumeProcessingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    finally:
        await file.close()


@app.post("/api/resume/enhance")
async def resume_enhance(
    file: UploadFile = File(...),
    target_role: str | None = Form(default=None),
) -> dict[str, Any]:
    """Analyze a resume with deterministic checks and existing role evidence."""
    try:
        contents = await file.read(MAX_RESUME_BYTES + 1)
        return enhance_resume_file(file.filename or "", contents, target_role)
    except ResumeProcessingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except UnknownResumeTargetRoleError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        await file.close()


@app.post("/api/student-skill-twin")
def student_skill_twin(payload: StudentSkillTwinRequest) -> list[dict[str, Any]]:
    return _build_student_twin(payload.records)


@app.post("/api/career-alignment")
def career_alignment(payload: StudentRoleRequest) -> dict[str, Any]:
    role, twin, gaps = _analyze_request(payload)
    try:
        alignment = build_career_alignment(gaps)
    except (UnknownSkillError, UnknownTargetRoleError, ValueError, FileNotFoundError) as exc:
        raise _client_error(exc) from exc
    return {**alignment, **{
        "matched_skills": gaps["matched_skills"],
        "partial_skills": gaps["partial_skills"],
        "missing_skills": gaps["missing_skills"],
        "matched_count": gaps["matched_count"],
        "partial_count": gaps["partial_count"],
        "missing_count": gaps["missing_count"],
    }}


@app.post("/api/learning-roadmap")
def learning_roadmap(payload: StudentRoleRequest) -> dict[str, Any]:
    role, twin, gaps = _analyze_request(payload)
    try:
        alignment = build_career_alignment(gaps)
        return generate_learning_roadmap(role, twin, gaps, career_alignment=alignment)
    except (UnknownSkillError, UnknownTargetRoleError, InvalidEvidenceError, ValueError, FileNotFoundError) as exc:
        raise _client_error(exc) from exc


@app.post("/api/learning-resources")
def learning_resources(payload: StudentRoleRequest) -> dict[str, Any]:
    role, twin, gaps = _analyze_request(payload)
    try:
        alignment = build_career_alignment(gaps)
        roadmap = generate_learning_roadmap(role, twin, gaps, career_alignment=alignment)
        return recommend_learning_resources(role, roadmap, twin)
    except (UnknownSkillError, UnknownTargetRoleError, InvalidEvidenceError, ValueError, FileNotFoundError) as exc:
        raise _client_error(exc) from exc


@app.post("/api/youtube-learning-videos")
def youtube_learning_videos(payload: StudentRoleRequest) -> dict[str, Any]:
    """Return a compact set of YouTube tutorials for a role's real skill gaps."""
    role, _twin, gaps = _analyze_request(payload)
    try:
        alignment = build_career_alignment(gaps)
        return search_learning_videos(
            role,
            alignment["prioritized_gaps"],
            gaps["matched_skills"],
        )
    except YouTubeConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except YouTubeAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except (UnknownSkillError, UnknownTargetRoleError, InvalidEvidenceError, ValueError, FileNotFoundError) as exc:
        raise _client_error(exc) from exc


@app.post("/api/project-recommendations")
def project_recommendations(payload: StudentRoleRequest) -> dict[str, Any]:
    role, twin, gaps = _analyze_request(payload)
    try:
        alignment = build_career_alignment(gaps)
        return recommend_projects(role, gaps, alignment["prioritized_gaps"], twin)
    except (UnknownSkillError, UnknownTargetRoleError, InvalidEvidenceError, ValueError, FileNotFoundError) as exc:
        raise _client_error(exc) from exc


@app.post("/api/job-matching")
def job_matching(payload: JobMatchingRequest) -> dict[str, Any]:
    twin = _build_student_twin(payload.student_records)
    try:
        return match_jobs(twin, payload.jobs)
    except (UnknownSkillError, InvalidEvidenceError, ValueError) as exc:
        raise _client_error(exc) from exc


def _current_progress_repository() -> MongoProgressRepository:
    global _progress_repository
    if _progress_repository is None:
        _progress_repository = MongoProgressRepository()
    return _progress_repository


def _progress_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ProgressStorageError):
        return HTTPException(status_code=503, detail=str(exc))
    return _client_error(exc)


@app.post("/api/progress/initialize")
def progress_initialize(payload: ProgressInitializeRequest) -> dict[str, Any]:
    try:
        result = _current_progress_repository().initialize(payload.student_id, payload.roadmap)
    except (UnknownSkillError, ValueError, ProgressStorageError) as exc:
        raise _progress_error(exc) from exc
    return {
        "progress": result["progress"],
        "summary": result["summary"],
        "roadmap_id": result["roadmap_id"],
        "target_role": result["target_role"],
    }


@app.put("/api/progress/update")
def progress_update(payload: ProgressUpdateRequest) -> dict[str, Any]:
    try:
        result = _current_progress_repository().update(
            payload.student_id, payload.roadmap_id, payload.skill, payload.status, payload.notes
        )
    except (UnknownSkillError, ValueError, ProgressNotFoundError, ProgressStorageError) as exc:
        raise _progress_error(exc) from exc
    canonical = normalize_skill(payload.skill)
    record = next(row for row in result["progress"] if row["skill"] == canonical)
    return {"progress": record, "newly_completed_skills": result["newly_completed_skills"]}


@app.get("/api/progress/summary")
def progress_summary(
    student_id: str = Query(..., min_length=1),
    roadmap_id: str = Query(..., min_length=1),
) -> dict[str, Any]:
    try:
        return _current_progress_repository().get_all(student_id, roadmap_id)["summary"]
    except (ValueError, ProgressNotFoundError, ProgressStorageError) as exc:
        raise _progress_error(exc) from exc


@app.get("/api/progress/completed-events")
def progress_completed_events(
    student_id: str = Query(..., min_length=1),
    roadmap_id: str = Query(..., min_length=1),
) -> dict[str, Any]:
    try:
        events = _current_progress_repository().get_all(student_id, roadmap_id)["newly_completed_skills"]
    except (ValueError, ProgressNotFoundError, ProgressStorageError) as exc:
        raise _progress_error(exc) from exc
    return {"newly_completed_skills": events, "total_events": len(events)}


@app.get("/api/progress/skill/{skill}")
def progress_for_skill(
    skill: str,
    student_id: str = Query(..., min_length=1),
    roadmap_id: str = Query(..., min_length=1),
) -> dict[str, Any]:
    try:
        result = _current_progress_repository().get_all(student_id, roadmap_id)
        normalized = normalize_skill(skill)
        record = next((row for row in result["progress"] if row["skill"] == normalized), None)
    except (UnknownSkillError, ValueError, ProgressNotFoundError, ProgressStorageError) as exc:
        raise _progress_error(exc) from exc
    if record is None:
        raise HTTPException(status_code=404, detail=f"No progress record exists for {skill!r}.")
    return record


@app.get("/api/progress")
def all_progress(
    student_id: str = Query(..., min_length=1),
    roadmap_id: str = Query(..., min_length=1),
) -> dict[str, Any]:
    try:
        result = _current_progress_repository().get_all(student_id, roadmap_id)
    except (ValueError, ProgressNotFoundError, ProgressStorageError) as exc:
        raise _progress_error(exc) from exc
    progress = result["progress"]
    return {"progress": progress, "total_skills": len(progress), "roadmap_id": result["roadmap_id"]}


@app.get("/api/analytics")
def analytics() -> dict[str, Any]:
    data = store.get("dma")
    if data is None:
        path = BASE_DIR / "data" / "raw" / "dma_dataset.csv"
        raise HTTPException(status_code=503, detail=_unavailable("Analytics", [path]))
    return {
        "career_interest": data["career_interest"].value_counts().to_dict(),
        "challenges": data["challenges"].value_counts().to_dict(),
        "support_required": data["support_required"].value_counts().to_dict(),
    }


@app.post("/api/jobs/search")
def search_jobs(request: JobSearchRequest) -> dict[str, Any]:
    skills = [skill.strip() for skill in request.skills if skill and skill.strip()]
    query = " ".join(skills[:3])
    jobs = _fetch_remote_jobs(
        f"https://remotive.com/api/remote-jobs?search={quote(query)}",
        "Remotive",
        request.limit,
    )
    jobs += _fetch_remote_jobs(
        "https://www.arbeitnow.com/api/job-board-api", "Arbeitnow", request.limit
    )
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for job in jobs:
        key = f"{_lower_text(job.get('title'))}|{_lower_text(job.get('company'))}|{_lower_text(job.get('url'))}"
        if key not in seen:
            seen.add(key)
            unique.append(job)
    filtered = _filter_by_location(unique, request.location)
    scored: list[dict[str, Any]] = []
    for job in filtered:
        score, matched = _score_job(job, skills)
        if skills and score == 0:
            continue
        scored.append({**job, "match_score": score, "matched_skills": matched})
    scored.sort(key=lambda item: (-item["match_score"], item.get("days_ago", 9999), item["title"]))
    results = scored[: request.limit]
    if not results:
        try:
            demo_jobs = _load_demo_jobs()
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            logger.warning("CareerAlign demo jobs unavailable: %s", exc)
            demo_jobs = []
        demo_results = []
        for job in demo_jobs:
            score, matched = _score_job({**job, "tags": job["skills"]}, skills)
            demo_results.append({
                **job,
                "description": "",
                "location": "Demo dataset",
                "url": "",
                "source": "CareerAlign demo dataset",
                "tags": job["skills"],
                "match_score": score,
                "matched_skills": matched,
            })
        demo_results.sort(key=lambda item: (-item["match_score"], item["job_id"]))
        results = demo_results[: request.limit]
        is_demo_fallback = bool(results)
    else:
        is_demo_fallback = False
    return {
        "jobs": results,
        "total_found": len(results),
        "jobs_with_skill_match": sum(bool(job["match_score"]) for job in results),
        "average_match_score": round(sum(job["match_score"] for job in results) / len(results), 1) if results else 0,
        "unique_companies": len({job.get("company") for job in results if job.get("company")}),
        "sources": sorted({job.get("source", "Unknown") for job in results}),
        "skills_searched": skills,
        "location_filter": request.location,
        "is_demo_fallback": is_demo_fallback,
        "source": "demo_fallback" if is_demo_fallback else "live_results",
    }


@app.post("/api/github/analyze")
def github_analyze(request: GitHubRequest) -> dict[str, Any]:
    return analyze_github_profile(request.username.strip())
