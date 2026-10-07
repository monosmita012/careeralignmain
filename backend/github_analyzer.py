"""
GitHub Profile Analyzer - Extracts projects and tech stack from public GitHub profiles.
Uses GitHub's public API (no auth required for public repos).
"""

import httpx
from collections import Counter
from typing import Optional


# Language to skill mapping
LANGUAGE_TO_SKILLS = {
    "python": ["Python", "Django", "Flask", "FastAPI", "Data Science"],
    "javascript": ["JavaScript", "Node.js", "React", "Vue", "Express"],
    "typescript": ["TypeScript", "Angular", "React", "Node.js"],
    "java": ["Java", "Spring Boot", "Maven", "Microservices"],
    "kotlin": ["Kotlin", "Android", "Spring Boot"],
    "swift": ["Swift", "iOS", "Xcode"],
    "go": ["Go", "Golang", "Microservices", "Cloud"],
    "rust": ["Rust", "Systems Programming", "WebAssembly"],
    "c++": ["C++", "Systems Programming", "Game Development"],
    "c": ["C", "Systems Programming", "Embedded"],
    "c#": ["C#", ".NET", "Unity", "ASP.NET"],
    "ruby": ["Ruby", "Ruby on Rails", "Web Development"],
    "php": ["PHP", "Laravel", "WordPress"],
    "html": ["HTML", "Web Development", "Frontend"],
    "css": ["CSS", "Web Development", "Frontend", "UI/UX"],
    "scss": ["SCSS", "CSS", "Frontend"],
    "shell": ["Shell", "Bash", "DevOps", "Linux"],
    "dockerfile": ["Docker", "DevOps", "Containerization"],
    "hcl": ["Terraform", "Infrastructure as Code", "DevOps"],
    "sql": ["SQL", "Databases", "Data Engineering"],
    "jupyter notebook": ["Python", "Data Science", "Machine Learning"],
    "r": ["R", "Data Science", "Statistics"],
    "scala": ["Scala", "Spark", "Big Data"],
    "dart": ["Dart", "Flutter", "Mobile Development"],
    "vue": ["Vue.js", "Frontend", "JavaScript"],
    "solidity": ["Solidity", "Blockchain", "Web3", "Smart Contracts"],
}

# Common repo name patterns to tech stack
REPO_PATTERN_SKILLS = {
    "react": ["React", "JavaScript", "Frontend"],
    "angular": ["Angular", "TypeScript", "Frontend"],
    "vue": ["Vue.js", "JavaScript", "Frontend"],
    "node": ["Node.js", "JavaScript", "Backend"],
    "express": ["Express.js", "Node.js", "Backend"],
    "django": ["Django", "Python", "Backend"],
    "flask": ["Flask", "Python", "Backend"],
    "fastapi": ["FastAPI", "Python", "Backend"],
    "spring": ["Spring Boot", "Java", "Backend"],
    "android": ["Android", "Kotlin", "Mobile"],
    "ios": ["iOS", "Swift", "Mobile"],
    "flutter": ["Flutter", "Dart", "Mobile"],
    "docker": ["Docker", "DevOps", "Containerization"],
    "kubernetes": ["Kubernetes", "DevOps", "Cloud"],
    "terraform": ["Terraform", "DevOps", "IaC"],
    "ml": ["Machine Learning", "Python", "Data Science"],
    "ai": ["AI", "Machine Learning", "Deep Learning"],
    "blockchain": ["Blockchain", "Web3", "Solidity"],
    "api": ["REST API", "Backend", "Microservices"],
    "microservice": ["Microservices", "Docker", "Cloud"],
    "aws": ["AWS", "Cloud", "DevOps"],
    "gcp": ["GCP", "Cloud", "DevOps"],
    "azure": ["Azure", "Cloud", "DevOps"],
    "graphql": ["GraphQL", "API", "Backend"],
    "mongodb": ["MongoDB", "NoSQL", "Database"],
    "postgres": ["PostgreSQL", "SQL", "Database"],
    "redis": ["Redis", "Caching", "Database"],
    "nextjs": ["Next.js", "React", "Full Stack"],
    "nuxt": ["Nuxt.js", "Vue.js", "Full Stack"],
}


async def fetch_github_profile(username: str) -> dict:
    """Fetch GitHub user profile info."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://api.github.com/users/{username}",
                headers={"Accept": "application/vnd.github.v3+json"}
            )
            if response.status_code == 200:
                return response.json()
            return {}
    except Exception as e:
        print(f"Error fetching GitHub profile: {e}")
        return {}


async def fetch_github_repos(username: str, limit: int = 30) -> list[dict]:
    """Fetch public repositories for a GitHub user."""
    repos = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"https://api.github.com/users/{username}/repos",
                params={"sort": "updated", "per_page": limit},
                headers={"Accept": "application/vnd.github.v3+json"}
            )
            if response.status_code == 200:
                repos = response.json()
    except Exception as e:
        print(f"Error fetching GitHub repos: {e}")
    return repos


async def fetch_repo_languages(username: str, repo_name: str) -> dict:
    """Fetch languages used in a specific repository."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://api.github.com/repos/{username}/{repo_name}/languages",
                headers={"Accept": "application/vnd.github.v3+json"}
            )
            if response.status_code == 200:
                return response.json()
            return {}
    except Exception:
        return {}


