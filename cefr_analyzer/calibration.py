"""Evaluate approximate labels, without fitting rules to individual transcripts."""

import re
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from .levels import number


def evaluate(analyzer, directory: Path, output: Path | None = None) -> dict:
    samples = []
    for path in sorted(directory.glob("*.txt")):
        label = re.search(r"_(A1|A2|B1|B2|C1|C2)$", path.stem)
        if not label:
            continue
        content = path.read_bytes()
        result = analyzer.analyze(content.decode("utf-8-sig"))
        actual = result["assessment"]["level"]
        expected = label.group(1)
        error = abs(number(actual) - number(expected)) if actual else None
        samples.append({"file": path.name, "approximate_label": expected, "prediction": actual,
                        "sha256": hashlib.sha256(content).hexdigest(),
                        "absolute_band_error": error, "coverage": result["statistics"]["coverage"],
                        "tokens": result["statistics"]["tokens"],
                        "lexical_score": result["assessment"]["lexical_score"],
                        "grammar_score": result["assessment"]["grammar_score"]})
    errors = [sample["absolute_band_error"] for sample in samples if sample["absolute_band_error"] is not None]
    report = {"samples": samples, "evaluated": len(errors),
              "scoring_config": asdict(analyzer.config),
              "dictionary_terms": len(analyzer.lexicon.entries),
              "mean_absolute_band_error": round(sum(errors) / len(errors), 3) if errors else None,
              "within_one_band": sum(error <= 1 for error in errors) / len(errors) if errors else None,
              "note": "Approximate labels, small calibration set, no held-out validation; not an accuracy guarantee."}
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
