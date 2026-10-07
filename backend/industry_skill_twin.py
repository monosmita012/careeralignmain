"""Build CareerAlign's evidence-based, role-level Industry Skill Twin."""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

try:
    from .skill_taxonomy import SKILL_TAXONOMY
except ImportError:  # Support ``python backend/industry_skill_twin.py``.
    from skill_taxonomy import SKILL_TAXONOMY


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "backend/data/processed/careeralign_job_skills.parquet"
DEFAULT_OUTPUT = ROOT / "backend/data/processed/careeralign_industry_skill_twin.parquet"
DEFAULT_SUMMARY = ROOT / "backend/data/processed/careeralign_industry_skill_twin_summary.json"
EXPECTED_RECORDS = 21_195
EXPECTED_ROLES = 7


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _priority(frequency_percentage: float) -> str:
    """Apply CareerAlign's initial, explicitly configurable frequency bands."""
    if frequency_percentage >= 30:
        return "core"
    if frequency_percentage >= 15:
        return "common"
    if frequency_percentage >= 5:
        return "supporting"
    return "occasional"


def build_industry_skill_twin(
    source_path: str | Path = DEFAULT_SOURCE,
    output_path: str | Path = DEFAULT_OUTPUT,
    summary_path: str | Path = DEFAULT_SUMMARY,
) -> dict[str, Any]:
    """Create the complete career-role × canonical-skill evidence matrix.

    Frequency is record-based: each canonical skill contributes at most once
    per source record, regardless of how often it appears in that description.
    This function does not train or invoke a predictive model.
    """
    source_path = Path(source_path)
    output_path = Path(output_path)
    summary_path = Path(summary_path)
    if not source_path.is_file():
        raise FileNotFoundError(f"Skill extraction dataset not found: {source_path}")

    source_hash_before = _sha256(source_path)
    table = pq.read_table(source_path, columns=["career_role", "extracted_skills"])
    records = table.to_pylist()
    if len(records) != EXPECTED_RECORDS:
        raise ValueError(f"Expected {EXPECTED_RECORDS} source records; found {len(records)}")

    definitions = {item.canonical_name: item for item in SKILL_TAXONOMY}
    skills = [item.canonical_name for item in SKILL_TAXONOMY]
    roles = sorted({record["career_role"] for record in records if record["career_role"]})
    if len(skills) != 93:
        raise ValueError(f"Expected 93 canonical skills; found {len(skills)}")
    if len(roles) != EXPECTED_ROLES:
        raise ValueError(f"Expected {EXPECTED_ROLES} roles; found {len(roles)}")

    role_totals: Counter[str] = Counter()
    role_skill_counts: dict[str, Counter[str]] = defaultdict(Counter)
    all_skill_counts: Counter[str] = Counter()
    records_with_skills = 0

    for record in records:
        role = record.get("career_role")
        if not role:
            raise ValueError("Source record has a missing career_role")
        role_totals[role] += 1
        extracted = record.get("extracted_skills") or []
        unknown = sorted(set(extracted) - definitions.keys())
        if unknown:
            raise ValueError(f"Unknown canonical skills in source record: {unknown}")
        # Record frequency deliberately de-duplicates repeated mentions.
        record_skills = set(extracted)
        if record_skills:
            records_with_skills += 1
        role_skill_counts[role].update(record_skills)
        all_skill_counts.update(record_skills)

    source_total = len(records)
    expected_matrix_size = len(roles) * len(skills)
    rows: list[dict[str, Any]] = []
    for role in roles:
        role_total = role_totals[role]
        for skill in skills:
            role_count = role_skill_counts[role][skill]
            overall_count = all_skill_counts[skill]
            role_frequency = role_count / role_total
            overall_frequency = overall_count / source_total
            association = role_frequency / overall_frequency if overall_frequency else 0.0
            rows.append({
                "career_role": role,
                "skill": skill,
                "category": definitions[skill].category,
                "role_record_count": role_count,
                "role_record_total": role_total,
                "role_frequency_percentage": role_frequency * 100,
                "all_role_record_count": overall_count,
                "all_role_record_total": source_total,
                "all_role_frequency_percentage": overall_frequency * 100,
                "role_association_ratio": association,
                "priority": _priority(role_frequency * 100),
            })

    expected_pairs = {(role, skill) for role in roles for skill in skills}
    actual_pairs = [(row["career_role"], row["skill"]) for row in rows]
    validations: dict[str, bool] = {
        "source_record_count_is_21195": len(records) == EXPECTED_RECORDS,
        "exactly_seven_roles": len(roles) == EXPECTED_ROLES,
        "exactly_93_canonical_skills": len(skills) == 93,
        "matrix_has_651_rows": len(rows) == 651,
        "one_row_per_role_skill_pair": len(actual_pairs) == len(set(actual_pairs)) and set(actual_pairs) == expected_pairs,
        "all_skills_belong_to_taxonomy": all(row["skill"] in definitions for row in rows),
        "role_totals_match_source": sum(role_totals.values()) == len(records),
        "role_counts_do_not_exceed_totals": all(row["role_record_count"] <= row["role_record_total"] for row in rows),
        "overall_counts_do_not_exceed_source": all(row["all_role_record_count"] <= source_total for row in rows),
        "frequencies_match_counts": all(
            math.isclose(row["role_frequency_percentage"], 100 * row["role_record_count"] / row["role_record_total"], rel_tol=1e-12, abs_tol=1e-12)
            and math.isclose(row["all_role_frequency_percentage"], 100 * row["all_role_record_count"] / row["all_role_record_total"], rel_tol=1e-12, abs_tol=1e-12)
            for row in rows
        ),
        "association_ratios_match_frequencies": all(
            math.isclose(
                row["role_association_ratio"],
                (row["role_record_count"] / row["role_record_total"]) / (row["all_role_record_count"] / source_total)
                if row["all_role_record_count"] else 0.0,
                rel_tol=1e-12,
                abs_tol=1e-12,
            )
            for row in rows
        ),
        "priority_labels_match_thresholds": all(
            row["priority"] == _priority(row["role_frequency_percentage"]) for row in rows
        ),
    }
    if not all(validations.values()):
        raise AssertionError(f"Industry Skill Twin validation failed: {validations}")

    schema = pa.schema([
        pa.field("career_role", pa.string()),
        pa.field("skill", pa.string()),
        pa.field("category", pa.string()),
        pa.field("role_record_count", pa.int64()),
        pa.field("role_record_total", pa.int64()),
        pa.field("role_frequency_percentage", pa.float64()),
        pa.field("all_role_record_count", pa.int64()),
        pa.field("all_role_record_total", pa.int64()),
        pa.field("all_role_frequency_percentage", pa.float64()),
        pa.field("role_association_ratio", pa.float64()),
        pa.field("priority", pa.string()),
    ])
    output_table = pa.Table.from_pylist(rows, schema=schema)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(output_table, output_path, compression="zstd")

    written = pq.read_table(output_path).to_pylist()
    validations["written_matrix_has_651_rows"] = len(written) == 651
    validations["written_matrix_has_unique_role_skill_pairs"] = len({(r["career_role"], r["skill"]) for r in written}) == 651
    if not validations["written_matrix_has_651_rows"] or not validations["written_matrix_has_unique_role_skill_pairs"]:
        raise AssertionError(f"Written matrix validation failed: {validations}")

    role_summaries: dict[str, Any] = {}
    for role in roles:
        role_rows = [row for row in rows if row["career_role"] == role]
        priority_counts = Counter(row["priority"] for row in role_rows)
        top_skills = sorted(role_rows, key=lambda row: (-row["role_record_count"], row["skill"]))[:15]
        association_rows = sorted(
            (row for row in role_rows if row["role_record_count"] > 0),
            key=lambda row: (-row["role_association_ratio"], -row["role_frequency_percentage"], row["skill"]),
        )[:10]
        role_summaries[role] = {
            "role_record_total": role_totals[role],
            "top_15_skills": [
                {
                    "skill": row["skill"],
                    "category": row["category"],
                    "record_count": row["role_record_count"],
                    "frequency_percentage": row["role_frequency_percentage"],
                    "priority": row["priority"],
                }
                for row in top_skills
            ],
            "priority_counts": {key: priority_counts[key] for key in ("core", "common", "supporting", "occasional")},
            "highest_role_association_skills": [
                {
                    "skill": row["skill"],
                    "role_association_ratio": row["role_association_ratio"],
                    "role_frequency_percentage": row["role_frequency_percentage"],
                    "all_role_frequency_percentage": row["all_role_frequency_percentage"],
                    "record_count": row["role_record_count"],
                }
                for row in association_rows
            ],
        }

    source_hash_after = _sha256(source_path)
    validations["source_dataset_unchanged"] = source_hash_before == source_hash_after
    if not validations["source_dataset_unchanged"]:
        raise AssertionError("Source skill dataset changed during matrix generation")

    summary: dict[str, Any] = {
        "source_path": str(source_path),
        "output_path": str(output_path),
        "source_row_count": source_total,
        "number_of_roles": len(roles),
        "number_of_canonical_skills": len(skills),
        "expected_matrix_size": expected_matrix_size,
        "actual_matrix_size": len(written),
        "records_with_skills": records_with_skills,
        "records_with_zero_skills": source_total - records_with_skills,
        "priority_thresholds": {
            "core": "role_frequency_percentage >= 30",
            "common": "15 <= role_frequency_percentage < 30",
            "supporting": "5 <= role_frequency_percentage < 15",
            "occasional": "role_frequency_percentage < 5",
            "interpretation": "Initial CareerAlign thresholds for observed descriptions; not universal industry standards.",
        },
        "frequency_definition": "Record frequency: a skill counts at most once per job-description record.",
        "role_association_definition": "(role_record_count / role_record_total) / (all_role_record_count / all_role_record_total); zero if the overall count is zero.",
        "role_summaries": role_summaries,
        "validation_results": validations,
        "interpretation_note": "Priority and association describe observed job-description evidence in this dataset, not universal industry requirements.",
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    result = build_industry_skill_twin()
    print(json.dumps({
        "source_row_count": result["source_row_count"],
        "actual_matrix_size": result["actual_matrix_size"],
        "validation_results": result["validation_results"],
    }, ensure_ascii=False, indent=2))