def extract_skills_from_languages(languages: dict) -> list[str]:
    """Convert GitHub languages to skills."""
    skills = []
    for lang in languages.keys():
        lang_lower = lang.lower()
        if lang_lower in LANGUAGE_TO_SKILLS:
            skills.extend(LANGUAGE_TO_SKILLS[lang_lower])
        else:
            skills.append(lang)
    return list(set(skills))


def extract_skills_from_repo_name(repo_name: str) -> list[str]:
    """Extract skills from repository name patterns."""
    skills = []
    name_lower = repo_name.lower()
    for pattern, pattern_skills in REPO_PATTERN_SKILLS.items():
        if pattern in name_lower:
            skills.extend(pattern_skills)
    return skills


def extract_skills_from_description(description: str) -> list[str]:
    """Extract skills from repository description."""
    if not description:
        return []
    
    skills = []
    desc_lower = description.lower()
    
    keywords = [
        ("react", "React"), ("angular", "Angular"), ("vue", "Vue.js"),
        ("node", "Node.js"), ("express", "Express.js"), ("django", "Django"),
        ("flask", "Flask"), ("fastapi", "FastAPI"), ("spring", "Spring Boot"),
        ("docker", "Docker"), ("kubernetes", "Kubernetes"), ("aws", "AWS"),
        ("machine learning", "Machine Learning"), ("deep learning", "Deep Learning"),
        ("tensorflow", "TensorFlow"), ("pytorch", "PyTorch"), ("pandas", "Pandas"),
        ("mongodb", "MongoDB"), ("postgresql", "PostgreSQL"), ("mysql", "MySQL"),
        ("redis", "Redis"), ("graphql", "GraphQL"), ("rest api", "REST API"),
        ("microservice", "Microservices"), ("blockchain", "Blockchain"),
        ("flutter", "Flutter"), ("android", "Android"), ("ios", "iOS"),
        ("ci/cd", "CI/CD"), ("devops", "DevOps"), ("terraform", "Terraform"),
    ]
    
    for keyword, skill in keywords:
        if keyword in desc_lower:
            skills.append(skill)
    
    return skills


async def analyze_github_profile(username: str) -> dict:
    """
    Analyze a GitHub profile and extract:
    - Projects (repos)
    - Tech stack (languages & frameworks)
    - Skills derived from projects
    """
    if not username:
        return {"error": "No GitHub username provided"}
    
    # Clean username (handle full URL)
    if "github.com/" in username:
        username = username.split("github.com/")[-1].strip("/").split("/")[0]
    username = username.strip().lstrip("@")
    
    # Fetch profile and repos
    profile = await fetch_github_profile(username)
    if not profile:
        return {"error": f"Could not fetch GitHub profile for '{username}'"}
    
    repos = await fetch_github_repos(username, limit=30)
    
    if not repos:
        return {
            "username": username,
            "profile": profile,
            "projects": [],
            "skills": [],
            "languages": {},
            "error": "No public repositories found"
        }
    
    all_languages = Counter()
    all_skills = []
    projects = []
    
    # Analyze each repo
    for repo in repos:
        if repo.get("fork"):  # Skip forked repos
            continue
        
        repo_name = repo.get("name", "")
        description = repo.get("description", "")
        languages = repo.get("language")
        stars = repo.get("stargazers_count", 0)
        
        # Extract skills from various sources
        repo_skills = []
        
        # From language
        if languages:
            all_languages[languages] += 1
            lang_lower = languages.lower()
            if lang_lower in LANGUAGE_TO_SKILLS:
                repo_skills.extend(LANGUAGE_TO_SKILLS[lang_lower][:2])
            else:
                repo_skills.append(languages)
        
        # From repo name
        repo_skills.extend(extract_skills_from_repo_name(repo_name))
        
        # From description
        repo_skills.extend(extract_skills_from_description(description))
        
        repo_skills = list(set(repo_skills))
        all_skills.extend(repo_skills)
        
        projects.append({
            "name": repo_name,
            "description": description or "No description",
            "language": languages,
            "stars": stars,
            "url": repo.get("html_url", ""),
            "updated": repo.get("updated_at", ""),
            "skills": repo_skills[:5],  # Top 5 skills
            "topics": repo.get("topics", []),
        })
    
    # Count skill occurrences
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
        "projects": sorted(projects, key=lambda x: x["stars"], reverse=True)[:15],
        "skills": top_skills,
        "languages": dict(all_languages.most_common(10)),
        "total_projects": len(projects),
    }
