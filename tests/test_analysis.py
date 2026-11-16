import json
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cefr_analyzer import Analyzer, analyze
from cefr_analyzer.morphology import resolve
from cefr_analyzer.scoring import ScoringConfig, score
from cefr_analyzer.sources import import_gse, import_kaikki
from collections import defaultdict


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analyzer = Analyzer()

    def grammar(self, text):
        return self.analyzer.analyze(text)["grammar_matches"]

    def test_predicative_adjectives(self):
        for text in ("That's annoying.", "That's disappointing.", "It is exciting."):
            matches = self.grammar(text)
            self.assertEqual(len(matches), 1)
            self.assertTrue(matches[0]["predicative_adjective"])
            self.assertNotIn("continuous", matches[0]["rule"])

    def test_verbal_annoying(self):
        match = self.grammar("She is annoying me.")[0]
        self.assertEqual(match["rule"], "present_continuous")
        self.assertFalse(match["ambiguous"])

    def test_annoying_noun_object(self):
        match = self.grammar("She is annoying the guests.")[0]
        self.assertEqual(match["rule"], "present_continuous")
        self.assertFalse(match["ambiguous"])

    def test_ambiguous_does_not_resolve_d_contraction(self):
        self.assertEqual(self.grammar("I'd put it there."), [])

    def test_whole_modal_chain(self):
        matches = self.grammar("It must have been exciting.")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["fragment"], "must have been exciting")
        self.assertEqual(matches[0]["rule"], "modal_perfect_copular")

    def test_modal_continuous_never_nested(self):
        matches = self.grammar("She must have been working.")
        self.assertEqual(len(matches), 1)
        self.assertNotEqual(matches[0]["rule"], "present_perfect_continuous")

    def test_actual_perfect_continuous(self):
        self.assertEqual(self.grammar("She has been working.")[0]["rule"], "present_perfect_continuous")

    def test_c1_modal_with_one_chain(self):
        matches = self.grammar("It may well have been exciting.")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["rule"], "may_well")
        self.assertEqual(matches[0]["level"], "C1")
        self.assertEqual(matches[0]["fragment"], "may well have been exciting")

    def test_as_well_consumes_inner_auxiliaries(self):
        matches = self.grammar("She might as well have been working.")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["rule"], "might_as_well")
        self.assertEqual(matches[0]["level"], "C2")

    def test_sourced_perfect_infinitive(self):
        matches = self.grammar("She seems to have written the letter.")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["fragment"], "to have written")
        self.assertEqual(matches[0]["level"], "C1")

    def test_frequent_real_c1_grammar(self):
        result = self.analyzer.analyze("She may well like the dog. " * 6)
        self.assertGreaterEqual(result["assessment"]["grammar_score"], 4)
        self.assertGreaterEqual(result["assessment"]["score"], 3)

    def test_chain_with_adverbs_and_negation(self):
        matches = self.grammar("It must not have really been exciting.")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["fragment"], "must not have really been exciting")

    def test_going_to_is_not_progressive(self):
        matches = self.grammar("She is going to work.")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["rule"], "going_to")

    def test_have_to_is_one_chain(self):
        self.assertEqual(self.grammar("She has to work.")[0]["rule"], "have_to")

    def test_negative_source_is_negative_row(self):
        match = self.grammar("She has not been working.")[0]
        self.assertEqual(match["rule"], "present_perfect_continuous_negative")
        self.assertTrue(all(source["row_id"] == "63-1" for source in match["sources"]))

    def test_ambiguous_predicate(self):
        self.assertTrue(self.grammar("That is annoying for everyone.")[0]["ambiguous"])

    def test_passive_chain(self):
        matches = self.grammar("The letter has been written by her.")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["rule"], "present_perfect_passive")

    def test_regular_inflections(self):
        for word, lemma in (("walked", "walk"), ("studied", "study"), ("running", "run"),
                            ("boxes", "box"), ("stopped", "stop"), ("making", "make")):
            self.assertIn(lemma, resolve(word, self.analyzer.lexicon)["lemma_candidates"])

    def test_irregular_inflections(self):
        self.assertIn("go", resolve("went", self.analyzer.lexicon)["lemma_candidates"])
        self.assertIn("child", resolve("children", self.analyzer.lexicon)["lemma_candidates"])

    def test_unknown_not_inferred_from_ending(self):
        result = self.analyzer.analyze("I saw zqxvbling.")
        self.assertIn({"word": "zqxvbling", "count": 1, "level": None}, result["unknown_words"])

    def test_inflected_phrase(self):
        matches = self.analyzer.analyze("It turned out well.")["lexical_matches"]
        phrase = next(match for match in matches if match["lemma"] == "turn out")
        self.assertEqual(phrase["fragment"], "turned out")
        self.assertTrue(phrase["level_conflict"])
        self.assertEqual(phrase["level"], "B1")  # GSE B1 beats Cambridge B2.

    def test_separated_phrase_components_only(self):
        result = self.analyzer.analyze("She turned it down.")
        matches = result["lexical_matches"]
        phrase = next(match for match in matches if match["lemma"] == "turn down")
        self.assertEqual(phrase["token_indices"], [1, 3])
        self.assertTrue(phrase["ambiguous"])
        self.assertTrue(any(match["fragment"] == "it" for match in matches))
        indices = [index for match in matches for index in match["token_indices"]]
        self.assertEqual(len(indices), len(set(indices)))

    def test_object_after_particle(self):
        result = self.analyzer.analyze("She turned down the offer.")
        self.assertTrue(any(match["lemma"] == "turn down" for match in result["lexical_matches"]))

    def test_no_phrase_across_sentence(self):
        result = self.analyzer.analyze("She turned. Out came a cat.")
        self.assertFalse(any(match["lemma"] == "turn out" for match in result["lexical_matches"]))

    def test_no_separated_phrase_across_clause(self):
        result = self.analyzer.analyze("Turn if I look down.")
        self.assertFalse(any(match["lemma"] == "turn down" for match in result["lexical_matches"]))

    def test_explicit_ignore_case_insensitive_multiword(self):
        result = self.analyzer.analyze("Zqxv visited New York.", ignore_terms=["zqxv", "New York"])
        self.assertEqual(result["statistics"]["ignored_tokens"], 3)
        self.assertNotIn("zqxv", [item["word"] for item in result["unknown_words"]])

    def test_uppercase_does_not_hide_unknown(self):
        result = self.analyzer.analyze("Zqxv visited London.")
        self.assertIn("zqxv", [item["word"] for item in result["unknown_words"]])

    def test_numbers_are_not_unknown_words(self):
        result = self.analyzer.analyze("I have 42 books.")
        self.assertEqual(result["statistics"]["numeric_tokens"], 1)
        self.assertNotIn("42", [item["word"] for item in result["unknown_words"]])

    def test_line_break_invariance(self):
        text = "That's annoying. She turned it down. It must have been exciting."
        flat = self.analyzer.analyze(text)
        wrapped = self.analyzer.analyze(text.replace(" ", "\n"))
        self.assertEqual(flat["assessment"], wrapped["assessment"])
        self.assertEqual(flat["statistics"], wrapped["statistics"])
        for key in ("lexical_matches", "grammar_matches", "unknown_occurrences"):
            def semantic(matches):
                return [{k: v for k, v in match.items() if k not in {"char_start", "char_end"}} for match in matches]
            self.assertEqual(semantic(flat[key]), semantic(wrapped[key]))

    def test_timestamp_rows_contractions(self):
        rows = [{"word": "That's", "time_code": "00:01"}, {"word": "annoying.", "time_code": "00:02"}]
        result = self.analyzer.analyze("That's annoying.", rows)
        self.assertEqual(result["grammar_matches"][0]["time_codes"], ["00:01", "00:02"])

    def test_dataframe_input_without_pandas_dependency(self):
        class Frame:
            def to_dict(self, orient):
                self.orient = orient
                return [{"word": "hello", "time_code": 0.5}]
        result = self.analyzer.analyze(words=Frame())
        self.assertEqual(result["lexical_matches"][0]["time_codes"], [0.5])

    @unittest.skipUnless(importlib.util.find_spec("pandas"), "optional pandas is not installed")
    def test_real_pandas_dataframe(self):
        import pandas as pd
        frame = pd.DataFrame([{"word": "She", "time_code": 0.0},
                              {"word": "is", "time_code": 0.1},
                              {"word": "annoying", "time_code": 0.3},
                              {"word": "me.", "time_code": 0.6}])
        result = self.analyzer.analyze("She is annoying me.", words=frame)
        self.assertEqual(result["grammar_matches"][0]["time_codes"], [0.1, 0.3])

    def test_timestamp_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, "differ"):
            self.analyzer.analyze("hello world", [{"word": "hello", "time_code": 0}])

    def test_missing_timestamp_column_rejected(self):
        with self.assertRaises(ValueError):
            self.analyzer.analyze(words=[{"word": "hello"}])

    def test_empty_input_has_no_level(self):
        result = self.analyzer.analyze("")
        self.assertIsNone(result["assessment"]["level"])
        self.assertEqual(result["unknown_words"], [])

    def test_word_levels_uses_surface_forms_and_unknown_null(self):
        result = self.analyzer.analyze("Cats cats zqxvbling.")
        self.assertEqual(result["word_levels"], {"cats": "A1", "zqxvbling": None})

    def test_word_levels_keeps_phrase_components_together(self):
        result = self.analyzer.analyze("She turned it down.")
        self.assertEqual(result["word_levels"], {"she": "A1", "turned down": "B1", "it": "A1"})

    def test_word_levels_excludes_ignored_words_and_numbers(self):
        result = self.analyzer.analyze("John likes 42 cats.", ignore_terms=["John"])
        self.assertNotIn("john", result["word_levels"])
        self.assertNotIn("42", result["word_levels"])

    def test_empty_word_levels(self):
        self.assertEqual(self.analyzer.analyze("")["word_levels"], {})

    def test_default_excludes_automatic(self):
        automatic = next(term for term, entries in self.analyzer.lexicon.entries.items()
                         if " " not in term and all(item["automatic"] for item in entries)
                         and entries[0]["level"] == "C2")
        result = self.analyzer.analyze(f"I like the {automatic}.")
        self.assertTrue(result["automatic_matches"])
        self.assertLess(result["assessment"]["lexical_score"], 6)

    def test_grammar_has_traceable_source(self):
        match = self.grammar("She has been working.")[0]
        self.assertTrue(match["sources"])
        self.assertTrue(all(source["row_id"] == "63" for source in match["sources"]))


