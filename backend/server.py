from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Optional
from urllib.error import URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

if __package__ in {None, ""}:
    import os
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Legacy HTTP-server implementation. The active API is ``backend.main:app``.


HOST = "0.0.0.0"
PORT = 8000


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    content_length = int(handler.headers.get("Content-Length", "0"))
    if content_length <= 0:
        return {}
    raw = handler.rfile.read(content_length)
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _lower_text(value: Any) -> str:
    return _normalize_text(value).lower()


def _days_ago_from_iso(value: Any) -> int:
    text = _normalize_text(value)
    if not text:
        return 0
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)
        return max(delta.days, 0)
    except Exception:
        return 0


def _github_request(path: str) -> Any:
    request = Request(
        f"https://api.github.com{path}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "CareerAlign"},
    )
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def analyze_github_profile(username: str) -> dict[str, Any]:
    if not username:
        return {"error": "No GitHub username provided"}

    if "github.com/" in username:
        username = username.split("github.com/")[-1].strip("/").split("/")[0]
    username = username.strip().lstrip("@").strip()

    try:
        profile = _github_request(f"/users/{username}")
    except Exception as exc:
        return {"error": f"Could not fetch GitHub profile for '{username}'", "details": str(exc)}

    try:
        repos = _github_request(f"/users/{username}/repos?sort=updated&per_page=30")
    except Exception:
        repos = []

    if not repos:
        return {
            "username": username,
            "profile": profile,
            "projects": [],
            "skills": [],
            "languages": {},
            "total_projects": 0,
            "error": "No public repositories found",
        }

    language_map = {
        "python": ["Python", "Django", "Flask", "FastAPI", "Data Science"],
        "javascript": ["JavaScript", "Node.js", "React", "Vue", "Express"],
        "typescript": ["TypeScript", "Angular", "React", "Node.js"],
        "java": ["Java", "Spring Boot", "Maven", "Microservices"],
        "go": ["Go", "Golang", "Microservices", "Cloud"],
        "html": ["HTML", "Web Development", "Frontend"],
        "css": ["CSS", "Web Development", "Frontend", "UI/UX"],
        "shell": ["Shell", "Bash", "DevOps", "Linux"],
        "sql": ["SQL", "Databases", "Data Engineering"],
        "dart": ["Dart", "Flutter", "Mobile Development"],
        "solidity": ["Solidity", "Blockchain", "Web3", "Smart Contracts"],
    }
    repo_pattern_skills = {
        "react": ["React", "JavaScript", "Frontend"],
        "node": ["Node.js", "JavaScript", "Backend"],
        "django": ["Django", "Python", "Backend"],
        "flask": ["Flask", "Python", "Backend"],
        "fastapi": ["FastAPI", "Python", "Backend"],
        "docker": ["Docker", "DevOps", "Containerization"],
        "kubernetes": ["Kubernetes", "DevOps", "Cloud"],
        "aws": ["AWS", "Cloud", "DevOps"],
        "graphql": ["GraphQL", "API", "Backend"],
        "mongodb": ["MongoDB", "NoSQL", "Database"],
        "postgres": ["PostgreSQL", "SQL", "Database"],
        "nextjs": ["Next.js", "React", "Full Stack"],
    }

    def extract_skills_from_description(description: str) -> list[str]:
        if not description:
            return []

        keywords = [
            ("react", "React"),
            ("angular", "Angular"),
            ("node", "Node.js"),
            ("express", "Express.js"),
            ("django", "Django"),
            ("flask", "Flask"),
            ("fastapi", "FastAPI"),
            ("docker", "Docker"),
            ("kubernetes", "Kubernetes"),
            ("aws", "AWS"),
            ("machine learning", "Machine Learning"),
            ("deep learning", "Deep Learning"),
            ("tensorflow", "TensorFlow"),
            ("pytorch", "PyTorch"),
            ("mongodb", "MongoDB"),
            ("postgresql", "PostgreSQL"),
            ("graphql", "GraphQL"),
            ("rest api", "REST API"),
            ("microservice", "Microservices"),
            ("flutter", "Flutter"),
            ("android", "Android"),
            ("ios", "iOS"),
            ("ci/cd", "CI/CD"),
            ("devops", "DevOps"),
            ("terraform", "Terraform"),
        ]

        lowered = description.lower()
        matches: list[str] = []
        for keyword, skill in keywords:
            if keyword in lowered:
                matches.append(skill)
        return matches

    all_languages: Counter[str] = Counter()
    all_skills: list[str] = []
    projects: list[dict[str, Any]] = []

    for repo in repos:
        if repo.get("fork"):
            continue

        repo_name = repo.get("name", "")
        description = repo.get("description", "") or ""
        language = repo.get("language")
        stars = repo.get("stargazers_count", 0)

        repo_skills: list[str] = []
        if language:
            all_languages[language] += 1
            repo_skills.extend(language_map.get(language.lower(), [language]))

        name_lower = repo_name.lower()
        for pattern, pattern_skills in repo_pattern_skills.items():
            if pattern in name_lower:
                repo_skills.extend(pattern_skills)

        repo_skills.extend(extract_skills_from_description(description))
        repo_skills = sorted(set(repo_skills))
        all_skills.extend(repo_skills)

        projects.append(
            {
                "name": repo_name,
                "description": description or "No description",
                "language": language,
                "stars": stars,
                "url": repo.get("html_url", ""),
                "updated": repo.get("updated_at", ""),
                "skills": repo_skills[:5],
                "topics": repo.get("topics", []),
                "forks": repo.get("forks_count", 0),
            }
        )

    skill_counts = Counter(all_skills)
    top_skills = [skill for skill, _ in skill_counts.most_common(15)]

    return {
        "username": username,
        "profile": {
            "name": profile.get("name") or username,
            "avatar": profile.get("avatar_url", ""),
            "bio": profile.get("bio", ""),
            "location": profile.get("location", ""),
            "company": profile.get("company", ""),
            "public_repos": profile.get("public_repos", 0),
            "followers": profile.get("followers", 0),
            "url": profile.get("html_url", ""),
        },
        "projects": sorted(projects, key=lambda item: item["stars"], reverse=True)[:15],
        "skills": top_skills,
        "languages": dict(all_languages.most_common(10)),
        "total_projects": len(projects),
    }


