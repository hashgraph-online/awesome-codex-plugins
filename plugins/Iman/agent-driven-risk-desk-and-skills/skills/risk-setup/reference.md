# Reference: installing and checking the runtime

Sources: `install.sh`, `INSTALL.md`, `pyproject.toml` and `wheel-hashes.json`
at the repository root, `src/riskdesk/server.py` and the plugin's own
`.mcp.json`. `wheel-hashes.json` is copied into the plugin root by
`scripts/package_plugin.py:14-15`, which is where the doctor reads it.

## What the package declares (`pyproject.toml`)

| item | value |
|---|---|
| Python | `requires-python = ">=3.11"` |
| core | `skfolio==1.1.0`, `pydantic>=2.11,<3`, `mcp==1.30.0`, `numpy==2.5.3`, `scipy==1.18.1`, `scikit-learn==1.9.1`, `optiondesk-engine==0.3.0` |
| extra `xva` | `open-source-risk-engine==1.8.16.0` |
| extra `dev` | `pytest`, `build`, `coverage` |
| commands | `riskdesk` (`riskdesk.cli:main`) and `riskdesk-mcp` (`riskdesk.server:main`) |

Only `src/riskdesk/ore_worker.py:10` imports `ORE`, so without the `xva`
extra everything except the ORE run works (`install.sh:17-20`).

## install.sh

POSIX sh, run from the checkout (`install.sh:1-22`).

| option | effect | lines |
|---|---|---|
| `--venv DIR` | environment directory, default `./.venv`, or `RISKDESK_VENV` | 27, 49 |
| `--python BIN` | interpreter, or `RISKDESK_PYTHON` | 46, 50 |
| `--no-xva` | skip the optional ORE extra | 51 |
| `--no-tests` | do not run the suite at the end | 52 |
| `--help` | usage, exit 0 | 53 |

Any other option exits 2 (`install.sh:54`). Without `--python` it tries
`python3.13`, `python3.12`, `python3.11`, `python3` and takes the first at
3.11 or later (`install.sh:61-74`). Steps: create the environment if it
has no `bin/python` (82-87); upgrade pip and install `.[dev]` (91-94); try
`.[xva]`, logging to `VENV/xva-install.log` and reporting the outcome
rather than failing (96-105); run `pytest -q --color=no` unless
`--no-tests` (107-110); print the two command paths and the ORE status
(112-118). It writes only inside the checkout and registers nothing
(`install.sh:13-15`).

When `.[dev]` fails it stops with a pointer to the pip output and
INSTALL.md (`install.sh:93-94`).

## The Option Desk engine wheel

Identity is the wheel's sha256, not its version: an earlier build also
numbered 0.3.0 lacks the Black-76 rho fix (`INSTALL.md`, "The Option Desk
engine"). The recorded entry (`wheel-hashes.json:134-140`):

- wheel `optiondesk_engine-0.3.0-py3-none-any.whl`
- sha256 `8f76f14c9026cad09d77d6d887823902d02085f98e395d67818dba50af0f8a0d`
- source: option-desk commit `4a282d91bdb9fafbb0e4d80f2e88ab790eac6f4c`,
  `engine/` built from a clean git archive

The wheel is on PyPI. On 4 November 2026 `pip download --no-deps
optiondesk-engine==0.3.0` fetched a file with exactly the recorded
sha256. INSTALL.md gives the check.

What an installed environment can prove: pip's `direct_url.json` (PEP
610) in the distribution's metadata, which the doctor reads. Observed with
pip 26.1.2 on 2026-11-04: installing the wheel by its path records
`archive_info.hashes.sha256`, which the doctor compares with
`wheel-hashes.json` and fails on a mismatch. Installing it through
`--find-links` writes no `direct_url.json`, so that install's identity
cannot be checked afterwards. An install from PyPI writes none either
(observed on 4 November 2026). An editable install records its source
directory and no hash. So check the wheel file's sha256 before you
install it, or install it by path.

## The ORE extra

`INSTALL.md`, "The optional ORE extra", records where the wheel resolved
when it was measured: macOS ARM64 under CPython 3.13 and `python:3.13-slim`
at linux/amd64, and not at linux/arm64. Those are that document's
measurements, not the doctor's. The pinned version and its wheel hash are
in `wheel-hashes.json:128-133`.

## risk_desk_status (`server.py:29-36`)

| field | value |
|---|---|
| `status` | `available` |
| `riskdesk_version` | the package version |
| `market_data` | `false` |
| `tools` | every registered tool name, sorted |
| `data_modes` | the Provenance literals, `synthetic` and `user-licensed` (`models.py:15`) |
| `xva_data_modes` | `ore.DATA_MODES`: those two and `upstream-example` (`ore.py:61`) |
| `conventions` | the reporting rules in `server.py:17-26` |

`tests/test_interfaces.py:65-74` checks these fields. The tool list does
not depend on the `xva` extra.

## How a client starts the server

The plugin's `.mcp.json` declares one stdio server, command `riskdesk-mcp`,
no arguments, found through PATH (`INSTALL.md`, routes 3 and 6). The server
speaks stdio and binds no socket (`INSTALL.md`, route 6). If a client lists no tools, the usual cause is a plugin
installed without the runtime, or a PATH without `riskdesk-mcp`
(`INSTALL.md`, "If something does not work").

## The doctor (`scripts/check_artifact.py`)

| check | FAIL when | DEGRADED when |
|---|---|---|
| riskdesk installed for this interpreter | not installed | |
| Python against `Requires-Python` | not met | |
| core requirements | one missing or outside its specifier | |
| extras | never; absent extras are reported | |
| engine sha256 against `wheel-hashes.json` | recorded and different | |
| `riskdesk-mcp` | not found on PATH or beside the interpreter | not on PATH, or PATH finds another environment's |
| `risk_desk_status` over stdio | no answer within 60 seconds, an error, or a version other than the installed one | |

It starts one server process for the status call and the process ends
with the call. It reads, and never writes, installs or edits configuration.
