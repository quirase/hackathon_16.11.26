"""Longest dictionary phrases first; only matched components are consumed."""

from .morphology import candidates
from .text import fragment

OBJECT_WORDS = {"me", "you", "him", "her", "it", "us", "them", "this", "that"}
DETERMINERS = {"the", "a", "an", "my", "your", "his", "her", "our", "their", "some", "this", "that"}
BLOCKERS = {"and", "but", "or", "if", "because", "when", "who", "which", "that", "to"}
COMPOSITIONAL = {"that is", "in that", "go to", "get to", "more like", "something like"}


def object_gap(words: list[str]) -> bool:
    if len(words) == 1 and words[0] in OBJECT_WORDS:
        return True
    return bool(words and words[0] in DETERMINERS and not (set(words[1:]) & BLOCKERS))


def contiguous(tokens, start: int, parts: list[str], lemmas: set[str]) -> list[int] | None:
    end = start + len(parts)
    if end > len(tokens) or tokens[end - 1].sentence != tokens[start].sentence:
        return None
    if parts[0] not in lemmas:
        return None
    if [token.word for token in tokens[start + 1:end]] != parts[1:]:
        return None
    return list(range(start, end))


def separated(tokens, start: int, rule: dict, lemmas: set[str]) -> list[int] | None:
    head, particle = rule["term"].split()
    if head not in lemmas:
        return None
    for end in range(start + 2, min(len(tokens), start + rule.get("max_gap", 4) + 2)):
        if tokens[end].sentence != tokens[start].sentence:
            break
        gap = [token.word for token in tokens[start + 1:end]]
        if tokens[end].word == particle and object_gap(gap):
            return [start, end]
    return None


def template_match(tokens, start, rule, lemmas):
    parts = rule["parts"]
    slot = parts.index("{object}")
    prefix = contiguous(tokens, start, parts[:slot], lemmas)
    if prefix is None:
        return None
    gap_start = start + slot
    for size in range(1, rule.get("max_gap", 4) + 1):
        suffix_start = gap_start + size
        if suffix_start >= len(tokens):
            break
        gap = [token.word for token in tokens[gap_start:suffix_start]]
        suffix = contiguous(tokens, suffix_start, parts[slot + 1:], {tokens[suffix_start].word})
        if suffix and object_gap(gap) and tokens[suffix[-1]].sentence == tokens[start].sentence:
            return prefix + suffix
    return None


def find_phrases(text, tokens, lexicon, ignored: set[int]) -> tuple[list[dict], set[int]]:
    proposals = []
    for start, token in enumerate(tokens):
        lemmas = {item["lemma"] for item in candidates(token.word, lexicon)} | {token.word}
        terms = set()
        for lemma in lemmas:
            terms.update(lexicon.phrase_index.get(lemma, []))
        for term in sorted(terms):
            indices = contiguous(tokens, start, term.split(), lemmas)
            if indices:
                proposals.append((indices, term, False))
        for rule in lexicon.phrase_rules:
            if rule.get("parts"):
                indices = template_match(tokens, start, rule, lemmas)
            elif rule.get("separable"):
                indices = separated(tokens, start, rule, lemmas)
            else:
                continue
            if indices:
                proposals.append((indices, rule["term"], True))
    proposals.sort(key=lambda item: (-len(item[0]), item[0][0], item[0][-1], item[1]))
    consumed = set(ignored)
    matches = []
    for indices, term, has_gap in proposals:
        if consumed.intersection(indices):
            continue
        evidence = lexicon.evidence(term)
        if evidence is None:
            continue
        # A separated surface pattern may also be literal motion; keep it uncertain.
        noun_head = indices[0] > 0 and tokens[indices[0] - 1].word in DETERMINERS
        match = {**fragment(text, tokens, indices), **evidence, "match": "phrase",
                 "ambiguous": has_gap or term in COMPOSITIONAL or noun_head,
                 "separated": has_gap}
        matches.append(match)
        consumed.update(indices)
    return sorted(matches, key=lambda match: match["token_indices"][0]), consumed - ignored
