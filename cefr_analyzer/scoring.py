"""Prevalence-based heuristic; unknown and ambiguous evidence cannot raise CEFR."""

from collections import Counter
from dataclasses import asdict, dataclass
from math import ceil

from .levels import LEVELS, band, number

# Function words carry little lexical difficulty and otherwise drown out content.
FUNCTION_WORDS = set("""a an the i you he she it we they me him her us them my your his
our their its this that these those am is are was were be been being have has had
do does did can could will would shall should may might must to of in on at for
from with by as and or but if so than then not no yes there here what who which
when where why how all any some each every both either neither much many more
most less few very too also just only even up down out into about over under
through between before after while because until since during""".split())


@dataclass(frozen=True)
class ScoringConfig:
    lexical_support: int = 3
    lexical_tail_share: float = 0.07
    advanced_tail_share: float = 0.05
    proficient_tail_share: float = 0.03
    advanced_type_support: int = 3
    grammar_support: int = 3
    grammar_full_density: float = 6.0  # occurrences per 100 words
    grammar_weight: float = 0.75
    include_automatic: bool = False

    def __post_init__(self):
        if self.lexical_support < 1 or self.grammar_support < 2:
            raise ValueError("Support must be positive; grammar_support must be >= 2")
        if not 0 < self.lexical_tail_share <= 1 or self.grammar_full_density <= 0:
            raise ValueError("Invalid prevalence thresholds")
        if not 0 <= self.grammar_weight <= 1:
            raise ValueError("grammar_weight must be in [0, 1]")
        if not 0 < self.proficient_tail_share <= self.advanced_tail_share <= self.lexical_tail_share <= 1:
            raise ValueError("Lexical shares must satisfy 0 < proficient <= advanced <= lexical <= 1")
        if self.advanced_type_support < 2:
            raise ValueError("advanced_type_support must be >= 2")


def eligible(match, config):
    return (match.get("level") in LEVELS and not match.get("ambiguous", False)
            and (config.include_automatic or not match.get("automatic", False)))


def distribution(matches) -> dict:
    counts = Counter(match["level"] for match in matches if match.get("level") in LEVELS)
    return {level: counts[level] for level in LEVELS}


def lexical_profile(content_words, config):
    lexical_score = 1.0
    lexical_tails = {}
    for level in LEVELS[1:]:
        evidence = [match for match in content_words if number(match["level"]) >= number(level)]
        support = len(evidence)
        types = len({match.get("lemma") for match in evidence})
        share = support / max(1, len(content_words))
        threshold = config.lexical_tail_share
        if level == "B2":
            threshold = config.advanced_tail_share
        if level in {"C1", "C2"}:
            threshold = config.proficient_tail_share
        diverse = number(level) < 4 or types >= config.advanced_type_support
        lexical_tails[level] = {"count": support, "share": round(share, 4),
                                "types": types, "required_share": threshold}
        if support >= config.lexical_support and share >= threshold and diverse:
            lexical_score = float(number(level))
    return lexical_score, lexical_tails


def grammar_profile(structures, word_count, config):
    grammar_score = 1.0
    grammar_tails = {}
    for level in LEVELS[1:]:
        support = sum(number(match["level"]) >= number(level) for match in structures)
        density = 100 * support / max(1, word_count)
        distinct = len({match["token_indices"][0] // 50 for match in structures
                        if number(match["level"]) >= number(level)})
        strength = min(1.0, density / config.grammar_full_density)
        if support < config.grammar_support:
            strength = 0.0
        # Fixed word windows also work for unpunctuated transcripts.
        available_windows = min(3, max(1, ceil(word_count / 50)))
        strength *= min(1.0, distinct / available_windows)
        grammar_score = max(grammar_score, 1 + (number(level) - 1) * strength)
        grammar_tails[level] = {"count": support, "per_100_words": round(density, 3),
                               "windows_50_words": distinct, "strength": round(strength, 3)}
    return grammar_score, grammar_tails


def score(lexical, grammar, word_count: int, coverage: float, config: ScoringConfig) -> dict:
    words = [match for match in lexical if eligible(match, config)]
    content_words = [match for match in words if match.get("lemma") not in FUNCTION_WORDS]
    structures = [match for match in grammar if eligible(match, config)]
    lexical_score, lexical_tails = lexical_profile(content_words, config)
    grammar_score, grammar_tails = grammar_profile(structures, word_count, config)
    combined = lexical_score + config.grammar_weight * max(0, grammar_score - lexical_score)
    enough = len(words) >= 3
    confidence = "low"
    if word_count >= 100 and coverage >= .9 and len(words) / max(1, len(lexical)) >= .75:
        confidence = "medium"  # Heuristic confidence, never a calibrated probability.
    return {"level": band(combined) if enough else None,
            "score": round(combined, 3) if enough else None,
            "confidence": confidence, "approximate": True,
            "lexical_score": lexical_score, "grammar_score": round(grammar_score, 3),
            "eligible_lexical_units": len(words), "eligible_grammar_matches": len(structures),
            "content_lexical_units": len(content_words),
            "lexical_tails": lexical_tails, "grammar_tails": grammar_tails,
            "config": asdict(config)}
