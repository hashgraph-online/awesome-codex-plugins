#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path.cwd()
SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = SKILL_DIR / "references" / "templates"

IGNORED_REPO_SCAN_PARTS = {
    ".agents",
    ".git",
    ".hg",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".svn",
    ".tmp",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "tmp",
    "venv",
    "vendor",
}


def _die(msg: str, code: int = 2) -> None:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(code)


def _run(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=check)


def _ensure_dirs(paths: list[Path]) -> None:
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


def _today_ymd() -> str:
    return _dt.date.today().isoformat()


def _slugify(s: str) -> str:
    out = []
    for ch in s.strip().lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in (" ", "-", "_", "/"):
            out.append("-")
    slug = "".join(out)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "product"


def _detect_docs_prefix_for_repo(analysis_root: Path) -> str:
    """
    Choose a sensible docs slug prefix for repos that do not use docs/features/.
    Returns a prefix with trailing slash.
    """
    candidates = [
        "docs/features/",
        "docs/code-map/",
        "docs/workflows/",
        "docs/levels/",
        "docs/",
    ]
    best = "docs/features/"
    best_count = -1
    for cand in candidates:
        base = analysis_root / cand.strip("/")
        if not base.exists() or not base.is_dir():
            continue
        count = 0
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in (".md", ".mdx"):
                count += 1
        if count > best_count:
            best = cand
            best_count = count
    if best_count >= 0:
        return best
    return "docs/features/"


def _detect_docs_prefix_from_paths(paths: list[str]) -> str:
    """
    Choose docs prefix from sitemap-style path inventory.
    """
    normalized: list[str] = []
    for raw in paths:
        p = raw.strip()
        if not p:
            continue
        if not p.startswith("/"):
            p = "/" + p
        normalized.append(p)

    if not normalized:
        return "docs/features/"

    candidates = [
        "docs/features/",
        "docs/code-map/",
        "docs/workflows/",
        "docs/levels/",
        "docs/",
    ]
    best = "docs/features/"
    best_count = -1
    for cand in candidates:
        prefix = "/" + cand.strip("/").rstrip("/")
        count = sum(1 for p in normalized if p == prefix or p.startswith(prefix + "/"))
        if count > best_count:
            best = cand
            best_count = count
    return best


def _render_template(src: Path, dst: Path, vars: dict[str, str]) -> None:
    text = src.read_text(encoding="utf-8")
    for k, v in vars.items():
        text = text.replace("{{" + k + "}}", v)
    dst.write_text(text, encoding="utf-8")


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def _should_skip_repo_scan_path(path: Path, repo_root: Path) -> bool:
    try:
        rel_parts = path.relative_to(repo_root).parts
    except ValueError:
        rel_parts = path.parts
    for part in rel_parts:
        if part in IGNORED_REPO_SCAN_PARTS:
            return True
    return False


def _extract_ts_backtick_const(src: Path, const_name: str) -> str | None:
    # Best-effort: extract `const <name> = `...`;` blocks (common for CLI help text).
    if not src.exists():
        return None
    text = _read_text(src)
    m = re.search(
        rf"\bconst\s+{re.escape(const_name)}\s*=\s*`([\s\S]*?)`;",
        text,
        flags=re.MULTILINE,
    )
    return m.group(1) if m else None


def _extract_ts_string_const(src: Path, const_name: str) -> str | None:
    if not src.exists():
        return None
    text = _read_text(src)
    m = re.search(rf"\b{re.escape(const_name)}\s*=\s*'([^']*)';", text)
    if m:
        return m.group(1)
    m = re.search(rf'\b{re.escape(const_name)}\s*=\s*"([^"]*)";', text)
    if m:
        return m.group(1)
    return None


def _extract_agents_from_registry_ts(registry_ts: Path) -> tuple[list[str], list[str]] | None:
    """
    Best-effort parser for agent keys + alias flags from a TS registry.
    Intended to resolve help text interpolations like `${agentKeys.join('|')}`.
    """
    if not registry_ts.exists():
        return None

    text = _read_text(registry_ts)
    start = text.find("export const agentDefinitions")
    if start < 0:
        return None
    tail = text[start:]

    # Limit to the agentDefinitions object body to reduce false matches.
    end = tail.find("} as const")
    if end > 0:
        tail = tail[:end]

    agent_keys: list[str] = []
    seen_keys: set[str] = set()

    for line in tail.splitlines():
        # Top-level agent keys in the registry are consistently 2-space indented. This avoids
        # accidentally matching nested object keys like `layout:` or `commands:`.
        m = re.match(r"^  (?:'([^']+)'|([A-Za-z0-9_-]+))\s*:\s*\{\s*$", line)
        if not m:
            continue
        key = (m.group(1) or m.group(2) or "").strip()
        if not key:
            continue
        if key not in seen_keys:
            agent_keys.append(key)
            seen_keys.add(key)

    alias_flags: set[str] = set()
    for m in re.finditer(r"aliasFlags:\s*\[([^\]]*)\]", tail, flags=re.MULTILINE):
        blob = m.group(1)
        for s in re.findall(r"'([^']+)'", blob):
            alias_flags.add(s)
        for s in re.findall(r"\"([^\"]+)\"", blob):
            alias_flags.add(s)

    return agent_keys, sorted(alias_flags)


def _find_node_cli_package(repo_root: Path, product_slug: str, product_name: str) -> dict[str, object] | None:
    # Detect Node CLI packages by locating a package.json with a "bin" field and matching name/bin key.
    product_name_lc = product_name.strip().lower()
    candidates: list[tuple[int, Path, dict[str, object]]] = []

    for pkg_json in sorted(repo_root.rglob("package.json")):
        if _should_skip_repo_scan_path(pkg_json, repo_root):
            continue
        try:
            data = json.loads(_read_text(pkg_json))
        except Exception:
            continue

        bin_field = data.get("bin")
        if not bin_field:
            continue

        name = str(data.get("name") or "")
        score = 0
        if name.lower() == product_slug or name.lower() == product_name_lc:
            score += 100

        # Normalize bin mapping.
        bin_map: dict[str, str] = {}
        if isinstance(bin_field, str):
            if name:
                bin_map[name] = bin_field
        elif isinstance(bin_field, dict):
            for k, v in bin_field.items():
                if isinstance(k, str) and isinstance(v, str):
                    bin_map[k] = v
        if product_slug in bin_map:
            score += 80
        if product_name_lc in (k.lower() for k in bin_map.keys()):
            score += 60

        # Prefer shallower packages when score ties (often the main package vs nested deps).
        depth = len(pkg_json.relative_to(repo_root).parts)
        score -= depth

        candidates.append((score, pkg_json, data))

    if not candidates:
        return None

    candidates.sort(key=lambda t: t[0], reverse=True)
    score, pkg_json, data = candidates[0]

    # Return a normalized payload for downstream rendering.
    bin_field = data.get("bin")
    bin_map: dict[str, str] = {}
    if isinstance(bin_field, str):
        name = str(data.get("name") or "")
        if name:
            bin_map[name] = bin_field
    elif isinstance(bin_field, dict):
        for k, v in bin_field.items():
            if isinstance(k, str) and isinstance(v, str):
                bin_map[k] = v

    return {
        "score": score,
        "package_json": str(pkg_json),
        "package_dir": str(pkg_json.parent),
        "name": str(data.get("name") or ""),
        "version": str(data.get("version") or ""),
        "bin": bin_map,
    }


