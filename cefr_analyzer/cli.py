"""Debug CLI, dataset preparation and a reproducible calibration report."""

import argparse
import csv
import json
import sys
from pathlib import Path

from .analyzer import Analyzer
from .calibration import evaluate
from .lexicon import DATA
from .scoring import ScoringConfig
from .sources import build, fetch


def parser():
    root = argparse.ArgumentParser(description="Approximate English transcript CEFR")
    commands = root.add_subparsers(dest="command", required=True)
    run = commands.add_parser("analyze")
    inputs = run.add_mutually_exclusive_group()
    inputs.add_argument("--text")
    inputs.add_argument("--file", type=Path)
    run.add_argument("--words", type=Path, help="CSV or JSON records: word,time_code")
    run.add_argument("--ignore", action="append", default=[], help="Explicit name/brand; repeatable")
    run.add_argument("--include-automatic", action="store_true")
    run.add_argument("--json", action="store_true", help="Print full JSON instead of brief summary")
    run.add_argument("--output", type=Path)
    run.add_argument("--data-dir", type=Path, default=DATA)
    prepare = commands.add_parser("prepare-data")
    prepare.add_argument("--raw-dir", type=Path, default=Path("words_data"))
    prepare.add_argument("--output-dir", type=Path, default=DATA)
    prepare.add_argument("--download", action="store_true", help="Explicit network access to listed sources")
    prepare.add_argument("--kaikki", type=Path, help="Optional local English Wiktextract .jsonl[.gz]")
    export = commands.add_parser("export-dictionaries")
    export.add_argument("--output-dir", type=Path, required=True)
    export.add_argument("--data-dir", type=Path, default=DATA)
    calibration = commands.add_parser("calibrate")
    calibration.add_argument("--directory", type=Path, default=Path("calibration_data"))
    calibration.add_argument("--output", type=Path)
    calibration.add_argument("--data-dir", type=Path, default=DATA)
    return root


def load_words(path):
    if not path:
        return None
    with path.open(encoding="utf-8-sig", newline="") as stream:
        if path.suffix.lower() == ".csv":
            return list(csv.DictReader(stream))
        return json.load(stream)


def run_analysis(args):
    text = args.text
    if args.file:
        text = args.file.read_text(encoding="utf-8-sig")
    if text is None and not args.words:
        text = sys.stdin.read()
    config = ScoringConfig(include_automatic=args.include_automatic)
    result = Analyzer(args.data_dir, config).analyze(text, load_words(args.words), ignore_terms=args.ignore)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    if args.json:
        print(payload)
        return
    assessment, stats = result["assessment"], result["statistics"]
    print(f"CEFR ~ {assessment['level'] or 'insufficient evidence'} | confidence: {assessment['confidence']}")
    print(f"Words: {stats['analyzed_tokens']} | coverage: {stats['coverage']:.1%} | automatic units: {len(result['automatic_matches'])}")
    print(f"Lexical: {assessment['lexical_score']:.2f} | grammar: {assessment['grammar_score']:.2f}")
    print("Unknown: " + (", ".join(item["word"] for item in result["unknown_words"][:20]) or "none"))
    for warning in result["warnings"]:
        print("Note: " + warning)


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "analyze":
            run_analysis(args)
        elif args.command == "prepare-data":
            if args.download:
                fetch(args.raw_dir)
            print(json.dumps(build(args.raw_dir, args.output_dir, kaikki=args.kaikki), indent=2))
        elif args.command == "export-dictionaries":
            print(json.dumps(Analyzer(args.data_dir).lexicon.export(args.output_dir), indent=2))
        else:
            print(json.dumps(evaluate(Analyzer(args.data_dir), args.directory, args.output), indent=2))
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    return 0
