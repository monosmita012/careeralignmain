import ast
from pathlib import Path
import pandas as pd
try:
    from .text_utils import split_skills
except ImportError:  # Support running these utilities as scripts from backend/.
    from text_utils import split_skills

BASE = Path(__file__).parent
RAW = BASE / "data" / "raw"
PROCESSED = BASE / "data" / "processed"


def _parse_skills(value):
    """Turn "['A', 'b']" (text) into a clean list: ['a', 'b']"""
    try:
        items = ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return []
    return sorted({s.strip().lower() for s in items if isinstance(s, str) and s.strip()})


def load_jobs() -> pd.DataFrame:
    cached = PROCESSED / "jobs_clean.pkl"
    if cached.exists():
        return pd.read_pickle(cached)

    df = pd.read_csv(RAW / "all_job_post.csv")
    df = df.drop_duplicates(subset="job_id")
    df["job_title"] = df["job_title"].str.lower().str.strip()
    df["category"] = df["category"].str.lower().str.strip()
    df["skills"] = df["job_skill_set"].apply(_parse_skills)
    df = df[df["skills"].str.len() > 0]          # drop rows with no skills
    df = df[["job_id", "category", "job_title", "job_description", "skills"]]

    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_pickle(cached)
    return df
def load_candidates() -> pd.DataFrame:
    df = pd.read_csv(RAW / "candidate_role.csv")
    df = df.drop_duplicates(subset="candidate_id")
    df["job_role"] = df["job_role"].str.strip()
    df["skills"] = df["skills"].apply(split_skills)
    df["skills_text"] = df["skills"].apply(", ".join)
    return df


def load_dma() -> pd.DataFrame:
    df = pd.read_csv(RAW / "dma_dataset.csv")
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]     # empty column
    df = df.drop(columns=["Name", "email_id"])                # personal data
    df.columns = (df.columns.str.strip().str.lower()
                  .str.replace(" ", "_").str.replace(".", "_", regex=False))
    df = df.rename(columns={"rating": "tech_rating", "rating_1": "soft_rating"})
    return df
