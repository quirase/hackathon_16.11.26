"""Public integration API. No network, model downloads, or global mutable state."""

from collections import Counter

from .grammar import find_grammar
from .lexicon import DATA, Lexicon
from .morphology import resolve
from .phrases import find_phrases
from .scoring import ScoringConfig, distribution, score
from .text import fragment, prepare, tokenize


def ignored_indices(tokens, terms) -> set[int]:
    ignored = set()
    for term in terms:
        parts = [token.word for token in tokenize(term)]
        if not parts:
            continue
        for start in range(len(tokens) - len(parts) + 1):
            end = start + len(parts)
            if tokens[start].sentence != tokens[end - 1].sentence:
                continue
            if [token.word for token in tokens[start:end]] == parts:
                ignored.update(range(start, end))
    return ignored


class Analyzer:
    def __init__(self, data_dir=DATA, config: ScoringConfig | None = None):
        self.lexicon = Lexicon(data_dir)
        self.config = config or ScoringConfig()

    def analyze(self, text: str | None = None, words=None, *, ignore_terms=()) -> dict:
        """Analyze text plus optional DataFrame/list of word,time_code records.

        If both are supplied, normalized word sequences must match exactly.
        ignore_terms explicitly excludes names/brands; capitalization never does.
        The result is JSON-compatible when input time_code values are JSON-compatible.
        """
        text, tokens = prepare(text, words)
        ignored = ignored_indices(tokens, ignore_terms)
        numbers = {i for i, token in enumerate(tokens) if token.word[0].isdigit()}
        excluded = ignored | numbers
        phrases, consumed = find_phrases(text, tokens, self.lexicon, excluded)
        lexical = list(phrases)
        unknown = []
        blocked = excluded | consumed
        for index, token in enumerate(tokens):
            if index in blocked:
                continue
            evidence = resolve(token.word, self.lexicon)
            location = fragment(text, tokens, [index])
            if evidence is None:
                unknown.append({"word": token.word, **location, "level": None})
                continue
            lexical.append({**location, **evidence})
        lexical.sort(key=lambda match: match["token_indices"][0])
        grammar = find_grammar(text, tokens, self.lexicon)
        for match in grammar:
            if excluded.intersection(match["token_indices"]):
                match["ambiguous"] = True
        word_count = len(tokens) - len(excluded)
        covered = sum(len(match["token_indices"]) for match in lexical)
        coverage = covered / max(1, word_count)
        summary = score(lexical, grammar, word_count, coverage, self.config)
        warnings = []
        if word_count < 100:
            warnings.append("Short transcript: the estimate is unstable.")
        if coverage < .85:
            warnings.append("Low dictionary coverage; unknown words have no assigned CEFR.")
        if summary["eligible_lexical_units"] < 3:
            warnings.append("Insufficient reliable lexical evidence to assign a level.")
        counts = Counter(item["word"] for item in unknown)
        return {"schema_version": "1.0", "assessment": summary,
                "statistics": {"tokens": len(tokens), "analyzed_tokens": word_count,
                               "sentences": len({token.sentence for token in tokens}),
                               "coverage": round(coverage, 4), "ignored_tokens": len(ignored),
                               "numeric_tokens": len(numbers), "lexical_distribution": distribution(lexical),
                               "grammar_distribution": distribution(grammar)},
                "lexical_matches": lexical, "grammar_matches": grammar,
                "unknown_words": [{"word": word, "count": count, "level": None} for word, count in sorted(counts.items())],
                "unknown_occurrences": unknown,
                "automatic_matches": [match for match in lexical if match["automatic"]],
                "ignored": [fragment(text, tokens, [i]) for i in sorted(ignored)],
                "sources": self.lexicon.manifest, "warnings": warnings}


def analyze(text: str | None = None, words=None, *, ignore_terms=(), data_dir=DATA,
            config: ScoringConfig | None = None) -> dict:
    """Convenience entry point; reuse Analyzer for batches to load dictionaries once."""
    return Analyzer(data_dir, config).analyze(text, words, ignore_terms=ignore_terms)
