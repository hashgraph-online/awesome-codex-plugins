#!/usr/bin/env python3
"""Build or query an optional local, rebuildable Project Memory similarity index."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path


WORD = re.compile(r"[a-z0-9][a-z0-9_-]{2,}")


def features(text: str) -> Counter[str]:
    words = WORD.findall(text.casefold())
    result: Counter[str] = Counter(f"w:{word}" for word in words)
    for word in words:
        padded = f"^{word}$"
        result.update(f"c:{padded[index:index + 3]}" for index in range(max(0, len(padded) - 2)))
    result.update(f"b:{left}_{right}" for left, right in zip(words, words[1:]))
    return result


def build(vault: Path) -> dict[str, object]:
    documents: list[tuple[str, Counter[str]]] = []
    for path in sorted(vault.rglob("*.md")):
        if any(part.casefold() in {".obsidian", "inbox"} for part in path.parts):
            continue
        documents.append((path.relative_to(vault).as_posix(), features(path.read_text(encoding="utf-8", errors="replace"))))
    document_frequency = Counter(feature for _, vector in documents for feature in vector)
    total = max(1, len(documents))
    weights: dict[str, float] = {feature: math.log((1 + total) / (1 + count)) + 1 for feature, count in document_frequency.items()}
    encoded = []
    for path, vector in documents:
        weighted = {feature: round(count * weights[feature], 6) for feature, count in vector.items()}
        norm = math.sqrt(sum(value * value for value in weighted.values())) or 1
        encoded.append({"file": path, "vector": weighted, "norm": round(norm, 6)})
    return {"version": 1, "documents": encoded, "idf": weights, "note": "Derived local index; safe to delete and rebuild."}


def search(index: dict[str, object], query: str, limit: int) -> list[dict[str, object]]:
    idf = index.get("idf", {})
    query_vector = {feature: count * float(idf.get(feature, 1.0)) for feature, count in features(query).items()}
    query_norm = math.sqrt(sum(value * value for value in query_vector.values())) or 1
    results = []
    for document in index.get("documents", []):
        vector = document["vector"]
        overlap = sorted(set(query_vector) & set(vector), key=lambda feature: query_vector[feature] * vector[feature], reverse=True)
        score = sum(query_vector[feature] * vector[feature] for feature in overlap) / (query_norm * float(document["norm"]))
        if score <= 0:
            continue
        reasons = [feature[2:].replace("_", " ") for feature in overlap if feature.startswith(("w:", "b:"))][:5]
        results.append({"file": document["file"], "score": round(score, 4), "matched_features": reasons})
    return sorted(results, key=lambda item: (-item["score"], item["file"].casefold()))[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("vault", type=Path)
    build_parser.add_argument("index", type=Path)
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("index", type=Path)
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    if args.command == "build":
        data = build(args.vault.resolve())
        args.index.parent.mkdir(parents=True, exist_ok=True)
        args.index.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
        print(json.dumps({"index": str(args.index), "documents": len(data["documents"])}, indent=2))
    else:
        data = json.loads(args.index.read_text(encoding="utf-8"))
        print(json.dumps({"query": args.query, "results": search(data, args.query, args.limit), "interpretation": "Similarity is a retrieval aid; inspect each note before relying on it."}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
