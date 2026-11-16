"""Integration guarantees, deliberately independent of predicted CEFR bands."""

import inspect
import json
import unittest

from cefr_analyzer import Analyzer, RESULT_SCHEMA_PATH, SCHEMA_VERSION, analyze

LEVELS = {"A1", "A2", "B1", "B2", "C1", "C2"}
REQUIRED = {"schema_version", "assessment", "word_levels", "statistics",
            "lexical_matches", "grammar_matches", "unknown_words",
            "unknown_occurrences", "automatic_matches", "ignored", "sources", "warnings"}


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analyzer = Analyzer()

    def assert_contract(self, result):
        self.assertIsInstance(result, dict)
        self.assertTrue(REQUIRED <= result.keys())
        self.assertEqual(result["schema_version"], SCHEMA_VERSION)
        assessment = result["assessment"]
        self.assertIn(assessment["level"], LEVELS | {None})
        self.assertEqual(assessment["level"] is None, assessment["score"] is None)
        self.assertIn(assessment["confidence"], {"low", "medium"})
        self.assertIs(assessment["approximate"], True)
        for word, level in result["word_levels"].items():
            self.assertIsInstance(word, str)
            self.assertEqual(word, word.lower())
            self.assertIn(level, LEVELS | {None})
        for name in ("lexical_matches", "grammar_matches", "unknown_occurrences", "ignored"):
            self.assertIsInstance(result[name], list)
            for match in result[name]:
                self.assertIsInstance(match["fragment"], str)
                self.assertLess(match["char_start"], match["char_end"])
                self.assertTrue(match["token_indices"])
                self.assertIsInstance(match["time_codes"], list)
        self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)

    def test_schema_is_packaged_and_agrees_with_public_fields(self):
        schema = json.loads(RESULT_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(set(schema["required"]), REQUIRED)
        self.assertEqual(schema["properties"]["schema_version"]["const"], SCHEMA_VERSION)
        self.assertTrue(schema["additionalProperties"])

    def test_public_signatures_remain_compatible(self):
        for function in (analyze, Analyzer.analyze):
            params = inspect.signature(function).parameters
            for name in ("text", "words"):
                self.assertIsNone(params[name].default)
            self.assertEqual(params["ignore_terms"].kind, inspect.Parameter.KEYWORD_ONLY)

    def test_nonempty_response_and_unknowns(self):
        result = self.analyzer.analyze("She turned it down. That's annoying. Zqxvbling.")
        self.assert_contract(result)
        self.assertIsNone(result["word_levels"]["zqxvbling"])
        self.assertTrue(result["lexical_matches"])
        self.assertTrue(result["grammar_matches"])
        self.assertEqual(result["unknown_words"], [{"word": "zqxvbling", "count": 1, "level": None}])
        self.assertTrue(all(not m["time_codes"] for m in result["lexical_matches"]))

    def test_empty_response_is_valid_without_level(self):
        result = self.analyzer.analyze()
        self.assert_contract(result)
        self.assertIsNone(result["assessment"]["level"])
        self.assertEqual(result["word_levels"], {})
        for name in REQUIRED - {"schema_version", "assessment", "statistics", "word_levels", "sources", "warnings"}:
            self.assertEqual(result[name], [])

    def test_structured_timestamps_are_preserved(self):
        times = [{"start": 1.0, "end": 1.2}, {"start": 1.3, "end": 1.7}]
        rows = [{"word": "That's", "time_code": times[0]},
                {"word": "annoying.", "time_code": times[1]}]
        result = self.analyzer.analyze(words=rows)
        self.assert_contract(result)
        self.assertEqual(result["grammar_matches"][0]["time_codes"], times)

    def test_alignment_error_remains_value_error(self):
        with self.assertRaises(ValueError):
            self.analyzer.analyze("different text", [{"word": "hello", "time_code": 0}])


if __name__ == "__main__":
    unittest.main()
