#!/usr/bin/env python3
"""Registry consistency lint.

Enforces the repo's three-places rule (CLAUDE.md): a skill's modes and agent
counts must agree across SKILL.md, MODE_REGISTRY.md, and the filesystem.

Checks:
  R1  every skill directory with a SKILL.md has a section in MODE_REGISTRY.md
  R2  mode names in SKILL.md's Modes table == mode names in its registry section
  R3  the registry section's declared "(N modes)" matches its table row count
  R4  SKILL.md's "Agent Team (N)" matches the number of files in agents/
  R5  the registry totals line (modes / skills / agents) matches computed sums

Usage: python3 scripts/check_registry_consistency.py [repo_root]
Exit codes: 0 = consistent · 1 = inconsistencies · 2 = error
"""

import re
import sys
from pathlib import Path

MODE_ROW = re.compile(r"^\|\s*`([a-z][a-z0-9-]*)`\s*\|")
REGISTRY_ROW = re.compile(r"^\|\s*([a-z][a-z0-9-]*)\s*\|")
REGISTRY_SECTION = re.compile(r"^##\s+([a-z][a-z0-9-]*)\s+\((\d+)\s+modes\)")
AGENT_TEAM = re.compile(r"^##\s+Agent Team\s+\((\d+)\)")
TOTALS = re.compile(r"\*\*Total:\s*(\d+)\s+modes\s+across\s+(\d+)\s+skills.*?,\s*(\d+)\s+agents\.\*\*")
TABLE_HEADER_CELLS = {"mode", "command", "purpose", "trigger-intent"}


def skill_modes(skill_md):
    """Mode names from the SKILL.md Modes table (backticked first cells, no underscores)."""
    modes = []
    for line in skill_md.read_text(encoding="utf-8").splitlines():
        m = MODE_ROW.match(line)
        if m and "_" not in m.group(1):
            modes.append(m.group(1))
    return modes


def skill_agent_count(skill_md):
    for line in skill_md.read_text(encoding="utf-8").splitlines():
        m = AGENT_TEAM.match(line)
        if m:
            return int(m.group(1))
    return None


def registry_sections(registry_path):
    """{skill: (declared_count, [modes])} from MODE_REGISTRY.md."""
    sections, current = {}, None
    for line in registry_path.read_text(encoding="utf-8").splitlines():
        sec = REGISTRY_SECTION.match(line)
        if sec:
            current = sec.group(1)
            sections[current] = (int(sec.group(2)), [])
            continue
        if line.startswith("## ") or line.startswith("# "):
            current = None
            continue
        if current:
            row = REGISTRY_ROW.match(line)
            if row and row.group(1) not in TABLE_HEADER_CELLS:
                sections[current][1].append(row.group(1))
    return sections


