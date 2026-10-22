#!/usr/bin/env python3
"""Corpus-wide skill description trigger scanner.

The per-skill deep audit (skill-builder audit mode) runs `description-has-triggers` / `trigger-clarity`
as WARN checks, so a missing trigger phrase never blocks a merge and the gap
accumulates silently across the corpus. This scanner is the corpus-wide
companion: it walks every `skills/*/SKILL.md`, applies the *same* three-form
trigger detection as `skill-builder/scripts/audit.sh`, scores each description,
and emits a prioritized remediation list with a suggested `Triggers:` stub for
each skill that lacks one.

Discovery in the runtime is pure LLM reasoning over the `description` field, so
a missing trigger phrase is a material skill-selection risk, not cosmetic. See
`skills/skill-builder/SKILL.md`.

Usage:
    python3 scan_descriptions.py [SKILLS_DIR] [--json] [--strict] [--quiet]
    python3 scan_descriptions.py [SKILLS_DIR] --probe "<phrase>" [--json]
    python3 scan_descriptions.py [SKILLS_DIR] --list-probes

Probe mode (`--probe "<phrase>"`) ranks every skill against the phrase using
ONLY the deterministic lexical ranker below — no live model, no `claude -p`, no
network — and asserts the skill that DECLARES the phrase in its
`trigger_probes:` frontmatter list ranks #1. Output is byte-stable across runs.

Exit codes:
    0  every emitted profile check passes (or --strict not set);
       in --probe mode: the declaring skill ranks #1 for the phrase
    1  one or more emitted profile checks is WARN/FAIL AND --strict is set;
       in --probe mode: the declaring skill does NOT rank #1
    2  usage error (skills dir not found, or no skill declares the phrase)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    from conformance_profile import ProfileError, load_profile, trigger_forms
except ModuleNotFoundError as exc:
    ProfileError = ValueError  # type: ignore[misc,assignment]
    load_profile = None  # type: ignore[assignment]
    trigger_forms = None  # type: ignore[assignment]
    _PROFILE_IMPORT_ERROR = exc
else:
    _PROFILE_IMPORT_ERROR = None

REPO_ROOT = Path(__file__).resolve().parents[3]

# Stop-words stripped when deriving a suggested trigger stub from the name.
_STOPWORDS = frozenset({"the", "a", "an", "for", "and", "to", "of", "with"})


@dataclass
class SkillScan:
    """Result of scanning one SKILL.md for trigger quality."""

    name: str
    path: Path
    description: str
    has_trigger: bool
    forms: list[str] = field(default_factory=list)
    score: int = 0
    suggestion: str = ""
    profile_id: str = ""
    checks: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Return a JSON-serializable view for --json / robot mode."""
        return {
            "name": self.name,
            "path": str(self.path),
            "has_trigger": self.has_trigger,
            "forms": self.forms,
            "score": self.score,
            "suggestion": self.suggestion,
            "profile_id": self.profile_id,
            "checks": self.checks,
        }


def split_frontmatter(text: str) -> tuple[str, str]:
    """Split a SKILL.md into (frontmatter, body). Empty frontmatter if absent."""
    if not text.startswith("---"):
        return "", text
    parts = text.split("\n---", 1)
    if len(parts) != 2:
        return "", text
    frontmatter = parts[0][len("---") :]
    body = parts[1].lstrip("-\n")
    return frontmatter, body


def parse_field(frontmatter: str, key: str) -> str:
    """Extract a single top-level scalar field's first line from frontmatter."""
    match = re.search(rf"^{re.escape(key)}:\s*(.*)$", frontmatter, re.MULTILINE)
    return match.group(1).strip() if match else ""


def description_block(frontmatter: str) -> str:
    """Return the full description value, including folded/literal continuations."""
    lines = frontmatter.splitlines()
    out: list[str] = []
    capturing = False
    for line in lines:
        if line.startswith("description:"):
            capturing = True
            out.append(line)
            continue
        if capturing:
            # A new top-level key (no leading whitespace, ends the block).
            if re.match(r"^[A-Za-z_-]+:", line):
                break
            out.append(line)
    return "\n".join(out)


