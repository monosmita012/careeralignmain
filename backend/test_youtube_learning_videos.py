"""Focused tests for the YouTube learning-video endpoint; no real API calls."""

import json
import os
import unittest
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

from fastapi.testclient import TestClient

from backend.main import app


class StubResponse:
    def __init__(self, payload):
        self.body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.body


class YouTubeLearningVideosEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)

    @staticmethod
    def payload():
        return {"target_role": "Data Analyst", "records": []}

    @staticmethod
    def api_item(video_id="video000001", skill="SQL"):
        return {
            "id": {"kind": "youtube#video", "videoId": video_id},
            "snippet": {
                "title": f"{skill} tutorial for Data Analyst",
                "description": "A practical lesson.",
                "thumbnails": {"medium": {"url": "https://i.ytimg.com/vi/example/mqdefault.jpg"}},
                "channelTitle": "Example Learning Channel",
                "publishedAt": "2025-01-01T00:00:00Z",
            },
        }

    def test_missing_api_key_returns_clear_configuration_error(self):
        with patch.dict(os.environ, {"YOUTUBE_API_KEY": ""}), patch(
            "backend.youtube_learning_videos.urlopen"
        ) as mocked_urlopen:
            response = self.client.post("/api/youtube-learning-videos", json=self.payload())
        self.assertEqual(503, response.status_code)
        self.assertIn("YOUTUBE_API_KEY", response.json()["detail"])
        mocked_urlopen.assert_not_called()

    def test_success_returns_role_relevant_videos_and_limited_searches(self):
        secret = "test-key-never-return-this"
        responses = [
            StubResponse({"items": [self.api_item(f"video{search_index}{item_index:05d}", f"Skill{search_index}") for item_index in range(1, 4)]})
            for search_index in range(1, 4)
        ]
        with patch.dict(os.environ, {"YOUTUBE_API_KEY": secret}), patch(
            "backend.youtube_learning_videos.urlopen", side_effect=responses
        ) as mocked_urlopen:
            response = self.client.post("/api/youtube-learning-videos", json=self.payload())

        self.assertEqual(200, response.status_code, response.text)
        body = response.json()
        self.assertEqual("Data Analyst", body["target_role"])
        self.assertEqual(9, body["total_videos"])
        self.assertTrue(all("tutorial" in item["title"].lower() for item in body["videos"]))
        self.assertTrue(all(item["youtube_url"].startswith("https://www.youtube.com/watch?v=") for item in body["videos"]))
        self.assertLessEqual(mocked_urlopen.call_count, 3)
        first_query = parse_qs(urlsplit(mocked_urlopen.call_args_list[0].args[0].full_url).query)
        self.assertIn("Data Analyst", first_query["q"][0])
        self.assertIn(body["topics"][0], first_query["q"][0])
        self.assertIn("tutorial", first_query["q"][0].lower())
        self.assertEqual(["video"], first_query["type"])
        self.assertEqual(["relevance"], first_query["order"])
        self.assertEqual(["strict"], first_query["safeSearch"])
        self.assertNotIn(secret, response.text)

    def test_empty_youtube_results_return_empty_list_and_message(self):
        with patch.dict(os.environ, {"YOUTUBE_API_KEY": "unit-test-key"}), patch(
            "backend.youtube_learning_videos.urlopen", return_value=StubResponse({"items": []})
        ):
            response = self.client.post("/api/youtube-learning-videos", json=self.payload())
        self.assertEqual(200, response.status_code)
        self.assertEqual([], response.json()["videos"])
        self.assertIn("No relevant learning videos", response.json()["message"])

    def test_youtube_api_failure_returns_controlled_error(self):
        error = HTTPError("https://youtube.invalid", 403, "denied", None, BytesIO(b"private error details"))
        with patch.dict(os.environ, {"YOUTUBE_API_KEY": "unit-test-key"}), patch(
            "backend.youtube_learning_videos.urlopen", side_effect=error
        ):
            response = self.client.post("/api/youtube-learning-videos", json=self.payload())
        self.assertEqual(502, response.status_code)
        self.assertIn("HTTP 403", response.json()["detail"])
        self.assertNotIn("unit-test-key", response.text)
        self.assertNotIn("private error details", response.text)

    def test_response_never_contains_configured_api_key(self):
        secret = "sensitive-youtube-key"
        with patch.dict(os.environ, {"YOUTUBE_API_KEY": secret}), patch(
            "backend.youtube_learning_videos.urlopen",
            return_value=StubResponse({"items": [self.api_item()]}),
        ):
            response = self.client.post("/api/youtube-learning-videos", json=self.payload())
        self.assertEqual(200, response.status_code)
        self.assertNotIn(secret, response.text)


if __name__ == "__main__":
    unittest.main()
