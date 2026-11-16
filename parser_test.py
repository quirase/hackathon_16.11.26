"""Manual smoke test: python parser_test.py YOUTUBE_URL (requires .[parser])."""

import argparse

from cefr_analyzer import Analyzer
from transcript_parser import get_transcript


def main():
    arguments = argparse.ArgumentParser()
    arguments.add_argument("url")
    args = arguments.parse_args()
    words, text = get_transcript(args.url)
    report = Analyzer().analyze(text=text, words=words)
    print(text)
    print("Words:", len(words["word"]))
    print("Approximate CEFR:", report["assessment"]["level"])


if __name__ == "__main__":
    main()
