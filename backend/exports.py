"""Export formatters (Anki CSV and Markdown study sheet) for LexisTube."""

from __future__ import annotations

import csv
import io
import re
from typing import Any


def slugify(text: str) -> str:
    """Convert text to a lowercase URL/filename-safe slug."""
    cleaned = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40]
    return cleaned or "vocabulary"


def _rows_to_csv(rows: list[list[str]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n", quoting=csv.QUOTE_ALL)
    writer.writerows(rows)
    return buf.getvalue().rstrip("\n")


def build_anki_csv_from_phrases(phrases: list[dict[str, Any]], video_title: str) -> tuple[str, str]:
    """Build an Anki-ready CSV from flagged phrases; returns (filename, csv_text)."""
    header = ["Front (Phrase)", "Back (Meaning)", "CEFR", "Part of Speech", "Example", "Source"]
    rows = [
        [
            str(p.get("phrase", "")),
            str(p.get("meaning", "")),
            str(p.get("cefr", "")),
            str(p.get("partOfSpeech", "")),
            str(p.get("contextSentence", "")),
            f"{video_title} ({p.get('timestampLabel', '')})",
        ]
        for p in phrases
    ]
    filename = f"lexistube-anki-{slugify(video_title)}.csv"
    return filename, _rows_to_csv([header, *rows])


def build_anki_csv_from_wordlist(words: list[dict[str, Any]]) -> tuple[str, str]:
    """Build an Anki-ready CSV from saved wordlist items; returns (filename, csv_text)."""
    header = ["Front (Word)", "Back (Meaning)", "CEFR", "Part of Speech", "Example", "Source"]
    rows = [
        [
            str(w.get("word", "")),
            str(w.get("meaning", "")),
            str(w.get("cefr", "")),
            str(w.get("partOfSpeech", "")),
            str(w.get("contextSentence") or ""),
            str(w.get("videoTitle", "")),
        ]
        for w in words
    ]
    return "lexistube-my-wordlist.csv", _rows_to_csv([header, *rows])


def build_markdown_study_sheet(result: dict[str, Any]) -> str:
    """Build a Markdown study sheet from a VideoAnalysisResult dict."""
    metrics = result.get("metrics") or []
    vocab_dist = result.get("vocabDistribution") or []
    flagged = result.get("flaggedPhrases") or []
    grammar = result.get("grammarPatterns") or []

    lines: list[str] = [
        f"# {result.get('title', '')}",
        f"**Channel:** {result.get('channel', '')} · **Duration:** {result.get('durationLabel', '')}",
        f"**URL:** {result.get('url', '')}",
        "",
        f"## CEFR Verdict: {result.get('detectedLevel', '')} ({result.get('confidence', '')}% confidence)",
        str(result.get("summary", "")),
        "",
        f"> **Learner Fit:** {result.get('learnerFit', '')}",
        "",
        "## Linguistic Metrics",
        *[f"- **{m.get('label', '')}:** {m.get('value', '')} — {m.get('detail', '')}" for m in metrics],
        "",
        "## Vocabulary Distribution",
        " | ".join(f"{v.get('level', '')}: {v.get('percentage', 0)}%" for v in vocab_dist),
        "",
        "## Flagged Vocabulary & Phrases",
        *[
            f"- **{p.get('phrase', '')}** (*{p.get('cefr', '')}*, {p.get('partOfSpeech', '')}, `{p.get('timestampLabel', '')}`): {p.get('meaning', '')}\n  - Example: \"{p.get('contextSentence', '')}\""
            for p in flagged
        ],
        "",
        "## Grammar & Phrasal Patterns",
        *[
            f"- **{g.get('pattern', '')}** (*{g.get('cefr', '')}*, {g.get('occurrences', 0)}x): {g.get('explanation', '')} — *\"{g.get('example', '')}\"*"
            for g in grammar
        ],
    ]
    return "\n".join(lines)
