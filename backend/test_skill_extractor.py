"""Focused tests for CareerAlign's taxonomy-backed free-text extractor."""

import unittest

try:
    from .skill_extractor import extract_skills
except ImportError:  # Support discovery with backend/ as the start directory.
    from skill_extractor import extract_skills


class SkillExtractorTests(unittest.TestCase):
    def test_basic_extraction(self) -> None:
        skills = extract_skills(
            "Experienced with Python, SQL, Pandas, React and MongoDB."
        )
        for expected in ("Python", "SQL", "Pandas", "React", "MongoDB"):
            with self.subTest(skill=expected):
                self.assertIn(expected, skills)

    def test_alias_extraction(self) -> None:
        self.assertEqual(
            extract_skills("Worked with JS, React.js, NodeJS, Mongo and Postgres."),
            ["JavaScript", "React", "Node.js", "MongoDB", "PostgreSQL"],
        )

    def test_case_whitespace_and_punctuation(self) -> None:
        self.assertEqual(
            extract_skills("  (pYtHoN); JAVA / spring boot, NODE.JS. POSTGRES  "),
            ["Python", "Java", "Spring Boot", "Node.js", "PostgreSQL"],
        )

    def test_boundary_safety_for_ambiguous_short_names(self) -> None:
        text = (
            "We're going to review a candidate's career, company code, "
            "training, paid leave, and ordinary words."
        )
        skills = extract_skills(text)
        for ambiguous in ("Go", "C", "R", "Artificial Intelligence"):
            with self.subTest(skill=ambiguous):
                self.assertNotIn(ambiguous, skills)

    def test_java_and_javascript_are_distinct(self) -> None:
        self.assertEqual(extract_skills("JavaScript developer"), ["JavaScript"])
        self.assertEqual(extract_skills("Java developer"), ["Java"])
        self.assertEqual(extract_skills("React Native developer"), ["React Native"])

    def test_punctuation_heavy_skill_names(self) -> None:
        self.assertEqual(
            extract_skills("Java, C++ / C#, Node.js and React.js; Postgres."),
            ["Java", "C++", "C#", "Node.js", "React", "PostgreSQL"],
        )
        self.assertNotIn("C++", extract_skills("C++foo is not a standalone skill token"))

    def test_ambiguous_languages_need_context_in_free_text(self) -> None:
        self.assertEqual(extract_skills("Go programming; C language"), ["Go", "C"])

    def test_duplicate_mentions_return_one_canonical_name(self) -> None:
        self.assertEqual(
            extract_skills("JS, javascript, React.js, ReactJS, React"),
            ["JavaScript", "React"],
        )

    def test_empty_and_non_string_inputs(self) -> None:
        for value in ("", "   ", None, 42, [], {}):
            with self.subTest(value=value):
                self.assertEqual(extract_skills(value), [])  # type: ignore[arg-type]

    def test_order_is_deterministic_and_follows_first_occurrence(self) -> None:
        text = "Postgres, Python, JS, PostgreSQL, Python"
        first = extract_skills(text)
        self.assertEqual(first, ["PostgreSQL", "Python", "JavaScript"])
        for _ in range(5):
            self.assertEqual(extract_skills(text), first)


if __name__ == "__main__":
    unittest.main()
