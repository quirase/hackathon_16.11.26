import json
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen

from backend.exports import (
    build_anki_csv_from_phrases,
    build_anki_csv_from_wordlist,
    build_markdown_study_sheet,
)
from backend.mock_data import build_mock_result
from backend.server import create_server, to_frontend_result
from dataframe import analyze_transcript
from transcript_parser import make_word_dict


class GlueServerTests(unittest.TestCase):
    def test_to_frontend_result_maps_real_cefr_report(self) -> None:
        segments = [
            {"text": "She turned it down despite the overwhelming evidence.", "start": 0.0, "end": 4.0},
            {"text": "We must have been working on this algorithm for hours.", "start": 4.5, "end": 9.0},
        ]
        word_dict = make_word_dict(segments)
        full_text = " ".join(word_dict["word"])
        report = analyze_transcript(text=full_text, word_dict=word_dict)
        result = to_frontend_result(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "dQw4w9WgXcQ",
            report,
            full_text=full_text,
            fetch_meta=False,
        )

        for key in (
            "id", "videoId", "url", "title", "channel", "durationLabel",
            "thumbnailUrl", "detectedLevel", "confidence", "summary",
            "learnerFit", "analyzedAt", "metrics", "vocabDistribution",
            "timeline", "grammarPatterns", "flaggedPhrases", "transcriptExcerpt",
        ):
            self.assertIn(key, result)
        self.assertFalse(result["isMock"])
        self.assertEqual(len(result["vocabDistribution"]), 6)
        self.assertEqual(sum(x["percentage"] for x in result["vocabDistribution"]), 100)
        self.assertEqual(len(result["metrics"]), 4)
        reconstructed = "".join(t["text"] for t in result["transcriptExcerpt"])
        self.assertEqual(reconstructed, full_text)
        self.assertIn("<svg", result["plots"]["jointSvg"])

    def test_http_analyze_and_export_endpoints(self) -> None:
        segments = [{"text": "Hello world, this is a simple test.", "start": 0.0, "end": 3.0}]
        word_dict = make_word_dict(segments)
        full_text = " ".join(word_dict["word"])
        real_report = analyze_transcript(text=full_text, word_dict=word_dict)

        server = create_server("127.0.0.1", 0)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch("backend.server.db.get_video_analysis", return_value=None), \
                 patch("backend.server._analyze_url", return_value=("dQw4w9WgXcQ", real_report, full_text)), \
                 patch("backend.server._fetch_oembed", return_value=("Test Title", "Test Channel")), \
                 patch("backend.server.db.save_video") as mock_save:
                req = Request(
                    f"http://127.0.0.1:{port}/api/analyze",
                    data=json.dumps({"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(req, timeout=5) as resp:
                    self.assertEqual(resp.status, 200)
                    payload = json.loads(resp.read().decode("utf-8"))
                    self.assertEqual(payload["videoId"], "dQw4w9WgXcQ")
                    self.assertEqual(payload["title"], "Test Title")
                    self.assertFalse(payload["isMock"])
                    mock_save.assert_called_once()

            with patch("backend.server.db.get_video_analysis", return_value={"videoId": "dQw4w9WgXcQ", "title": "Cached Title", "isMock": False}), \
                 patch("backend.server._analyze_url") as mock_analyze:
                req = Request(
                    f"http://127.0.0.1:{port}/api/analyze",
                    data=json.dumps({"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(req, timeout=5) as resp:
                    self.assertEqual(resp.status, 200)
                    cached_payload = json.loads(resp.read().decode("utf-8"))
                    self.assertEqual(cached_payload["title"], "Cached Title")
                    mock_analyze.assert_not_called()

            with patch(
                "backend.server.db.get_videos_by_level",
                return_value=[{"videoId": "dQw4w9WgXcQ", "url": "https://youtu.be/dQw4w9WgXcQ", "title": "Test Title", "level": "B1"}],
            ):
                with urlopen(f"http://127.0.0.1:{port}/api/recommendations?level=B1", timeout=5) as resp:
                    self.assertEqual(resp.status, 200)
                    rec_payload = json.loads(resp.read().decode("utf-8"))
                    self.assertEqual(rec_payload["level"], "B1")
                    self.assertEqual(rec_payload["items"][0]["title"], "Test Title")

            with patch("backend.server.analyze_transcript", return_value=real_report):
                with urlopen(f"http://127.0.0.1:{port}/api/export?url=dQw4w9WgXcQ", timeout=5) as resp:
                    self.assertEqual(resp.status, 200)
                    csv_text = resp.read().decode("utf-8")
                    self.assertIn("word,lemma,level", csv_text)
        finally:
            server.shutdown()
            server.server_close()

    def test_exports_and_mock_endpoints(self) -> None:
        mock_res = build_mock_result("https://www.youtube.com/watch?v=8S0FDjFBj8o", "8S0FDjFBj8o")
        self.assertTrue(mock_res["isMock"])
        self.assertEqual(mock_res["videoId"], "8S0FDjFBj8o")

        fallback_res = build_mock_result("https://www.youtube.com/watch?v=abcdefghijk", "abcdefghijk")
        self.assertTrue(fallback_res["isMock"])
        self.assertEqual(fallback_res["videoId"], "abcdefghijk")

        fname, csv_phrases = build_anki_csv_from_phrases(mock_res["flaggedPhrases"], mock_res["title"])
        self.assertTrue(fname.startswith("lexistube-anki-"))
        self.assertIn("Front (Phrase)", csv_phrases)

        wname, csv_words = build_anki_csv_from_wordlist([
            {
                "word": "nuanced",
                "meaning": "subtle",
                "cefr": "C1",
                "partOfSpeech": "adjective",
                "contextSentence": "A nuanced view.",
                "videoTitle": "Demo",
            }
        ])
        self.assertEqual(wname, "lexistube-my-wordlist.csv")
        self.assertIn("nuanced", csv_words)

        md = build_markdown_study_sheet(mock_res)
        self.assertIn(f"# {mock_res['title']}", md)
        self.assertIn("## Flagged Vocabulary & Phrases", md)

        server = create_server("127.0.0.1", 0, use_mock=True)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with urlopen(f"http://127.0.0.1:{port}/api/health", timeout=5) as resp:
                health = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(health["mock"])

            req = Request(
                f"http://127.0.0.1:{port}/api/analyze",
                data=json.dumps({"url": "https://youtu.be/dQw4w9WgXcQ"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(req, timeout=5) as resp:
                analyzed = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(analyzed["isMock"])
                self.assertEqual(analyzed["videoId"], "dQw4w9WgXcQ")

            anki_req = Request(
                f"http://127.0.0.1:{port}/api/export/anki",
                data=json.dumps({
                    "mode": "phrases",
                    "phrases": analyzed["flaggedPhrases"],
                    "videoTitle": analyzed["title"],
                }).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(anki_req, timeout=5) as resp:
                self.assertEqual(resp.status, 200)
                self.assertIn("Front (Phrase)", resp.read().decode("utf-8"))

            md_req = Request(
                f"http://127.0.0.1:{port}/api/export/markdown",
                data=json.dumps({"result": analyzed}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(md_req, timeout=5) as resp:
                self.assertEqual(resp.status, 200)
                md_payload = json.loads(resp.read().decode("utf-8"))
                self.assertIn("## CEFR Verdict:", md_payload["markdown"])
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
