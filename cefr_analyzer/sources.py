"""Explicit adapters for upstream schemas; no CEFR inference for unknown words."""

import csv
import gzip
import hashlib
import json
import re
import shutil
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

from .levels import LEVELS, lowest

OLP = "https://raw.githubusercontent.com/openlanguageprofiles/olp-en-cefrj/master/"
OPENJAM = "https://raw.githubusercontent.com/amirj4m/openjam/main/"
SOURCES = {
    "cefrj-vocabulary-profile-1.5.csv": OLP + "cefrj-vocabulary-profile-1.5.csv",
    "octanove-vocabulary-profile-c1c2-1.0.csv": OLP + "octanove-vocabulary-profile-c1c2-1.0.csv",
    "cefrj-grammar-profile-20180315.csv": OLP + "cefrj-grammar-profile-20180315.csv",
    "words_en.json": OPENJAM + "data/json/words_en.json",
    "word_forms.json": OPENJAM + "data/json/word_forms.json",
    "cefr_mega_dataset.csv": "https://raw.githubusercontent.com/kamronsaparbaev/cefr-dataset/main/cefr_mega_dataset.csv",
    "gse_vocabulary.json": "https://www.english.com/gse/teacher-toolkit/user/api/v1/vocabulary/search?page=0&size=50000",
}
GRAMMAR_COLUMNS = ("CEFR-J Level", "Core Inventory", "EGP", "GSELO")
GRAMMAR_ROWS = {
    "present": "59", "past": "65", "present_copular": "10", "past_copular": "64",
    "present_continuous": "61", "past_continuous": "66",
    "present_perfect": "62", "past_perfect": "67",
    "present_perfect_continuous": "63", "past_perfect_continuous": "68",
    "future": "69", "future_copular": "69", "future_continuous": "70",
    "future_perfect": "71", "future_perfect_copular": "71", "future_perfect_continuous": "72",
    "present_passive": "73", "present_continuous_passive": "74",
    "present_perfect_passive": "75", "past_passive": "76",
    "past_continuous_passive": "77", "past_perfect_passive": "78",
    "future_passive": "79", "future_continuous_passive": "80", "future_perfect_passive": "81",
    "modal": "123", "modal_copular": "123", "modal_continuous": "144",
    "modal_perfect": "145", "modal_perfect_copular": "145",
    "modal_passive": "82", "modal_perfect_passive": "84",
    "present_perfect_copular": "62", "past_perfect_copular": "67",
    "negative_inversion": "234", "third_conditional": "216",
    "modal_can": "123", "modal_could": "124", "modal_may": "129", "modal_might": "132",
    "modal_must": "135", "modal_should": "139", "modal_would": "142",
    "going_to": "122", "have_to": "127",
    "may_well": "131", "may_as_well": "130", "might_as_well": "133",
    "perfect_infinitive": "90",
}


def csv_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as stream:
        yield from csv.DictReader(stream)


def json_read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def normalize_term(term: str) -> str:
    return " ".join(term.lower().replace("’", "'").replace("_", " ").replace("-", " ").split())


def add(entries, term, level, source, automatic, pos=(), **metadata):
    term = normalize_term(term)
    if level not in LEVELS or not re.fullmatch(r"[a-z]+(?:[ '-][a-z]+)*", term):
        return
    entry = {"level": level, "source": source, "automatic": automatic, "pos": sorted(set(pos)), **metadata}
    if entry not in entries[term]:
        entries[term].append(entry)


def import_profile(path, entries, source):
    for row in csv_rows(path):
        # Slash-separated spelling alternatives, not a single word with slashes.
        for term in row["headword"].split("/"):
            add(entries, term, row["CEFR"], source, False, [row["pos"]])


def import_openjam(directory, entries, forms):
    words = json_read(directory / "words_en.json")
    ids = {}
    for word in words:
        ids[word["id"]] = normalize_term(word["english"])
        pos = [sense["part_of_speech"] for sense in word.get("senses", [])]
        add(entries, word["english"], word["level"], "openjam", True, pos)
    for form in json_read(directory / "word_forms.json"):
        lemma = ids.get(form["word_id"])
        if not lemma:
            raise ValueError(f"Unresolved OpenJam word_id: {form['word_id']}")
        record = {"lemma": lemma, "kind": form["form_type"], "source": "openjam"}
        key = normalize_term(form["form"])
        if record not in forms[key]:
            forms[key].append(record)


def import_mega(path, entries):
    for row in csv_rows(path):
        add(entries, row["Word"], row["CEFR"], "mega", True)


