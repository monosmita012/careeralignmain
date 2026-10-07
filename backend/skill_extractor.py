"""Boundary-aware extraction of known CareerAlign skills from free text."""

from __future__ import annotations

import re

try:
    from .skill_taxonomy import SKILL_TAXONOMY
except ImportError:  # Support ``python skill_extractor.py`` from backend/.
    from skill_taxonomy import SKILL_TAXONOMY


def _compile_alias_pattern(alias: str) -> re.Pattern[str]:
    """Compile an exact alias pattern with token boundaries.

    Leading punctuation is allowed inside a larger token for names such as
    ``.NET`` (for example, in ``ASP.NET``). Alphabetic/digit aliases still
    require a non-word boundary on both sides.
    """
    escaped = re.escape(alias)
    left_boundary = r"(?<!\w)" if alias[0].isalnum() or alias[0] == "_" else ""
    if alias[-1].isalnum() or alias[-1] == "_":
        right_boundary = r"(?!\w)"
    elif alias[-1] in "+#":
        right_boundary = r"(?![\w+#])"
    else:
        right_boundary = ""
    return re.compile(left_boundary + escaped + right_boundary, re.IGNORECASE)


_PATTERNS: list[tuple[int, str, str, re.Pattern[str]]] = []
for _skill_index, _skill in enumerate(SKILL_TAXONOMY):
    for _name in (_skill.canonical_name, *_skill.aliases):
        _PATTERNS.append(
            (_skill_index, _skill.canonical_name, _name, _compile_alias_pattern(_name))
        )


def _short_ambiguous_mention_is_clear(
    canonical_name: str, surface: str, text: str, start: int, end: int
) -> bool:
    """Avoid treating common standalone words/letters as programming skills."""
    if canonical_name == "Go" and surface.casefold() == "go":
        context = text[max(0, start - 40) : min(len(text), end + 40)]
        go_context = re.compile(
            r"\b(?:go\s+(?:language|programming|developer|engineer)|"
            r"(?:language|programming)\s+(?:in\s+)?go)\b",
            re.IGNORECASE,
        )
        return bool(go_context.search(context))

    if canonical_name == "C" and surface.casefold() == "c":
        context = text[max(0, start - 40) : min(len(text), end + 40)]
        c_context = re.compile(
            r"\b(?:c\s+(?:language|programming|developer|engineer)|"
            r"(?:language|programming)\s+(?:in\s+)?c)\b|"
            r"\bc\s*/\s*c\+\+(?!\w)|\bc\s+and\s+c\+\+(?!\w)",
            re.IGNORECASE,
        )
        return bool(c_context.search(context))

    return True


def extract_skills(text: str) -> list[str]:
    """Extract known canonical skill names from arbitrary free text.

    Matching is case-insensitive and boundary-aware. Alias and canonical
    patterns come only from :data:`SKILL_TAXONOMY`. If matches overlap, the
    longest matching name wins (so ``React Native`` does not also emit
    ``React``). Results are unique and ordered by first occurrence in ``text``.

    ``Go`` and ``C`` are accepted by :func:`normalize_skill` as exact supplied
    skill names, but free-text extraction requires language context for them
    because the bare terms are highly ambiguous. ``R`` is not in the current
    taxonomy. Non-string and blank inputs return an empty list.
    """
    if not isinstance(text, str) or not text:
        return []

    candidates: list[tuple[int, int, int, str, str]] = []
    for skill_index, canonical, alias, pattern in _PATTERNS:
        for match in pattern.finditer(text):
            surface = match.group(0)
            if not _short_ambiguous_mention_is_clear(
                canonical, surface, text, match.start(), match.end()
            ):
                continue
            candidates.append(
                (match.start(), match.end(), skill_index, canonical, alias)
            )

    # At each position, prefer a longer alias; taxonomy order breaks ties.
    candidates.sort(key=lambda item: (item[0], -(item[1] - item[0]), item[2]))
    accepted_spans: list[tuple[int, int]] = []
    results: list[str] = []
    seen: set[str] = set()
    for start, end, _, canonical, _ in candidates:
        if any(start < accepted_end and end > accepted_start for accepted_start, accepted_end in accepted_spans):
            continue
        accepted_spans.append((start, end))
        if canonical not in seen:
            seen.add(canonical)
            results.append(canonical)
    return results
