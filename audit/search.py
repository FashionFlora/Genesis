#!/usr/bin/env python3
"""Find similar algorithm records using deterministic TF-IDF cosine similarity.

Uses only the Python standard library. By default, searches every area file in
registry/areas/ (the current catalog layout), falling back to
registry/algorithms.jsonl if no area files exist. Example:
  python3 audit/search.py "local Hebbian prediction error" --top 10
"""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AREA_DIR = ROOT / "registry" / "areas"
MASTER_REGISTRY = ROOT / "registry" / "algorithms.jsonl"
TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)


def tokens(text: str) -> list[str]:
    return [t.casefold() for t in TOKEN_RE.findall(text)]


def document(record: dict) -> str:
    """Weight the mechanism fields by repeating them, not names/metadata."""
    principle = str(record.get("principle") or "")
    rule = str(record.get("learning_rule") or "")
    signals = " ".join(map(str, record.get("learning_signals") or []))
    return " ".join([principle, principle, rule, rule, signals])


def registry_paths(explicit: Path | None) -> list[Path]:
    if explicit is not None:
        return [explicit]
    area_files = sorted(AREA_DIR.glob("*.jsonl"))
    if area_files:
        return area_files
    return [MASTER_REGISTRY]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="candidate description")
    parser.add_argument("--top", type=int, default=10, help="maximum results (default: 10)")
    parser.add_argument("--registry", type=Path,
                        help="one JSONL registry file (default: all registry/areas/*.jsonl;")
    args = parser.parse_args()
    if args.top < 0:
        parser.error("--top must be non-negative")
    records = []
    paths = registry_paths(args.registry)
    for path in paths:
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as stream:
            for line_no, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    parser.error(f"{args.registry}:{line_no}: invalid JSON: {exc}")
                if isinstance(record, dict):
                    record["_registry_file"] = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
                    records.append(record)
    query_terms = tokens(args.query)
    docs = [tokens(document(record)) for record in records]
    if not records:
        print("No registry records found.")
        return 0
    vocabulary = set(query_terms)
    for doc in docs:
        vocabulary.update(doc)
    n = len(docs) + 1  # include query in IDF corpus
    df = Counter()
    for doc in docs:
        df.update(set(doc))
    idf = {term: math.log((n + 1) / (df[term] + 1)) + 1.0 for term in vocabulary}

    def vector(items: list[str]) -> dict[str, float]:
        counts = Counter(items)
        return {term: (1 + math.log(count)) * idf[term] for term, count in counts.items()}

    qvec = vector(query_terms)
    qnorm = math.sqrt(sum(value * value for value in qvec.values()))
    ranked = []
    for record, items in zip(records, docs):
        vec = vector(items)
        norm = math.sqrt(sum(value * value for value in vec.values()))
        dot = sum(value * vec.get(term, 0.0) for term, value in qvec.items())
        score = dot / (qnorm * norm) if qnorm and norm else 0.0
        ranked.append((score, str(record.get("id", "")), record))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    for score, _, record in ranked[:args.top]:
        print(json.dumps({"score": round(score, 6), "id": record.get("id"),
                          "name": record.get("name"), "area": record.get("area"),
                          "registry_file": record.get("_registry_file"),
                          "principle": record.get("principle"),
                          "learning_rule": record.get("learning_rule"),
                          "sources": record.get("sources", [])},
                         ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
