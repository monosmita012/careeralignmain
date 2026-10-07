"""Controlled skill names and exact alias normalization for CareerAlign.

This module intentionally normalizes one supplied skill name at a time. It
does not scan job descriptions, resumes, or other free text for skill mentions.
"""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class SkillDefinition:
    """One canonical skill and the exact names accepted as aliases."""

    canonical_name: str
    category: str
    aliases: tuple[str, ...] = ()


SKILL_TAXONOMY: tuple[SkillDefinition, ...] = (
    # Programming Languages
    SkillDefinition("Python", "Programming Languages", ("py", "python 3", "python3")),
    SkillDefinition("JavaScript", "Programming Languages", ("js", "javascript", "java script")),
    SkillDefinition("TypeScript", "Programming Languages", ("ts", "typescript", "type script")),
    SkillDefinition("Java", "Programming Languages"),
    SkillDefinition("C", "Programming Languages", ("c language",)),
    SkillDefinition("C++", "Programming Languages", ("cpp", "cplusplus")),
    SkillDefinition("C#", "Programming Languages", ("c sharp", "csharp")),
    SkillDefinition("Go", "Programming Languages", ("golang",)),
    SkillDefinition("Ruby", "Programming Languages"),
    SkillDefinition("PHP", "Programming Languages"),
    SkillDefinition("Swift", "Programming Languages"),
    SkillDefinition("Kotlin", "Programming Languages"),
    SkillDefinition("Bash", "Programming Languages", ("shell scripting",)),
    # Frontend
    SkillDefinition("React", "Frontend", ("react.js", "reactjs", "react js")),
    SkillDefinition("Angular", "Frontend", ("angular.js", "angularjs")),
    SkillDefinition("Vue.js", "Frontend", ("vue", "vuejs", "vue js")),
    SkillDefinition("HTML", "Frontend", ("html5",)),
    SkillDefinition("CSS", "Frontend", ("css3",)),
    SkillDefinition("Next.js", "Frontend", ("nextjs", "next js")),
    SkillDefinition("Redux", "Frontend"),
    SkillDefinition("Tailwind CSS", "Frontend", ("tailwind", "tailwindcss")),
    # Backend
    SkillDefinition("Node.js", "Backend", ("nodejs", "node.js", "node js")),
    SkillDefinition("Express.js", "Backend", ("express", "expressjs", "express.js")),
    SkillDefinition("Django", "Backend"),
    SkillDefinition("Flask", "Backend"),
    SkillDefinition("FastAPI", "Backend", ("fast api",)),
    SkillDefinition("Spring Boot", "Backend", ("springboot",)),
    SkillDefinition(".NET", "Backend", ("dotnet", "dot net")),
    SkillDefinition("REST API", "Backend", ("restful api", "rest apis", "restful apis")),
    SkillDefinition("GraphQL", "Backend"),
    # Databases
    SkillDefinition("PostgreSQL", "Databases", ("postgres", "postgresql", "postgre sql")),
    SkillDefinition("MySQL", "Databases", ("mysql server",)),
    SkillDefinition("SQLite", "Databases", ("sqlite3",)),
    SkillDefinition("MongoDB", "Databases", ("mongo", "mongodb", "mongo db")),
    SkillDefinition("Redis", "Databases"),
    SkillDefinition("Elasticsearch", "Databases", ("elastic search",)),
    SkillDefinition("SQL", "Databases", ("structured query language",)),
    # Data Analysis / BI
    SkillDefinition("Pandas", "Data Analysis / BI"),
    SkillDefinition("NumPy", "Data Analysis / BI", ("numpy",)),
    SkillDefinition("Microsoft Excel", "Data Analysis / BI", ("excel",)),
    SkillDefinition("Tableau", "Data Analysis / BI"),
    SkillDefinition("Power BI", "Data Analysis / BI", ("powerbi",)),
    SkillDefinition("Looker", "Data Analysis / BI"),
    # Data Engineering
    SkillDefinition("Apache Spark", "Data Engineering", ("spark", "pyspark", "py spark")),
    SkillDefinition("Apache Kafka", "Data Engineering", ("kafka",)),
    SkillDefinition("Apache Airflow", "Data Engineering", ("airflow",)),
    SkillDefinition("dbt", "Data Engineering", ("data build tool",)),
    SkillDefinition("Snowflake", "Data Engineering"),
    SkillDefinition("Google BigQuery", "Data Engineering", ("bigquery", "big query")),
    SkillDefinition("Databricks", "Data Engineering"),
    SkillDefinition("ETL", "Data Engineering", ("extract transform load",)),
    # Machine Learning / AI
    SkillDefinition("Machine Learning", "Machine Learning / AI", ("ml",)),
    SkillDefinition("Deep Learning", "Machine Learning / AI"),
    SkillDefinition("TensorFlow", "Machine Learning / AI", ("tensorflow", "tensor flow")),
    SkillDefinition("PyTorch", "Machine Learning / AI", ("pytorch", "py torch")),
    SkillDefinition("scikit-learn", "Machine Learning / AI", ("sklearn", "scikit learn")),
    SkillDefinition("Natural Language Processing", "Machine Learning / AI", ("nlp",)),
    SkillDefinition("Artificial Intelligence", "Machine Learning / AI", ("ai",)),
    SkillDefinition("Generative AI", "Machine Learning / AI", ("genai", "generative artificial intelligence")),
    # DevOps / Cloud
    SkillDefinition("Docker", "DevOps / Cloud"),
    SkillDefinition("Kubernetes", "DevOps / Cloud", ("k8s", "kube")),
    SkillDefinition("AWS", "DevOps / Cloud", ("amazon web services",)),
    SkillDefinition("Microsoft Azure", "DevOps / Cloud", ("azure",)),
    SkillDefinition("Google Cloud", "DevOps / Cloud", ("gcp", "google cloud platform")),
    SkillDefinition("Terraform", "DevOps / Cloud"),
    SkillDefinition("Jenkins", "DevOps / Cloud"),
    SkillDefinition("GitHub Actions", "DevOps / Cloud"),
    SkillDefinition("Linux", "DevOps / Cloud"),
    # Testing / QA
    SkillDefinition("Selenium", "Testing / QA"),
    SkillDefinition("Playwright", "Testing / QA"),
    SkillDefinition("Cypress", "Testing / QA"),
    SkillDefinition("pytest", "Testing / QA", ("py.test",)),
    SkillDefinition("JUnit", "Testing / QA", ("j unit",)),
    SkillDefinition("Jest", "Testing / QA"),
    SkillDefinition("Postman", "Testing / QA"),
    SkillDefinition("Test Automation", "Testing / QA", ("automated testing", "automation testing")),
    # Cybersecurity
    SkillDefinition("OWASP", "Cybersecurity"),
    SkillDefinition("Penetration Testing", "Cybersecurity", ("pentest", "pen testing")),
    SkillDefinition("SIEM", "Cybersecurity"),
    # Mobile Development
    SkillDefinition("Android", "Mobile Development"),
    SkillDefinition("iOS", "Mobile Development", ("ios development",)),
    SkillDefinition("Flutter", "Mobile Development"),
    SkillDefinition("React Native", "Mobile Development", ("react-native", "reactnative")),
    # Tools / Version Control
    SkillDefinition("Git", "Tools / Version Control"),
    SkillDefinition("GitHub", "Tools / Version Control"),
    SkillDefinition("GitLab", "Tools / Version Control"),
    SkillDefinition("Jira", "Tools / Version Control", ("atlassian jira",)),
    SkillDefinition("Visual Studio Code", "Tools / Version Control", ("vscode", "vs code")),
    # Project / Product / Business Analysis
    SkillDefinition("Agile", "Project / Product / Business Analysis"),
    SkillDefinition("Scrum", "Project / Product / Business Analysis"),
    SkillDefinition("Project Management", "Project / Product / Business Analysis"),
    SkillDefinition("Product Management", "Project / Product / Business Analysis"),
    SkillDefinition("Business Analysis", "Project / Product / Business Analysis"),
)

