"""Load editable word groups as immutable sets, with readable validation errors."""

from .lexicon import DATA, read_json


def load_word_groups(path=DATA / "grammar_words.json"):
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected an object of word lists")
    groups = {}
    for name, words in payload.items():
        if not isinstance(words, list) or not words:
            raise ValueError(f"{path}: {name} must be a nonempty word list")
        for word in words:
            if not isinstance(word, str) or not word or word != word.strip().lower():
                raise ValueError(f"{path}: {name} must contain nonempty lowercase strings")
        groups[name] = frozenset(words)
    return groups