def _find_python_cli(repo_root: Path) -> dict[str, object] | None:
    """Detect Python CLI packages via pyproject.toml or setup.cfg entry_points."""
    result: dict[str, object] = {"language": "python", "bin": {}, "framework": None, "entry_module": None}

    # Try pyproject.toml first (modern standard).
    for pyproject in sorted(repo_root.rglob("pyproject.toml")):
        if _should_skip_repo_scan_path(pyproject, repo_root):
            continue
        text = _read_text(pyproject)
        # [project.scripts] section (PEP 621).
        m = re.search(r'\[project\.scripts\]\s*\n((?:[^\[].+\n)*)', text)
        if m:
            for line in m.group(1).strip().splitlines():
                parts = line.split("=", 1)
                if len(parts) == 2:
                    name = parts[0].strip().strip('"').strip("'")
                    entry = parts[1].strip().strip('"').strip("'")
                    result["bin"][name] = entry  # type: ignore[index]
                    if not result["entry_module"]:
                        result["entry_module"] = entry.split(":")[0] if ":" in entry else entry
        # [tool.poetry.scripts] section.
        m2 = re.search(r'\[tool\.poetry\.scripts\]\s*\n((?:[^\[].+\n)*)', text)
        if m2:
            for line in m2.group(1).strip().splitlines():
                parts = line.split("=", 1)
                if len(parts) == 2:
                    name = parts[0].strip().strip('"').strip("'")
                    entry = parts[1].strip().strip('"').strip("'")
                    result["bin"][name] = entry  # type: ignore[index]
        if result["bin"]:
            break

    # Try setup.cfg if pyproject didn't find scripts.
    if not result["bin"]:
        for setup_cfg in sorted(repo_root.rglob("setup.cfg")):
            if _should_skip_repo_scan_path(setup_cfg, repo_root):
                continue
            text = _read_text(setup_cfg)
            m = re.search(r'\[options\.entry_points\]\s*\nconsole_scripts\s*=\s*\n((?:\s+.+\n)*)', text)
            if m:
                for line in m.group(1).strip().splitlines():
                    parts = line.strip().split("=", 1)
                    if len(parts) == 2:
                        result["bin"][parts[0].strip()] = parts[1].strip()  # type: ignore[index]
                if result["bin"]:
                    break

    if not result["bin"]:
        return None

    # Detect CLI framework via source scan (best-effort, cap file count).
    scanned = 0
    for py_file in sorted(repo_root.rglob("*.py")):
        if _should_skip_repo_scan_path(py_file, repo_root):
            continue
        scanned += 1
        if scanned > 200:
            break
        text = _read_text(py_file)
        if "@click.command" in text or "@click.group" in text:
            result["framework"] = "click"
            break
        if "typer.Typer" in text or "@app.command" in text:
            result["framework"] = "typer"
            break
        if "ArgumentParser(" in text and "add_argument" in text:
            result["framework"] = "argparse"

    return result


def _find_go_cli(repo_root: Path) -> dict[str, object] | None:
    """Detect Go CLI packages via go.mod + main.go + flag/cobra usage."""
    result: dict[str, object] = {"language": "go", "bin": {}, "framework": None, "module": None}

    # Find go.mod for module name.
    go_mod = repo_root / "go.mod"
    if not go_mod.exists():
        # Check one level deeper (monorepo).
        for gm in sorted(repo_root.rglob("go.mod")):
            if _should_skip_repo_scan_path(gm, repo_root):
                continue
            go_mod = gm
            break
    if go_mod.exists():
        text = _read_text(go_mod)
        m = re.search(r'^module\s+(.+)$', text, re.MULTILINE)
        if m:
            result["module"] = m.group(1).strip()

    # Find main.go files (entry points).
    main_files: list[Path] = []
    for mg in sorted(repo_root.rglob("main.go")):
        if _should_skip_repo_scan_path(mg, repo_root) or "testdata" in mg.parts:
            continue
        main_files.append(mg)

    if not main_files and not result["module"]:
        return None

    # Derive binary names from cmd/ pattern or root main.go.
    for mf in main_files:
        rel = mf.relative_to(repo_root)
        parts = rel.parts
        if len(parts) >= 3 and parts[-3] == "cmd":
            # cmd/<name>/main.go pattern.
            result["bin"][parts[-2]] = str(rel)  # type: ignore[index]
        elif len(parts) == 1:
            # Root main.go — use module basename or directory name.
            mod = str(result.get("module") or "")
            name = mod.rsplit("/", 1)[-1] if mod else repo_root.name
            result["bin"][name] = str(rel)  # type: ignore[index]

    if not result["bin"]:
        return None

    # Detect CLI framework (cobra vs stdlib flag).
    scanned = 0
    for go_file in sorted(repo_root.rglob("*.go")):
        if _should_skip_repo_scan_path(go_file, repo_root) or "testdata" in go_file.parts:
            continue
        scanned += 1
        if scanned > 200:
            break
        text = _read_text(go_file)
        if "cobra.Command" in text or '"github.com/spf13/cobra"' in text:
            result["framework"] = "cobra"
            break
        if "flag.String" in text or "flag.Bool" in text or "flag.Int" in text:
            result["framework"] = "flag"

    return result


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _render_placeholders(s: str, vars: dict[str, str]) -> str:
    out = s
    for k, v in vars.items():
        out = out.replace("{{" + k + "}}", v)
    return out


def _enrich_registry_with_binary_evidence(
    registry_yaml: Path,
    tmp_dir: Path,
    output_dir: Path,
    *,
    product_name: str,
    date: str,
) -> bool:
    """Enrich feature-registry.yaml with binary string evidence.

    Reads cli-commands.txt and binary strings to create evidence-backed groups.
    Also generates binary-symbols.txt in the output dir.
    Returns True if enrichment was applied.
    """
    commands_file = tmp_dir / "binary" / "cli-commands.txt"
    _strings_file = tmp_dir / "binary" / "strings.head.txt"
    _ba_file = tmp_dir / "binary" / "binary-analysis.md"

    # Generate binary-symbols.txt from strings
    full_strings = tmp_dir / "binary" / "strings.head.txt"
    symbols_out = output_dir / "binary-symbols.txt"
    if full_strings.exists() and not symbols_out.exists():
        shutil.copyfile(full_strings, symbols_out)

    # Gather command groups from cli-commands.txt
    cmd_groups: dict[str, list[str]] = {}
    if commands_file.exists():
        for line in commands_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            group = parts[0]
            cmd_groups.setdefault(group, []).append(line)

    if not cmd_groups:
        return False

    # Try to load the existing registry (manual parse, no yaml dep)
    reg: dict = {"groups": {}}
    try:
        text = registry_yaml.read_text(encoding="utf-8")
        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            if stripped.startswith("docs_features_prefix:"):
                reg["docs_features_prefix"] = stripped.split(":", 1)[1].strip().strip("'\"")
            elif stripped.startswith("docs_features:"):
                reg.setdefault("docs_features", [])
            elif raw_line.startswith("  - ") and "docs_features" in reg and "groups" not in text.split(raw_line)[0].rsplit("docs_features:", 1)[-1]:
                reg.setdefault("docs_features", []).append(stripped[2:].strip().strip("'\""))
        # Parse groups using the same logic as the validator
        cur = None
        in_groups = False
        in_anchors = False
        for raw_line in text.splitlines():
            line = raw_line.rstrip()
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if line == "groups:":
                in_groups = True
                continue
            if not in_groups:
                continue
            if line.startswith("  ") and not line.startswith("    ") and line.endswith(":"):
                name = line.strip()[:-1]
                cur = {"impl": None, "anchors": [], "notes": ""}
                reg["groups"][name] = cur
                in_anchors = False
                continue
            if cur is None:
                continue
            s = line.strip()
            if s.startswith("impl:"):
                cur["impl"] = s.split(":", 1)[1].strip()
            elif s.startswith("anchors:"):
                in_anchors = True
                if s.endswith("[]"):
                    cur["anchors"] = []
            elif in_anchors and s.startswith("- "):
                cur["anchors"].append(s[2:].strip().strip("'\""))
            elif s.startswith("notes:"):
                cur["notes"] = s.split(":", 1)[1].strip().strip("'\"")
    except Exception:
        return False

    groups = reg.get("groups", {})

    # Check if registry is already populated (has non-empty groups with notes)
    has_content = any(g.get("notes") for g in groups.values()) if groups else False
    if has_content:
        # Already enriched or populated — don't overwrite
        return False

    # Build new groups from binary command data
    new_groups: dict[str, dict] = {}
    for grp_name, cmds in sorted(cmd_groups.items()):
        slug = grp_name.replace("-", "_")
        subcmds = [c for c in cmds if c != grp_name]
        sub_str = ", ".join(subcmds) if subcmds else "no subcommands"
        new_groups[slug] = {
            "impl": "client",
            "anchors": ["binary-symbols.txt"],
            "notes": f"{grp_name} ({len(cmds)} commands: {sub_str})",
        }

    # Write registry in the manual format expected by validate_feature_registry.py
    lines: list[str] = []
    lines.append("schema_version: 1")
    lines.append(f"product_name: {product_name!r}")
    lines.append(f"generated_at: {date!r}")
    lines.append("evidence_source: 'binary --help + string extraction'")
    # Preserve docs_features_prefix if present
    dfp = reg.get("docs_features_prefix", "docs/features/")
    lines.append(f"docs_features_prefix: {dfp!r}")
    # Preserve docs_features list if present
    docs_feats = reg.get("docs_features", [])
    if docs_feats:
        lines.append("docs_features:")
        for df in docs_feats:
            lines.append(f"  - {df!r}")
    lines.append("groups:")
    for slug, grp in new_groups.items():
        lines.append(f"  {slug}:")
        lines.append(f"    impl: {grp['impl']}")
        lines.append("    anchors:")
        for a in grp["anchors"]:
            lines.append(f"      - {a}")
        lines.append(f"    notes: {grp['notes']!r}")

    registry_yaml.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def _write_binary_cli_surface_spec(
    output_dir: Path,
    tmp_dir: Path,
    *,
    product_name: str,
    date: str,
) -> bool:
    """Write spec-cli-surface.md from binary --help output or binary strings.

    Returns True if a spec was written.
    """
    help_tree = tmp_dir / "binary" / "cli-help-tree.txt"
    commands_file = tmp_dir / "binary" / "cli-commands.txt"
    strings_file = tmp_dir / "binary" / "strings.head.txt"

    lines: list[str] = []
    lines.append(f"# CLI Surface Spec: {product_name}")
    lines.append("")
    lines.append(f"- Date: {date}")
    lines.append("- Source: binary --help output" if help_tree.exists() else "- Source: binary string extraction")
    lines.append("")

    cmd_count = 0
    if commands_file.exists():
        cmds = [c.strip() for c in commands_file.read_text(encoding="utf-8").splitlines() if c.strip()]
        cmd_count = len(cmds)

    if help_tree.exists():
        tree_text = help_tree.read_text(encoding="utf-8")
        lines.append("## Command Count")
        lines.append("")
        lines.append(f"- **{cmd_count} commands** discovered via recursive `--help` execution")
        lines.append("")

        # Extract top-level commands and subcommands
        if commands_file.exists():
            top_level = sorted(set(c.split()[0] for c in cmds if c.strip()))
            lines.append("## Top-Level Commands")
            lines.append("")
            lines.append("| Command | Subcommands |")
            lines.append("|---------|-------------|")
            for top in top_level:
                subs = [c for c in cmds if c.startswith(top + " ") and c != top]
                sub_names = [c.split(maxsplit=1)[1] if " " in c else "" for c in subs]
                sub_str = ", ".join(f"`{s}`" for s in sub_names if s) if sub_names else "—"
                lines.append(f"| `{top}` | {sub_str} |")
            lines.append("")

        lines.append("## Full Help Tree")
        lines.append("")
        lines.append("```")
        # Truncate to avoid massive output
        tree_lines = tree_text.splitlines()
        if len(tree_lines) > 500:
            lines.extend(tree_lines[:500])
            lines.append(f"... ({len(tree_lines) - 500} more lines)")
        else:
            lines.extend(tree_lines)
        lines.append("```")
        lines.append("")
    elif strings_file.exists():
        # Fallback: extract command-like patterns from strings
        raw = strings_file.read_text(encoding="utf-8", errors="replace")
        usage_lines = [line.strip() for line in raw.splitlines() if "usage" in line.lower() or "Usage" in line]
        lines.append("## CLI Surface (from binary strings, best-effort)")
        lines.append("")
        if usage_lines:
            for u in usage_lines[:20]:
                lines.append(f"- `{u[:200]}`")
        else:
            lines.append("_No usage patterns found in binary strings._")
        lines.append("")
    else:
        return False

    out = output_dir / "spec-cli-surface.md"
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return True


