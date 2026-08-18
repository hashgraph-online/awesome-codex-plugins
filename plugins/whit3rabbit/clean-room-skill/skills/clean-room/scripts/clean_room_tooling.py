"""Tool discovery helpers for clean-room source-index preflight."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
from typing import Any


COMMAND_TIMEOUT_SECONDS = 30
SKILL_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = Path(__file__).resolve().parents[3]
SKILL_TOOLS_DIR = SKILL_ROOT / "tools"
USER_TOOLS_DIR = Path.home() / ".cache" / "re-skills" / "clean-room-tools"
USER_NPM_PREFIX = USER_TOOLS_DIR / "npm"
PROJECT_TOOLS_ENV = "RE_SKILLS_TRUST_PROJECT_TOOLS"
SYSTEM_PATH_PREFIXES = (
    Path("/bin"),
    Path("/usr/bin"),
    Path("/usr/sbin"),
    Path("/sbin"),
    Path("/Library/Apple/usr/bin"),
)
USER_TOOLCHAIN_PATH_PREFIXES = (
    Path("/opt/homebrew"),
    Path("/usr/local"),
)

TOOL_ENV = {
    "ast-grep": "AST_GREP_BIN",
    "ctags": "CTAGS_BIN",
    "node": "NODE_BIN",
    "npm": "NPM_BIN",
    "scip": "SCIP_BIN",
    "sg": "SG_BIN",
    "universal-ctags": "UNIVERSAL_CTAGS_BIN",
}

BREW_HINTS = {
    "ast-grep": "Offer to run: brew install ast-grep",
    "ctags": "Offer to run: brew install universal-ctags",
    "node": "Offer to run: brew install node",
    "npm": "Offer to run: brew install node",
    "scip": "Install scip only when source-index export is explicitly needed.",
    "sg": "Offer to run: brew install ast-grep",
    "universal-ctags": "Offer to run: brew install universal-ctags",
}

LOCAL_HINTS = {
    "ast-grep": "Or run scripts/clean_room_tool_manager.py --install-local ast-grep --version <exact-version>.",
    "ctags": "Or place ctags under ~/.cache/re-skills/clean-room-tools/bin/ or set CTAGS_BIN.",
    "node": "Or place node under ~/.cache/re-skills/clean-room-tools/bin/ or set NODE_BIN.",
    "npm": "Or place npm under ~/.cache/re-skills/clean-room-tools/bin/ or set NPM_BIN.",
    "scip": "Or place scip under ~/.cache/re-skills/clean-room-tools/bin/ or set SCIP_BIN.",
    "sg": "Or place sg under ~/.cache/re-skills/clean-room-tools/bin/ or set SG_BIN.",
    "universal-ctags": "Or place universal-ctags under ~/.cache/re-skills/clean-room-tools/bin/ or set UNIVERSAL_CTAGS_BIN.",
}


@dataclass(frozen=True)
class ResolvedTool:
    path: Path
    source: str


def path_is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def project_tools_allowed(allow_project_tools: bool = False) -> bool:
    env_value = os.environ.get(PROJECT_TOOLS_ENV, "")
    return allow_project_tools or env_value.lower() in {"1", "true", "yes", "on"}


def trust_mode_name(allow_project_tools: bool = False) -> str:
    return "project-tools" if project_tools_allowed(allow_project_tools) else "system-and-user-toolchains"


def fact(status: str, value: Any = None, evidence: Any = None, note: str | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {"status": status, "value": value}
    if evidence is not None:
        item["evidence"] = evidence
    if note:
        item["note"] = note
    return item


def observed(value: Any, evidence: Any = None, note: str | None = None) -> dict[str, Any]:
    return fact("observed", value, evidence, note)


def unknown(note: str, value: Any = None) -> dict[str, Any]:
    return fact("unknown", value, note=note)


def error_fact(message: str, evidence: Any = None) -> dict[str, Any]:
    return fact("error", None, evidence=evidence, note=message)


def run_command(argv: list[str], timeout: int = COMMAND_TIMEOUT_SECONDS) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return error_fact(f"command timed out after {timeout} seconds", evidence=argv)
    except Exception as exc:
        return error_fact(str(exc), evidence=argv)

    return fact(
        "observed" if completed.returncode == 0 else "error",
        {
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        },
    )


def probe_command(argv: list[str], timeout: int = COMMAND_TIMEOUT_SECONDS) -> str | None:
    # Probes are optional discovery signals, so failures collapse to None.
    # Status and install commands use run_command so callers get structured error facts.
    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except Exception:
        return None
    if completed.returncode != 0:
        return None
    value = completed.stdout.strip()
    return value or None


def local_executable_candidates(name: str) -> list[tuple[Path, str]]:
    candidates: list[tuple[Path, str]] = []
    for root, source in [(USER_TOOLS_DIR, "user-cache"), (SKILL_TOOLS_DIR, "skill-local")]:
        candidates.extend(
            [
                (root / name, source),
                (root / "bin" / name, source),
                (root / name / "bin" / name, source),
                (root / "npm" / "node_modules" / ".bin" / name, source),
            ]
        )
    return candidates


def project_executable_candidates(name: str) -> list[tuple[Path, str]]:
    return [
        (Path.cwd() / ".local" / "bin" / name, "working-project-local"),
        (Path.cwd() / ".bin" / name, "working-project-bin"),
        (Path.cwd() / "node_modules" / ".bin" / name, "working-project-node-modules"),
        (SKILL_ROOT / "node_modules" / ".bin" / name, "skill-node-modules"),
        (PLUGIN_ROOT / "node_modules" / ".bin" / name, "plugin-local"),
    ]


def path_allowlist_candidates(name: str) -> list[tuple[Path, str]]:
    candidates: list[tuple[Path, str]] = []
    for raw_dir in os.environ.get("PATH", "").split(os.pathsep):
        if not raw_dir:
            continue
        directory = Path(raw_dir).expanduser()
        candidate = directory / name
        try:
            normalized_dir = directory.resolve(strict=False)
        except RuntimeError:
            normalized_dir = directory.absolute()
        if any(path_is_relative_to(normalized_dir, prefix) for prefix in SYSTEM_PATH_PREFIXES):
            candidates.append((candidate, "system-path"))
        elif any(path_is_relative_to(normalized_dir, prefix) for prefix in USER_TOOLCHAIN_PATH_PREFIXES):
            candidates.append((candidate, "user-toolchain-path"))
    return candidates


def source_allows_version_probe(source: str, allow_user_toolchain_probes: bool = False) -> bool:
    return source != "user-toolchain-path" or allow_user_toolchain_probes


def npm_path(
    command: list[str],
    allow_project_tools: bool = False,
    allow_user_toolchain_probes: bool = False,
) -> Path | None:
    npm = find_executable("npm", allow_project_tools, allow_user_toolchain_probes=allow_user_toolchain_probes)
    if npm is None:
        return None
    if not source_allows_version_probe(npm.source, allow_user_toolchain_probes):
        return None
    value = probe_command([npm.path.as_posix(), *command])
    if value is None:
        return None
    return Path(value).expanduser()


def executable_candidates(
    name: str,
    allow_project_tools: bool = False,
    probe_tools: bool = False,
    allow_user_toolchain_probes: bool = False,
) -> list[tuple[Path, str]]:
    candidates: list[tuple[Path, str]] = []
    env_name = TOOL_ENV.get(name)
    if env_name:
        env_value = os.environ.get(env_name)
        if env_value:
            candidates.append((Path(env_value), env_name))

    candidates.extend(local_executable_candidates(name))

    if project_tools_allowed(allow_project_tools):
        candidates.extend(project_executable_candidates(name))
        if probe_tools:
            prefix = npm_path(
                ["prefix"],
                allow_project_tools=False,
                allow_user_toolchain_probes=allow_user_toolchain_probes,
            )
            if prefix is not None:
                candidates.append((prefix / "node_modules" / ".bin" / name, "npm-prefix"))
            root = npm_path(
                ["root"],
                allow_project_tools=False,
                allow_user_toolchain_probes=allow_user_toolchain_probes,
            )
            if root is not None:
                candidates.append((root / ".bin" / name, "npm-prefix"))
            global_prefix = npm_path(
                ["prefix", "-g"],
                allow_project_tools=False,
                allow_user_toolchain_probes=allow_user_toolchain_probes,
            )
            if global_prefix is not None:
                candidates.append((global_prefix / "bin" / name, "npm-global"))

    candidates.extend(path_allowlist_candidates(name))
    return candidates


def find_executable(
    name: str,
    allow_project_tools: bool = False,
    probe_tools: bool = False,
    allow_user_toolchain_probes: bool = False,
) -> ResolvedTool | None:
    seen: set[Path] = set()
    for candidate, source in executable_candidates(
        name,
        allow_project_tools,
        probe_tools,
        allow_user_toolchain_probes,
    ):
        candidate = candidate.expanduser()
        try:
            normalized = candidate.resolve(strict=False)
        except RuntimeError:
            normalized = candidate.absolute()
        if normalized in seen:
            continue
        seen.add(normalized)
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return ResolvedTool(candidate.resolve(), source)
    return None


def checked_executable_locations(
    name: str,
    allow_project_tools: bool = False,
    probe_tools: bool = False,
) -> list[str]:
    locations: list[str] = []
    env_name = TOOL_ENV.get(name)
    if env_name:
        env_value = os.environ.get(env_name)
        locations.append(f"${env_name}" if not env_value else f"${env_name}={env_value}")
    locations.extend(path.as_posix() for path, _source in local_executable_candidates(name))
    if project_tools_allowed(allow_project_tools):
        locations.extend(path.as_posix() for path, _source in project_executable_candidates(name))
        locations.append("npm prefix/global bins" if probe_tools else "npm prefix/global bins require --probe-tools")
    locations.append("system and user toolchain PATH allowlist")
    return locations


def missing_tool_hint(name: str) -> str:
    brew = BREW_HINTS.get(name, f"Install {name} with Homebrew if available.")
    local = LOCAL_HINTS.get(name, f"Or place {name} under {USER_TOOLS_DIR.as_posix()} or set an explicit env var.")
    return f"{name} unavailable. {brew}. {local}"


def executable_status(
    name: str,
    version_args: list[str] | None = None,
    allow_project_tools: bool = False,
    probe_tools: bool = False,
    allow_user_toolchain_probes: bool = False,
) -> dict[str, Any]:
    resolved = find_executable(name, allow_project_tools, probe_tools, allow_user_toolchain_probes)
    if resolved is None:
        return unknown(
            missing_tool_hint(name),
            value={
                "checked_locations": checked_executable_locations(name, allow_project_tools, probe_tools),
                "brew_option": BREW_HINTS.get(name),
                "local_option": LOCAL_HINTS.get(name),
                "tool_trust_mode": trust_mode_name(allow_project_tools),
            },
        )
    if not probe_tools:
        return observed(
            {
                "path": resolved.path.as_posix(),
                "source": resolved.source,
                "version": unknown("not probed; pass --probe-tools to execute version commands"),
            }
        )
    if not source_allows_version_probe(resolved.source, allow_user_toolchain_probes):
        return observed(
            {
                "path": resolved.path.as_posix(),
                "source": resolved.source,
                "version": unknown(
                    "not probed; pass --allow-user-toolchain-probes with --probe-tools to execute "
                    "tools discovered under /opt/homebrew or /usr/local"
                ),
            }
        )
    argv = [resolved.path.as_posix(), *(version_args or ["--version"])]
    return observed(
        {
            "path": resolved.path.as_posix(),
            "source": resolved.source,
            "version": run_command(argv),
        }
    )


def node_resolver_roots(allow_project_tools: bool = False) -> list[Path]:
    roots = [
        USER_NPM_PREFIX,
        USER_TOOLS_DIR,
        SKILL_TOOLS_DIR,
    ]
    if project_tools_allowed(allow_project_tools):
        roots.extend([Path.cwd(), SKILL_ROOT, PLUGIN_ROOT])
    return roots


def tool_trust_mode(allow_project_tools: bool = False) -> dict[str, Any]:
    return observed(
        trust_mode_name(allow_project_tools),
        evidence={
            "explicit_allow_project_tools": bool(allow_project_tools),
            "env": PROJECT_TOOLS_ENV if os.environ.get(PROJECT_TOOLS_ENV) else None,
        },
    )


def dependency_report(
    allow_project_tools: bool = False,
    probe_tools: bool = False,
    allow_user_toolchain_probes: bool = False,
) -> dict[str, Any]:
    npm_prefix = (
        npm_path(["prefix"], allow_project_tools=False, allow_user_toolchain_probes=allow_user_toolchain_probes)
        if probe_tools and project_tools_allowed(allow_project_tools)
        else None
    )
    npm_root = (
        npm_path(["root"], allow_project_tools=False, allow_user_toolchain_probes=allow_user_toolchain_probes)
        if probe_tools and project_tools_allowed(allow_project_tools)
        else None
    )
    return {
        "external_tools_policy": observed(
            "Source-index preflight detects optional AST and indexing tools with filesystem checks by default. "
            "It executes version probes only when --probe-tools is set. Tools discovered under /opt/homebrew "
            "or /usr/local are kept stat-only unless --allow-user-toolchain-probes is also set. It does not "
            f"consider project-local executables unless --allow-working-project-tools or {PROJECT_TOOLS_ENV}=1 is set."
        ),
        "tool_trust_mode": tool_trust_mode(allow_project_tools),
        "tool_locations": observed(
            {
                "user_cache": USER_TOOLS_DIR.as_posix(),
                "user_npm_prefix": USER_NPM_PREFIX.as_posix(),
                "skill_local_tools": SKILL_TOOLS_DIR.as_posix(),
                "system_path_prefixes": [path.as_posix() for path in SYSTEM_PATH_PREFIXES],
                "user_toolchain_path_prefixes": [path.as_posix() for path in USER_TOOLCHAIN_PATH_PREFIXES],
                "project_local_candidates": [
                    ".local/bin",
                    ".bin",
                    "node_modules/.bin",
                ],
            }
        ),
        "tool_probe_mode": observed(
            "execute-version-with-user-toolchains"
            if probe_tools and allow_user_toolchain_probes
            else "execute-version-system-explicit"
            if probe_tools
            else "stat-only"
        ),
        "node": executable_status(
            "node",
            allow_project_tools=allow_project_tools,
            probe_tools=probe_tools,
            allow_user_toolchain_probes=allow_user_toolchain_probes,
        ),
        "npm": executable_status(
            "npm",
            allow_project_tools=allow_project_tools,
            probe_tools=probe_tools,
            allow_user_toolchain_probes=allow_user_toolchain_probes,
        ),
        "ast_grep": executable_status(
            "ast-grep",
            allow_project_tools=allow_project_tools,
            probe_tools=probe_tools,
            allow_user_toolchain_probes=allow_user_toolchain_probes,
        ),
        "sg": executable_status(
            "sg",
            allow_project_tools=allow_project_tools,
            probe_tools=probe_tools,
            allow_user_toolchain_probes=allow_user_toolchain_probes,
        ),
        "ctags": executable_status(
            "ctags",
            allow_project_tools=allow_project_tools,
            probe_tools=probe_tools,
            allow_user_toolchain_probes=allow_user_toolchain_probes,
        ),
        "universal_ctags": executable_status(
            "universal-ctags",
            allow_project_tools=allow_project_tools,
            probe_tools=probe_tools,
            allow_user_toolchain_probes=allow_user_toolchain_probes,
        ),
        "scip": executable_status(
            "scip",
            allow_project_tools=allow_project_tools,
            probe_tools=probe_tools,
            allow_user_toolchain_probes=allow_user_toolchain_probes,
        ),
        "npm_prefix": observed(npm_prefix.as_posix()) if npm_prefix else unknown("npm prefix not probed"),
        "npm_root": observed(npm_root.as_posix()) if npm_root else unknown("npm root not probed"),
    }