def count_trigger_list(frontmatter: str) -> int:
    """Count items under a `metadata.triggers:` (or `triggers:`) YAML list."""
    lines = frontmatter.splitlines()
    in_list = False
    count = 0
    for line in lines:
        if re.match(r"^\s+triggers:\s*$", line):
            in_list = True
            continue
        if in_list:
            if re.match(r"^\s+-\s+", line):
                count += 1
                continue
            if re.match(r"^\s*[A-Za-z_-]+:", line):
                break
    return count


def split_flow_items(inner: str) -> list[str]:
    """Split a simple YAML flow sequence body without breaking quoted commas."""
    items: list[str] = []
    current: list[str] = []
    quote = ""
    i = 0
    while i < len(inner):
        char = inner[i]
        if quote:
            if char == "\\" and quote == '"' and i + 1 < len(inner):
                current.append(inner[i + 1])
                i += 2
                continue
            if char == quote:
                if quote == "'" and i + 1 < len(inner) and inner[i + 1] == "'":
                    current.append("'")
                    i += 2
                    continue
                quote = ""
            else:
                current.append(char)
        elif char in ("'", '"'):
            quote = char
        elif char == ",":
            items.append("".join(current))
            current = []
        else:
            current.append(char)
        i += 1
    items.append("".join(current))
    return items


def parse_trigger_probes(frontmatter: str) -> list[str]:
    """Return the items under a top-level `trigger_probes:` YAML list.

    Supports the flow form (`trigger_probes: ["a", "b"]`) and the block form
    (`trigger_probes:` followed by indented `- item` lines). Quotes are
    stripped; order is preserved. Purely lexical — no YAML library required so
    the scanner stays dependency-free and deterministic.
    """
    lines = frontmatter.splitlines()
    probes: list[str] = []
    for idx, line in enumerate(lines):
        flow = re.match(r"^trigger_probes:\s*\[(.*)\]\s*$", line)
        if flow:
            inner = flow.group(1).strip()
            if inner:
                for item in split_flow_items(inner):
                    cleaned = item.strip().strip("'\"").strip()
                    if cleaned:
                        probes.append(cleaned)
            return probes
        if re.match(r"^trigger_probes:\s*$", line):
            for follow in lines[idx + 1 :]:
                item = re.match(r"^\s+-\s+(.*)$", follow)
                if item:
                    cleaned = item.group(1).strip().strip("'\"").strip()
                    if cleaned:
                        probes.append(cleaned)
                    continue
                if re.match(r"^\S", follow):
                    break
            return probes
    return probes


_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    """Lowercase alphanumeric tokens, in order, for deterministic scoring."""
    return _WORD_RE.findall(text.lower())


def lexical_score(phrase: str, scan: SkillScan) -> tuple:
    """Deterministic lexical relevance of one skill to a probe phrase.

    Pure token math over the skill's own SEARCHABLE TEXT (name + description) —
    no model, no network, and deliberately NOT a function of the skill's
    `trigger_probes:` declaration. The declaration only identifies *which*
    skill is expected to win; the ranking itself is earned purely by lexical
    overlap, so a skill that stops describing its phrase genuinely drops in
    rank. Returns a tuple sort key (higher is more relevant); ties break by
    name so the ranking is total and byte-stable. Signals, in priority order:

    1. fraction of phrase tokens present in the searchable text (coverage),
    2. raw count of phrase-token hits,
    3. name-token overlap (a phrase word that is also a name word).
    """
    phrase_tokens = _tokens(phrase)
    name_tokens = set(_tokens(scan.name))
    haystack = " ".join([scan.name, scan.description])
    hay_tokens = _tokens(haystack)
    hay_set = set(hay_tokens)

    if phrase_tokens:
        present = sum(1 for t in phrase_tokens if t in hay_set)
        coverage = present / len(phrase_tokens)
        hits = sum(hay_tokens.count(t) for t in set(phrase_tokens))
    else:
        coverage = 0.0
        hits = 0
    name_overlap = sum(1 for t in set(phrase_tokens) if t in name_tokens)
    return (coverage, hits, name_overlap)


