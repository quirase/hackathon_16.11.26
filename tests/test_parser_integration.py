"""Provider fixtures -> real parser -> real analyzer, without network or API keys."""

import sys
import types
import unittest
from unittest.mock import Mock, patch

import transcript_parser as parser
from cefr_analyzer import Analyzer


class ParserIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analyzer = Analyzer()

    def parse(self, texts):
        segments = [{"text": text, "start": index, "end": index + 1} for index, text in enumerate(texts)]
        with patch.object(parser, "get_segments_from_youtube", return_value=segments):
            columns, text = parser.get_transcript("dQw4w9WgXcQ")
        self.assertEqual(text, " ".join(columns["word"]))
        self.assertEqual(len(columns["word"]), len(columns["time_code"]))
        return columns, text, self.analyzer.analyze(text=text, words=columns)

    def test_preserves_numbers_and_unicode_words(self):
        columns, _, result = self.parse(["She paid 42 dollars at the café. Well—maybe."])
        self.assertIn("42", columns["word"])
        self.assertIn("café.", columns["word"])
        self.assertIn("Well—maybe.", columns["word"])
        self.assertIn("café", result["word_levels"])
        self.assertNotIn("caf", result["word_levels"])
        self.assertEqual(result["statistics"]["numeric_tokens"], 1)

    def test_caption_split_does_not_break_auxiliary_chain(self):
        _, text, result = self.parse(["She must have", "been working for hours."])
        self.assertEqual(text, "She must have been working for hours.")
        matches = result["grammar_matches"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["fragment"], "must have been working")
        self.assertNotEqual(matches[0]["rule"], "present_perfect_continuous")

    def test_phrase_across_caption_split(self):
        _, _, result = self.parse(["It turned", "out well."])
        self.assertTrue(any(match["lemma"] == "turn out" for match in result["lexical_matches"]))

    def test_actual_sentence_boundary_is_retained(self):
        _, _, result = self.parse(["It turned.", "Out came a cat."])
        self.assertFalse(any(match["lemma"] == "turn out" for match in result["lexical_matches"]))

    def test_html_annotations_and_curly_apostrophes(self):
        columns, text, _ = self.parse(["[Music] >> <i>We’re</i>&nbsp;ready &#39;now&#39; ♪"])
        self.assertEqual(text, "We're ready 'now'")
        self.assertEqual(columns["word"], ["We're", "ready", "'now'"])

    def test_no_words_is_explicit_error(self):
        with self.assertRaisesRegex(RuntimeError, "no words"):
            self.parse(["[Music] ♪"])

    def test_timestamp_order_including_equal_starts(self):
        segments = [{"text": "Last caption", "start": 2, "end": 3},
                    {"text": "First caption", "start": 0, "end": 10},
                    {"text": "Same start", "start": 0, "end": 2}]
        columns = parser.make_word_dict(segments)
        self.assertEqual(columns["word"], ["First", "caption", "Same", "start", "Last", "caption"])
        self.assertEqual(columns["time_code"], sorted(columns["time_code"]))

    def test_invalid_times_are_rejected(self):
        for start, end in ((-1, 2), (2, 1), (float("nan"), 2), (0, float("inf"))):
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                parser.make_word_dict([{"text": "hello", "start": start, "end": end}])

    def test_column_lengths_must_match(self):
        with self.assertRaisesRegex(ValueError, "equal lengths"):
            self.analyzer.analyze(words={"word": ["hello"], "time_code": []})

    def test_english_unavailable_does_not_use_fallback(self):
        with patch.object(parser, "get_segments_from_youtube", side_effect=parser.TranscriptUnavailableError("no English")), patch.object(parser, "get_segments_from_serpapi") as fallback:
            with self.assertRaises(parser.TranscriptUnavailableError):
                parser.get_transcript("dQw4w9WgXcQ")
            fallback.assert_not_called()

    def test_wrong_language_does_not_use_fallback(self):
        with patch.object(parser, "get_segments_from_youtube", side_effect=parser.TranscriptLanguageError("French")), patch.object(parser, "get_segments_from_serpapi") as fallback:
            with self.assertRaises(parser.TranscriptLanguageError):
                parser.get_transcript("dQw4w9WgXcQ")
            fallback.assert_not_called()

    def test_network_failure_uses_fallback(self):
        segments = [{"text": "Hello there.", "start": 0, "end": 1}]
        with patch.object(parser, "get_segments_from_youtube", side_effect=ConnectionError()), patch.object(parser, "get_segments_from_serpapi", return_value=segments) as fallback:
            with self.assertLogs(parser.LOGGER, level="WARNING"):
                columns, text = parser.get_transcript("dQw4w9WgXcQ")
            fallback.assert_called_once_with("dQw4w9WgXcQ", "en")
            self.analyzer.analyze(text, columns)


class ProviderAdapterTests(unittest.TestCase):
    def test_youtube_never_selects_arbitrary_language(self):
        sdk = types.ModuleType("youtube_transcript_api")
        sdk.NoTranscriptFound = type("NoTranscriptFound", (Exception,), {})
        sdk.TranscriptsDisabled = type("TranscriptsDisabled", (Exception,), {})
        sdk.VideoUnavailable = type("VideoUnavailable", (Exception,), {})
        sdk.YouTubeTranscriptApi = Mock()
        api = sdk.YouTubeTranscriptApi.return_value
        api.fetch.side_effect = sdk.NoTranscriptFound()
        with patch.dict(sys.modules, {"youtube_transcript_api": sdk}):
            with self.assertRaises(parser.TranscriptUnavailableError):
                parser.get_segments_from_youtube("dQw4w9WgXcQ", "en")
        api.fetch.assert_called_once_with("dQw4w9WgXcQ", languages=["en"])
        api.list.assert_not_called()

    def test_serpapi_language_and_millisecond_conversion(self):
        sdk = types.ModuleType("serpapi")
        sdk.HTTPError = type("HTTPError", (Exception,), {})
        sdk.Client = Mock()
        search = sdk.Client.return_value.search
        for code, expected_error in (("en", None), ("fr", parser.TranscriptLanguageError), (None, parser.TranscriptLanguageError)):
            search.return_value = {"available_transcripts": [{"selected": True, "language_code": code}],
                                   "transcript": [{"snippet": "Hello", "start_ms": 1200, "end_ms": 2400}]}
            with patch.dict(sys.modules, {"serpapi": sdk}), patch.object(parser, "SERPAPI_KEYS", ["test-key"]), patch.object(parser, "blocked_until", {}):
                if expected_error:
                    with self.assertRaises(expected_error):
                        parser.get_segments_from_serpapi("dQw4w9WgXcQ", "en")
                else:
                    self.assertEqual(parser.get_segments_from_serpapi("dQw4w9WgXcQ", "en"),
                                     [{"text": "Hello", "start": 1.2, "end": 2.4}])

    def test_supported_urls_and_invalid_hosts(self):
        for url in ("dQw4w9WgXcQ", "https://youtu.be/dQw4w9WgXcQ?t=2", "https://youtube.com/watch?v=dQw4w9WgXcQ", "https://www.youtube.com/shorts/dQw4w9WgXcQ"):
            self.assertEqual(parser.get_video_id(url), "dQw4w9WgXcQ")
        for url in ("https://example.org/?v=dQw4w9WgXcQ", "https://youtube.com.evil.org/watch?v=dQw4w9WgXcQ", "https://youtu.be/dQw4w9WgXcQextra"):
            with self.assertRaises(ValueError):
                parser.get_video_id(url)
