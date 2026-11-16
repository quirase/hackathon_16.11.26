"""Mock analysis payloads for LexisTube preview mode."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

_MOCK_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_data.json")


@lru_cache(maxsize=1)
def load_mock_library() -> dict[str, dict[str, Any]]:
    """Load the static mock video templates from backend/mock_data.json."""
    if not os.path.exists(_MOCK_JSON_PATH):
        return {}
    with open(_MOCK_JSON_PATH, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, dict) else {}


def deterministic_fallback(video_id: str) -> dict[str, Any]:
    """Generate a deterministic synthetic preview for an arbitrary YouTube video ID."""
    levels = ["B1", "B2", "C1", "A2"]
    total = sum(ord(ch) for ch in video_id)
    detected_level = levels[total % len(levels)]
    wpm = 128 + (total % 45)
    confidence = 82 + (total % 14)

    return {
        "videoId": video_id,
        "title": f"YouTube Video ({video_id}) — Mock Preview",
        "channel": "Connected Video Preview",
        "durationLabel": "08:24",
        "thumbnailUrl": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
        "detectedLevel": detected_level,
        "confidence": confidence,
        "summary": (
            "Synthetic preview generated in mock mode. Disable mock mode to run "
            "live transcript & CEFR analysis."
        ),
        "learnerFit": f"Estimated {detected_level} difficulty profile based on mock preview parameters.",
        "metrics": [
            {
                "id": "speechRate",
                "label": "Speech Rate",
                "value": f"{wpm} WPM",
                "score": min(95, round((wpm / 210) * 100)),
                "detail": "Simulated speaking tempo for this preview.",
                "badge": "Brisk" if wpm > 155 else "Moderate",
            },
            {
                "id": "vocabulary",
                "label": "Vocabulary Difficulty",
                "value": "68% Core",
                "score": 64,
                "detail": "Estimated lexical band distribution.",
                "badge": detected_level,
            },
            {
                "id": "grammar",
                "label": "Grammar Complexity",
                "value": "1.9 Clauses",
                "score": 58,
                "detail": "Estimated syntactic subordination depth.",
                "badge": "Balanced",
            },
            {
                "id": "clarity",
                "label": "Accent & Clarity",
                "value": "89 / 100",
                "score": 89,
                "detail": "Estimated speech intelligibility index.",
                "badge": "Clear",
            },
        ],
        "vocabDistribution": [
            {"level": "A1", "percentage": 36},
            {"level": "A2", "percentage": 26},
            {"level": "B1", "percentage": 19},
            {"level": "B2", "percentage": 12},
            {"level": "C1", "percentage": 5},
            {"level": "C2", "percentage": 2},
        ],
        "timeline": [
            {"id": "t1", "startSec": 0, "endSec": 120, "startLabel": "0:00", "endLabel": "2:00", "level": "B1", "wpm": wpm - 10, "intensity": 46, "note": "Opening context"},
            {"id": "t2", "startSec": 120, "endSec": 240, "startLabel": "2:00", "endLabel": "4:00", "level": detected_level, "wpm": wpm, "intensity": 64, "note": "Core explanation"},
            {"id": "t3", "startSec": 240, "endSec": 360, "startLabel": "4:00", "endLabel": "6:00", "level": detected_level, "wpm": wpm + 8, "intensity": 72, "note": "Dense terminology"},
            {"id": "t4", "startSec": 360, "endSec": 504, "startLabel": "6:00", "endLabel": "8:24", "level": "B1", "wpm": wpm - 6, "intensity": 50, "note": "Summary & wrap-up"},
        ],
        "grammarPatterns": [
            {
                "id": "mg1",
                "pattern": "Subordinate Contrast Clauses",
                "cefr": "B2",
                "occurrences": 6,
                "explanation": 'Connecting contrasting ideas with "although", "whereas", or "while".',
                "example": "While the concept sounds abstract, the daily habit is straightforward.",
            },
            {
                "id": "mg2",
                "pattern": "Modal Hedging",
                "cefr": "B2",
                "occurrences": 8,
                "explanation": 'Softening claims using "might", "tend to", or "could indicate".',
                "example": "This pattern tends to appear in upper-intermediate explanations.",
            },
        ],
        "flaggedPhrases": [
            {
                "id": "m1",
                "timestampSec": 18,
                "timestampLabel": "00:18",
                "phrase": "nuanced perspective",
                "cefr": "C1",
                "partOfSpeech": "noun phrase",
                "meaning": "A viewpoint that accounts for subtle distinctions.",
                "contextSentence": "Mock timestamp — click to jump the embedded player to 00:18.",
            },
            {
                "id": "m2",
                "timestampSec": 64,
                "timestampLabel": "01:04",
                "phrase": "take into account",
                "cefr": "B2",
                "partOfSpeech": "idiomatic verb phrase",
                "meaning": "To consider a factor when making a judgment.",
                "contextSentence": "Mock timestamp — click to jump the embedded player to 01:04.",
            },
        ],
        "transcriptExcerpt": [
            {"text": "This is a "},
            {
                "text": "synthetic",
                "cefr": "B2",
                "pos": "adjective",
                "definition": "Generated as a demonstration placeholder.",
                "timestampSec": 10,
            },
            {"text": " transcript preview for video "},
            {"text": video_id},
            {"text": ". Once live analysis runs, "},
            {
                "text": "empirical",
                "cefr": "C1",
                "pos": "adjective",
                "definition": "Based on observed, measured data rather than theory.",
                "timestampSec": 32,
            },
            {"text": " CEFR token annotations will render interactively right here."},
        ],
    }


def build_mock_result(url: str, video_id: str) -> dict[str, Any]:
    """Return a full mock VideoAnalysisResult dict for the given video ID."""
    library = load_mock_library()
    template = dict(library.get(video_id) or deterministic_fallback(video_id))
    template.update({
        "id": f"{video_id}-{int(time.time() * 1000)}",
        "url": url,
        "analyzedAt": datetime.now(timezone.utc).isoformat(),
        "isMock": True,
    })
    return template
