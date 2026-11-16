"""Thin HTTP glue server connecting transcript_parser + cefr_analyzer + dataframe + db to the React frontend."""

from __future__ import annotations

import argparse
import json
import threading
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

import db
from cefr_analyzer import Analyzer
from dataframe import analyze_transcript, build_csv
from transcript_parser import (
    TranscriptLanguageError,
    TranscriptUnavailableError,
    get_transcript,
    get_video_id,
)

CEFR_LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")
LEVEL_RANK = {lvl: i + 1 for i, lvl in enumerate(CEFR_LEVELS)}
_ANALYZER = Analyzer()
_DB_LOCK = threading.Lock()


def _fmt_time(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _fetch_oembed(url: str, video_id: str) -> tuple[str, str]:
    try:
        endpoint = f"https://www.youtube.com/oembed?url={urllib.request.quote(url, safe='')}&format=json"
        with urllib.request.urlopen(endpoint, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("title") or f"YouTube Video ({video_id})", data.get("author_name") or "YouTube"
    except Exception:
        return f"YouTube Video ({video_id})", "YouTube"


def _build_timeline(matches: list[dict[str, Any]], max_sec: float, fallback_level: str) -> list[dict[str, Any]]:
    if max_sec <= 0 or not matches:
        return []
    buckets = min(6, max(1, int(max_sec // 60) or 1))
    step = max(1.0, max_sec / buckets)
    grouped: list[list[dict[str, Any]]] = [[] for _ in range(buckets)]
    for m in matches:
        tcs = m.get("time_codes") or []
        if tcs and isinstance(tcs[0], (int, float)):
            idx = min(buckets - 1, max(0, int(tcs[0] / step)))
            grouped[idx].append(m)

    segments = []
    for i, items in enumerate(grouped):
        start_s = int(round(i * step))
        end_s = int(round((i + 1) * step)) if i + 1 < buckets else int(round(max_sec))
        ranks = [LEVEL_RANK[x["level"]] for x in items if x.get("level") in LEVEL_RANK]
        avg_rank = round(sum(ranks) / len(ranks)) if ranks else LEVEL_RANK.get(fallback_level, 3)
        lvl = CEFR_LEVELS[min(5, max(0, avg_rank - 1))]
        wpm = round(len(items) / max(1 / 60, (end_s - start_s) / 60))
        segments.append({
            "id": f"seg-{i+1}",
            "startSec": start_s,
            "endSec": end_s,
            "startLabel": _fmt_time(start_s),
            "endLabel": _fmt_time(end_s),
            "level": lvl,
            "wpm": wpm,
            "intensity": min(100, max(15, round((avg_rank / 6) * 100))),
            "note": f"{len(items)} analyzed units",
        })
    return segments


def _build_transcript_excerpt(lexical: list[dict[str, Any]], full_text: str | None, limit: int = 1200) -> list[dict[str, Any]]:
    if not full_text:
        tokens = []
        for m in lexical[:80]:
            ts = next((t for t in (m.get("time_codes") or []) if isinstance(t, (int, float))), None)
            tokens.append({
                "text": (m.get("fragment") or "") + " ",
                "cefr": m.get("level"),
                "pos": m.get("match"),
                "definition": f"Lemma: {m.get('lemma', '')}" if m.get("lemma") else None,
                "timestampSec": round(ts) if ts is not None else None,
            })
        return tokens

    snippet = full_text[:limit]
    if len(full_text) > limit:
        cut = snippet.rfind(" ")
        if cut > limit // 2:
            snippet = snippet[:cut] + "..."

    tokens: list[dict[str, Any]] = []
    cursor = 0
    for m in sorted(lexical, key=lambda x: x.get("char_start", 0)):
        start = m.get("char_start")
        end = m.get("char_end")
        if not isinstance(start, int) or not isinstance(end, int):
            continue
        if start < cursor or start >= len(snippet):
            continue
        end = min(end, len(snippet))
        if start > cursor:
            tokens.append({"text": snippet[cursor:start]})
        ts = next((t for t in (m.get("time_codes") or []) if isinstance(t, (int, float))), None)
        tokens.append({
            "text": snippet[start:end],
            "cefr": m.get("level"),
            "pos": m.get("match"),
            "definition": f"Lemma: {m.get('lemma', '')}" if m.get("lemma") else None,
            "timestampSec": round(ts) if ts is not None else None,
        })
        cursor = end

    if cursor < len(snippet):
        tokens.append({"text": snippet[cursor:]})
    return tokens


def to_frontend_result(
    url: str,
    video_id: str,
    report: dict[str, Any],
    full_text: str | None = None,
    fetch_meta: bool = True,
) -> dict[str, Any]:
    """Map cefr_analyzer v1.0 output dict to the frontend VideoAnalysisResult shape."""
    assessment = report.get("assessment") or {}
    stats = report.get("statistics") or {}
    lexical = report.get("lexical_matches") or []
    grammar = report.get("grammar_matches") or []

    level = assessment.get("level") or "B1"
    conf_label = assessment.get("confidence", "low")
    confidence = 78 if conf_label == "medium" else 58

    lex_dist = stats.get("lexical_distribution") or {}
    total_lex = sum(lex_dist.get(lvl, 0) for lvl in CEFR_LEVELS)
    if total_lex > 0:
        vocab_dist = [
            {"level": lvl, "percentage": round(lex_dist.get(lvl, 0) * 100 / total_lex)}
            for lvl in CEFR_LEVELS
        ]
        diff = 100 - sum(x["percentage"] for x in vocab_dist)
        if diff != 0:
            top_item = max(vocab_dist, key=lambda x: x["percentage"])
            top_item["percentage"] = max(0, top_item["percentage"] + diff)
    else:
        vocab_dist = [{"level": lvl, "percentage": 0} for lvl in CEFR_LEVELS]

    all_tcs = [tc for m in lexical for tc in (m.get("time_codes") or []) if isinstance(tc, (int, float))]
    max_sec = max(all_tcs) if all_tcs else 0.0
    tokens = stats.get("tokens", 0)
    wpm = round(tokens / (max_sec / 60)) if max_sec > 0 else 0
    coverage_pct = round((stats.get("coverage", 0) or 0) * 100)
    lex_score = assessment.get("lexical_score") or 3.0
    gram_score = assessment.get("grammar_score") or 3.0

    metrics = [
        {
            "id": "speechRate",
            "label": "Speech Rate",
            "value": f"{wpm} WPM" if wpm else f"{tokens} words",
            "score": min(100, round((wpm / 200) * 100)) if wpm else 60,
            "detail": f"{tokens} tokens across {stats.get('sentences', 0)} sentences.",
            "badge": "Brisk" if wpm > 155 else "Moderate",
        },
        {
            "id": "vocabulary",
            "label": "Vocabulary Difficulty",
            "value": f"{coverage_pct}% Matched",
            "score": min(100, round((lex_score / 6) * 100)),
            "detail": f"Lexical score {lex_score:.2f}/6.0 ({assessment.get('eligible_lexical_units', 0)} units).",
            "badge": level,
        },
        {
            "id": "grammar",
            "label": "Grammar Complexity",
            "value": f"{len(grammar)} Patterns",
            "score": min(100, round((gram_score / 6) * 100)),
            "detail": f"Grammar score {gram_score:.2f}/6.0 across {len(grammar)} matches.",
            "badge": f"{len(grammar)} hits",
        },
        {
            "id": "clarity",
            "label": "Lexicon Coverage",
            "value": f"{coverage_pct}%",
            "score": coverage_pct,
            "detail": f"Confidence: {conf_label}.",
            "badge": conf_label.title(),
        },
    ]

    gram_groups: Counter[tuple[str, str]] = Counter()
    gram_examples: dict[tuple[str, str], str] = {}
    for g in grammar:
        key = (g.get("rule", "pattern"), g.get("level") or level)
        gram_groups[key] += 1
        gram_examples.setdefault(key, g.get("fragment", ""))

    grammar_patterns = [
        {
            "id": f"g-{i+1}",
            "pattern": rule.replace("_", " ").title(),
            "cefr": g_lvl,
            "occurrences": count,
            "explanation": f"Detected {count} occurrence(s) of {rule.replace('_', ' ')}.",
            "example": gram_examples[(rule, g_lvl)],
        }
        for i, ((rule, g_lvl), count) in enumerate(gram_groups.most_common(6))
    ]

    seen_phrases: set[str] = set()
    flagged_phrases = []
    for m in sorted(lexical, key=lambda x: LEVEL_RANK.get(x.get("level", "A1"), 1), reverse=True):
        frag = (m.get("fragment") or "").strip()
        lvl = m.get("level")
        if lvl not in ("B2", "C1", "C2") or not frag or frag.lower() in seen_phrases:
            continue
        seen_phrases.add(frag.lower())
        ts = next((t for t in (m.get("time_codes") or []) if isinstance(t, (int, float))), 0.0)
        flagged_phrases.append({
            "id": f"fp-{len(flagged_phrases)+1}",
            "timestampSec": round(ts),
            "timestampLabel": _fmt_time(ts),
            "phrase": frag,
            "cefr": lvl,
            "partOfSpeech": m.get("match", "lexical"),
            "meaning": f"Lemma: {m.get('lemma', frag)} (CEFR {lvl}).",
            "contextSentence": f"Appears at {_fmt_time(ts)} in transcript.",
        })
        if len(flagged_phrases) >= 10:
            break

    title, channel = _fetch_oembed(url, video_id) if fetch_meta else (f"YouTube Video ({video_id})", "YouTube")

    return {
        "id": f"{video_id}-{int(datetime.now(timezone.utc).timestamp())}",
        "videoId": video_id,
        "url": url,
        "title": title,
        "channel": channel,
        "durationLabel": _fmt_time(max_sec) if max_sec else "00:00",
        "thumbnailUrl": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
        "detectedLevel": level,
        "confidence": confidence,
        "summary": (
            f"Estimated {level} CEFR level (lexical {lex_score:.2f}/6, grammar {gram_score:.2f}/6, "
            f"{coverage_pct}% lexicon coverage across {tokens} tokens)."
        ),
        "learnerFit": f"Best suited for {level} learners based on vocabulary and grammar distribution.",
        "analyzedAt": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "vocabDistribution": vocab_dist,
        "timeline": _build_timeline(lexical, max_sec, level),
        "grammarPatterns": grammar_patterns,
        "flaggedPhrases": flagged_phrases,
        "transcriptExcerpt": _build_transcript_excerpt(lexical, full_text),
        "isMock": False,
    }


def _analyze_url(url: str) -> tuple[str, dict[str, Any], str]:
    video_id = get_video_id(url)
    word_dict, full_text = get_transcript(url)
    report = _ANALYZER.analyze(text=full_text, words=word_dict)
    return video_id, report, full_text


class LexisTubeHandler(BaseHTTPRequestHandler):
    """JSON REST handler exposing /api/health, /api/analyze, and /api/export."""

    server_version = "LexisTubePython/1.0"

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path == "/api/health":
            self._send_json(HTTPStatus.OK, {"status": "ok", "service": "lexistube-backend"})
            return

        if path == "/api/export":
            url = parse_qs(parsed.query).get("url", [""])[0]
            if not url.strip():
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Missing required 'url' query parameter."})
                return
            try:
                video_id = get_video_id(url)
                report = analyze_transcript(url=url, analyzer=_ANALYZER)
                csv_bytes = build_csv(report).encode("utf-8")
            except ValueError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            except (TranscriptUnavailableError, TranscriptLanguageError) as exc:
                self._send_json(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": str(exc)})
                return
            except Exception as exc:  # pragma: no cover
                self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"Export failed: {exc}"})
                return

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="cefr-{video_id}.csv"')
            self.send_header("Content-Length", str(len(csv_bytes)))
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(csv_bytes)
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/api/analyze":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid Content-Length header"})
            return

        raw_body = self.rfile.read(content_length) if content_length > 0 else b""
        try:
            data = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Request body must be valid JSON."})
            return

        url = data.get("url") if isinstance(data, dict) else None
        if not isinstance(url, str) or not url.strip():
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Missing required 'url' field."})
            return

        try:
            video_id, report, full_text = _analyze_url(url)
            result = to_frontend_result(url, video_id, report, full_text=full_text)
            with _DB_LOCK:
                db.save_data(0, {**result, "assessment": result["detectedLevel"]})
        except ValueError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        except (TranscriptUnavailableError, TranscriptLanguageError) as exc:
            self._send_json(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": str(exc)})
            return
        except Exception as exc:  # pragma: no cover
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"Analysis failed: {exc}"})
            return

        self._send_json(HTTPStatus.OK, result)

    def log_message(self, format: str, *args: Any) -> None:
        return


def create_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    """Create a configured ThreadingHTTPServer instance."""
    return ThreadingHTTPServer((host, port), LexisTubeHandler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the LexisTube glue HTTP server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    server = create_server(host=args.host, port=args.port)
    print(f"LexisTube glue backend listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
