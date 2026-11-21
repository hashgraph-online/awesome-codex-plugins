---
name: risk-setup
description: Install and verify the Risk Desk runtime when its CLI or MCP tools are missing, an optional extra (xva for ORE, dev for tests) is absent, or the Option Desk engine wheel will not resolve. Includes a doctor script that reports what is installed and whether risk_desk_status answers, without installing anything. Use for setup, not risk analysis.
---

# Risk Setup

Start with the doctor. It installs nothing:

    .venv/bin/python plugins/risk-desk/skills/risk-setup/scripts/check_artifact.py

Run it with the Python the MCP client will use. It reports the riskdesk
version, every core requirement and extra, how the Option Desk engine was
installed, whether `riskdesk-mcp` is on PATH, and what `risk_desk_status`
answers over stdio.

Install the runtime from the user's actual Risk Desk checkout: `./install.sh`, or `python -m pip install .` in their chosen environment. Add `python -m pip install '.[xva]'` for the optional ORE backend. Do not guess a public repository URL.

The runtime needs `optiondesk-engine` 0.3.0, which pip installs from PyPI. Its identity is the sha256 in `wheel-hashes.json`, not the version number. To check it before the install, follow the Option Desk engine section of INSTALL.md. Do not install another build of the same version number, and do not copy the engine's source into the checkout.

Verify `riskdesk --help` and the local example commands described in the repository README. Over MCP, call `risk_desk_status`: it returns the installed version and every registered tool. The plugin starts `riskdesk-mcp` through PATH, so install the runtime in the environment used by the client. A plugin manifest alone does not install Python packages.

If the ORE wheel is unavailable for the platform, report that limitation and use the documented upstream build route; do not substitute another package named ore. No broker credentials or market-data access are needed for synthetic examples.

## Report first

1. The doctor's verdict. FAIL means the runtime is unusable here; DEGRADED
   means it works but the plugin cannot start it through PATH.
2. Which extras are absent, and what that removes: without `xva`, only
   the ORE run fails (`risk_xva`, `riskdesk xva`); without `dev`, the test suite cannot run.
3. Whether the engine's identity was checked against `wheel-hashes.json`.
   An editable or index install cannot be checked; say so.

## What not to claim

- `risk_desk_status` lists `risk_xva` with or without ORE; a tool in the list is not a working backend.
- A clean doctor run says the install is consistent, not that any model result is right.
- Never install anything the user did not ask for, and never edit their PATH or client configuration without saying what changes.

## Going deeper

- `reference.md`: what `install.sh` does, the requirements and extras, the engine wheel identity, and every field of `risk_desk_status`, with source lines.
- `workflows/install-and-verify.md`: from an empty environment to a tool call.
- `scripts/check_artifact.py`: the doctor. Exit 0 for OK or DEGRADED, 1 for FAIL.