# These exact, narrowly scoped names may be retained as student profile context,
# but are not part of the industry requirement taxonomy or free-text extractor.
# Jupyter Notebook is a distinct tool, not an alias for Python.
INFORMATIONAL_SKILLS: tuple[SkillDefinition, ...] = (
    SkillDefinition("Jupyter Notebook", "Data Analysis / BI", ("jupyter notebook",)),
)


def _normalize_key(value: str) -> str:
    """Normalize casing and whitespace without fuzzy/punctuation removal."""
    return re.sub(r"\s+", " ", value.strip().casefold())


_ALIAS_TO_CANONICAL: dict[str, str] = {}
for _skill in (*SKILL_TAXONOMY, *INFORMATIONAL_SKILLS):
    for _name in (_skill.canonical_name, *_skill.aliases):
        _key = _normalize_key(_name)
        _existing = _ALIAS_TO_CANONICAL.get(_key)
        if _existing is not None and _existing != _skill.canonical_name:
            raise ValueError(f"Skill alias {_name!r} maps to multiple canonical skills")
        _ALIAS_TO_CANONICAL[_key] = _skill.canonical_name


def normalize_skill(skill: str) -> str | None:
    """Return a known skill's canonical name, or ``None`` for unknown input.

    Matching is exact after trimming, case-folding, and collapsing whitespace.
    Punctuation is retained and no substring/fuzzy matching is performed, so
    aliases such as ``go`` or ``ai`` only normalize when supplied as the whole
    skill value.
    """
    if not isinstance(skill, str):
        return None
    key = _normalize_key(skill)
    if not key:
        return None
    return _ALIAS_TO_CANONICAL.get(key)


def get_skill_category(skill: str) -> str | None:
    """Return the category for a known canonical name or alias."""
    canonical = normalize_skill(skill)
    if canonical is None:
        return None
    for definition in (*SKILL_TAXONOMY, *INFORMATIONAL_SKILLS):
        if definition.canonical_name == canonical:
            return definition.category
    return None
