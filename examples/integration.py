"""Run with: python -m examples.integration (from repository root)."""

from cefr_analyzer import Analyzer


def main():
    rows = [
        {"word": "She", "time_code": {"start": 0.0, "end": 0.2}},
        {"word": "turned", "time_code": {"start": 0.2, "end": 0.5}},
        {"word": "it", "time_code": {"start": 0.5, "end": 0.6}},
        {"word": "down.", "time_code": {"start": 0.6, "end": 0.9}},
    ]
    analyzer = Analyzer()
    report = analyzer.analyze("She turned it down.", words=rows, ignore_terms=["John"])
    print(report["assessment"])
    for match in report["lexical_matches"]:
        print(match["fragment"], match["level"], match["time_codes"])


if __name__ == "__main__":
    main()