def _write_cli_surface_spec(
    output_dir: Path,
    *,
    product_name: str,
    product_slug: str,
    date: str,
    analysis_root: Path,
) -> bool:
    """
    Return True if a CLI was detected and spec-cli-surface.md was written.

    Repo-mode only. This is best-effort and aims to capture a mechanically-verifiable contract:
    - entrypoints (package.json bin)
    - help/usage text (static extraction, with interpolation resolved when possible)
    - config/env surface
    """
    if not analysis_root.exists():
        return False

    node_cli = _find_node_cli_package(analysis_root, product_slug, product_name)
    python_cli = _find_python_cli(analysis_root) if not node_cli else None
    go_cli = _find_go_cli(analysis_root) if not node_cli and not python_cli else None

    if not node_cli and not python_cli and not go_cli:
        return False

    # If Python or Go CLI detected (non-Node), write a language-appropriate spec.
    if python_cli or go_cli:
        cli_info = python_cli or go_cli
        assert cli_info is not None
        out = output_dir / "spec-cli-surface.md"
        lines: list[str] = []
        lang = str(cli_info["language"]).capitalize()
        lines.append(f"# CLI Surface Spec: {product_name}")
        lines.append("")
        lines.append(f"- Date: {date}")
        lines.append(f"- Language: {lang}")
        lines.append(f"- Analysis root: `{analysis_root}`")
        if cli_info.get("framework"):
            lines.append(f"- Framework: {cli_info['framework']}")
        if cli_info.get("module"):
            lines.append(f"- Module: `{cli_info['module']}`")
        if cli_info.get("entry_module"):
            lines.append(f"- Entry module: `{cli_info['entry_module']}`")
        lines.append("")
        lines.append("## Entrypoints (Code-Proven)")
        lines.append("")
        bin_map = cli_info.get("bin") or {}
        if isinstance(bin_map, dict) and bin_map:
            for k in sorted(bin_map.keys()):
                lines.append(f"- `{k}` -> `{bin_map[k]}`")
        else:
            lines.append("- _No entrypoints extracted._")
        lines.append("")
        lines.append("## Notes For 1:1 Fidelity")
        lines.append("")
        lines.append("- Run `<binary> --help` to capture the full CLI contract as a golden test fixture.")
        if lang == "Python":
            lines.append("- For Click/Typer apps, consider `<binary> --help` per subcommand for full coverage.")
        elif lang == "Go":
            lines.append("- For Cobra apps, consider `<binary> help <subcommand>` for full coverage.")
        out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        return True

    out = output_dir / "spec-cli-surface.md"
    pkg_dir = Path(str(node_cli["package_dir"]))

    pkg_json_rel = Path(str(node_cli["package_json"])).relative_to(analysis_root).as_posix()
    src_index = pkg_dir / "src" / "index.ts"
    src_cli = pkg_dir / "src" / "cli.ts"
    src_store = pkg_dir / "src" / "cli" / "store.ts"
    src_agents = pkg_dir / "src" / "agents" / "registry.ts"

    help_text = _extract_ts_backtick_const(src_index, "helpText")
    config_file = _extract_ts_string_const(src_store, "CONFIG_FILE")

    # Resolve common interpolations in helpText for higher-fidelity output.
    if help_text and src_agents.exists():
        extracted = _extract_agents_from_registry_ts(src_agents)
        if extracted:
            agent_keys, alias_flags = extracted
            if agent_keys:
                help_text = help_text.replace("${agentKeys.join('|')}", "|".join(agent_keys))
            alias_line = ""
            if alias_flags:
                alias_line = f"  {' | '.join(alias_flags)}  Agent alias flags\n"
            help_text = help_text.replace("${agentAliasLine}", alias_line)

    # Env vars: scan the src tree for process.env.<NAME> patterns.
    env_vars: list[str] = []
    src_root = pkg_dir / "src"
    if src_root.exists():
        pat = re.compile(r"\bprocess\.env\.([A-Z][A-Z0-9_]*)\b")
        found = set()
        for p in sorted(src_root.rglob("*")):
            if not p.is_file() or p.suffix.lower() not in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"):
                continue
            for m in pat.finditer(_read_text(p)):
                found.add(m.group(1))
        env_vars = sorted(found)

    lines: list[str] = []
    lines.append(f"# CLI Surface Spec: {product_name}")
    lines.append("")
    lines.append(f"- Date: {date}")
    lines.append(f"- Analysis root: `{analysis_root}`")
    lines.append("")
    lines.append("## Entrypoints (Code-Proven)")
    lines.append("")
    lines.append(f"- Node package: `{pkg_dir.relative_to(analysis_root).as_posix()}`")
    lines.append(f"- package.json: `{pkg_json_rel}`")
    if node_cli.get("name"):
        lines.append(f"- package name: `{node_cli['name']}`")
    if node_cli.get("version"):
        lines.append(f"- version: `{node_cli['version']}`")
    lines.append("")
    lines.append("### Binaries")
    lines.append("")
    bin_map = node_cli.get("bin") or {}
    if isinstance(bin_map, dict) and bin_map:
        for k in sorted(bin_map.keys()):
            v = str(bin_map[k])
            lines.append(f"- `{k}` -> `{v}`")
    else:
        lines.append("- _No `bin` mapping extracted (unexpected)._")

    if src_cli.exists():
        lines.append("")
        lines.append("### Source Entry (Heuristic)")
        lines.append("")
        lines.append(f"- `{src_cli.relative_to(analysis_root).as_posix()}` (node shebang entry; typically calls `runCli`)")

    lines.append("")
    lines.append("## Usage / Help (Code-Proven Where Possible)")
    lines.append("")
    if help_text:
        lines.append("```text")
        lines.append(help_text.rstrip("\n"))
        lines.append("```")
        lines.append("")
        lines.append("Evidence:")
        lines.append(f"- `{src_index.relative_to(analysis_root).as_posix()}` (`helpText`)")
    else:
        lines.append("- _Help text not extracted (pattern not found)._")
        lines.append("Evidence:")
        lines.append(f"- `{src_index.relative_to(analysis_root).as_posix()}`")

    lines.append("")
    lines.append("## Config / Env (Code-Proven Where Possible)")
    lines.append("")
    wrote_any = False
    if config_file:
        lines.append(f"- User config file: `{config_file}` (loaded from CWD).")
        lines.append(f"  Evidence: `{src_store.relative_to(analysis_root).as_posix()}`")
        wrote_any = True
    if env_vars:
        lines.append(f"- Environment variables: `{', '.join(env_vars)}`")
        lines.append(f"  Evidence: scan of `{src_root.relative_to(analysis_root).as_posix()}` for `process.env.<NAME>`.")
        wrote_any = True
    if not wrote_any:
        lines.append("- _No config/env surface extracted._")

    lines.append("")
    lines.append("## Notes For 1:1 Fidelity")
    lines.append("")
    lines.append("- Treat `--help` output as the CLI contract; include it as a golden test fixture for regressions.")
    lines.append("- If the repo does not ship built artifacts (ex: `dist/`), building may be required to execute the CLI directly.")

    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return True


