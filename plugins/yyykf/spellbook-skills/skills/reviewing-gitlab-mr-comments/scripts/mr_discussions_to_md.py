#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path


def _normalize_position(position):
    if not position:
        return None
    file_path = position.get("new_path") or position.get("old_path")
    if not file_path:
        return None

    line_range = position.get("line_range") or {}
    start = line_range.get("start") or {}
    end = line_range.get("end") or {}
    start_line = start.get("new_line") or start.get("old_line")
    end_line = end.get("new_line") or end.get("old_line")
    range_type = start.get("type") or end.get("type")

    if start_line is None:
        start_line = position.get("new_line") or position.get("old_line")
        end_line = start_line
        if position.get("new_line") is not None:
            range_type = range_type or "new"
        elif position.get("old_line") is not None:
            range_type = range_type or "old"

    if start_line is None:
        return None

    return {
        "file_path": file_path,
        "start_line": start_line,
        "end_line": end_line if end_line is not None else start_line,
        "range_type": range_type,
    }


def _detect_language(file_path):
    ext = Path(file_path).suffix.lower()
    mapping = {
        ".java": "java",
        ".py": "python",
        ".js": "javascript",
        ".ts": "ts",
        ".tsx": "tsx",
        ".jsx": "jsx",
        ".json": "json",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".xml": "xml",
        ".md": "md",
        ".sql": "sql",
        ".sh": "bash",
    }
    return mapping.get(ext, "")


def _render_snippet(repo_root, file_path, start_line, end_line, context):
    abs_path = Path(repo_root) / file_path
    if not abs_path.exists():
        return None, f"file not found: {file_path}"
    lines = abs_path.read_text(encoding="utf-8", errors="replace").splitlines()
    total = len(lines)
    start = max(1, start_line - context)
    end = min(total, end_line + context)
    width = len(str(end))
    snippet = []
    for idx in range(start, end + 1):
        text = lines[idx - 1]
        snippet.append(f"{str(idx).rjust(width)} | {text}")
    return "\n".join(snippet), None


def main():
    parser = argparse.ArgumentParser(description="Format GitLab MR discussions as Markdown")
    parser.add_argument("--repo-root", default=os.getcwd(), help="Repository root used to read files")
    parser.add_argument("--context", type=int, default=3, help="Context lines around the range")
    snippet_group = parser.add_mutually_exclusive_group()
    snippet_group.add_argument("--snippet", action="store_true", help="Enable code snippet output")
    snippet_group.add_argument("--no-snippet", action="store_true", help="Disable code snippet output")
    args = parser.parse_args()
    show_snippet = args.snippet and not args.no_snippet

    data = json.load(sys.stdin)
    out = []
    for discussion in data:
        notes = discussion.get("notes", [])
        for note in notes:
            if note.get("system"):
                continue
            body = (note.get("body") or "").strip()
            author = (note.get("author") or {}).get("username")
            position = _normalize_position(note.get("position"))
            out.append({
                "author": author,
                "body": body,
                "position": position,
                "created_at": note.get("created_at"),
            })

    out.sort(key=lambda x: (
        x["position"] is None,
        x["position"].get("file_path") if x["position"] else "",
        x["position"].get("start_line") if x["position"] else 0,
    ))

    for item in out:
        if item["position"]:
            fp = item["position"].get("file_path") or "(unknown file)"
            start_line = item["position"].get("start_line") or "?"
            end_line = item["position"].get("end_line") or start_line
            range_type = item["position"].get("range_type")
            if start_line == end_line:
                header = f"- {fp}:{start_line}"
            else:
                header = f"- {fp}:{start_line}-{end_line}"
            if range_type:
                header += f" ({range_type})"
        else:
            header = "- (general comment)"
        print(header)
        if item["position"] and show_snippet:
            start_line = item["position"].get("start_line")
            end_line = item["position"].get("end_line")
            snippet, error = _render_snippet(args.repo_root, fp, start_line, end_line, args.context)
            if error:
                print(f"  [snippet unavailable] {error}")
            else:
                lang = _detect_language(fp)
                fence = f"```{lang}" if lang else "```"
                print(fence)
                print(snippet)
                print("```")
        author = item.get("author") or "unknown"
        body = item.get("body") or ""
        print(f"  @{author}: {body}")


if __name__ == "__main__":
    try:
        main()
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON input: {exc}", file=sys.stderr)
        sys.exit(1)