@dataclass
class ProbeResult:
    """One skill's deterministic rank for a probe phrase."""

    name: str
    score_key: tuple
    declares_phrase: bool

    def to_dict(self) -> dict:
        """JSON-serializable view (score_key as a list for stable output)."""
        return {
            "name": self.name,
            "score_key": list(self.score_key),
            "declares_phrase": self.declares_phrase,
        }


def probe_corpus(
    skills_dir: Path, phrase: str, profile: dict | None = None
) -> list[ProbeResult]:
    """Rank every skill against `phrase` using the deterministic lexical ranker.

    Sorted by descending score, then ascending name — a total, byte-stable
    order. Each result records whether that skill declares the phrase in its
    `trigger_probes:` list.
    """
    ranked: list[ProbeResult] = []
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        if profile is None:
            try:
                text = skill_md.read_text(encoding="utf-8")
            except OSError:
                continue
            frontmatter, _ = split_frontmatter(text)
            scan = SkillScan(
                name=parse_field(frontmatter, "name") or skill_md.parent.name,
                path=skill_md,
                description=description_block(frontmatter),
                has_trigger=False,
            )
        else:
            scan = scan_skill(skill_md, profile)
        if scan is None:
            continue
        frontmatter, _ = split_frontmatter(skill_md.read_text(encoding="utf-8"))
        probes = parse_trigger_probes(frontmatter)
        key = lexical_score(phrase, scan)
        declares = phrase.strip().lower() in {p.strip().lower() for p in probes}
        ranked.append(ProbeResult(name=scan.name, score_key=key, declares_phrase=declares))

    def sort_key(result: ProbeResult) -> tuple:
        # Descending score (negate the numeric components), ascending name.
        return (tuple(-x for x in result.score_key), result.name)

    ranked.sort(key=sort_key)
    return ranked


def render_probe(phrase: str, ranked: list[ProbeResult]) -> str:
    """Render a deterministic human-readable probe report."""
    declaring = [r.name for r in ranked if r.declares_phrase]
    lines = [
        "# Trigger probe",
        "",
        f"- Phrase: {phrase!r}",
        f"- Skills ranked: {len(ranked)}",
        f"- Declaring skills: {', '.join(declaring) if declaring else '(none)'}",
        "",
        "## Ranking (deterministic lexical, no model)",
        "",
        "| Rank | Skill | Declares | Score key |",
        "|------|-------|----------|-----------|",
    ]
    for i, r in enumerate(ranked, start=1):
        mark = "yes" if r.declares_phrase else ""
        lines.append(f"| {i} | `{r.name}` | {mark} | {list(r.score_key)} |")
    return "\n".join(lines)


def detect_trigger(text: str, profile: dict) -> list[str]:
    """Return canonical trigger form IDs from the selected profile semantics."""
    if trigger_forms is None:
        raise ProfileError(f"profile configuration loader missing: {_PROFILE_IMPORT_ERROR}")
    return trigger_forms(text, profile)


def score_trigger(description: str) -> int:
    """Score 0-3, mirroring skill-builder/scripts/score_agentops_skill.py."""
    signals = sum(
        marker.lower().strip("*").rstrip(":") in description.lower()
        for marker in ("Use when", "Triggers", "Perfect for")
    )
    return min(3, int(bool(description.strip())) + signals)


def suggest_triggers(name: str, description: str) -> str:
    """Derive a deterministic `Triggers:` stub from the skill name + first verb."""
    tokens = [t for t in name.split("-") if t not in _STOPWORDS]
    spaced = " ".join(tokens)
    first_sentence = re.split(r"[.\n]", description.strip(), maxsplit=1)[0]
    words = first_sentence.split()
    verb = words[0].lower().strip("'\"") if words else ""
    candidates = [name, spaced]
    # Only add a verb phrase when the verb adds a word not already in the name.
    if verb and tokens and verb not in tokens:
        candidates.append(f"{verb} {tokens[-1]}")
    seen: list[str] = []
    for phrase in candidates:
        cleaned = " ".join(dict.fromkeys(phrase.strip().lower().split()))
        if cleaned and cleaned not in seen:
            seen.append(cleaned)
    quoted = ", ".join(f'"{p}"' for p in seen)
    return f"Triggers: {quoted}"


