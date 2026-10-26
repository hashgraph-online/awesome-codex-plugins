#!/usr/bin/env python3
"""Roll calls.jsonl up into the tables the diagnosis starts from: summary.md and summary.json.

    aggregate.py calls.jsonl --out-dir DIR [--patterns patterns.json]

--patterns adds machine-specific shell patterns ahead of the built-in ones: a JSON list of
[category, label, regex]. Use it to name the commands behind a large "Other shell" or
"Scripts & data" bucket.
"""
import argparse
import bisect
import collections
import json
import math
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import first_cmd  # noqa: E402

# The first pattern that matches anywhere in the command names the call, so heavy steps come
# first: `mkdir out && blender -b ...` counts as a Blender run, not as mkdir.
SHELL_PATTERNS = [
    ("Wait / poll", "until loop", r"\buntil\b"),
    ("Wait / poll", "while + sleep loop", r"\bwhile\b.*\bsleep\b"),
    ("Wait / poll", "watch command", r"\bgh (run|pr) (watch|checks\b.*--watch)|--watch\b|\bwait\.sh\b"),
    ("Tests: e2e / UI", "lock-wrapped run", r"\b(lockf|flock)\b"),
    ("Tests: e2e / UI", "e2e suite", r"(pnpm|npm|bun|yarn)( run)? (test:)?e2e\b|playwright test|cypress run|\bpytest\b[^\n;&|]*\be2e"),
    ("Tests: e2e / UI", "screenshot run", r"\bshoot\.sh\b|\bscreencapture\b|\bshot\.(ts|mjs|js|py)\b"),
    ("Render / 3D", "Blender headless", r"\bblender\s+(-b|--background)\b"),
    ("Tests: unit / types / build", "vitest / jest", r"\b(vitest|jest)\b"),
    ("Tests: unit / types / build", "pytest", r"\bpytest\b"),
    ("Tests: unit / types / build", "cargo / go test", r"\b(cargo test|cargo nextest|go test)\b"),
    ("Tests: unit / types / build", "typecheck", r"\btsc\b|typecheck|\bmypy\b|\bpyright\b"),
    ("Tests: unit / types / build", "lint / format", r"\blint\b|eslint|oxlint|biome|ruff|prettier|fmt:check"),
    ("Tests: unit / types / build", "test script", r"(pnpm|npm|bun|yarn)( run)? test\b|\bmake test\b"),
    ("Tests: unit / types / build", "build", r"(pnpm|npm|bun|yarn)( run)? build\b|xcodebuild|swift build|cargo build|go build|gradle|mvn |docker (build|compose build)"),
    ("Install", "package install", r"\b(pnpm|npm|bun|yarn) (install|i|add|ci)\b|pip install|uv (sync|pip)|brew install|cargo install"),
    ("Wait / poll", "sleep", r"(^|[;&|\s])sleep\s+\d"),
    ("Git / forge", "gh / glab", r"(^|[;&|\s(])(gh|glab)\s"),
    ("Git / forge", "git network", r"\bgit (push|fetch|pull|clone)\b"),
    ("Scripts & data", "node / tsx script", r"\b(npx tsx|tsx|node|bun run|deno)\b"),
    ("Scripts & data", "python script", r"\b(python3?(\.\d+)?|uv run)\b"),
    ("Git / forge", "git local", r"\bgit\b"),
    ("Read & search", "read / search shell", r"\b(cat|sed|grep|rg|ls|find|fd|head|tail|wc|jq|awk|stat|du|tree)\b"),
]
CATEGORY_BY_KIND = {"read": ("Read & search", "read tool"), "search": ("Read & search", "search tool"),
                    "edit": ("Edit & write", "edit tool"), "web": ("Web", "web tool"),
                    "subagent": ("Subagents", "subagent"), "wait": ("Wait / poll", "wait tool"),
                    "review": ("Approval review", "automatic reviewer"), "ask_user": ("Waiting on you", "question"),
                    "other": ("Other built-in", None)}
BROWSER_MCP = re.compile(r"playwright|chrome|browser|puppeteer|computer.?use|cua|devtools")
WAIT_MCP = re.compile(r"wait|status|poll")
SLOW_MS = 30_000
CAP_MIN_MS = 60_000


