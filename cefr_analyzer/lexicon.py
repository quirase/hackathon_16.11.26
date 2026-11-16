"""Dictionary storage and provenance. Conflicts always resolve downwards."""

import gzip
import json
from collections import defaultdict
from pathlib import Path

from .levels import LEVELS, lowest

DATA = Path(__file__).with_name("data")


def read_json(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


class Lexicon:
    def __init__(self, data_dir: Path | str = DATA):
        self.data_dir = Path(data_dir)
        self.entries = read_json(self.data_dir / "lexicon.json.gz")
        self.forms = read_json(self.data_dir / "forms.json.gz")
        self.phrase_rules = read_json(self.data_dir / "phrases.json")
        self.grammar_rules = read_json(self.data_dir / "grammar.json")
        self.manifest = read_json(self.data_dir / "manifest.json")
        self.phrase_index = defaultdict(list)
        for term in self.entries:
            if " " in term:
                self.phrase_index[term.split()[0]].append(term)

    def evidence(self, term: str) -> dict | None:
        entries = self.entries.get(term)
        if not entries:
            return None
        level = lowest(entry["level"] for entry in entries)
        selected = [entry for entry in entries if entry["level"] == level]
        automatic = all(entry["automatic"] for entry in selected)
        return {"lemma": term, "level": level, "automatic": automatic,
                "level_conflict": len({entry["level"] for entry in entries}) > 1,
                "sources": entries}

    def has_pos(self, lemma: str, pos: str) -> bool:
        for entry in self.entries.get(lemma, []):
            if pos in entry.get("pos", []):
                return True
        return False

    def export(self, output_dir: Path):
        """Separate material by source, then CEFR, retaining automatic flags."""
        groups = defaultdict(list)
        for term, entries in sorted(self.entries.items()):
            for entry in entries:
                groups[(entry["source"], entry["level"])].append({"term": term, **entry,
                    "kind": "expression" if " " in term else "word"})
        for (source, level), entries in groups.items():
            folder = output_dir / source
            folder.mkdir(parents=True, exist_ok=True)
            (folder / f"{level}.json").write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
        return {level: sum(1 for term in self.entries if self.evidence(term)["level"] == level)
                for level in LEVELS}