class ScoringTests(unittest.TestCase):
    def lexical(self):
        return [{"lemma": "dog", "level": "A1", "ambiguous": False, "automatic": False}] * 100

    def grammar(self, count, ambiguous=False):
        return [{"rule": "advanced", "level": "C1", "ambiguous": ambiguous,
                 "token_indices": [index * 50], "sentence": index} for index in range(count)]

    def test_rare_grammar_does_not_raise_level(self):
        result = score(self.lexical(), self.grammar(1), 200, 1.0, ScoringConfig())
        self.assertEqual(result["level"], "A1")

    def test_frequent_grammar_has_strong_influence(self):
        result = score(self.lexical(), self.grammar(15), 250, 1.0, ScoringConfig())
        self.assertGreaterEqual(result["score"], 4)

    def test_frequent_grammar_in_short_text(self):
        structures = self.grammar(3)
        for match in structures:
            match["token_indices"] = [0]
        result = score(self.lexical(), structures, 40, 1.0, ScoringConfig())
        self.assertGreaterEqual(result["score"], 4)

    def test_ambiguous_grammar_cannot_raise_level(self):
        result = score(self.lexical(), self.grammar(15, True), 250, 1.0, ScoringConfig())
        self.assertEqual(result["level"], "A1")

    def test_automatic_opt_in(self):
        words = [{"lemma": "hardword", "level": "C1", "automatic": True}] * 20
        self.assertIsNone(score(words, [], 20, 1, ScoringConfig())["level"])
        self.assertEqual(score(words, [], 20, 1, ScoringConfig(include_automatic=True))["level"], "C1")

    def test_invalid_config(self):
        with self.assertRaises(ValueError):
            ScoringConfig(grammar_support=1)