def classify(c, patterns):
    if c.get("human_wait") and c["kind"] != "ask_user":
        return "Waiting on you", "approval prompt"
    if c["kind"] == "shell":
        cmd = c.get("command") or ""
        for cat, label, pat in patterns:
            if pat.search(cmd):
                return cat, label
        return "Other shell", first_cmd(cmd)
    if c["kind"] == "mcp":
        server, tool = c.get("mcp_server") or "?", c.get("mcp_tool") or c["tool"]
        if BROWSER_MCP.search(server.lower()):
            return "Browser / computer use", server
        if WAIT_MCP.search(tool.lower()):
            return "Wait / poll", f"{server} {tool}"
        return "MCP", server
    cat, label = CATEGORY_BY_KIND[c["kind"]]
    return cat, label or c["tool"]


def q(xs, p):
    """Nearest-rank percentile: the smallest value with at least p of the values at or below it."""
    xs = sorted(xs)
    return xs[max(0, math.ceil(p * len(xs)) - 1)] if xs else None


def stats(calls):
    d = [c["dur_ms"] for c in calls]
    return dict(n=len(d), p50=q(d, .5), p90=q(d, .9), max=max(d) if d else None,
                hours=round(sum(d) / 3.6e6, 2), slow=sum(v >= SLOW_MS for v in d))


def find_caps(calls):
    """Durations a tool keeps ending at, i.e. timeout caps, as [(cap_ms, calls), ...].

    A cap is a spike above a minute: calls from at least 3 separate moments ending within
    CAP_SPREAD of the same duration, well above what the surrounding range (0.8x to 1.25x) predicts
    for a window that narrow, since ordinary work also often takes about as long as a cap. A tool
    can have several (Claude Code's Bash stops at its 2-minute default and at any longer timeout the
    agent asks for). Calls that end together, parallel calls from one message or edits queued behind
    one approval prompt, count once; calls that waited on the user are left out.
    """
    longs = sorted((c["dur_ms"], round((c["ts"] + c["dur_ms"]) / 10_000)) for c in calls
                   if c["dur_ms"] >= CAP_MIN_MS * 0.8 and not c.get("background") and not c.get("human_wait"))
    durations = [d for d, _ in longs]
    spikes = []
    for i, (low, _) in enumerate(longs):
        if low < CAP_MIN_MS:
            continue
        spread = cap_spread(low)
        j = i
        while j + 1 < len(longs) and longs[j + 1][0] <= low + spread:
            j += 1
        ends = {e for _, e in longs[i:j + 1]}
        window = longs[bisect.bisect_left(durations, low * 0.8):bisect.bisect_right(durations, low * 1.25)]
        expected = len({e for _, e in window} - ends) * spread / (0.45 * low - spread)
        if len(ends) >= 3 + 3 * expected:
            spikes.append((len(ends), low, i, j))
    caps, taken = [], set()
    for size, low, i, j in sorted(spikes, key=lambda s: (-s[0], s[1])):
        if taken.isdisjoint(range(i, j + 1)):
            taken.update(range(i, j + 1))
            caps.append((low, size))
    return sorted(caps)


def cap_spread(cap_ms):
    """How far past a cap a capped call can end: the harness's own overhead, about 2 s, or 0.5%."""
    return max(2_000, cap_ms * 0.005)


def at_cap(call, caps):
    if call.get("background") or call.get("human_wait"):
        return False
    return any(cap <= call["dur_ms"] <= cap + cap_spread(cap) for cap, _ in caps)


def table(rows, cols):
    head = "| " + " | ".join(h for h, _ in cols) + " |\n|" + "---|" * len(cols) + "\n"
    return head + "".join("| " + " | ".join(str(f(r)).replace("|", "\\|") for _, f in cols) + " |\n" for r in rows)