def scan_skill(skill_md: Path, profile: dict | None = None) -> SkillScan | None:
    """Scan one SKILL.md. Returns None if the file is unreadable/empty."""
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError:
        return None
    if profile is None:
        if load_profile is None:
            raise ProfileError(f"profile configuration loader missing: {_PROFILE_IMPORT_ERROR}")
        profile = load_profile(REPO_ROOT, os.environ.get("SKILL_CONFORMANCE_PROFILE_ID"))
    frontmatter, _body = split_frontmatter(text)
    if re.search(r"^implementation:\s*false\s*$", frontmatter, re.MULTILINE):
        return None
    name = parse_field(frontmatter, "name") or skill_md.parent.name
    description = description_block(frontmatter)
    forms = detect_trigger(text, profile)
    has_trigger = bool(forms)
    rules = profile["rules"]
    checks = []
    for rule_id in ("description-has-triggers", "trigger-clarity"):
        accepted = rules[rule_id].get("accepted_forms", profile["trigger_forms"]["accepted"])
        passed = any(form in accepted for form in forms)
        severity = rules[rule_id]["severity"]
        checks.append(
            {
                "id": rule_id,
                "severity": severity,
                "status": "pass" if passed else severity.lower(),
            }
        )
    scan = SkillScan(
        name=name,
        path=skill_md,
        description=description,
        has_trigger=has_trigger,
        forms=forms,
        score=score_trigger(description),
        profile_id=profile["id"],
        checks=checks,
    )
    if not has_trigger:
        scan.suggestion = suggest_triggers(name, parse_field(frontmatter, "description"))
    return scan


def scan_corpus(skills_dir: Path, profile: dict | None = None) -> list[SkillScan]:
    """Scan every `<skill>/SKILL.md` under skills_dir, sorted by name."""
    results: list[SkillScan] = []
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        scan = scan_skill(skill_md, profile)
        if scan is not None:
            results.append(scan)
    return results


def aggregate_verdict(results: list[SkillScan]) -> str:
    """Derive the scanner verdict solely from emitted profile check statuses."""
    statuses = {
        check["status"] for result in results for check in result.checks
    }
    if "fail" in statuses:
        return "FAIL"
    if any(status != "pass" for status in statuses):
        return "WARN"
    return "PASS"


def list_probe_pairs(skills_dir: Path) -> list[tuple[str, str]]:
    """Return every (skill-id, probe-phrase) pair declared in the corpus.

    The skill-id is the SKILL.md's parent directory name (matching what the
    rest of the tooling keys on). Phrases come from the SAME `parse_trigger_probes`
    parser used by --probe, so any downstream consumer that wants the parsed
    pairs reuses this one parser instead of reimplementing the YAML walk.
    Sorted by (skill-id, phrase) for byte-stable output.
    """
    pairs: list[tuple[str, str]] = []
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        try:
            text = skill_md.read_text(encoding="utf-8")
        except OSError:
            continue
        frontmatter, _body = split_frontmatter(text)
        sid = skill_md.parent.name
        for phrase in parse_trigger_probes(frontmatter):
            pairs.append((sid, phrase))
    return sorted(set(pairs))


