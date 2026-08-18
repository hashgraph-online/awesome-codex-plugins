#!/usr/bin/env python3
"""Explicit local tool setup for clean-room source-index preflight."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import os
import re
import sys
import time
from typing import Any

import clean_room_tooling


LOCAL_INSTALL_TIMEOUT_SECONDS = 600
LOCAL_INSTALL_LOCK_TIMEOUT_SECONDS = 600
LOCAL_INSTALL_LOCK_POLL_SECONDS = 0.2
STRICT_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$")
NPM_TOOLS = {
    "ast-grep": {
        "package": "@ast-grep/cli",
        "source": "https://www.npmjs.com/package/@ast-grep/cli",
        "bin": "ast-grep",
    },
}
STATUS_TOOLS = [
    "node",
    "npm",
    "ast-grep",
    "sg",
    "ctags",
    "universal-ctags",
    "scip",
]
STATUS_PACKAGES = ["@ast-grep/cli"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report or explicitly install local clean-room source-index helper tools into the user cache."
    )
    parser.add_argument("--status", action="store_true", help="Print tool discovery status as JSON")
    parser.add_argument(
        "--install-local",
        choices=sorted(NPM_TOOLS),
        help="Install one approved npm-backed tool into ~/.cache/re-skills/clean-room-tools/npm",
    )
    parser.add_argument(
        "--version",
        type=exact_version_arg,
        help="Exact npm package version to install. Required with --install-local.",
    )
    parser.add_argument(
        "--allow-npm-scripts",
        action="store_true",
        help="Allow npm lifecycle scripts during local install. Default is --ignore-scripts.",
    )
    parser.add_argument(
        "--allow-working-project-tools",
        action="store_true",
        help="Include project-local .local/bin, .bin, node_modules/.bin, and npm prefix/global tools in --status output.",
    )
    parser.add_argument(
        "--probe-tools",
        action="store_true",
        help="Execute discovered tools with version commands in --status output. Default is stat-only.",
    )
    parser.add_argument(
        "--allow-user-toolchain-probes",
        action="store_true",
        help="With --probe-tools, execute version commands for tools found under /opt/homebrew or /usr/local.",
    )
    args = parser.parse_args()
    if not args.status and not args.install_local:
        parser.error("choose --status or --install-local")
    if args.install_local and not args.version:
        parser.error("--install-local requires --version")
    return args


def exact_version_arg(value: str) -> str:
    if not STRICT_SEMVER_RE.fullmatch(value):
        raise argparse.ArgumentTypeError(
            "--version must be an exact SemVer version like 1.2.3, 1.2.3-alpha.1, or 1.2.3+build.1"
        )
    return value


def write_json(data: dict[str, Any]) -> None:
    json.dump(data, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def package_status(allow_project_tools: bool = False) -> dict[str, Any]:
    status: dict[str, Any] = {}
    for package in STATUS_PACKAGES:
        parts = package.split("/")
        checked = [
            (root / "node_modules").joinpath(*parts)
            for root in clean_room_tooling.node_resolver_roots(allow_project_tools)
        ]
        found = next((path for path in checked if path.exists()), None)
        status[package] = (
            clean_room_tooling.observed(found.as_posix())
            if found
            else clean_room_tooling.unknown(
                "package unavailable",
                value={"checked_locations": [path.as_posix() for path in checked]},
            )
        )
    return status


def status_report(
    allow_project_tools: bool = False,
    probe_tools: bool = False,
    allow_user_toolchain_probes: bool = False,
) -> dict[str, Any]:
    dependency_report = clean_room_tooling.dependency_report(
        allow_project_tools,
        probe_tools,
        allow_user_toolchain_probes,
    )
    return {
        "schema_version": 1,
        "policy": dependency_report["external_tools_policy"],
        "tool_probe_mode": dependency_report["tool_probe_mode"],
        "tool_trust_mode": clean_room_tooling.tool_trust_mode(allow_project_tools),
        "local_cache": clean_room_tooling.observed(clean_room_tooling.USER_TOOLS_DIR.as_posix()),
        "installable_local_tools": {
            name: {"package": item["package"], "source": item["source"]}
            for name, item in sorted(NPM_TOOLS.items())
        },
        "tools": {
            name: clean_room_tooling.executable_status(
                name,
                allow_project_tools=allow_project_tools,
                probe_tools=probe_tools,
                allow_user_toolchain_probes=allow_user_toolchain_probes,
            )
            for name in STATUS_TOOLS
        },
        "node_packages": package_status(allow_project_tools),
    }


def npm_package_spec(package: str, version: str) -> str:
    return f"{package}@{version}"


@contextmanager
def local_install_lock() -> Any:
    clean_room_tooling.USER_TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    lock_dir = clean_room_tooling.USER_TOOLS_DIR / "npm.install.lock"
    deadline = time.monotonic() + LOCAL_INSTALL_LOCK_TIMEOUT_SECONDS
    acquired = False
    while not acquired:
        try:
            lock_dir.mkdir()
            try:
                (lock_dir / "owner.json").write_text(
                    json.dumps({"pid": os.getpid(), "created_at": time.time()}, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
            except Exception:
                try:
                    lock_dir.rmdir()
                except OSError:
                    pass
                raise
            acquired = True
        except FileExistsError as exc:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"local npm install lock is held: {lock_dir}") from exc
            time.sleep(LOCAL_INSTALL_LOCK_POLL_SECONDS)
    try:
        yield
    finally:
        try:
            for child in lock_dir.iterdir():
                child.unlink()
            lock_dir.rmdir()
        except FileNotFoundError:
            pass


def install_result_base(tool: str, version: str, allow_npm_scripts: bool) -> dict[str, Any]:
    spec = NPM_TOOLS[tool]
    package_spec = npm_package_spec(str(spec["package"]), version)
    return {
        "schema_version": 1,
        "tool": tool,
        "source": spec["source"],
        "version": version,
        "package_spec": package_spec,
        "install_root": clean_room_tooling.observed(clean_room_tooling.USER_NPM_PREFIX.as_posix()),
        "install_trust_mode": clean_room_tooling.observed(
            "explicit-version",
            evidence={"npm_lifecycle_scripts": "allowed" if allow_npm_scripts else "ignored"},
        ),
    }


def install_npm_tool(tool: str, version: str, allow_npm_scripts: bool = False) -> dict[str, Any]:
    spec = NPM_TOOLS[tool]
    result = install_result_base(tool, version, allow_npm_scripts)
    npm = clean_room_tooling.find_executable("npm")
    if npm is None:
        result["command"] = clean_room_tooling.error_fact(
            "npm unavailable; install Node/npm first or set NPM_BIN",
            evidence={"checked_locations": clean_room_tooling.checked_executable_locations("npm")},
        )
        result["resolved_tool"] = clean_room_tooling.unknown("install did not run")
        return result

    prefix = clean_room_tooling.USER_NPM_PREFIX
    package_spec = str(result["package_spec"])
    argv = [
        npm.path.as_posix(),
        "install",
        "--prefix",
        prefix.as_posix(),
        "--save-exact",
    ]
    if not allow_npm_scripts:
        argv.append("--ignore-scripts")
    argv.append(package_spec)

    try:
        with local_install_lock():
            try:
                prefix.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                result["command"] = clean_room_tooling.error_fact(
                    f"could not create npm install prefix: {exc.__class__.__name__}",
                    evidence={"install_root": prefix.as_posix()},
                )
                result["resolved_tool"] = clean_room_tooling.unknown("install did not run")
                return result

            result["command"] = clean_room_tooling.run_command(argv, LOCAL_INSTALL_TIMEOUT_SECONDS)
    except TimeoutError as exc:
        result["command"] = clean_room_tooling.error_fact(
            str(exc),
            evidence={"lock_timeout_seconds": LOCAL_INSTALL_LOCK_TIMEOUT_SECONDS},
        )
        result["resolved_tool"] = clean_room_tooling.unknown("install did not run")
        return result
    except OSError as exc:
        result["command"] = clean_room_tooling.error_fact(
            f"local npm install lock failed: {exc.__class__.__name__}",
            evidence={"lock_root": clean_room_tooling.USER_TOOLS_DIR.as_posix()},
        )
        result["resolved_tool"] = clean_room_tooling.unknown("install did not run")
        return result

    resolved = clean_room_tooling.find_executable(str(spec["bin"]))
    result["resolved_tool"] = (
        clean_room_tooling.observed({"path": resolved.path.as_posix(), "source": resolved.source})
        if resolved
        else clean_room_tooling.unknown("tool installed but executable was not resolved")
    )
    return result


def main() -> int:
    args = parse_args()
    if args.status:
        write_json(status_report(args.allow_working_project_tools, args.probe_tools, args.allow_user_toolchain_probes))
    if args.install_local:
        result = install_npm_tool(args.install_local, args.version, args.allow_npm_scripts)
        write_json(result)
        if result.get("status") == "error" or result.get("command", {}).get("status") == "error":
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