def sec(ms):
    return "—" if ms is None else f"{ms / 1000:.1f}s" if ms < 600_000 else f"{ms / 60000:.0f}m"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("calls")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--patterns", help="JSON list of [category, label, regex], checked first")
    args = ap.parse_args()
    extra = []
    if args.patterns:
        with open(args.patterns) as fh:
            extra = json.load(fh)
    patterns = [(c, l, re.compile(p)) for c, l, p in extra + SHELL_PATTERNS]

    with open(args.calls) as fh:
        calls = [json.loads(line) for line in fh]
    if not calls:
        raise SystemExit("no calls")
    for c in calls:
        c["cat"], c["label"] = classify(c, patterns)
    harnesses = [h for h, _ in collections.Counter(c["harness"] for c in calls).most_common()]

    caps = {}
    by_tool = collections.defaultdict(list)
    for c in calls:
        by_tool[(c["harness"], c["tool"])].append(c)
    for key, cs in by_tool.items():
        found = find_caps(cs)
        if found:
            caps[key] = found
    for c in calls:
        c["capped"] = at_cap(c, caps.get((c["harness"], c["tool"]), []))

    def capped(cs):
        return sum(c["capped"] for c in cs)

    out = {"window": [min(c["ts"] for c in calls), max(c["ts"] for c in calls)], "total": stats(calls)}
    out["harnesses"] = [dict(harness=h, capped=capped([c for c in calls if c["harness"] == h]),
                             **stats([c for c in calls if c["harness"] == h])) for h in harnesses]

    groups = collections.defaultdict(list)
    for c in calls:
        groups[c["cat"]].append(c)
    out["categories"] = sorted(
        [dict(category=k, **stats(v), hours_by_harness={h: round(sum(c["dur_ms"] for c in v if c["harness"] == h) / 3.6e6, 2)
                                                         for h in harnesses}) for k, v in groups.items()],
        key=lambda r: -r["hours"])

    labels = collections.defaultdict(list)
    for c in calls:
        labels[(c["cat"], c["label"])].append(c)
    patterns_out = []
    for (cat, label), v in labels.items():
        if len(v) < 5:
            continue
        patterns_out.append(dict(category=cat, label=label, capped=capped(v), **stats(v),
                                 projects=collections.Counter(c.get("project", "?") for c in v).most_common(3),
                                 harnesses=collections.Counter(c["harness"] for c in v).most_common(2)))
    out["patterns_by_hours"] = sorted(patterns_out, key=lambda r: -r["hours"])[:30]
    out["patterns_by_p50"] = sorted([p for p in patterns_out if p["n"] >= 10], key=lambda r: -r["p50"])[:15]

    cap_rows = []
    for (h, t), found in caps.items():
        for cap, _ in found:
            hit = [c for c in by_tool[(h, t)] if at_cap(c, [(cap, 0)])]
            cap_rows.append(dict(harness=h, tool=t, cap_ms=cap, n=len(hit),
                                 hours=round(sum(c["dur_ms"] for c in hit) / 3.6e6, 2),
                                 labels=collections.Counter(c["label"] for c in hit).most_common(5)))
    out["caps"] = sorted(cap_rows, key=lambda r: -r["hours"])

    # Cheap operations should cost the same everywhere. Where they don't, the gap is harness
    # overhead (an approval check, a slow release), not the work.
    fast_ops = [("read tool", lambda c: c["kind"] == "read"), ("edit tool", lambda c: c["kind"] == "edit"),
                ("shell read / search", lambda c: c["label"] == "read / search shell"),
                ("shell git local", lambda c: c["label"] == "git local")]
    overhead, versions = [], []
    for op, pred in fast_ops:
        cells = collections.defaultdict(list)
        vcells = collections.defaultdict(list)
        for c in calls:
            if pred(c) and not c.get("human_wait") and not c.get("background"):
                cells[(c["harness"], c.get("mode") or "—", c.get("approval") or "—")].append(c["dur_ms"])
                vcells[(c["agent"], c.get("approval") or "—", c.get("version") or "—")].append(c["dur_ms"])
        for (h, mode, approval), d in sorted(cells.items()):
            if len(d) >= 20:
                overhead.append(dict(op=op, harness=h, mode=mode, approval=approval, n=len(d), p50=q(d, .5), p90=q(d, .9)))
        # A release whose calls went through a slower approval path more often looks slow when
        # mixed; compare releases within one approval path only.
        rows = [dict(op=op, agent=a, approval=ap, version=v, n=len(d), p50=q(d, .5))
                for (a, ap, v), d in vcells.items() if len(d) >= 20]
        for key in {(r["agent"], r["approval"]) for r in rows}:
            mine = [r for r in rows if (r["agent"], r["approval"]) == key]
            typical = statistics.median(r["p50"] for r in mine)
            for r in mine:
                r["outlier"] = len(mine) >= 3 and r["p50"] >= 3 * typical and r["p50"] - typical >= 200
        versions += sorted(rows, key=lambda r: (r["agent"], r["approval"], r["version"]))
    out["fast_op_overhead"] = overhead
    out["fast_op_by_version"] = versions

    mcp = collections.defaultdict(list)
    for c in calls:
        if c["kind"] == "mcp":
            mcp[c.get("mcp_server") or "?"].append(c)
    out["mcp_servers"] = sorted([dict(server=k, **stats(v)) for k, v in mcp.items() if len(v) >= 5], key=lambda r: -r["hours"])

    other = collections.defaultdict(list)
    for c in calls:
        if c["cat"] in ("Other shell", "Scripts & data"):
            other[(c["cat"], first_cmd(c.get("command") or ""))].append(c)
    out["unnamed_shell"] = sorted([dict(category=k[0], family=k[1], **stats(v)) for k, v in other.items()],
                                  key=lambda r: -r["hours"])[:20]

    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "summary.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    with open(os.path.join(args.out_dir, "summary.md"), "w") as fh:
        fh.write(render(out))
    print(f"{len(calls)} calls, {out['total']['hours']} h -> {args.out_dir}/summary.md")


