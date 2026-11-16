"""Tokenization, contraction expansion and strict word/timestamp alignment."""

import re
from dataclasses import dataclass

WORD = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?|\d+(?:\.\d+)?")
BOUNDARY = re.compile(r"[.!?;:]")
CONTRACTIONS = {
    "can't": ("can", "not"), "cannot": ("can", "not"),
    "won't": ("will", "not"), "shan't": ("shall", "not"),
    "let's": ("let", "us"),
}
SUBJECTS = {"i", "you", "he", "she", "it", "we", "they", "that", "there", "what", "who"}


@dataclass(frozen=True)
class Token:
    word: str
    start: int
    end: int
    sentence: int
    time_code: object = None
    row: int | None = None


def expand(word: str, following: str = "") -> tuple[str, ...]:
    word = word.lower().replace("’", "'")
    if word in CONTRACTIONS:
        return CONTRACTIONS[word]
    if word.endswith("n't"):
        return word[:-3], "not"
    for ending, auxiliary in (("'m", "am"), ("'re", "are"), ("'ve", "have"), ("'ll", "will")):
        if word.endswith(ending):
            return word[:-len(ending)], auxiliary
    if word.endswith("'s") and word[:-2] in SUBJECTS:
        return word[:-2], "has" if following == "been" else "is"
    if word.endswith("'s"):
        return (word[:-2],)  # Possessive; never guess an auxiliary for a name.
    if word.endswith("'d"):
        return word[:-2], "had" if following == "been" else "'d"
    return (word,)


def tokenize(text: str) -> list[Token]:
    matches = list(WORD.finditer(text))
    result = []
    sentence = 0
    previous_end = 0
    for index, match in enumerate(matches):
        if BOUNDARY.search(text[previous_end:match.start()]):
            sentence += 1
        following = matches[index + 1].group().lower() if index + 1 < len(matches) else ""
        for word in expand(match.group(), following):
            result.append(Token(word, match.start(), match.end(), sentence))
        previous_end = match.end()
    return result


def records_from(words) -> list[dict]:
    if words is None:
        return []
    if hasattr(words, "to_dict"):
        return words.to_dict(orient="records")
    return list(words)


def prepare(text: str | None, words=None) -> tuple[str, list[Token]]:
    records = records_from(words)
    for row in records:
        if "word" not in row or "time_code" not in row or not isinstance(row["word"], str):
            raise ValueError("Each row needs a string 'word' and a 'time_code'.")
    if text is None:
        text = " ".join(row["word"] for row in records)
    if not isinstance(text, str):
        raise ValueError("text must be a string or None")
    tokens = tokenize(text)
    if not records:
        if words is not None and tokens:
            raise ValueError("Timestamp rows are empty but text contains words.")
        return text, tokens
    row_text = " ".join(row["word"] for row in records)
    row_tokens = tokenize(row_text)
    if [token.word for token in tokens] != [token.word for token in row_tokens]:
        raise ValueError("Text and timestamp words differ; timestamps cannot be aligned safely.")
    row_ends = []
    cursor = 0
    for row in records:
        cursor += len(row["word"]) + 1
        row_ends.append(cursor)
    row_index = 0
    aligned = []
    for token, row_token in zip(tokens, row_tokens):
        while row_token.start >= row_ends[row_index]:
            row_index += 1
        aligned.append(Token(token.word, token.start, token.end, token.sentence,
                             records[row_index]["time_code"], row_index))
    return text, aligned


def fragment(text: str, tokens: list[Token], indices: list[int]) -> dict:
    first, last = tokens[min(indices)], tokens[max(indices)]
    times = []
    seen = set()
    for index in indices:
        token = tokens[index]
        if token.row is not None and token.row not in seen:
            times.append(token.time_code)
            seen.add(token.row)
    return {"fragment": " ".join(text[first.start:last.end].split()),
            "char_start": first.start, "char_end": last.end,
            "token_indices": indices, "sentence": first.sentence, "time_codes": times}
