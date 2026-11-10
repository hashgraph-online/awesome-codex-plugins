# Workflow: install and verify the runtime

Commands run from the root of the user's Risk Desk checkout.

1. Diagnose first. Run the doctor with the interpreter the client uses:

       .venv/bin/python plugins/risk-desk/skills/risk-setup/scripts/check_artifact.py

   If `.venv` does not exist yet, go to step 2. If the verdict is OK, skip
   to step 5.
2. Ask before installing. Then run the installer, which writes only inside
   the checkout:

       ./install.sh --help
       ./install.sh

   Add `--no-xva` if the user does not want the ORE extra, `--no-tests` to
   skip the suite.
3. pip installs `optiondesk-engine` 0.3.0 from PyPI. If pip stops with
   `No matching distribution found for optiondesk-engine==0.3.0`, pip
   cannot reach PyPI or an index that carries it: report that and stop.
   To check the engine's identity, follow "The Option Desk engine" in
   INSTALL.md and compare the sha256 with the `optiondesk-engine` entry
   of `wheel-hashes.json`. If the hashes differ, the wheel is a different
   build: stop and say so.
4. If the installer reports the ORE extra as not installed, read
   `.venv/xva-install.log`. Report it as a platform limitation; everything
   except the ORE run still works.
5. Check the command line on a shipped example:

       .venv/bin/riskdesk --help
       .venv/bin/riskdesk exposure --input examples/portfolio.json

6. Check the server starts and exits cleanly:

       .venv/bin/riskdesk-mcp < /dev/null

7. Run the doctor again. DEGRADED for PATH means the plugin cannot start
   the server: activate `.venv` in the environment that launches the
   client, or point the client at `.venv/bin/riskdesk-mcp` by absolute
   path (INSTALL.md, routes 3, 4 and 6). Say what you would change before
   changing a client's configuration.
8. In the client, call `risk_desk_status`. Its `riskdesk_version` must
   equal the doctor's, and its `tools` list must be non-empty.

## Before reporting

- Give the doctor's verdict line and every FAIL or DEGRADED reason.
- Name each absent extra and what it removes.
- Say whether the engine's identity was checked or could not be.
- Do not report setup as done on the strength of a plugin install alone.