def render_markdown(results: list[SkillScan], profile_id: str = "") -> str:
    """Render a human-readable remediation report."""
    total = len(results)
    missing = [r for r in results if not r.has_trigger]
    selected_profile = profile_id or (results[0].profile_id if results else "unknown")
    verdict = aggregate_verdict(results)
    lines = [
        "# Skill description trigger scan",
        "",
        f"- Profile: **{selected_profile}**",
        f"- Verdict: **{verdict}**",
        f"- Skills scanned: **{total}**",
        f"- With trigger marker: **{total - len(missing)}**",
        f"- Missing trigger marker: **{len(missing)}** "
        f"({(len(missing) / total * 100):.0f}%)" if total else "- Missing: 0",
        "",
    ]
    if not missing:
        lines.append("All descriptions carry a trigger marker. ✅")
        return "\n".join(lines)
    lines += [
        "## Remediation backlog (add a trigger marker to each)",
        "",
        "| Skill | Score | Suggested stub |",
        "|-------|-------|----------------|",
    ]
    for r in missing:
        lines.append(f"| `{r.name}` | {r.score}/3 | `{r.suggestion}` |")
    return "\n".join(lines)


def _run_probe(
    skills_dir: Path,
    phrase: str,
    *,
    profile: dict | None,
    json_mode: bool,
    quiet: bool,
) -> int:
    """Drive --probe: rank the corpus and assert the declaring skill wins.

    Returns 2 if no skill declares the phrase (a usage error — nothing to
    assert), 0 if the declaring skill ranks #1, 1 otherwise.
    """
    ranked = probe_corpus(skills_dir, phrase, profile)
    declaring = [r for r in ranked if r.declares_phrase]
    top = ranked[0] if ranked else None
    declarer_is_top = bool(top and top.declares_phrase)

    if json_mode:
        payload = {
            "phrase": phrase,
            "ranked": len(ranked),
            "declaring": [r.name for r in declaring],
            "top": top.name if top else None,
            "declarer_is_top": declarer_is_top,
            "skills": [r.to_dict() for r in ranked],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    elif not quiet:
        print(render_probe(phrase, ranked))

    if not declaring:
        if not json_mode:
            print(f"error: no skill declares the probe phrase: {phrase!r}", file=sys.stderr)
        return 2
    return 0 if declarer_is_top else 1


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "skills_dir",
        nargs="?",
        default="skills",
        help="Path to the skills/ directory (default: skills)",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON (robot mode)")
    parser.add_argument(
        "--strict", action="store_true", help="Exit 1 if any emitted profile check is non-pass"
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress the human report")
    parser.add_argument(
        "--probe",
        metavar="PHRASE",
        default=None,
        help="Deterministic lexical probe: assert the skill that declares PHRASE "
        "in trigger_probes: ranks #1 (no live model, no network)",
    )
    parser.add_argument(
        "--list-probes",
        action="store_true",
        help="Emit every declared (skill-id<TAB>phrase) pair, one per line, using "
        "the SAME parser as --probe (so consumers don't reimplement the YAML walk)",
    )
    args = parser.parse_args(argv)

    skills_dir = Path(args.skills_dir)
    if not skills_dir.is_dir():
        print(f"error: skills dir not found: {skills_dir}", file=sys.stderr)
        return 2

    if args.list_probes:
        for sid, phrase in list_probe_pairs(skills_dir):
            print(f"{sid}\t{phrase}")
        return 0

    if args.probe is not None:
        return _run_probe(
            skills_dir,
            args.probe,
            profile=None,
            json_mode=args.json,
            quiet=args.quiet,
        )

    if load_profile is None:
        print(f"profile configuration loader missing: {_PROFILE_IMPORT_ERROR}", file=sys.stderr)
        return 2
    try:
        profile = load_profile(REPO_ROOT, os.environ.get("SKILL_CONFORMANCE_PROFILE_ID"))
    except ProfileError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    results = scan_corpus(skills_dir, profile)
    missing = [r for r in results if not r.has_trigger]
    verdict = aggregate_verdict(results)

    if args.json:
        payload = {
            "profile_id": profile["id"],
            "verdict": verdict,
            "scanned": len(results),
            "missing": len(missing),
            "skills": [r.to_dict() for r in results],
        }
        print(json.dumps(payload, indent=2))
    elif not args.quiet:
        print(render_markdown(results, profile["id"]))

    return 1 if (args.strict and verdict != "PASS") else 0


if __name__ == "__main__":
    sys.exit(main())
