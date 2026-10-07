import copy
import unittest

from backend.job_matching import match_jobs
from backend.student_skill_twin import InvalidEvidenceError, UnknownSkillError, merge_skill_evidence


def evidence(skill, proficiency, confidence="high", source="project"):
    return {
        "skill": skill,
        "source": source,
        "evidence": f"Used {skill} in a sample project.",
        "proficiency": proficiency,
        "confidence": confidence,
    }


class JobMatchingTests(unittest.TestCase):
    def setUp(self):
        self.student = merge_skill_evidence([
            evidence("Python", "intermediate"),
            evidence("SQL", "beginner", "low"),
        ])

    def test_basic_job_matching(self):
        result = match_jobs(self.student, [{"job_id": "j1", "title": "Analyst", "skills": ["Python", "SQL", "Docker"]}])
        job = result["matches"][0]
        self.assertEqual(["Python"], job["matched_skills"])
        self.assertEqual(["SQL"], job["partial_skills"])
        self.assertEqual(["Docker"], job["missing_skills"])

    def test_strong_evidence_produces_matched_skill(self):
        result = match_jobs(self.student, [{"job_id": "j1", "title": "Engineer", "skills": ["Python"]}])
        self.assertEqual(["Python"], result["matches"][0]["matched_skills"])

    def test_weak_evidence_produces_partial_skill(self):
        result = match_jobs(self.student, [{"job_id": "j1", "title": "Analyst", "skills": ["SQL"]}])
        self.assertEqual(["SQL"], result["matches"][0]["partial_skills"])

    def test_absent_student_skill_is_missing(self):
        result = match_jobs(self.student, [{"job_id": "j1", "title": "Engineer", "skills": ["Docker"]}])
        self.assertEqual(["Docker"], result["matches"][0]["missing_skills"])

    def test_all_strong_matches_produce_100_percent(self):
        result = match_jobs(self.student, [{"job_id": "j1", "title": "Engineer", "skills": ["Python"]}])
        self.assertEqual(100.0, result["matches"][0]["score"])

    def test_one_partial_and_no_matches_produces_50_percent(self):
        partial = merge_skill_evidence([evidence("SQL", "beginner", "low")])
        result = match_jobs(partial, [{"job_id": "j1", "title": "Analyst", "skills": ["SQL"]}])
        self.assertEqual(50.0, result["matches"][0]["score"])

    def test_mixed_score_matches_formula(self):
        result = match_jobs(self.student, [{"job_id": "j1", "title": "Engineer", "skills": ["Python", "SQL", "Docker"]}])
        self.assertEqual(50.0, result["matches"][0]["score"])

    def test_zero_skill_job_returns_zero(self):
        result = match_jobs(self.student, [{"job_id": "empty", "title": "Unspecified", "skills": []}])
        self.assertEqual(0.0, result["matches"][0]["score"])
        self.assertEqual(0, result["matches"][0]["total_skill_count"])

    def test_duplicate_job_skills_are_deduplicated(self):
        result = match_jobs(self.student, [{"job_id": "j1", "title": "Engineer", "skills": ["Python", "py", "Python"]}])
        job = result["matches"][0]
        self.assertEqual(["Python"], job["matched_skills"])
        self.assertEqual(1, job["total_skill_count"])

    def test_duplicate_student_evidence_is_deterministic(self):
        duplicate_records = [evidence("Python", "intermediate"), evidence("Python", "intermediate")]
        twin_a = merge_skill_evidence(duplicate_records)
        twin_b = merge_skill_evidence(list(reversed(duplicate_records)))
        job = [{"job_id": "j1", "title": "Engineer", "skills": ["Python"]}]
        self.assertEqual(match_jobs(twin_a, job), match_jobs(twin_b, job))

    def test_unknown_job_skill_is_rejected(self):
        with self.assertRaisesRegex(UnknownSkillError, "Unknown or empty job skill"):
            match_jobs(self.student, [{"job_id": "j1", "title": "Engineer", "skills": ["Made Up"]}])

    def test_unknown_student_skill_is_rejected(self):
        with self.assertRaises(UnknownSkillError):
            match_jobs([{"skill": "Made Up", "evidence": []}], [])

    def test_invalid_or_missing_job_fields_are_rejected(self):
        for invalid in (
            {"title": "Engineer", "skills": []},
            {"job_id": "j1", "skills": []},
            {"job_id": "j1", "title": "Engineer"},
            {"job_id": "j1", "title": "Engineer", "skills": "Python"},
            {"job_id": "j1", "title": "Engineer", "skills": [], "company": 123},
        ):
            with self.subTest(job=invalid), self.assertRaises(ValueError):
                match_jobs(self.student, [invalid])
        with self.assertRaises(InvalidEvidenceError):
            match_jobs(["bad student entry"], [])

    def test_jobs_rank_by_score(self):
        jobs = [
            {"job_id": "low", "title": "Low", "skills": ["Docker"]},
            {"job_id": "high", "title": "High", "skills": ["Python"]},
        ]
        self.assertEqual(["high", "low"], [job["job_id"] for job in match_jobs(self.student, jobs)["matches"]])

    def test_job_id_is_deterministic_final_tiebreaker(self):
        jobs = [
            {"job_id": "z-job", "title": "Z", "skills": ["Python"]},
            {"job_id": "a-job", "title": "A", "skills": ["Python"]},
        ]
        self.assertEqual(["a-job", "z-job"], [job["job_id"] for job in match_jobs(self.student, jobs)["matches"]])

    def test_matched_count_breaks_equal_score_before_partial_count(self):
        student = merge_skill_evidence([
            evidence("Python", "intermediate"), evidence("Java", "intermediate"),
            evidence("SQL", "beginner", "low"), evidence("React", "beginner", "low"),
        ])
        jobs = [
            {"job_id": "b-job", "title": "B", "skills": ["Python", "SQL", "React", "Docker"]},
            {"job_id": "a-job", "title": "A", "skills": ["Python", "Java", "Docker", "Linux"]},
        ]
        ranked = match_jobs(student, jobs)["matches"]
        self.assertEqual(["a-job", "b-job"], [job["job_id"] for job in ranked])
        self.assertEqual(ranked[0]["score"], ranked[1]["score"])
        self.assertGreater(ranked[0]["matched_count"], ranked[1]["matched_count"])

    def test_explanation_contains_each_skill_group(self):
        job = match_jobs(self.student, [{"job_id": "j1", "title": "Engineer", "skills": ["Python", "SQL", "Docker"]}])["matches"][0]
        self.assertIn("Python", job["explanation"])
        self.assertIn("Partial alignment: SQL", job["explanation"])
        self.assertIn("Missing: Docker", job["explanation"])

    def test_self_reported_only_evidence_is_partial(self):
        student = merge_skill_evidence([evidence("Python", "advanced", "high", "self_declared")])
        result = match_jobs(student, [{"job_id": "j1", "title": "Engineer", "skills": ["Python"]}])
        self.assertEqual(["Python"], result["matches"][0]["partial_skills"])

    def test_student_twin_is_not_modified(self):
        before = copy.deepcopy(self.student)
        match_jobs(self.student, [{"job_id": "j1", "title": "Engineer", "skills": ["Python", "SQL"]}])
        self.assertEqual(before, self.student)

    def test_empty_job_list_is_safe(self):
        self.assertEqual([], match_jobs(self.student, []) ["matches"])

    def test_optional_context_and_taxonomy_aliases_are_preserved_canonicalized(self):
        result = match_jobs(self.student, [{
            "job_id": "j1", "title": "Engineer", "career_role": "Data Engineer", "company": "Example", "skills": ["py"]
        }])["matches"][0]
        self.assertEqual("Data Engineer", result["career_role"])
        self.assertEqual("Example", result["company"])
        self.assertEqual(["Python"], result["matched_skills"])


if __name__ == "__main__":
    unittest.main()