def _score_job(job: dict[str, Any], skills: list[str]) -> tuple[int, list[str]]:
    if not skills:
        return 0, []

    haystack = " ".join(
        [
            _lower_text(job.get("title")),
            _lower_text(job.get("company")),
            _lower_text(job.get("description")),
            " ".join(_lower_text(tag) for tag in job.get("tags", [])),
            _lower_text(job.get("location")),
        ]
    )

    matched: list[str] = []
    score = 0
    for skill in skills:
        skill_lower = skill.lower()
        if skill_lower and skill_lower in haystack:
            matched.append(skill)
            score += 15

    return min(score, 100), sorted(set(matched))


def _extract_job_fields(job: dict[str, Any], source: str) -> dict[str, Any]:
    title = _normalize_text(job.get("title") or job.get("position") or job.get("job_title") or job.get("name"))
    company = _normalize_text(job.get("company_name") or job.get("company") or job.get("organization")) or "Unknown Company"
    url = _normalize_text(job.get("url") or job.get("job_url") or job.get("redirect_url") or job.get("html_url"))
    description = _normalize_text(job.get("description") or job.get("content") or job.get("summary"))
    location = _normalize_text(job.get("candidate_required_location") or job.get("location") or ("Remote" if job.get("remote") else ""))
    tags = job.get("tags") or []
    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
    if not isinstance(tags, list):
        tags = []

    return {
        "title": title,
        "company": company,
        "url": url,
        "description": description,
        "location": location or "Remote",
        "job_type": _normalize_text(job.get("job_type") or job.get("type") or ("Remote" if job.get("remote") else "Full-time")),
        "days_ago": _days_ago_from_iso(job.get("publication_date") or job.get("created_at") or job.get("date") or job.get("posted_at")),
        "source": source,
        "tags": tags[:10],
    }


def _sample_jobs() -> list[dict[str, Any]]:
    return [
        {
            "title": "Frontend Engineer",
            "company": "Northstar Labs",
            "location": "Remote",
            "job_type": "Remote",
            "source": "CareerAlign Demo",
            "url": "https://example.com/jobs/frontend-engineer",
            "days_ago": 2,
            "tags": ["React", "TypeScript", "UI"],
            "description": "Build polished interfaces for a student career platform.",
            "criteria": {"min_cgpa": 6.5, "min_10th": 65, "min_12th": 65},
        },
        {
            "title": "Python Backend Developer",
            "company": "CloudBridge Systems",
            "location": "Bangalore",
            "job_type": "Full-time",
            "source": "CareerAlign Demo",
            "url": "https://example.com/jobs/python-backend-developer",
            "days_ago": 4,
            "tags": ["Python", "FastAPI", "SQL", "Docker"],
            "description": "Work on APIs, integrations, and platform automation.",
            "criteria": {"min_cgpa": 7.0, "min_10th": 70, "min_12th": 70},
        },
        {
            "title": "Junior Data Analyst",
            "company": "InsightWorks",
            "location": "Hybrid",
            "job_type": "Hybrid",
            "source": "CareerAlign Demo",
            "url": "https://example.com/jobs/junior-data-analyst",
            "days_ago": 1,
            "tags": ["Python", "SQL", "Analytics", "Tableau"],
            "description": "Support reporting, dashboards, and decision making.",
            "criteria": {"min_cgpa": 6.0, "min_10th": 60, "min_12th": 60},
        },
        {
            "title": "DevOps Associate",
            "company": "Orbit Cloud",
            "location": "India",
            "job_type": "Full-time",
            "source": "CareerAlign Demo",
            "url": "https://example.com/jobs/devops-associate",
            "days_ago": 3,
            "tags": ["AWS", "Docker", "Kubernetes", "CI/CD"],
            "description": "Support deployment pipelines and cloud infrastructure.",
            "criteria": {"min_cgpa": 6.5, "min_10th": 65, "min_12th": 65},
        },
    ]


