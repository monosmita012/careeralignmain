"""Role- and skill-relevant YouTube search using the official Data API."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from typing import Any


YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
MAX_SEARCHES = 3
RESULTS_PER_SEARCH = 3
VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")


class YouTubeConfigurationError(RuntimeError):
    """The server-side YouTube API key is not configured."""


class YouTubeAPIError(RuntimeError):
    """The YouTube API request failed or returned an unusable response."""


def _video_topics(
    target_role: str,
    prioritized_gaps: Sequence[Mapping[str, Any]],
    matched_skills: Sequence[Mapping[str, Any]],
) -> list[str]:
    """Choose up to three real CareerAlign skills for small, focused searches."""
    gap_order = {"missing": 0, "partial": 1}
    gaps = sorted(
        (item for item in prioritized_gaps if item.get("gap_type") in gap_order),
        key=lambda item: (
            gap_order[item["gap_type"]],
            -float(item.get("priority_score") or 0),
            str(item.get("skill") or "").casefold(),
        ),
    )
    skills: list[str] = []
    for item in gaps:
        skill = item.get("skill")
        if isinstance(skill, str) and skill.strip() and skill not in skills:
            skills.append(skill.strip())
        if len(skills) == MAX_SEARCHES:
            break

    if not skills:
        matched = sorted(
            matched_skills,
            key=lambda item: (
                -float(item.get("role_frequency_percentage") or 0),
                str(item.get("skill") or "").casefold(),
            ),
        )
        for item in matched:
            skill = item.get("skill")
            if isinstance(skill, str) and skill.strip() and skill not in skills:
                skills.append(skill.strip())
            if len(skills) == MAX_SEARCHES:
                break
    return skills or [target_role]


def search_learning_videos(
    target_role: str,
    prioritized_gaps: Sequence[Mapping[str, Any]],
    matched_skills: Sequence[Mapping[str, Any]],
    *,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Fetch at most nine videos with no more than three YouTube searches."""
    key = api_key if api_key is not None else os.getenv("YOUTUBE_API_KEY", "")
    if not key.strip():
        raise YouTubeConfigurationError(
            "YouTube learning videos are not configured. Set the server environment variable YOUTUBE_API_KEY."
        )
    key = key.strip()

    topics = _video_topics(target_role, prioritized_gaps, matched_skills)
    videos: list[dict[str, Any]] = []
    seen_video_ids: set[str] = set()

    for topic in topics[:MAX_SEARCHES]:
        query = f"{target_role} {topic} tutorial" if topic != target_role else f"{target_role} learning tutorial"
        params = urlencode({
            "part": "snippet",
            "q": query,
            "type": "video",
            "order": "relevance",
            "safeSearch": "strict",
            "relevanceLanguage": "en",
            "maxResults": RESULTS_PER_SEARCH,
            "key": key,
        })
        request = Request(f"{YOUTUBE_SEARCH_URL}?{params}", headers={"Accept": "application/json"})
        try:
            with urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise YouTubeAPIError(f"YouTube search failed (HTTP {exc.code}).") from None
        except (URLError, TimeoutError, OSError):
            raise YouTubeAPIError("YouTube search is temporarily unavailable.") from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise YouTubeAPIError("YouTube returned an unreadable search response.") from None

        if not isinstance(payload, Mapping) or payload.get("error"):
            raise YouTubeAPIError("YouTube returned an unsuccessful search response.")
        items = payload.get("items", [])
        if not isinstance(items, list):
            raise YouTubeAPIError("YouTube returned an invalid search response.")

        for item in items:
            if not isinstance(item, Mapping):
                continue
            video_id = (item.get("id") or {}).get("videoId") if isinstance(item.get("id"), Mapping) else None
            if not isinstance(video_id, str) or not VIDEO_ID_PATTERN.fullmatch(video_id) or video_id in seen_video_ids:
                continue
            snippet = item.get("snippet")
            if not isinstance(snippet, Mapping):
                continue
            thumbnails = snippet.get("thumbnails") if isinstance(snippet.get("thumbnails"), Mapping) else {}
            thumbnail_url = ""
            for size in ("high", "medium", "default"):
                candidate = thumbnails.get(size) if isinstance(thumbnails, Mapping) else None
                candidate_url = candidate.get("url") if isinstance(candidate, Mapping) else None
                if isinstance(candidate_url, str) and candidate_url.startswith("https://"):
                    thumbnail_url = candidate_url
                    break
            description = snippet.get("description")
            videos.append({
                "video_id": video_id,
                "title": str(snippet.get("title") or "Untitled YouTube video"),
                "description": (description[:240] + ("…" if len(description) > 240 else "")) if isinstance(description, str) else "",
                "thumbnail_url": thumbnail_url,
                "channel_title": str(snippet.get("channelTitle") or ""),
                "published_at": str(snippet.get("publishedAt") or ""),
                "topic": topic,
                "youtube_url": f"https://www.youtube.com/watch?v={video_id}",
            })
            seen_video_ids.add(video_id)
            if len(videos) >= MAX_SEARCHES * RESULTS_PER_SEARCH:
                break

    return {
        "target_role": target_role,
        "topics": topics[:MAX_SEARCHES],
        "videos": videos,
        "total_videos": len(videos),
        "message": None if videos else "No relevant learning videos were found for this role.",
    }
