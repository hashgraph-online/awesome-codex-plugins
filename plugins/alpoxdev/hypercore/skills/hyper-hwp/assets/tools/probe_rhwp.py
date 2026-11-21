#!/usr/bin/env python3
"""Probe the rhwp CLI and report whether it can do what this skill requires.

Prints one JSON object on stdout and exits 0 when the binary satisfies the
skill's command set, 1 when it does not, 2 when the probe itself cannot run.
Standard library only; no network access.
"""

import json
import os
import re
import shutil
import subprocess
import sys

MIN_VERSION = (0, 9, 0)
# Commands the workflow calls. A binary without these cannot run the skill.
REQUIRED_COMMANDS = [
    "info",
    "explain",
    "export-text",
    "export-structure",
    "export-tables",
    "fields",
    "search",
    "scaffold",
    "convert",
    "export-hwpx",
    "verify",
    "hwpx-roundtrip",
    "hwp5-roundtrip",
    "layout-anomaly",
    "run",
]
REQUIRED_EDIT = [
    "replace-text",
    "set-cell",
    "insert-text",
    "insert-table",
    "insert-paragraph",
    "fill-fields",
    "insert-footnote",
    "insert-footnote-text",
    "apply-char-format",
    "apply-para-format",
    "set-column-widths",
    "merge-cells",
    "set-cell-props",
]
CANDIDATES = [
    "rhwp",
    os.path.expanduser("~/.cargo/bin/rhwp"),
    "/opt/homebrew/bin/rhwp",
    "/usr/local/bin/rhwp",
]


def find_binary():
    for candidate in CANDIDATES:
        found = shutil.which(candidate) if os.sep not in candidate else candidate
        if found and os.path.isfile(found) and os.access(found, os.X_OK):
            return found
    return None


def run(binary, *args):
    proc = subprocess.run(
        [binary, *args],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def parse_version(text):
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", text)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def main():
    binary = find_binary()
    if binary is None:
        print(
            json.dumps(
                {
                    "ok": False,
                    "reason": "rhwp_not_found",
                    "install": "brew install edwardkim/rhwp/rhwp  # or download the v0.9.0+ release tarball",
                    "searched": CANDIDATES,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    code, out, err = run(binary, "--version")
    version = parse_version(out + err)
    if version is None:
        print(
            json.dumps(
                {
                    "ok": False,
                    "reason": "version_unreadable",
                    "binary": binary,
                    "stdout": out[:400],
                    "stderr": err[:400],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    code, caps_out, caps_err = run(binary, "capabilities")
    commands = []
    edits = []
    if code == 0:
        try:
            parsed = json.loads(caps_out)
            commands = [entry.get("name", "") for entry in parsed.get("commands", [])]
            for entry in parsed.get("commands", []):
                if entry.get("name") == "edit":
                    edits = [sub.get("name", "") for sub in entry.get("subcommands", [])]
        except (json.JSONDecodeError, AttributeError):
            pass

    missing_commands = [name for name in REQUIRED_COMMANDS if name not in commands]
    missing_edits = [name for name in REQUIRED_EDIT if name not in edits]
    version_ok = version >= MIN_VERSION
    ok = version_ok and not missing_commands and not missing_edits

    report = {
        "ok": ok,
        "binary": binary,
        "version": ".".join(str(part) for part in version),
        "minimum_version": ".".join(str(part) for part in MIN_VERSION),
        "version_ok": version_ok,
        "capabilities_readable": bool(commands),
        "missing_commands": missing_commands,
        "missing_edit_subcommands": missing_edits,
    }
    if not version_ok:
        report["reason"] = "version_too_old"
        report["upgrade"] = "reinstall from the v0.9.0+ release tarball; older builds have no edit or scaffold"
    elif missing_commands or missing_edits:
        report["reason"] = "command_set_incomplete"
    else:
        report["reason"] = "ready"

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.TimeoutExpired:
        print(json.dumps({"ok": False, "reason": "probe_timeout"}, ensure_ascii=False))
        sys.exit(2)
