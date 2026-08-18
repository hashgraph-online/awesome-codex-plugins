#!/usr/bin/env python3
"""
Prompt Miner — Extract and cluster prompts across agent session logs.

Mines user prompts from Claude Code, Codex CLI, and Gemini CLI sessions,
clusters them by similarity, and identifies "ritual" prompts (repeated patterns
that indicate working workflows).

Usage:
    python prompt_miner.py --workspace /data/projects/PROJECT [OPTIONS]

Examples:
    # Find repeated prompts in a project
    python prompt_miner.py --workspace /data/projects/beads_rust --top 30

    # Mine all sessions with custom glob
    python prompt_miner.py --glob "~/.claude/projects/**/*.jsonl" --top 50

    # Only show rituals (10+ occurrences)
    python prompt_miner.py --workspace /path --min-count 10

    # Output as JSON for further processing
    python prompt_miner.py --workspace /path --json

    # Filter by agent
    python prompt_miner.py --workspace /path --agent claude_code
"""

import json
import re
import glob
import argparse
import os
import sys
from datetime import datetime, timezone
from typing import Optional


def normalize(s: str) -> str:
    """Normalize whitespace for clustering."""
    return re.sub(r"\s+", " ", s.strip())


def truncate(s: str, max_len: int = 100) -> str:
    """Truncate string with ellipsis."""
    if len(s) <= max_len:
        return s
    return s[:max_len-3] + "..."


def parse_iso(ts: str) -> Optional[datetime]:
    """Parse ISO timestamp, handling various formats."""
    if not ts:
        return None
    # Handle Z suffix
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    # Handle missing timezone
    if "+" not in ts and "-" not in ts[-6:]:
        ts = ts + "+00:00"
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def extract_text_from_content(content) -> str:
    """Extract text from various content formats."""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict):
                if "text" in c:
                    parts.append(str(c["text"]))
                elif "content" in c:
                    parts.append(extract_text_from_content(c["content"]))
        return " ".join(parts)
    elif isinstance(content, dict):
        if "text" in content:
            return str(content["text"])
        elif "content" in content:
            return extract_text_from_content(content["content"])
    return ""


def detect_agent(path: str, obj: dict) -> str:
    """Detect which agent produced this session."""
    path_lower = path.lower()
    if ".claude" in path_lower:
        return "claude_code"
    elif "codex" in path_lower:
        return "codex"
    elif "gemini" in path_lower:
        return "gemini"
    # Fallback: check object structure
    if obj.get("type") == "user":
        return "claude_code"
    elif obj.get("role") == "user":
        return "codex"  # or gemini
    return "unknown"


def mine_prompts(
    glob_pattern: str,
    agent_filter: Optional[str] = None
) -> list[tuple[datetime, str, str, str]]:
    """
    Mine user prompts from session logs.

    Returns list of (timestamp, source_path, prompt_text, agent).
    """
    items = []
    expanded_pattern = os.path.expanduser(glob_pattern)

    for path in glob.glob(expanded_pattern, recursive=True):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(obj, dict):
                        continue

                    try:
                        agent = detect_agent(path, obj)
                        if agent_filter and agent != agent_filter:
                            continue

                        text = None
                        ts = None

                        # Claude Code format
                        if obj.get("type") == "user":
                            msg = obj.get("message", {})
                            if not isinstance(msg, dict):
                                continue
                            content = msg.get("content", "")
                            text = extract_text_from_content(content)
                            ts = obj.get("timestamp")

                        # Codex/Gemini format
                        elif obj.get("role") == "user" and "content" in obj:
                            text = extract_text_from_content(obj["content"])
                            ts = obj.get("timestamp") or obj.get("created_at")

                        if text and text.strip():
                            dt = parse_iso(ts) or datetime.now(timezone.utc)
                            items.append((dt, path, text.strip(), agent))
                    except Exception:
                        continue

        except Exception:
            # Skip unreadable files
            pass

    items.sort(key=lambda x: x[0])
    return items


