"""agent_bridge - an agent's own Telegram interface to its human operator.

An AI agent (a coding agent, a CI job, an autonomous worker) uses a bot to
report, ask, wait for answers, request approvals and take commands. This
package is the small, SDK-independent core of that loop:

* AgentBridge      - notify / progress / ask / approve / send_file / report /
                     stream / listen (bridge.py)
* Allowlist        - who may talk to the agent, by numeric id only (security.py)
* ApprovalBook     - approvals bound to request id + approver + nonce + expiry
                     (approvals.py)
* Redactor         - token and secret redaction for messages and logs (redact.py)
* JsonStore        - offset, pending requests and status cards survive a
                     restart (store.py)
* intake           - long polling, fixtures, webhook verification, dedup
                     (intake.py)
* hooks            - Claude Code / Codex hook adapters (hooks.py)
* cli              - `py -3 -m agent_bridge <command>` (cli.py)

Standard library only. Offline (dry-run) by default: nothing reaches Telegram
unless `--live` is passed AND the token env var is set. Verified against the
official Bot API docs on 2026-11-22 (Bot API 10.5, the newest version then).
Example code to copy and adapt, not a published package.
"""
__version__ = "0.1.0"
BOT_API_VERSION = "10.5"
VERIFIED = "2026-11-22"