def main(argv=None):
    root = Path(argv[0]) if argv else Path(__file__).resolve().parent.parent
    registry_path = root / "MODE_REGISTRY.md"
    if not registry_path.exists():
        print("error: MODE_REGISTRY.md not found", file=sys.stderr)
        return 2

    problems = []
    registry = registry_sections(registry_path)

    skill_dirs = sorted(d for d in root.iterdir()
                        if d.is_dir() and (d / "SKILL.md").exists())

    total_modes = total_agents = 0
    for d in skill_dirs:
        name = d.name
        modes = skill_modes(d / "SKILL.md")
        total_modes += len(modes)

        # R1 / R2 / R3
        if name not in registry:
            problems.append(f"R1: {name} has no section in MODE_REGISTRY.md")
        else:
            declared, reg_modes = registry[name]
            if set(modes) != set(reg_modes):
                only_skill = sorted(set(modes) - set(reg_modes))
                only_reg = sorted(set(reg_modes) - set(modes))
                problems.append(
                    f"R2: {name} mode mismatch — only in SKILL.md: {only_skill or '—'}; "
                    f"only in registry: {only_reg or '—'}")
            if declared != len(reg_modes):
                problems.append(
                    f"R3: {name} registry header declares {declared} modes, table has {len(reg_modes)}")

        # R4
        agents_dir = d / "agents"
        n_files = len(list(agents_dir.glob("*.md"))) if agents_dir.exists() else 0
        total_agents += n_files
        declared_agents = skill_agent_count(d / "SKILL.md")
        if declared_agents is not None and declared_agents != n_files:
            problems.append(
                f"R4: {name} SKILL.md declares Agent Team ({declared_agents}), "
                f"agents/ has {n_files} files")

    # orphan registry sections
    skill_names = {d.name for d in skill_dirs}
    for name in registry:
        if name not in skill_names:
            problems.append(f"R1: registry section '{name}' has no skill directory")

    # R5 totals
    m = TOTALS.search(registry_path.read_text(encoding="utf-8"))
    if not m:
        problems.append("R5: totals line not found in MODE_REGISTRY.md")
    else:
        t_modes, t_skills, t_agents = (int(x) for x in m.groups())
        if t_modes != total_modes:
            problems.append(f"R5: totals line says {t_modes} modes, computed {total_modes}")
        if t_skills != len(skill_dirs):
            problems.append(f"R5: totals line says {t_skills} skills, found {len(skill_dirs)}")
        if t_agents != total_agents:
            problems.append(f"R5: totals line says {t_agents} agents, counted {total_agents}")

    # R6-R9: JSON manifests + ARCHITECTURE version/counts (the drift we kept hitting by hand)
    check_manifests_and_docs(root, total_modes, len(skill_dirs), total_agents, problems)

    for p in problems:
        print(p)
    print(f"{'INCONSISTENT' if problems else 'CONSISTENT'} — "
          f"{len(skill_dirs)} skills, {total_modes} modes, {total_agents} agents")
    return 1 if problems else 0


def _counts_in(text):
    """Extract (skills, modes, agents) counts from a description string, any order."""
    s = re.search(r"(\d+)\s+skills", text)
    m = re.search(r"(\d+)\s+modes", text)
    a = re.search(r"(\d+)[\s-]+agent", text)
    return (int(s.group(1)) if s else None,
            int(m.group(1)) if m else None,
            int(a.group(1)) if a else None)


def check_manifests_and_docs(root, modes, skills, agents, problems):
    """R6: plugin/marketplace versions agree. R7/R8: their description counts match
    the filesystem. R9: docs/ARCHITECTURE.md version header matches plugin.json."""
    import json as _json
    plugin_p = root / ".claude-plugin" / "plugin.json"
    market_p = root / ".claude-plugin" / "marketplace.json"
    arch_p = root / "docs" / "ARCHITECTURE.md"

    plugin_ver = None
    if plugin_p.exists():
        plugin = _json.loads(plugin_p.read_text(encoding="utf-8"))
        plugin_ver = plugin.get("version")
        s, m, a = _counts_in(plugin.get("description", ""))
        for label, got, want in (("skills", s, skills), ("modes", m, modes), ("agents", a, agents)):
            if got is not None and got != want:
                problems.append(f"R7: plugin.json description says {got} {label}, filesystem has {want}")
    if market_p.exists():
        market = _json.loads(market_p.read_text(encoding="utf-8"))
        mver = market.get("plugins", [{}])[0].get("version")
        if plugin_ver and mver and mver != plugin_ver:
            problems.append(f"R6: marketplace.json version {mver} != plugin.json version {plugin_ver}")
        for p in market.get("plugins", []):
            s, m, a = _counts_in(p.get("description", ""))
            for label, got, want in (("skills", s, skills), ("modes", m, modes)):
                if got is not None and got != want:
                    problems.append(f"R8: marketplace.json says {got} {label}, filesystem has {want}")
    if arch_p.exists() and plugin_ver:
        head = arch_p.read_text(encoding="utf-8").splitlines()[0]
        vm = re.search(r"v(\d+\.\d+\.\d+)", head)
        if vm and vm.group(1) != plugin_ver:
            problems.append(f"R9: ARCHITECTURE.md header v{vm.group(1)} != plugin.json version {plugin_ver}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
