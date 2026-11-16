"""
dataframe.py

Glues together transcript parser, CEFR file/text analyzer, and tabular data/DataFrame export.
"""

from typing import Any, Dict, List, Optional
from cefr_analyzer import Analyzer


def analyze_transcript(
    url: Optional[str] = None,
    text: Optional[str] = None,
    word_dict: Optional[Dict[str, List[Any]]] = None,
    analyzer: Optional[Analyzer] = None,
) -> Dict[str, Any]:
    """
    Get transcript from YouTube URL or provided text/word_dict and run CEFR analyzer.
    Returns the complete analysis report dictionary.
    """
    if analyzer is None:
        analyzer = Analyzer()

    if url:
        from transcript_parser import get_transcript

        word_dict, full_text = get_transcript(url)
        return analyzer.analyze(text=full_text, words=word_dict)

    if text is not None or word_dict is not None:
        return analyzer.analyze(text=text, words=word_dict)

    raise ValueError("Either 'url', 'text', or 'word_dict' must be provided.")


def build_word_rows(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Build structured tabular rows linking lexical matches/words with their
    CEFR level, lemma, time codes, and frequency/statistics.
    """
    rows: List[Dict[str, Any]] = []

    # If lexical matches with time codes exist, use them
    lexical_matches = report.get("lexical_matches", [])
    if lexical_matches:
        for match in lexical_matches:
            time_codes = match.get("time_codes", [])
            tc_val = time_codes[0] if len(time_codes) == 1 else (time_codes if time_codes else None)
            rows.append(
                {
                    "word": match.get("fragment"),
                    "lemma": match.get("lemma"),
                    "level": match.get("level"),
                    "time_code": tc_val,
                    "match": match.get("match"),
                    "ambiguous": match.get("ambiguous", False),
                }
            )
        return rows

    # Fallback to word_levels dictionary
    word_levels = report.get("word_levels", {})
    for word, level in word_levels.items():
        rows.append(
            {
                "word": word,
                "lemma": word,
                "level": level,
                "time_code": None,
                "match": "exact",
                "ambiguous": False,
            }
        )
    return rows


def build_df(report: Optional[Dict[str, Any]] = None, rows: Optional[List[Dict[str, Any]]] = None):
    """
    Convert analysis report rows into a pandas DataFrame (if pandas is installed),
    or return the structured rows.
    """
    if rows is None:
        if report is None:
            raise ValueError("Either 'report' or 'rows' must be provided.")
        rows = build_word_rows(report)

    try:
        import pandas as pd

        return pd.DataFrame(rows)
    except ImportError:
        return rows


def build_csv(
    report: Optional[Dict[str, Any]] = None,
    rows: Optional[List[Dict[str, Any]]] = None,
    filepath: Optional[str] = None,
) -> str:
    """
    Export rows to CSV format (works with or without pandas).
    """
    if rows is None:
        if report is None:
            raise ValueError("Either 'report' or 'rows' must be provided.")
        rows = build_word_rows(report)

    try:
        import pandas as pd

        df = pd.DataFrame(rows)
        if filepath:
            df.to_csv(filepath, index=False)
        return df.to_csv(index=False)
    except ImportError:
        import csv
        import io

        if not rows:
            return ""

        fieldnames = list(rows[0].keys())
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        content = output.getvalue()
        if filepath:
            with open(filepath, "w", encoding="utf-8", newline="") as f:
                f.write(content)
        return content


if __name__ == "__main__":
    from transcript_parser import make_word_dict

    sample_segments = [
        {"text": "She turned it down.", "start": 0.0, "end": 1.0},
        {"text": "We need to analyze this data.", "start": 1.2, "end": 3.0},
    ]
    w_dict = make_word_dict(sample_segments)
    txt = " ".join(w_dict["word"])

    rep = analyze_transcript(text=txt, word_dict=w_dict)
    print("Assessment:", rep.get("assessment"))
    print("Word levels:", rep.get("word_levels"))

    table = build_df(rep)
    print("\nTable preview (rows or df):")
    print(table)

    csv_data = build_csv(rep)
    print("\nCSV Output preview:")
    print(csv_data)