def import_gse(path, entries, phrases):
    payload = json_read(path)
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise ValueError("GSE response must contain a data array")
    if len(payload["data"]) < payload.get("count", 0):
        raise ValueError("Incomplete GSE response: download all pages before building")
    placeholders = {"sth", "sb", "somebody", "something", "someone"}
    for row in payload["data"]:
        # Use the CEFR supplied by Pearson, never guess a conversion from GSE.
        level = lowest([row.get("cefr", "")])
        pos = ["verb" if p == "phrasal verb" else p for p in row.get("grammaticalCategories", [])]
        term = normalize_term(row["expression"])
        add(entries, term, level, "gse", False, pos,
            original_level=row.get("cefr"), item_id=row["itemId"])
        parts = term.split()
        slots = [index for index, part in enumerate(parts) if part in placeholders]
        if len(slots) == 1 and 0 < slots[0] < len(parts) - 1 and level:
            parts[slots[0]] = "{object}"
            rule = {"term": term, "parts": parts, "level": level, "source": "gse",
                    "separable": False, "max_gap": 4}
            if rule not in phrases:
                phrases.append(rule)


def import_kaikki(path, forms):
    """Stream optional English Wiktextract JSONL; it supplies forms, never CEFR."""
    opener = gzip.open if str(path).endswith(".gz") else open
    tags = {"past": "past", "participle": "past_participle", "plural": "plural", "gerund": "gerund"}
    with opener(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            word = json.loads(line)
            if word.get("lang_code") != "en":
                continue
            lemma = normalize_term(word["word"])
            for form in word.get("forms", []):
                kind = "inflection"
                for tag, value in tags.items():
                    if tag in form.get("tags", []):
                        kind = value
                if "present" in form.get("tags", []) and "participle" in form.get("tags", []):
                    kind = "gerund"
                record = {"lemma": lemma, "kind": kind, "source": "kaikki"}
                key = normalize_term(form["form"])
                if record not in forms[key]:
                    forms[key].append(record)


def import_grammar(path):
    rows = {row["ID"]: row for row in csv_rows(path)}
    grammar = {}
    mapping = dict(GRAMMAR_ROWS)
    for name, row_id in GRAMMAR_ROWS.items():
        if row_id + "-1" in rows:
            mapping[name + "_negative"] = row_id + "-1"
    for name, row_id in mapping.items():
        row = rows[row_id]
        sources = []
        for column in GRAMMAR_COLUMNS:
            level = lowest([row[column]])
            if level:
                sources.append({"source": "cefrj_grammar", "row_id": row_id,
                                "column": column, "original_level": row[column], "level": level,
                                "code": row["Shorthand Code"], "url": SOURCES[path.name]})
        grammar[name] = {"level": lowest(s["level"] for s in sources), "sources": sources,
                         "automatic": False}
    return grammar


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if path.suffix == ".gz":
        # Stable artifact hash across builds, without embedding the current time.
        path.write_bytes(gzip.compress(content, mtime=0))
    else:
        path.write_bytes(content)


def fetch(directory: Path, names=None):
    directory.mkdir(parents=True, exist_ok=True)
    for name in names or SOURCES:
        request = urllib.request.Request(SOURCES[name], headers={"User-Agent": "transcript-cefr/0.1"})
        temporary = directory / (name + ".part")
        try:
            with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as target:
                shutil.copyfileobj(response, target)
            temporary.replace(directory / name)
        finally:
            temporary.unlink(missing_ok=True)


def build(directory: Path, output: Path, *, kaikki=None):
    entries, forms = defaultdict(list), defaultdict(list)
    import_profile(directory / "cefrj-vocabulary-profile-1.5.csv", entries, "cefrj")
    import_profile(directory / "octanove-vocabulary-profile-c1c2-1.0.csv", entries, "octanove")
    import_openjam(directory, entries, forms)
    import_mega(directory / "cefr_mega_dataset.csv", entries)
    phrases = json_read(Path(__file__).with_name("data") / "phrase_seeds.json")
    if (directory / "gse_vocabulary.json").exists():
        import_gse(directory / "gse_vocabulary.json", entries, phrases)
    if kaikki:
        import_kaikki(kaikki, forms)
    for phrase in phrases:
        if phrase["source"] != "gse":
            add(entries, phrase["term"], phrase["level"], phrase["source"], False, ["verb"], url=phrase["url"])
    grammar = import_grammar(directory / "cefrj-grammar-profile-20180315.csv")
    counts = defaultdict(Counter)
    for records in entries.values():
        for record in records:
            counts[record["source"]][record["level"]] += 1
    manifest = {"schema_version": 1, "sources": [], "terms": len(entries), "forms": len(forms),
                "entries_by_source_and_level": {key: dict(value) for key, value in counts.items()}}
    for filename, url in SOURCES.items():
        path = directory / filename
        if not path.exists():
            continue
        manifest["sources"].append({"file": filename, "url": url,
                                     "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                     "bytes": path.stat().st_size})
    if kaikki:
        manifest["kaikki"] = {"file": str(kaikki), "role": "morphology_only"}
    write_json(output / "lexicon.json.gz", entries)
    write_json(output / "forms.json.gz", forms)
    write_json(output / "grammar.json", grammar)
    write_json(output / "phrases.json", phrases)
    write_json(output / "manifest.json", manifest)
    return manifest
