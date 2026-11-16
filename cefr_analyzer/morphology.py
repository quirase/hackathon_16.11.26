"""Inflections are accepted only when the resulting lemma is in the lexicon."""

from .levels import number


def regular_candidates(word: str) -> list[tuple[str, str, str]]:
    found = []
    if word.endswith("ies") and len(word) > 4:
        found.append((word[:-3] + "y", "plural_or_present", "noun,verb"))
    if word.endswith("s") and not word.endswith(("ss", "us", "is")):
        found.append((word[:-1], "plural_or_present", "noun,verb"))
    if word.endswith("es"):
        found.append((word[:-2], "plural_or_present", "noun,verb"))
    for ending, kind in (("ing", "gerund"), ("ed", "past_participle"),
                         ("er", "comparative"), ("est", "superlative")):
        if not word.endswith(ending) or len(word) <= len(ending) + 2:
            continue
        stem = word[:-len(ending)]
        pos = "verb" if ending in {"ing", "ed"} else "adjective"
        found.extend([(stem, kind, pos), (stem + "e", kind, pos)])
        if stem.endswith("i") and ending != "ing":
            found.append((stem[:-1] + "y", kind, pos))
        if len(stem) > 2 and stem[-1] == stem[-2]:
            found.append((stem[:-1], kind, pos))
        if ending == "ing" and stem.endswith("y"):
            found.append((stem[:-1] + "ie", kind, pos))
    return found


def candidates(word: str, lexicon) -> list[dict]:
    result = []
    if word in lexicon.entries:
        result.append({"lemma": word, "kind": "exact"})
    for form in lexicon.forms.get(word, []):
        if form["lemma"] in lexicon.entries:
            result.append({"lemma": form["lemma"], "kind": form["kind"]})
    for lemma, kind, parts in regular_candidates(word):
        if any(lexicon.has_pos(lemma, pos) for pos in parts.split(",")):
            result.append({"lemma": lemma, "kind": kind})
    return result


def resolve(word: str, lexicon) -> dict | None:
    choices = []
    for candidate in candidates(word, lexicon):
        evidence = lexicon.evidence(candidate["lemma"])
        choices.append({**evidence, "match": candidate["kind"]})
    if not choices:
        return None
    choices.sort(key=lambda entry: (number(entry["level"]), entry["automatic"], entry["match"] != "exact"))
    chosen = choices[0]
    alternatives = sorted({entry["lemma"] for entry in choices})
    return {**chosen, "lemma_candidates": alternatives, "ambiguous": len(alternatives) > 1}


def is_form(word: str, kind: str, lexicon) -> bool:
    for candidate in candidates(word, lexicon):
        if candidate["kind"] == kind and lexicon.has_pos(candidate["lemma"], "verb"):
            return True
    return False
