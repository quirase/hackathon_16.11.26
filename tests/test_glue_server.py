import json
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen

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
            with patch("backend.server._analyze_url", return_value=("dQw4w9WgXcQ", real_report, full_text)), \
                 patch("backend.server._fetch_oembed", return_value=("Test Title", "Test Channel")), \
                 patch("backend.server.db.save_data") as mock_save:
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

            with patch("backend.server.analyze_transcript", return_value=real_report):
                with urlopen(f"http://127.0.0.1:{port}/api/export?url=dQw4w9WgXcQ", timeout=5) as resp:
                    self.assertEqual(resp.status, 200)
                    csv_text = resp.read().decode("utf-8")
                    self.assertIn("word,lemma,level", csv_text)
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