def render(o):
    t = o["total"]
    wait = next((r for r in o["categories"] if r["category"] == "Waiting on you"), None)
    waited = (f" {wait['hours']} h of it is agents waiting on the user (approval prompts and questions): "
              "report it on its own line, apart from need and waste." if wait else "")
    md = [f"# Tool-call latency summary\n\n{t['n']} calls, {t['hours']} h of tool time.{waited}\n"]
    md.append("## By harness\n\n" + table(o["harnesses"], [
        ("Harness", lambda r: r["harness"]), ("Calls", lambda r: r["n"]), ("Hours", lambda r: r["hours"]),
        ("p50", lambda r: sec(r["p50"])), ("p90", lambda r: sec(r["p90"])), ("≥30 s", lambda r: r["slow"]),
        ("At cap", lambda r: r["capped"])]))
    md.append("## By category\n\n" + table(o["categories"], [
        ("Category", lambda r: r["category"]), ("Calls", lambda r: r["n"]), ("Hours", lambda r: r["hours"]),
        ("p50", lambda r: sec(r["p50"])), ("p90", lambda r: sec(r["p90"])), ("≥30 s", lambda r: r["slow"]),
        ("Top harness", lambda r: max(r["hours_by_harness"].items(), key=lambda kv: kv[1])[0])]))
    pat_cols = [("Pattern", lambda r: f"{r['category']}: {r['label']}"), ("Calls", lambda r: r["n"]),
                ("Hours", lambda r: r["hours"]), ("p50", lambda r: sec(r["p50"])), ("p90", lambda r: sec(r["p90"])),
                ("At cap", lambda r: r["capped"]),
                ("Where", lambda r: ", ".join(f"{p} ({n})" for p, n in r["projects"][:2]))]
    md.append("## Patterns by total time\n\n" + table(o["patterns_by_hours"], pat_cols))
    md.append("## Slowest typical patterns (p50, at least 10 calls)\n\n" + table(o["patterns_by_p50"], pat_cols))
    if o["caps"]:
        md.append("## Calls ending at a timeout cap\n\n" + table(o["caps"], [
            ("Harness", lambda r: r["harness"]), ("Tool", lambda r: r["tool"]), ("Cap", lambda r: sec(r["cap_ms"])),
            ("Calls", lambda r: r["n"]), ("Hours", lambda r: r["hours"]),
            ("Patterns", lambda r: ", ".join(f"{l} ({n})" for l, n in r["labels"][:3]))]))
    md.append("## Cheap operations by harness, mode and approval path\n\n" + table(o["fast_op_overhead"], [
        ("Operation", lambda r: r["op"]), ("Harness", lambda r: r["harness"]), ("Mode", lambda r: r["mode"]),
        ("Approval", lambda r: r["approval"]), ("Calls", lambda r: r["n"]), ("p50", lambda r: f"{r['p50']:.0f} ms"),
        ("p90", lambda r: f"{r['p90']:.0f} ms")]))
    outliers = [r for r in o["fast_op_by_version"] if r.get("outlier")]
    md.append("## Releases where cheap operations were slow\n\n" + (table(outliers, [
        ("Operation", lambda r: r["op"]), ("Agent", lambda r: r["agent"]), ("Approval", lambda r: r["approval"]),
        ("Version", lambda r: r["version"]),
        ("Calls", lambda r: r["n"]), ("p50", lambda r: f"{r['p50']:.0f} ms")]) if outliers else "None.\n"))
    if o["mcp_servers"]:
        md.append("## MCP servers\n\n" + table(o["mcp_servers"][:15], [
            ("Server", lambda r: r["server"]), ("Calls", lambda r: r["n"]), ("Hours", lambda r: r["hours"]),
            ("p50", lambda r: sec(r["p50"])), ("p90", lambda r: sec(r["p90"]))]))
    md.append("## Unnamed shell commands (candidates for --patterns)\n\n" + table(o["unnamed_shell"], [
        ("Bucket", lambda r: r["category"]), ("Command family", lambda r: r["family"]), ("Calls", lambda r: r["n"]),
        ("Hours", lambda r: r["hours"]), ("p50", lambda r: sec(r["p50"]))]))
    return "\n".join(md)


if __name__ == "__main__":
    main()