class ImportTests(unittest.TestCase):
    def test_gse_uses_explicit_cefr_not_numeric_gse(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "gse.json"
            payload = {"count": 1, "data": [{"itemId": "1", "expression": "test",
                       "cefr": "B1+ (51-58)", "gse": "99", "grammaticalCategories": ["noun"]}]}
            path.write_text(json.dumps(payload), encoding="utf-8")
            entries = defaultdict(list)
            import_gse(path, entries, [])
            self.assertEqual(entries["test"][0]["level"], "B1")

    def test_gse_incomplete_response_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "gse.json"
            path.write_text('{"count": 2, "data": []}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Incomplete"):
                import_gse(path, defaultdict(list), [])

    def test_kaikki_morphology_only_english(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "kaikki.jsonl"
            rows = [{"word": "go", "lang_code": "en", "forms": [{"form": "went", "tags": ["past"]}]},
                    {"word": "ir", "lang_code": "es", "forms": [{"form": "fui", "tags": ["past"]}]}]
            path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
            forms = defaultdict(list)
            import_kaikki(path, forms)
            self.assertEqual(forms["went"][0]["lemma"], "go")
            self.assertNotIn("fui", forms)


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-m", "cefr_analyzer", *args], capture_output=True, text=True, encoding="utf-8")

    def test_json_cli(self):
        result = self.run_cli("analyze", "--text", "I like cats.", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("assessment", json.loads(result.stdout))
        self.assertEqual(json.loads(result.stdout)["word_levels"]["cats"], "A1")

    def test_error_cli(self):
        result = self.run_cli("analyze", "--file", "missing-transcript-file.txt")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Error:", result.stderr)


if __name__ == "__main__":
    unittest.main()
