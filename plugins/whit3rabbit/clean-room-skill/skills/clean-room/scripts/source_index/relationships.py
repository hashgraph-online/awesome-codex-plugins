"""Import resolution and source-index grouping."""

from __future__ import annotations

import re
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from source_index.metrics import language_counts, metric_sum
from source_index.scanners import RESOLVE_EXTENSIONS


def normalized_relative(path: Path) -> str:
    return path.as_posix()


def add_path_aliases(path_map: dict[str, str], root_id: str, relative_path: Path, file_id: str) -> None:
    rel = normalized_relative(relative_path)
    key = f"{root_id}:{rel}"
    path_map[key] = file_id
    suffix = relative_path.suffix
    if suffix:
        path_map[f"{root_id}:{normalized_relative(relative_path.with_suffix(''))}"] = file_id
    if relative_path.name in {
        "__init__.py",
        "index.js",
        "index.jsx",
        "index.ts",
        "index.tsx",
        "index.mjs",
        "index.cjs",
        "mod.rs",
    }:
        path_map[f"{root_id}:{normalized_relative(relative_path.parent)}"] = file_id


def resolve_candidate(path_map: dict[str, str], root_id: str, candidate: Path) -> str | None:
    candidates = [candidate]
    if not candidate.suffix:
        candidates.extend(candidate.with_suffix(ext) for ext in RESOLVE_EXTENSIONS)
        candidates.extend(candidate / f"index{ext}" for ext in RESOLVE_EXTENSIONS if ext != ".pyi")
        candidates.append(candidate / "__init__.py")
    for item in candidates:
        key = f"{root_id}:{normalized_relative(item)}"
        if key in path_map:
            return path_map[key]
    return None


def resolve_import(
    path_map: dict[str, str],
    file_record: dict[str, Any],
    import_record: dict[str, Any],
) -> str | None:
    root_id = file_record["root_id"]
    path = Path(file_record["path"])
    specifier = import_record["specifier"]
    kind = import_record["kind"]
    if kind == "python-from-import" and specifier.startswith("."):
        dot_count = len(specifier) - len(specifier.lstrip("."))
        module = specifier[dot_count:]
        base = path.parent
        for _ in range(max(dot_count - 1, 0)):
            base = base.parent
        if not module:
            return resolve_candidate(path_map, root_id, base)
        candidate = base / Path(module.replace(".", "/")) if module else base
        return resolve_candidate(path_map, root_id, candidate)
    if kind == "python-import" and not specifier.startswith("."):
        candidate = Path(specifier.replace(".", "/"))
        return resolve_candidate(path_map, root_id, candidate)
    if specifier.startswith("."):
        return resolve_candidate(path_map, root_id, path.parent / specifier)
    if kind == "rust-mod":
        return resolve_candidate(path_map, root_id, path.parent / specifier)
    if kind == "rust-use":
        cleaned = re.sub(r"[{}*]", "", specifier)
        first = cleaned.split("::", 1)[0]
        if first in {"crate", "self"}:
            remainder = cleaned.split("::", 1)[1] if "::" in cleaned else ""
            base = Path("") if first == "crate" else path.parent
            if remainder:
                return resolve_candidate(path_map, root_id, base / Path(remainder.replace("::", "/")))
        if first == "super":
            remainder = cleaned.split("::", 1)[1] if "::" in cleaned else ""
            base = path.parent.parent
            if remainder:
                return resolve_candidate(path_map, root_id, base / Path(remainder.replace("::", "/")))
    if kind.endswith("-include") and import_record.get("is_relative"):
        return resolve_candidate(path_map, root_id, path.parent / specifier)
    if kind in {"java-import", "kotlin-import", "csharp-using"}:
        return resolve_candidate(path_map, root_id, Path(specifier.rstrip(".*").replace(".", "/")))
    if kind in {"go-import", "swift-import"}:
        return resolve_candidate(path_map, root_id, Path(specifier.replace(".", "/")))
    return None


def resolve_relationships(files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    path_map: dict[str, str] = {}
    for file_record in files:
        add_path_aliases(path_map, file_record["root_id"], Path(file_record["path"]), file_record["file_id"])

    relationships: list[dict[str, Any]] = []
    for file_record in files:
        for import_record in file_record["imports"]:
            resolved = resolve_import(path_map, file_record, import_record)
            import_record["resolved_file_id"] = resolved
            relationships.append(
                {
                    "from_file_id": file_record["file_id"],
                    "to_file_id": resolved,
                    "specifier": import_record["specifier"],
                    "kind": import_record["kind"],
                }
            )
    return relationships


def build_groups(files: list[dict[str, Any]], relationships: list[dict[str, Any]]) -> list[dict[str, Any]]:
    file_ids = [file_record["file_id"] for file_record in files]
    adjacency: dict[str, set[str]] = {file_id: set() for file_id in file_ids}
    related: set[str] = set()
    for relationship in relationships:
        to_file_id = relationship.get("to_file_id")
        if isinstance(to_file_id, str) and to_file_id in adjacency:
            from_file_id = relationship["from_file_id"]
            adjacency[from_file_id].add(to_file_id)
            adjacency[to_file_id].add(from_file_id)
            related.add(from_file_id)
            related.add(to_file_id)

    visited: set[str] = set()
    raw_groups: list[tuple[str, list[str], str]] = []
    for file_id in file_ids:
        if file_id in visited or file_id not in related:
            continue
        queue: deque[str] = deque([file_id])
        visited.add(file_id)
        component: list[str] = []
        while queue:
            current = queue.popleft()
            component.append(current)
            for neighbor in sorted(adjacency[current]):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        raw_groups.append(("dependency-component", sorted(component), "Files connected by resolved local imports."))

    by_directory: dict[str, list[str]] = defaultdict(list)
    file_by_id = {file_record["file_id"]: file_record for file_record in files}
    for file_id in file_ids:
        if file_id in visited:
            continue
        directory = str(Path(file_by_id[file_id]["path"]).parent)
        by_directory[directory].append(file_id)
    for directory in sorted(by_directory):
        raw_groups.append(
            (
                "directory-cluster",
                sorted(by_directory[directory]),
                f"Files grouped by directory fallback: {directory}.",
            )
        )

    groups: list[dict[str, Any]] = []
    for index, (reason, group_file_ids, note) in enumerate(raw_groups, start=1):
        group_file_id_set = set(group_file_ids)
        groups.append(
            {
                "group_id": f"group-{index:04d}",
                "reason": reason,
                "file_ids": group_file_ids,
                "metrics": metric_sum(files, group_file_ids),
                "language_counts": language_counts(files, group_file_ids),
                "relationship_count": sum(
                    1
                    for relationship in relationships
                    if relationship["from_file_id"] in group_file_id_set
                    and relationship.get("to_file_id") in group_file_id_set
                ),
                "notes": note,
            }
        )
    return groups
