#!/usr/bin/env python3
"""Advisory craft instrumentation for one skill package (audit Pass 4).

Reports three advisory blocks over a skill's SKILL.md:

1. A 12-element craft score with named gaps. Elements are the cheaply
   machine-detectable authoring elements enumerated in
   references/skill-template.md (section 8). Presence is detected, never
   quality; scoring quality stays a fresh validator's judgment.
2. Provenance resolution: cited repo paths and .agents/ao verdict/intent
   digests (full or prefix...suffix abbreviated) must resolve; dead
   citations are named findings.
3. Loop safety: iteration prose lacking a checkable stop-condition phrase
   in the same section, and agent-dispatch loops lacking a budget phrase,
   are named findings.

Everything here is advisory-only: this script never gates, and audit.sh
embeds its output without letting it change exit codes or verdicts.

HTML comments are stripped before detection so the init.sh scaffolding
stubs (<!-- craft:... -->) never satisfy an element; only authored prose
counts.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

MAX_SCORE = 12

# Checkable stop-condition phrases: a bare "until <vague goal>" does not
# count; the phrase must name a greppable boundary (count, exit code,
# passing check).
STOP_CONDITION = re.compile(
    r"(?i)("
    r"stop[- ](when|after|if|condition)s?|stops (when|after)|halt (when|after)"
    r"|at most \d+|no more than \d+|max(imum)?\s*(of\s+)?\d+"
    r"|\d+\s+(iterations?|attempts?|passes|times|rounds)"
    r"|give up after|exit (when|0|code 0)"
    r"|until [^.\n]*\b(exit 0|exits 0|passes|pass\b|green\b|zero findings|\d+)"
    r")"
)

LOOP_PROSE = re.compile(r"(?i)\b(repeat(ed|s)?|iterat(e|es|ing|ion|ions)|loop(s|ing)?)\b")

DISPATCH_PROSE = re.compile(
    r"(?i)\b(agents?|subagents?|dispatch(es|ing)?|spawn(s|ed|ing)?|workers?|lanes?|swarm)\b"
)

BUDGET_PHRASE = re.compile(
    r"(?i)\b("
    r"budget|timebox|deadline"
    r"|at most \d+|no more than \d+|max(imum)?\s*(of\s+)?\d+"
    r"|\d+\s+(agents?|subagents?|workers?|lanes?|dispatches|attempts?|iterations?)"
    r")\b"
)

DIGEST_ABBREV = re.compile(r"\b([0-9a-f]{6,63})(?:\.\.\.|…)([0-9a-f]{2,63})\b")
DIGEST_PREFIX = re.compile(r"\b([0-9a-f]{8,63})(?:\.\.\.|…)(?![0-9a-f])")
DIGEST_FULL = re.compile(r"\b[0-9a-f]{64}\b")

REPO_PATH = re.compile(
    r"(?<![\w/.-])"
    r"((?:docs|scripts|skills|skills-codex|tests|cli|schemas|evidence|\.agentops|\.agents)"
    r"/[A-Za-z0-9._\-][A-Za-z0-9._/\-]*)"
)


def frontmatter_and_body(text: str) -> tuple[dict, str]:
    parts = text.split("---", 2)
    if len(parts) != 3:
        return {}, text
    try:
        data = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    return data, parts[2]


def strip_html_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def split_sections(body: str) -> list[tuple[str, str]]:
    """Split body into (heading, section_text) pairs; preamble uses ''."""
    sections: list[tuple[str, str]] = []
    heading = ""
    lines: list[str] = []
    for line in body.splitlines():
        match = re.match(r"^#{1,6}\s+(.*)$", line)
        if match:
            sections.append((heading, "\n".join(lines)))
            heading = match.group(1).strip()
            lines = []
        else:
            lines.append(line)
    sections.append((heading, "\n".join(lines)))
    return sections


def resolve_digest(citation: str, digest_stems: list[str]) -> bool:
    if "..." in citation or "…" in citation:
        prefix, _, suffix = re.split(r"(\.\.\.|…)", citation, maxsplit=1)
        return any(
            stem.startswith(prefix) and (not suffix or stem.endswith(suffix))
            for stem in digest_stems
        )
    return citation in digest_stems


def check_provenance(text: str, repo_root: Path, skill_dir: Path) -> dict:
    # Fenced code blocks are illustrative examples, not citations; extracting
    # from them produces false dead findings (e.g. "skills/example").
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    digest_stems = [
        path.stem
        for pattern in ("verdicts", "intents")
        for path in sorted((repo_root / ".agents" / "ao" / pattern / "sha256").glob("*"))
        if path.is_file()
    ]

    citations: list[tuple[str, str]] = []
    seen: set[str] = set()
    for regex in (DIGEST_ABBREV, DIGEST_PREFIX):
        for match in regex.finditer(text):
            token = match.group(0)
            if token not in seen:
                seen.add(token)
                citations.append((token, "digest"))
    for match in DIGEST_FULL.finditer(text):
        token = match.group(0)
        if token not in seen and not any(token in c for c, _ in citations):
            seen.add(token)
            citations.append((token, "digest"))
    for match in REPO_PATH.finditer(text):
        token = match.group(1).rstrip("./")
        if token and token not in seen:
            seen.add(token)
            citations.append((token, "path"))

    dead = []
    resolved = 0
    for citation, kind in citations:
        if kind == "digest":
            ok = resolve_digest(citation, digest_stems)
        else:
            ok = (repo_root / citation).exists() or (skill_dir / citation).exists()
        if ok:
            resolved += 1
        else:
            dead.append({"citation": citation, "kind": kind})

    return {
        "advisory": True,
        "citations": len(citations),
        "resolved": resolved,
        "dead": dead,
    }


def check_loop_safety(sections: list[tuple[str, str]]) -> list[dict]:
    findings = []
    for heading, text in sections:
        if not LOOP_PROSE.search(text):
            continue
        label = heading or "(preamble)"
        if not STOP_CONDITION.search(text):
            findings.append(
                {
                    "type": "loop-missing-stop-condition",
                    "section": label,
                    "evidence": "iteration prose without a checkable stop-condition phrase in the same section",
                }
            )
        if DISPATCH_PROSE.search(text) and not BUDGET_PHRASE.search(text):
            findings.append(
                {
                    "type": "dispatch-loop-missing-budget",
                    "section": label,
                    "evidence": "agent-dispatch loop without a budget phrase in the same section",
                }
            )
    return findings


def detect_elements(
    description: str,
    body: str,
    sections: list[tuple[str, str]],
    provenance: dict,
) -> list[dict]:
    def grep(pattern: str, text: str) -> bool:
        return re.search(pattern, text, re.I) is not None

    named_loop = False
    for _, text in sections:
        if LOOP_PROSE.search(text) and STOP_CONDITION.search(text):
            named_loop = True
            break

    anti_pattern_paired = False
    for _, text in sections:
        if grep(r"\b(anti-pattern|avoid|never|don'?t|do not)\b", text) and grep(
            r"\b(instead|corrective|rather than|replace with)\b", text
        ):
            anti_pattern_paired = True
            break

    fenced = re.findall(r"```([a-zA-Z]*)\n(.*?)```", body, re.S)
    runnable = any(
        lang.lower() in ("bash", "sh", "shell", "console", "zsh")
        or re.search(r"(?m)^\s*(bash|python3|ao|sh)\s+\S", code)
        for lang, code in fenced
    )

    router = grep(r"(?m)^#{1,6}\s.*\b(modes|routing|router)\b", body) or grep(
        r"(?m)^\|[^\n]*\b(mode|trigger)\b[^\n]*\|", body
    )

    checks = [
        (
            "causal-insight-line",
            grep(r"(insight:|\*\*why:?\*\*|\bbecause\b|why this works)", body),
            "a line stating the causal mechanism (Insight:/Why:/because)",
        ),
        (
            "named-failure-mode",
            grep(r"(failure mode|fails when|failure behavior|known failure)", body),
            "a named failure mode or failure-behavior section",
        ),
        (
            "frozen-prompts",
            grep(r"(copy-paste-only|copy paste only|frozen prompt|verbatim prompt)", body),
            "a prompt block marked copy-paste-only/frozen/verbatim",
        ),
        (
            "named-loop-stop-condition",
            named_loop,
            "loop prose with a checkable stop-condition phrase in the same section",
        ),
        (
            "quantified-rules",
            grep(
                r"(at most \d|at least \d|no more than \d|within \d|max(imum)? (of )?\d"
                r"|<=\s?\d|>=\s?\d|\b\d+ (lines|files|attempts|iterations|passes|seconds|minutes|checks|bullets)\b)",
                body,
            ),
            "a rule with a number and unit or comparator",
        ),
        (
            "negative-space",
            grep(
                r"(non-goal|not for\b|not ideal for|do not use|not when|out of scope|does not\b|never\b)",
                body,
            ),
            "explicit negative space (non-goals / not-for)",
        ),
        (
            "anti-pattern-with-corrective",
            anti_pattern_paired,
            "an anti-pattern paired with a corrective (instead/corrective) in the same section",
        ),
        (
            "provenance-citation",
            provenance["citations"] > 0 and provenance["resolved"] > 0,
            "at least one resolvable repo-path or .agents/ao digest citation",
        ),
        (
            "measurable-done",
            grep(
                r"(done when|complete when|exit (code )?0|exits? 0\b|exits? nonzero|passes when|validator command)",
                body,
            ),
            "a machine-checkable done signal (exit code / done-when phrase)",
        ),
        (
            "router-shape",
            router,
            "a modes/routing table or heading mapping triggers to entry points",
        ),
        (
            "trigger-rich-description",
            grep(r"(triggers:|use when)", description or ""),
            "frontmatter description with Triggers:/Use when phrases",
        ),
        (
            "runnable-commands",
            runnable,
            "a fenced block with runnable commands",
        ),
    ]

    return [
        {
            "id": element_id,
            "present": bool(present),
            "evidence": ("found: " if present else "missing: ") + what,
        }
        for element_id, present, what in checks
    ]


def craft_report(skill_dir: Path, repo_root: Path) -> dict:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        raise SystemExit(f"SKILL.md not found: {skill_md}")
    raw = skill_md.read_text(encoding="utf-8")
    text = strip_html_comments(raw)
    fm, body = frontmatter_and_body(text)
    sections = split_sections(body)

    provenance = check_provenance(text, repo_root, skill_dir)
    loop_findings = check_loop_safety(sections)
    elements = detect_elements(str(fm.get("description") or ""), body, sections, provenance)

    score = sum(1 for element in elements if element["present"])
    missing = [element["id"] for element in elements if not element["present"]]
    summary = f"craft {score}/{MAX_SCORE}"
    if missing:
        summary += "; missing: " + ", ".join(missing)

    return {
        "score": score,
        "max": MAX_SCORE,
        "advisory": True,
        "missing": missing,
        "elements": elements,
        "provenance": provenance,
        "loop_safety": {"advisory": True, "findings": loop_findings},
        "summary": summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_path")
    parser.add_argument(
        "--audit-block",
        action="store_true",
        help="Emit the advisory craft block embedded by audit.sh (same JSON as default).",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repo root for provenance resolution (default: this script's repo).",
    )
    args = parser.parse_args()

    script_repo = Path(__file__).resolve().parents[3]
    repo_root = Path(args.repo_root).resolve() if args.repo_root else script_repo
    report = craft_report(Path(args.skill_path).expanduser().resolve(), repo_root)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