def find_repeated_prompts(
    items: list[tuple],
    top_n: int = 30,
    min_count: int = 2
) -> list[dict]:
    """Find most repeated prompts with metadata."""
    # Group by normalized text
    groups = {}
    for dt, path, text, agent in items:
        key = normalize(text)
        if key not in groups:
            groups[key] = {
                "text": text,  # Keep original (first occurrence)
                "count": 0,
                "agents": set(),
                "first_seen": dt,
                "last_seen": dt,
                "paths": []
            }
        groups[key]["count"] += 1
        groups[key]["agents"].add(agent)
        groups[key]["last_seen"] = max(groups[key]["last_seen"], dt)
        if path not in groups[key]["paths"] and len(groups[key]["paths"]) < 3:  # Keep first 3 unique paths
            groups[key]["paths"].append(path)

    # Convert to list and sort
    results = []
    for key, data in groups.items():
        if data["count"] >= min_count:
            results.append({
                "prompt": data["text"],
                "count": data["count"],
                "agents": sorted(data["agents"]),
                "first_seen": data["first_seen"].isoformat() if data["first_seen"] else None,
                "last_seen": data["last_seen"].isoformat() if data["last_seen"] else None,
                "example_paths": data["paths"],
                "is_ritual": data["count"] >= 10
            })

    results.sort(key=lambda x: -x["count"])
    return results[:top_n]


def workspace_to_glob(workspace: str) -> str:
    """Convert workspace path to glob pattern for session files."""
    workspace = os.path.expanduser(workspace)
    # Claude Code stores sessions in ~/.claude/projects/-path-to-project/
    # Convert /data/projects/foo to -data-projects-foo pattern
    escaped = workspace.replace("/", "-").lstrip("-")
    return f"~/.claude/projects/*{escaped}*/**/*.jsonl"


def main():
    parser = argparse.ArgumentParser(
        description="Mine prompts from agent session logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s --workspace /data/projects/beads_rust --top 30
    %(prog)s --glob "~/.claude/**/*.jsonl" --min-count 10
    %(prog)s --workspace /path --json > prompts.json
        """
    )
    parser.add_argument(
        "--workspace",
        help="Project workspace path (auto-generates glob pattern)"
    )
    parser.add_argument(
        "--glob",
        help="Glob pattern for session files (overrides --workspace)"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=30,
        help="Number of top repeated prompts to show (default: 30)"
    )
    parser.add_argument(
        "--min-count",
        type=int,
        default=2,
        help="Minimum repetition count to include (default: 2)"
    )
    parser.add_argument(
        "--agent",
        choices=["claude_code", "codex", "gemini"],
        help="Filter by agent type"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--rituals-only",
        action="store_true",
        help="Only show ritual prompts (10+ occurrences)"
    )

    args = parser.parse_args()

    if args.top <= 0:
        print("ERROR: --top must be greater than 0", file=sys.stderr)
        return 1
    if args.min_count <= 0:
        print("ERROR: --min-count must be greater than 0", file=sys.stderr)
        return 1

    # Determine glob pattern
    if args.glob:
        glob_pattern = args.glob
    elif args.workspace:
        glob_pattern = workspace_to_glob(args.workspace)
    else:
        glob_pattern = "~/.claude/projects/**/*.jsonl"

    # Set min count for rituals-only mode
    min_count = args.min_count
    if args.rituals_only:
        min_count = max(min_count, 10)

    # Mine prompts
    if not args.json:
        print(f"Mining prompts from: {glob_pattern}")

    items = mine_prompts(glob_pattern, args.agent)

    if not args.json:
        print(f"Found {len(items)} user prompts")

    # Find repeated prompts
    repeated = find_repeated_prompts(items, args.top, min_count)

    # Output
    if args.json:
        print(json.dumps({
            "glob_pattern": glob_pattern,
            "total_prompts": len(items),
            "repeated_prompts": repeated
        }, indent=2, default=str))
    else:
        print(f"\nTop {len(repeated)} repeated prompts (count >= {min_count}):\n")
        for item in repeated:
            ritual_marker = " [RITUAL]" if item["is_ritual"] else ""
            display = truncate(item["prompt"], 100)
            agents = ", ".join(item["agents"])
            print(f"{item['count']:3d}x ({agents}){ritual_marker}: {display}")


if __name__ == "__main__":
    sys.exit(main())