def _filter_by_location(jobs: list[dict[str, Any]], location: Optional[str]) -> list[dict[str, Any]]:
    if not location:
        return jobs

    wanted = location.lower().strip()
    if not wanted:
        return jobs

    filtered = []
    for job in jobs:
        haystack = " ".join(
            [
                _lower_text(job.get("location")),
                _lower_text(job.get("job_type")),
                _lower_text(job.get("title")),
                _lower_text(job.get("company")),
                " ".join(_lower_text(tag) for tag in job.get("tags", [])),
            ]
        )
        if wanted == "remote":
            if "remote" in haystack or "work from home" in haystack:
                filtered.append(job)
        elif wanted in haystack:
            filtered.append(job)

    return filtered or jobs


def _fetch_remote_jobs(url: str, source: str, limit: int) -> list[dict[str, Any]]:
    try:
        request = Request(url, headers={"Accept": "application/json", "User-Agent": "CareerAlign"})
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return []

    raw_jobs: list[dict[str, Any]] = []
    if source == "Remotive":
        raw_jobs = payload.get("jobs", []) or []
    elif source == "Arbeitnow":
        raw_jobs = payload.get("data", []) or []

    return [_extract_job_fields(job, source) for job in raw_jobs[:limit]]


def _build_jobs_response(skills: list[str], location: Optional[str], limit: int) -> dict[str, Any]:
    remotive_jobs = _fetch_remote_jobs("https://remotive.com/api/remote-jobs", "Remotive", limit)
    arbeitnow_jobs = _fetch_remote_jobs("https://www.arbeitnow.com/api/job-board-api", "Arbeitnow", limit)
    combined = remotive_jobs + arbeitnow_jobs + _sample_jobs()

    unique_jobs: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for job in combined:
        key = f"{_lower_text(job.get('title'))}|{_lower_text(job.get('company'))}|{_lower_text(job.get('url'))}"
        if key in seen_keys:
            continue
        seen_keys.add(key)
        unique_jobs.append(job)

    filtered = _filter_by_location(unique_jobs, location)
    scored: list[dict[str, Any]] = []
    for job in filtered:
        match_score, matched_skills = _score_job(job, skills)
        if skills and match_score == 0:
            continue
        scored.append({**job, "match_score": match_score, "matched_skills": matched_skills})

    scored.sort(key=lambda item: (-item["match_score"], item.get("days_ago", 9999), item["title"]))
    limited = scored[:limit]

    return {
        "jobs": limited,
        "total_found": len(limited),
        "jobs_with_skill_match": sum(1 for job in limited if job.get("match_score", 0) > 0),
        "average_match_score": round(sum(job.get("match_score", 0) for job in limited) / len(limited), 1) if limited else 0,
        "unique_companies": len({job.get("company") for job in limited if job.get("company")}),
        "sources": sorted({job.get("source", "Unknown") for job in limited}),
        "skills_searched": skills,
        "location_filter": location,
    }


class CareerAlignHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            _json_response(self, 200, {"status": "ok"})
            return

        if parsed.path == "/api/skill-gap/roles":
            _json_response(self, 410, {"error": "This legacy server is inactive; use backend.main:app."})
            return

        _json_response(self, 404, {"error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        body = _read_json_body(self)

        if parsed.path == "/api/skill-gap":
            _json_response(self, 410, {"error": "This legacy server is inactive; use backend.main:app."})
            return

        if parsed.path == "/api/jobs/search":
            skills = [skill for skill in body.get("skills", []) if _normalize_text(skill)]
            location = _normalize_text(body.get("location")) or None
            limit = int(body.get("limit") or 30)
            _json_response(self, 200, _build_jobs_response(skills, location, limit))
            return

        if parsed.path == "/api/github/analyze":
            username = _normalize_text(body.get("username"))
            _json_response(self, 200, analyze_github_profile(username))
            return

        _json_response(self, 404, {"error": "Not found"})


def main() -> None:
    raise SystemExit("backend.server is legacy; run 'uvicorn backend.main:app --reload' instead.")


if __name__ == "__main__":
    main()
