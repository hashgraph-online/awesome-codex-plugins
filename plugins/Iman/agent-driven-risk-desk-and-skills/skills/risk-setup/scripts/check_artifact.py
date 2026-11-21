#!/usr/bin/env python3
"""Doctor: report what of Risk Desk this Python has installed, and whether risk_desk_status answers.

It installs nothing and changes nothing. Run it with the interpreter the MCP
client will use, for example from the checkout:

    .venv/bin/python plugins/risk-desk/skills/risk-setup/scripts/check_artifact.py

It reads the installed riskdesk metadata for its core requirements and
extras, compares the optiondesk-engine install with wheel-hashes.json where
pip recorded a wheel hash, finds riskdesk-mcp on PATH, and starts that
server once over stdio to call risk_desk_status; the server stops when the
call returns. Exit 0 when the runtime is usable (OK, or DEGRADED when the
plugin could not start this server through PATH), 1 on FAIL.
"""
import asyncio
import json
from importlib import metadata
from pathlib import Path
import platform
import shutil
import sys

HASHES = Path(__file__).resolve().parents[3] / "wheel-hashes.json"  # the plugin root


def installed(name):
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def requirements():
    """(group, requirement, installed version, satisfied) for the core and every extra of riskdesk."""
    from packaging.requirements import Requirement
    extras = metadata.metadata("riskdesk").get_all("Provides-Extra") or []
    rows = []
    for text in metadata.requires("riskdesk") or []:
        req = Requirement(text)
        if req.marker is None or req.marker.evaluate({"extra": ""}):
            group = "core"
        else:
            group = next((e for e in extras if req.marker.evaluate({"extra": e})), None)
            if group is None:
                continue  # a marker for another platform
        version = installed(req.name)
        rows.append((group, req.name + str(req.specifier), version,
                     version is not None and req.specifier.contains(version, prereleases=True)))
    return rows


def origin(name):
    """How pip installed a distribution, from its direct_url.json (PEP 610), and the wheel sha256 if recorded."""
    text = metadata.distribution(name).read_text("direct_url.json")
    if not text:
        return "installed from an index or find-links", None
    info = json.loads(text)
    if info.get("dir_info", {}).get("editable"):
        return "editable from " + info["url"], None
    return "installed from " + info["url"], (info.get("archive_info", {}).get("hashes") or {}).get("sha256")


async def _status(command):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    async with stdio_client(StdioServerParameters(command=command, args=[])) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            result = await session.call_tool("risk_desk_status", {})
    if result.isError:
        raise RuntimeError(result.content[0].text)
    return json.loads(result.content[0].text)


def status_over_stdio(command, timeout=60):
    return asyncio.run(asyncio.wait_for(_status(command), timeout))


def main():
    notes, problems, warnings = [], [], []
    version = installed("riskdesk")
    if version is None:
        print("FAIL riskdesk is not installed for " + sys.executable)
        print("  install it from the checkout with ./install.sh (INSTALL.md); a plugin alone installs nothing")
        return 1
    from packaging.specifiers import SpecifierSet
    wanted = metadata.metadata("riskdesk")["Requires-Python"] or ""
    if not SpecifierSet(wanted).contains(platform.python_version()):
        problems.append("Python {} does not meet riskdesk's Requires-Python {}".format(platform.python_version(), wanted))
    notes.append("riskdesk {}, {}".format(version, origin("riskdesk")[0]))
    rows = requirements()
    for group, req, have, ok in rows:
        if group == "core" and not ok:
            problems.append("core requirement {}: {}".format(req, "installed " + have if have else "not installed"))
    for extra in sorted({g for g, *_ in rows} - {"core"}):
        members = [(req, have, ok) for g, req, have, ok in rows if g == extra]
        missing = [req if have is None else "{} (installed {})".format(req, have) for req, have, ok in members if not ok]
        notes.append("extra {}: {}".format(extra, "absent, needs " + ", ".join(missing) if missing else "present"))
    if installed("optiondesk-engine"):
        how, sha = origin("optiondesk-engine")
        recorded = next((w["sha256"] for w in json.loads(HASHES.read_text(encoding="utf-8"))
                         if w["name"] == "optiondesk-engine"), None) if HASHES.is_file() else None
        if sha and recorded and sha != recorded:
            problems.append("optiondesk-engine wheel sha256 {} is not the one in wheel-hashes.json".format(sha))
        identity = ("matches wheel-hashes.json" if sha and sha == recorded else
                    "identity not checked: pip recorded no wheel hash" if not sha else
                    "identity not checked: no wheel-hashes.json beside this skill" if not recorded else "")
        notes.append("optiondesk-engine {}, {}; {}".format(installed("optiondesk-engine"), how, identity).rstrip("; "))
    beside = Path(sys.executable).parent / "riskdesk-mcp"
    on_path = shutil.which("riskdesk-mcp")
    if on_path is None:
        warnings.append("riskdesk-mcp is not on PATH; the plugin starts it through PATH, so point the client at "
                        + str(beside) + " or activate this environment")
    elif beside.exists() and Path(on_path).resolve() != beside.resolve():
        warnings.append("PATH finds {}, not this interpreter's {}".format(on_path, beside))
    command = on_path or (str(beside) if beside.exists() else None)
    if command is None:
        problems.append("no riskdesk-mcp command found")
    else:
        try:
            status = status_over_stdio(command)
        except Exception as exc:  # any failure to answer is the finding
            problems.append("risk_desk_status did not answer through {}: {}: {}".format(command, type(exc).__name__, exc))
        else:
            notes.append("risk_desk_status through {}: {}, riskdesk {}, {} tools, data modes {}, xva data modes {}".format(
                command, status.get("status"), status.get("riskdesk_version"), len(status.get("tools", [])),
                status.get("data_modes"), status.get("xva_data_modes")))
            if status.get("riskdesk_version") != version:
                problems.append("the server reports riskdesk {} but {} is installed here".format(
                    status.get("riskdesk_version"), version))
    verdict = "FAIL" if problems else ("DEGRADED" if warnings else "OK")
    print("{} riskdesk {} on Python {} at {}".format(verdict, version, platform.python_version(), sys.executable))
    for line in problems + warnings + notes:
        print("  " + line)
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) != 1:
        print("usage: check_artifact.py   (no arguments; run it with the Python the MCP client uses)")
        raise SystemExit(2)
    raise SystemExit(main())