def _write_artifact_surface_spec(
    output_dir: Path,
    *,
    product_name: str,
    product_slug: str,
    date: str,
    analysis_root: Path,
) -> None:
    """
    Higher-fidelity extraction of "what the product writes/installs" for template-driven CLIs.

    Emits:
    - spec-artifact-surface.md (human summary)
    - artifact-registry.json (machine-usable: manifests + template file hashes)
    """
    out_md = output_dir / "spec-artifact-surface.md"
    out_json = output_dir / "artifact-registry.json"

    if not analysis_root.exists():
        out_md.write_text(
            f"# Artifact Surface Spec: {product_name}\n\n- Date: {date}\n\n- _No repo content available to analyze._\n",
            encoding="utf-8",
        )
        return

    node_cli = _find_node_cli_package(analysis_root, product_slug, product_name)
    if not node_cli:
        out_md.write_text(
            f"# Artifact Surface Spec: {product_name}\n\n- Date: {date}\n\n- _No Node CLI package detected; artifact extraction not implemented for this repo._\n",
            encoding="utf-8",
        )
        return

    pkg_dir = Path(str(node_cli["package_dir"]))
    manifests_dir = pkg_dir / "templates" / "manifests"
    if not manifests_dir.exists():
        out_md.write_text(
            f"# Artifact Surface Spec: {product_name}\n\n- Date: {date}\n\n"
            f"- _No `templates/manifests/` directory found under `{pkg_dir.relative_to(analysis_root).as_posix()}`._\n",
            encoding="utf-8",
        )
        return

    manifest_files = sorted(manifests_dir.glob("*.json"))
    manifests: list[dict[str, object]] = []
    resolved_sources: list[dict[str, object]] = []

    for mf in manifest_files:
        try:
            data = json.loads(_read_text(mf))
        except Exception:
            continue

        agent = None
        artifacts = data.get("artifacts") if isinstance(data, dict) else None
        if isinstance(artifacts, list):
            for a in artifacts:
                if isinstance(a, dict):
                    when = a.get("when")
                    if isinstance(when, dict) and isinstance(when.get("agent"), str):
                        agent = when.get("agent")
                        break

        manifests.append(
            {
                "path": mf.relative_to(analysis_root).as_posix(),
                "agent": agent,
                "raw": data,
            }
        )

        # Build resolved source inventory (what files are copied from templates).
        if not isinstance(artifacts, list):
            continue

        placeholder_vars = {"AGENT": agent} if isinstance(agent, str) else {}
        for a in artifacts:
            if not isinstance(a, dict):
                continue
            source = a.get("source")
            if not isinstance(source, dict):
                continue
            stype = source.get("type")
            if stype == "templateDir":
                from_dir = source.get("fromDir")
                if not isinstance(from_dir, str):
                    continue
                from_dir_res = _render_placeholders(from_dir, placeholder_vars) if placeholder_vars else from_dir
                abs_from = pkg_dir / from_dir_res
                if abs_from.exists() and abs_from.is_dir():
                    for fp in sorted(abs_from.rglob("*")):
                        if not fp.is_file():
                            continue
                        resolved_sources.append(
                            {
                                "manifest": mf.relative_to(analysis_root).as_posix(),
                                "artifact_id": a.get("id"),
                                "source_type": "templateDir",
                                "from": from_dir_res,
                                "file": fp.relative_to(pkg_dir).as_posix(),
                                "sha256": _sha256_file(fp),
                            }
                        )
            elif stype == "templateFile":
                from_file = source.get("from")
                if not isinstance(from_file, str):
                    continue
                from_file_res = _render_placeholders(from_file, placeholder_vars) if placeholder_vars else from_file
                abs_from = pkg_dir / from_file_res
                if abs_from.exists() and abs_from.is_file():
                    resolved_sources.append(
                        {
                            "manifest": mf.relative_to(analysis_root).as_posix(),
                            "artifact_id": a.get("id"),
                            "source_type": "templateFile",
                            "from": from_file_res,
                            "file": abs_from.relative_to(pkg_dir).as_posix(),
                            "sha256": _sha256_file(abs_from),
                        }
                    )

    out_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "product_name": product_name,
                "generated_at": date,
                "analysis_root": str(analysis_root),
                "node_package_dir": pkg_dir.relative_to(analysis_root).as_posix(),
                "manifests": manifests,
                "resolved_template_files": resolved_sources,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    lines: list[str] = []
    lines.append(f"# Artifact Surface Spec: {product_name}")
    lines.append("")
    lines.append(f"- Date: {date}")
    lines.append(f"- Analysis root: `{analysis_root}`")
    lines.append(f"- Node package: `{pkg_dir.relative_to(analysis_root).as_posix()}`")
    lines.append(f"- Manifests dir: `{manifests_dir.relative_to(analysis_root).as_posix()}`")
    lines.append(f"- Machine registry: `{out_json.relative_to(output_dir).as_posix()}`")
    lines.append("")
    lines.append("## Manifest Inventory (Code-Proven)")
    lines.append("")
    if manifest_files:
        for mf in manifest_files:
            rel = mf.relative_to(analysis_root).as_posix()
            agent = None
            for m in manifests:
                if m.get("path") == rel:
                    agent = m.get("agent")
                    break
            agent_note = f" (agent={agent})" if agent else ""
            lines.append(f"- `{rel}`{agent_note}")
    else:
        lines.append("- _No manifest JSON files found._")

    lines.append("")
    lines.append("## Template Source File Inventory (Hashed)")
    lines.append("")
    lines.append(f"- Files hashed: `{len(resolved_sources)}`")
    lines.append("- Use `artifact-registry.json` as the source of truth for 1:1 template content equivalence.")

    out_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _get_upstream_commit(analysis_root: Path) -> str | None:
    """Return the HEAD commit SHA if analysis_root is a git repo, else None."""
    git_dir = analysis_root / ".git"
    if not git_dir.exists():
        return None
    try:
        sha = subprocess.check_output(
            ["git", "-C", str(analysis_root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        return sha if sha else None
    except Exception:
        return None


def _collect_env_vars_with_evidence(
    analysis_root: Path,
) -> list[dict[str, object]]:
    """
    Scan source files for environment variable references and return a sorted list
    with per-var file evidence.  Covers:
      - TypeScript/JavaScript: process.env.VAR_NAME
      - Python: os.environ['VAR'] / os.environ.get('VAR') / os.getenv('VAR')
      - Go: os.Getenv("VAR") / os.LookupEnv("VAR")
      - Shell: $VAR_NAME (upper-snake only, cap at 300 files)
    """
    var_files: dict[str, set[str]] = {}

    patterns: list[tuple[re.Pattern[str], set[str]]] = [
        (re.compile(r"\bprocess\.env\.([A-Z][A-Z0-9_]+)\b"), {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}),
        (re.compile(r"""os\.environ(?:\.get)?\s*\(\s*['"]([A-Z][A-Z0-9_]+)['"]\s*\)"""), {".py"}),
        (re.compile(r"""\bos\.getenv\s*\(\s*['"]([A-Z][A-Z0-9_]+)['"]\s*\)"""), {".py"}),
        (re.compile(r"""\bos\.(?:Getenv|LookupEnv)\s*\(\s*"([A-Z][A-Z0-9_]+)"\s*\)"""), {".go"}),
        (re.compile(r'\$\{?([A-Z][A-Z0-9_]{2,})\}?'), {".sh", ".bash", ".env", ".envrc"}),
    ]

    scanned = 0
    for p in sorted(analysis_root.rglob("*")):
        if not p.is_file():
            continue
        # Skip irrelevant dirs
        skip_dirs = {"node_modules", ".git", ".venv", "vendor", "testdata", "__pycache__"}
        if any(part in skip_dirs for part in p.parts):
            continue
        suffix = p.suffix.lower()
        matching_pats = [pat for pat, suffixes in patterns if suffix in suffixes]
        if not matching_pats:
            continue
        scanned += 1
        if scanned > 500:
            break
        try:
            text = _read_text(p)
        except Exception:
            continue
        rel = p.relative_to(analysis_root).as_posix()
        for pat in matching_pats:
            for m in pat.finditer(text):
                name = m.group(1)
                var_files.setdefault(name, set()).add(rel)

    result: list[dict[str, object]] = []
    for var_name in sorted(var_files.keys()):
        result.append({
            "name": var_name,
            "files": sorted(var_files[var_name]),
        })
    return result


def _collect_schema_files(analysis_root: Path) -> list[str]:
    """
    Return sorted relative paths of schema-like files in the repo.
    Matches: *.schema.json, *schema*.json, openapi*.json/yaml, swagger*.json/yaml,
             *.proto, *.avsc, *.thrift, graphql schema files.
    """
    schema_patterns = [
        "**/*.schema.json",
        "**/*schema*.json",
        "**/openapi*.json",
        "**/openapi*.yaml",
        "**/openapi*.yml",
        "**/swagger*.json",
        "**/swagger*.yaml",
        "**/swagger*.yml",
        "**/*.proto",
        "**/*.avsc",
        "**/*.thrift",
        "**/schema.graphql",
        "**/*.graphql",
    ]
    skip_dirs = {"node_modules", ".git", ".venv", "vendor", "testdata", "__pycache__"}
    found: set[str] = set()
    for pattern in schema_patterns:
        for p in analysis_root.glob(pattern):
            if not p.is_file():
                continue
            if any(part in skip_dirs for part in p.relative_to(analysis_root).parts):
                continue
            found.add(p.relative_to(analysis_root).as_posix())
    return sorted(found)


def _collect_config_files(analysis_root: Path) -> list[str]:
    """
    Return sorted relative paths of config files commonly read at runtime.
    Matches common config naming patterns at any depth (capped at 300 files).
    """
    config_name_patterns = re.compile(
        r"^(config|configuration|settings|\.env|app\.config|appsettings"
        r"|pyproject|setup\.cfg|cargo\.toml|go\.mod|tsconfig|jest\.config"
        r"|webpack\.config|vite\.config|babel\.config|eslint.*|\.eslintrc.*"
        r"|prettier.*|\.prettierrc.*)(\.(json|yaml|yml|toml|ini|cfg|js|ts|cjs|mjs))?$",
        re.IGNORECASE,
    )
    skip_dirs = {"node_modules", ".git", ".venv", "vendor", "testdata", "__pycache__"}
    found: set[str] = set()
    count = 0
    for p in sorted(analysis_root.rglob("*")):
        if not p.is_file():
            continue
        if any(part in skip_dirs for part in p.relative_to(analysis_root).parts):
            continue
        if config_name_patterns.match(p.name):
            found.add(p.relative_to(analysis_root).as_posix())
            count += 1
            if count >= 300:
                break
    return sorted(found)


def _write_repo_contract_json(
    output_dir: Path,
    analysis_root: Path,
    *,
    product_name: str,
    product_slug: str,
) -> Path:
    """
    Write a deterministic, machine-checkable contract JSON to
    output_dir/contracts/repo-contract.json.

    Contract includes:
    - upstream_commit (if analysis_root is a git repo)
    - cli surface: bin map, help text (static extraction), config file, env vars with file evidence
    - manifest inventory + template file hashes (from artifact-registry.json if present)
    - schema-like files
    - config files discovered in repo

    No absolute paths, no dates — stable across runs on the same commit.
    """
    contracts_dir = output_dir / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)
    out_path = contracts_dir / "repo-contract.json"

    contract: dict[str, object] = {
        "schema_version": 1,
        "product_name": product_name,
    }

    # upstream_commit
    upstream_commit = _get_upstream_commit(analysis_root)
    if upstream_commit:
        contract["upstream_commit"] = upstream_commit

    # --- CLI surface ---
    cli_surface: dict[str, object] = {}

    node_cli = _find_node_cli_package(analysis_root, product_slug, product_name)
    python_cli_info = _find_python_cli(analysis_root) if node_cli is None else None
    go_cli_info = _find_go_cli(analysis_root) if node_cli is None and python_cli_info is None else None

    if node_cli:
        pkg_dir = Path(str(node_cli["package_dir"]))
        # bin map with relative paths
        raw_bin = node_cli.get("bin") or {}
        bin_map: dict[str, str] = {}
        if isinstance(raw_bin, dict):
            for k, v in raw_bin.items():
                bin_map[k] = v
        cli_surface["language"] = "node"
        cli_surface["package_json"] = Path(str(node_cli["package_json"])).relative_to(analysis_root).as_posix()
        cli_surface["package_dir"] = pkg_dir.relative_to(analysis_root).as_posix()
        cli_surface["package_name"] = str(node_cli.get("name") or "")
        cli_surface["bin"] = {k: bin_map[k] for k in sorted(bin_map)}

        # Help text (static extraction)
        src_index = pkg_dir / "src" / "index.ts"
        src_agents = pkg_dir / "src" / "agents" / "registry.ts"
        help_text = _extract_ts_backtick_const(src_index, "helpText")
        if help_text and src_agents.exists():
            extracted = _extract_agents_from_registry_ts(src_agents)
            if extracted:
                agent_keys, alias_flags = extracted
                if agent_keys:
                    help_text = help_text.replace("${agentKeys.join('|')}", "|".join(agent_keys))
                alias_line = ""
                if alias_flags:
                    alias_line = f"  {' | '.join(alias_flags)}  Agent alias flags\n"
                help_text = help_text.replace("${agentAliasLine}", alias_line)
        if help_text is not None:
            cli_surface["help_text"] = help_text
            cli_surface["help_text_source"] = src_index.relative_to(analysis_root).as_posix() if src_index.exists() else None

        # Config file from store.ts
        src_store = pkg_dir / "src" / "cli" / "store.ts"
        config_file = _extract_ts_string_const(src_store, "CONFIG_FILE")
        if config_file:
            cli_surface["config_file"] = config_file
            cli_surface["config_file_source"] = src_store.relative_to(analysis_root).as_posix() if src_store.exists() else None

    elif python_cli_info:
        raw_bin_py = python_cli_info.get("bin") or {}
        cli_surface["language"] = "python"
        cli_surface["framework"] = python_cli_info.get("framework")
        cli_surface["entry_module"] = python_cli_info.get("entry_module")
        cli_surface["bin"] = {k: str(raw_bin_py[k]) for k in sorted(raw_bin_py)} if isinstance(raw_bin_py, dict) else {}

    elif go_cli_info:
        raw_bin_go = go_cli_info.get("bin") or {}
        cli_surface["language"] = "go"
        cli_surface["framework"] = go_cli_info.get("framework")
        cli_surface["module"] = go_cli_info.get("module")
        cli_surface["bin"] = {k: str(raw_bin_go[k]) for k in sorted(raw_bin_go)} if isinstance(raw_bin_go, dict) else {}

    contract["cli"] = cli_surface

    # --- Env vars with per-var file evidence ---
    contract["env_vars"] = _collect_env_vars_with_evidence(analysis_root)

    # --- Manifest inventory + template file hashes ---
    artifact_registry_path = output_dir / "artifact-registry.json"
    if artifact_registry_path.exists():
        try:
            artifact_data = json.loads(_read_text(artifact_registry_path))
            manifests_raw = artifact_data.get("manifests") or []
            template_files_raw = artifact_data.get("resolved_template_files") or []

            # Manifests: keep only path and agent (drop raw JSON for contract stability)
            manifests_clean: list[dict[str, object]] = []
            for m in manifests_raw:
                entry: dict[str, object] = {"path": m.get("path")}
                if m.get("agent"):
                    entry["agent"] = m["agent"]
                manifests_clean.append(entry)

            # Template files: keep path, sha256 (no absolute paths; already relative in artifact-registry)
            template_hashes: list[dict[str, object]] = []
            for tf in template_files_raw:
                template_hashes.append({
                    "file": tf.get("file"),
                    "manifest": tf.get("manifest"),
                    "sha256": tf.get("sha256"),
                    "source_type": tf.get("source_type"),
                })

            contract["manifests"] = sorted(manifests_clean, key=lambda x: str(x.get("path", "")))
            contract["template_files"] = sorted(template_hashes, key=lambda x: str(x.get("file", "")))
        except Exception:
            pass

    # --- Schema-like files ---
    contract["schema_files"] = _collect_schema_files(analysis_root)

    # --- Config files ---
    contract["config_files"] = _collect_config_files(analysis_root)

    out_path.write_text(
        json.dumps(contract, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return out_path


def _write_comparison_report(
    output_dir: Path,
    tmp_dir: Path,
    *,
    product_name: str,
    date: str,
) -> bool:
    """Write comparison-report.md contrasting binary vs repo analysis results.

    Returns True if a report was written.
    """
    # --- Command discovery ---
    binary_cmds: list[str] = []
    commands_file = tmp_dir / "binary" / "cli-commands.txt"
    if commands_file.exists():
        binary_cmds = [c.strip() for c in commands_file.read_text(encoding="utf-8").splitlines() if c.strip()]

    repo_cmds: list[str] = []
    repo_cli_spec = output_dir / "spec-cli-surface.md"
    if repo_cli_spec.exists():
        # Extract command names from the table rows (| `cmd` | ... |)
        text = repo_cli_spec.read_text(encoding="utf-8")
        for m in re.finditer(r"^\|\s*`([^`]+)`\s*\|", text, re.MULTILINE):
            cmd = m.group(1).strip()
            if cmd and cmd not in ("Command",):
                repo_cmds.append(cmd)

    binary_set = set(binary_cmds)
    repo_set = set(repo_cmds)
    only_binary = sorted(binary_set - repo_set)
    only_repo = sorted(repo_set - binary_set)
    delta = len(binary_cmds) - len(repo_cmds)

    # --- Registry groups ---
    binary_groups = 0
    _repo_groups = 0
    registry_yaml = output_dir / "feature-registry.yaml"
    if registry_yaml.exists():
        text = registry_yaml.read_text(encoding="utf-8")
        in_groups = False
        for raw_line in text.splitlines():
            line = raw_line.rstrip()
            if line == "groups:":
                in_groups = True
                continue
            if not in_groups:
                continue
            # Group entries are 2-space indented, end with ':'
            if line.startswith("  ") and not line.startswith("    ") and line.rstrip().endswith(":"):
                # Determine source from notes field
                binary_groups += 1

        # For the comparison we count total groups; binary-enriched have "binary-symbols.txt" anchor
        binary_enriched = 0
        repo_scaffold = 0
        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            if stripped == "- binary-symbols.txt":
                binary_enriched += 1

        # Groups without binary anchor are repo-scaffolded
        repo_scaffold = binary_groups - binary_enriched

    # --- Coverage percentage ---
    if repo_cmds:
        coverage_pct = round(len(binary_set & repo_set) / len(repo_set) * 100)
        coverage_line = f"Binary analysis found {coverage_pct}% of repo-discovered commands."
    elif binary_cmds:
        coverage_line = f"Binary analysis found {len(binary_cmds)} commands; repo analysis found none (no CLI detected in repo)."
    else:
        coverage_line = "Neither source discovered CLI commands."

    # --- Write report ---
    lines: list[str] = []
    lines.append(f"# Comparison Report: {product_name}")
    lines.append("")
    lines.append(f"**Date:** {date}")
    lines.append("**Mode:** both (binary + repo)")
    lines.append("")
    lines.append("## Command Discovery")
    lines.append("")
    lines.append("| Source | Commands Found |")
    lines.append("|--------|---------------|")
    lines.append(f"| Binary --help | {len(binary_cmds)} |")
    lines.append(f"| Repo analysis | {len(repo_cmds)} |")
    delta_str = f"+{delta}" if delta > 0 else str(delta)
    lines.append(f"| Delta | {delta_str} |")
    lines.append("")

    lines.append("## Commands Only in Binary")
    lines.append("")
    if only_binary:
        for cmd in only_binary:
            lines.append(f"- `{cmd}`")
    else:
        lines.append("_None._")
    lines.append("")

    lines.append("## Commands Only in Repo")
    lines.append("")
    if only_repo:
        for cmd in only_repo:
            lines.append(f"- `{cmd}`")
    else:
        lines.append("_None._")
    lines.append("")

    lines.append("## Registry Groups")
    lines.append("")
    lines.append("| Source | Groups |")
    lines.append("|--------|--------|")
    lines.append(f"| Binary enriched | {binary_enriched} |")
    lines.append(f"| Repo scaffold | {repo_scaffold} |")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(coverage_line)

    out = output_dir / "comparison-report.md"
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return True


def _write_wrapper_validate_feature_registry(output_dir: Path) -> None:
    skill_validate_path = (SKILL_DIR / "scripts" / "validate_feature_registry.py").resolve()
    wrapper = output_dir / "validate-feature-registry.py"
    wrapper.write_text(
        f"""#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_VALIDATE_CANDIDATES = [
    Path({str(skill_validate_path)!r}),
    Path(__file__).resolve().parents[3] / "skills" / "reverse-engineer" / "scripts" / "validate_feature_registry.py",
    Path(__file__).resolve().parents[2] / "skills" / "reverse-engineer" / "scripts" / "validate_feature_registry.py",
    Path.cwd() / "skills" / "reverse-engineer" / "scripts" / "validate_feature_registry.py",
]

def _resolve_validator() -> Path:
    for cand in SKILL_VALIDATE_CANDIDATES:
        if cand.exists():
            return cand
    raise FileNotFoundError("Could not locate validate_feature_registry.py")

def main() -> int:
    # Delegate to the canonical validator, but default paths to this output dir.
    args = sys.argv[1:]
    if not args:
        root_path = HERE / "analysis-root-path.txt"
        local_root = (root_path.read_text(encoding="utf-8").strip() if root_path.exists() else str(HERE / "analysis-root"))
        args = [
            "--feature-registry", str(HERE / "feature-registry.yaml"),
            "--docs-features", str(HERE / "docs-features.txt"),
            "--local-clone-dir", local_root,
        ]
    validator = _resolve_validator()
    p = subprocess.run([sys.executable, str(validator), *args])
    return p.returncode

if __name__ == "__main__":
    raise SystemExit(main())
""",
        encoding="utf-8",
    )
    wrapper.chmod(0o755)


def _copy_security_validators(output_dir: Path) -> None:
    sec_dir = output_dir / "security"
    _ensure_dirs([sec_dir])

    # Copy validator + secret scan + sbom generator so the audit folder is self-validating.
    for rel in [
        "scripts/security/validate_security_audit.sh",
        "scripts/security/scan_secrets.sh",
        "scripts/security/generate_sbom.sh",
    ]:
        src = SKILL_DIR / rel
        dst = sec_dir / Path(rel).name.replace("_", "-")
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        dst.chmod(0o755)


def main() -> int:
    ap = argparse.ArgumentParser(prog="reverse_engineer.py")
    ap.add_argument("product_name")
    ap.add_argument(
        "--authorized",
        action="store_true",
        help="Required for binary analysis. Confirms explicit written authorization to analyze the target binary.",
    )

    ap.add_argument("--docs-sitemap-url", default=None)
    ap.add_argument(
        "--docs-features-prefix",
        default="auto",
        help="Docs slug prefix, e.g. docs/features/. Use 'auto' to detect from repo/sitemap (default).",
    )
    ap.add_argument("--upstream-repo", default=None)
    ap.add_argument("--upstream-ref", default=None, help="Pin clone to a specific commit, tag, or branch. Records resolved SHA in clone-metadata.json.")
    ap.add_argument("--local-clone-dir", default=None)
    ap.add_argument("--output-dir", default=None)
    ap.add_argument("--mode", default="repo", choices=["repo", "binary", "both"])
    ap.add_argument("--binary-path", default=None)

    ap.add_argument("--security-audit", action="store_true")
    ap.add_argument("--sbom", action="store_true")
    ap.add_argument("--fuzz", action="store_true")
    ap.add_argument(
        "--materialize-archives",
        action="store_true",
        help="(Deprecated; now default in binary mode) Authorized-only: extract the best embedded ZIP candidate under local_clone_dir/extracted (do not commit).",
    )
    ap.add_argument(
        "--no-materialize-archives",
        action="store_true",
        help="Authorized-only: skip extracting embedded ZIP candidates (index-only).",
    )

    args = ap.parse_args()

    product_slug = _slugify(args.product_name)
    local_clone_dir = Path(args.local_clone_dir or f".tmp/{product_slug}").resolve()
    output_dir = Path(args.output_dir or f".agents/research/{product_slug}/").resolve()
    analysis_root = local_clone_dir

    tmp_dir = (REPO_ROOT / ".tmp" / f"reverse-engineer-{product_slug}").resolve()
    _ensure_dirs([local_clone_dir, output_dir, tmp_dir])

    docs_features_txt = output_dir / "docs-features.txt"
    effective_docs_prefix = args.docs_features_prefix

    # Acquire code (repo mode): shallow clone if requested.
    # NOTE: this must happen before docs inventory, otherwise docs/features extraction runs against an empty dir.
    if args.mode in ("repo", "both"):
        if args.upstream_repo and not (local_clone_dir / ".git").exists():
            clone_cmd = ["git", "clone"]
            if not args.upstream_ref:
                clone_cmd.append("--depth=1")
            clone_cmd.extend([args.upstream_repo, str(local_clone_dir)])
            _run(clone_cmd, check=True)
            if args.upstream_ref:
                _run(["git", "-C", str(local_clone_dir), "fetch", "--depth=1", "origin", args.upstream_ref], check=True)
                _run(["git", "-C", str(local_clone_dir), "checkout", "FETCH_HEAD"], check=True)
            # Record clone metadata for reproducibility.
            resolved_sha = subprocess.check_output(
                ["git", "-C", str(local_clone_dir), "rev-parse", "HEAD"], text=True,
            ).strip()
            clone_meta = {
                "upstream_repo": args.upstream_repo,
                "upstream_ref": args.upstream_ref,
                "resolved_commit": resolved_sha,
                "clone_date": _today_ymd(),
            }
            (output_dir / "clone-metadata.json").write_text(
                json.dumps(clone_meta, indent=2) + "\n", encoding="utf-8",
            )
            analysis_root = local_clone_dir

    # Determine an analysis root for repo mode.
    # Priority:
    # 1) local_clone_dir if it looks like a git checkout already
    # 2) git toplevel of the current working directory (if inside a repo)
    # 3) local_clone_dir (created)
    if args.mode in ("repo", "both"):
        if (local_clone_dir / ".git").exists():
            analysis_root = local_clone_dir
        else:
            try:
                top = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
                if top:
                    analysis_root = Path(top).resolve()
            except Exception:
                analysis_root = local_clone_dir

    # 1) Mechanical docs inventory (NO heavy crawling).
    if args.docs_sitemap_url:
        sitemap_xml = tmp_dir / f"{product_slug}-sitemap.xml"
        _run([sys.executable, str(SKILL_DIR / "scripts" / "fetch_url.py"), args.docs_sitemap_url, str(sitemap_xml)])

        paths_txt = tmp_dir / f"{product_slug}-sitemap-paths.txt"
        sitemap_paths = subprocess.check_output([str(SKILL_DIR / "scripts" / "extract_sitemap_paths.sh"), str(sitemap_xml)], text=True)
        paths_txt.write_text(sitemap_paths, encoding="utf-8")

        if args.docs_features_prefix in ("", "auto"):
            effective_docs_prefix = _detect_docs_prefix_from_paths(sitemap_paths.splitlines())

        docs_features = subprocess.check_output(
            [
                str(SKILL_DIR / "scripts" / "extract_docs_features.sh"),
                str(paths_txt),
                effective_docs_prefix,
            ],
            text=True,
        )
        docs_features_txt.write_text(docs_features, encoding="utf-8")
    else:
        # No sitemap: for repo mode, inventory docs/features from the repo tree; otherwise empty.
        if args.mode in ("repo", "both") and analysis_root.exists():
            if args.docs_features_prefix in ("", "auto"):
                effective_docs_prefix = _detect_docs_prefix_for_repo(analysis_root)
            # Backward-compatibility fallback for explicit old default.
            elif args.docs_features_prefix == "docs/features/":
                if not (analysis_root / "docs" / "features").exists() and (analysis_root / "docs").exists():
                    effective_docs_prefix = "docs/"

            prefix_dir = effective_docs_prefix.strip("/").rstrip("/")
            base = analysis_root / prefix_dir
            slugs: list[str] = []
            if base.exists() and base.is_dir():
                for p in sorted(base.rglob("*")):
                    if not p.is_file():
                        continue
                    if p.suffix.lower() not in (".md", ".mdx"):
                        continue
                    rel = p.relative_to(analysis_root).as_posix()
                    # Normalize to slug without extension to match sitemap-style slugs.
                    slugs.append(rel[: -len(p.suffix)])
            docs_features_txt.write_text("\n".join(slugs) + ("\n" if slugs else ""), encoding="utf-8")
        else:
            docs_features_txt.write_text("", encoding="utf-8")

    # 2) Binary analysis mode.
    if args.mode in ("binary", "both"):
        if not args.authorized:
            _die("--authorized is required for binary analysis (hard guardrail)")
        if not args.binary_path:
            _die("--binary-path is required when --mode includes binary")
        binary_path = Path(args.binary_path).expanduser().resolve()
        if not binary_path.exists():
            _die(f"binary not found: {binary_path}")

        _ensure_dirs([tmp_dir / "binary"])

        _run(
            [
                str(SKILL_DIR / "scripts" / "binary" / "analyze_binary.sh"),
                str(binary_path),
                str(tmp_dir / "binary"),
            ],
            check=True,
        )
        ba = tmp_dir / "binary" / "binary-analysis.md"
        if ba.exists():
            shutil.copyfile(ba, output_dir / "binary-analysis.md")

        # After analyze_binary.sh completes, run CLI help capture
        capture_script = SKILL_DIR / "scripts" / "binary" / "capture_cli_help.sh"
        if capture_script.exists():
            _run(
                ["bash", str(capture_script), str(binary_path), str(tmp_dir / "binary")],
                check=False,  # best-effort
            )
            # Copy results to output dir if they exist
            for fname in ("cli-help-tree.txt", "cli-commands.txt"):
                src = tmp_dir / "binary" / fname
                if src.exists():
                    shutil.copyfile(src, output_dir / fname)

        # Embedded archive inventory (index only by default; does not dump content into output_dir).
        _run(
            [
                sys.executable,
                str(SKILL_DIR / "scripts" / "binary" / "list_embedded_archives.py"),
                "--binary",
                str(binary_path),
                "--out-json",
                str(tmp_dir / "binary" / "embedded-archives.json"),
                "--out-index-md",
                str(output_dir / "binary-embedded-archives.md"),
            ],
            check=True,
        )

        # Default: materialize archives in binary mode (must-have workflow), unless explicitly disabled.
        if args.no_materialize_archives and args.materialize_archives:
            _die("flags conflict: --materialize-archives and --no-materialize-archives")

        if not args.no_materialize_archives:
            extract_root = local_clone_dir / "extracted"
            _ensure_dirs([extract_root])
            _run(
                [
                    sys.executable,
                    str(SKILL_DIR / "scripts" / "binary" / "extract_embedded_archives.py"),
                    "--binary",
                    str(binary_path),
                    "--out-dir",
                    str(extract_root),
                ],
                check=True,
            )
            primary = extract_root / "PRIMARY.txt"
            if primary.exists():
                analysis_root = Path(primary.read_text(encoding="utf-8").strip())

    # 4) Generate feature inventory (docs-first when available).
    inventory_md = output_dir / "feature-inventory.md"
    _run(
        [
            sys.executable,
            str(SKILL_DIR / "scripts" / "generate_feature_inventory_md.py"),
            "--product-name",
            args.product_name,
            "--docs-features",
            str(docs_features_txt),
            "--out",
            str(inventory_md),
        ],
        check=True,
    )

    # 5) Registry-first mapping.
    registry_yaml = output_dir / "feature-registry.yaml"
    _run(
        [
            sys.executable,
            str(SKILL_DIR / "scripts" / "scaffold_feature_registry.py"),
            "--product-name",
            args.product_name,
            "--docs-features-prefix",
            effective_docs_prefix,
            "--docs-features",
            str(docs_features_txt),
            "--out",
            str(registry_yaml),
        ],
        check=True,
    )

    # 5b) Enrich registry with binary evidence when available.
    if args.mode in ("binary", "both"):
        _enrich_registry_with_binary_evidence(
            registry_yaml,
            tmp_dir,
            output_dir,
            product_name=args.product_name,
            date=_today_ymd(),
        )

    catalog_md = output_dir / "feature-catalog.md"
    _run(
        [
            sys.executable,
            str(SKILL_DIR / "scripts" / "generate_feature_catalog_md.py"),
            "--registry",
            str(registry_yaml),
            "--out",
            str(catalog_md),
        ],
        check=True,
    )

    # 6) Specs (template render).
    vars = {"PRODUCT_NAME": args.product_name, "DATE": _today_ymd()}
    for tmpl, out_name in [
        ("spec-architecture.md.tmpl", "spec-architecture.md"),
        ("spec-code-map.md.tmpl", "spec-code-map.md"),
        ("spec-clone-vs-use.md.tmpl", "spec-clone-vs-use.md"),
        ("spec-clone-mvp.md.tmpl", "spec-clone-mvp.md"),
    ]:
        _render_template(TEMPLATES_DIR / tmpl, output_dir / out_name, vars)

    # CLI surface is optional; only write spec-cli-surface.md if a CLI is detected.
    wrote_cli = False
    if args.mode in ("repo", "both"):
        wrote_cli = _write_cli_surface_spec(
            output_dir,
            product_name=args.product_name,
            product_slug=product_slug,
            date=vars["DATE"],
            analysis_root=analysis_root,
        )

    if not wrote_cli and args.mode in ("binary", "both"):
        wrote_cli = _write_binary_cli_surface_spec(
            output_dir,
            tmp_dir,
            product_name=args.product_name,
            date=vars["DATE"],
        )

    if not wrote_cli:
        # Required behavior: omit the file, but leave an explicit note somewhere deterministic.
        (output_dir / "spec-code-map.md").write_text(
            (output_dir / "spec-code-map.md").read_text(encoding="utf-8")
            + "\n\n## CLI Surface\n\n_Omitted: no CLI surface detected (or mode did not include repo)._ \n",
            encoding="utf-8",
        )

    # Artifact surface: best-effort extraction of what the product writes/installs (high-fidelity cloning aid).
    if args.mode in ("repo", "both"):
        _write_artifact_surface_spec(
            output_dir,
            product_name=args.product_name,
            product_slug=product_slug,
            date=vars["DATE"],
            analysis_root=analysis_root,
        )

    # 6b) Deterministic repo-mode contract JSON (CLI/config/env + artifact I/O surface).
    if args.mode in ("repo", "both"):
        _write_repo_contract_json(
            output_dir,
            analysis_root,
            product_name=args.product_name,
            product_slug=product_slug,
        )

    # 6c) Comparison report (binary vs repo) when both sources are available.
    if args.mode == "both":
        _write_comparison_report(output_dir, tmp_dir, product_name=args.product_name, date=_today_ymd())

    # 7) Validation gate: produce a self-contained validator in the output dir and run it once.
    _write_wrapper_validate_feature_registry(output_dir)
    # Store analysis root pointer for validators (repo clone dir or a placeholder).
    (output_dir / "analysis-root").mkdir(exist_ok=True)
    (output_dir / "analysis-root-path.txt").write_text(str(analysis_root), encoding="utf-8")
    # Keep docs-features alongside outputs for deterministic validation.
    # (Already written as output_dir/docs-features.txt)
    _run(
        [
            sys.executable,
            str(SKILL_DIR / "scripts" / "validate_feature_registry.py"),
            "--feature-registry",
            str(registry_yaml),
            "--docs-features",
            str(docs_features_txt),
            "--local-clone-dir",
            str(analysis_root if analysis_root.exists() else output_dir / "analysis-root"),
        ],
        check=True,
    )

    # 8) Security audit artifacts + gates.
    if args.security_audit:
        sec_dir = output_dir / "security"
        _ensure_dirs([sec_dir])
        for name in [
            "threat-model.md.tmpl",
            "attack-surface.md.tmpl",
            "dataflow.md.tmpl",
            "crypto-review.md.tmpl",
            "authn-authz.md.tmpl",
            "findings.md.tmpl",
            "reproducibility.md.tmpl",
        ]:
            _render_template(TEMPLATES_DIR / "security" / name, sec_dir / name.replace(".tmpl", ""), vars)

        _copy_security_validators(output_dir)

        if args.sbom:
            _run([str(sec_dir / "generate-sbom.sh"), str(analysis_root), str(sec_dir)], check=False)

        # Run validation gate (includes secret scan over output_dir).
        _run([str(sec_dir / "validate-security-audit.sh"), str(output_dir), "--sbom" if args.sbom else "--no-sbom"], check=True)

    # 9) Reports (vibe-style + postmortem) + learning.
    council_dir = REPO_ROOT / ".agents" / "council"
    _ensure_dirs([council_dir])
    vibe_path = council_dir / f"{_today_ymd()}-vibe-{product_slug}.md"
    post_path = council_dir / f"{_today_ymd()}-postmortem-{product_slug}.md"

    _render_template(TEMPLATES_DIR / "vibe-report.md.tmpl", vibe_path, {**vars, "OUTPUT_DIR": str(output_dir)})
    _render_template(TEMPLATES_DIR / "postmortem.md.tmpl", post_path, {**vars, "OUTPUT_DIR": str(output_dir)})

    learning_path = REPO_ROOT / ".agents" / "learnings" / f"{_today_ymd()}-{product_slug}-reverse-engineer.md"
    if not learning_path.exists():
        learning_path.write_text(
            f"---\n"
            f"id: learn-{_today_ymd()}-{product_slug}-reverse-engineer\n"
            f"date: {_today_ymd()}\n"
            f"source_epic: reverse-engineer\n"
            f"tags:\n"
            f"  - reverse-engineer\n"
            f"  - evidence\n"
            f"  - analysis\n"
            f"---\n\n"
            f"# Learning: Separate documentary hints from proven product evidence\n\n"
            f"Reverse-engineering output should keep documentation, marketing pages, and control-plane descriptions in a provisional lane. "
            f"Features only become confirmed when the repo, binary, runtime trace, or CLI surface proves them directly. "
            f"Treating hosted or control-plane behavior as unknown until evidence exists prevents inflated feature registries, keeps downstream planning honest, "
            f"and makes later security or release decisions easier to defend.\n",
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
