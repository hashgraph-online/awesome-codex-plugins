"""Write examples/payloads/r4N-*.json from recipes 40-49 (same format as export_payloads.py).

  py -3 -m agent_bridge export-payloads [--check]     (cwd: examples/python)
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.dirname(HERE)
OUT = os.path.join(os.path.dirname(PY), "payloads")


def _scenarios():
    sys.path.insert(0, os.path.join(PY, "recipes"))
    import r40_deploy_approval_gate as r40
    import r41_build_live_status as r41
    import r42_nightly_digest as r42
    import r43_ask_and_continue as r43
    import r44_streamed_research_stop as r44
    import r45_multi_job_dashboard_topics as r45
    import r46_team_group_personal_replies as r46
    import r47_incident_alert as r47
    import r48_coding_agent_hooks as r48
    import r49_intake_security_drill as r49
    return {
        "r40-deploy-approval-gate": (lambda: r40.run()[0], "production", "private (operator chat); group variant in code"),
        "r41-build-live-status": (lambda: r41.run()[0], "production", "private"),
        "r42-nightly-digest": (lambda: r42.run()[0], "production", "private"),
        "r43-ask-and-continue": (lambda: r43.run()[2], "production", "private"),
        "r44-streamed-research-stop": (lambda: r44.run()[0], "production", "private"),
        "r45-multi-job-dashboard-topics": (lambda: r45.run()[0], "production (widget: private chats only)", "private chat with topics"),
        "r46-team-group-personal-replies": (lambda: r46.run()[0], "production", "supergroup"),
        "r47-incident-alert": (lambda: r47.run()[1][0], "production", "private (two on-call chats)"),
        "r48-coding-agent-hooks": (lambda: r48.run()["claude-permission"][2], "production", "private"),
        "r49-intake-security-drill": (lambda: r49.run()[0], "production", "private + unknown group"),
    }


def build(name: str, spec) -> dict:
    fn, status, context = spec
    with contextlib.redirect_stdout(io.StringIO()):
        transport = fn()
    return {"scenario": name, "status": status, "context": context,
            "evidence": "offline contract: captured from the recipe code via FakeTransport; not sent to Telegram",
            "bot_api": "10.4 (verified 2026-11-15)",
            "steps": [{"method": m, "params": p} for m, p in transport.calls]}


def main(check: bool = False) -> int:
    drift = []
    scenarios = _scenarios()
    for name, spec in scenarios.items():
        text = json.dumps(build(name, spec), ensure_ascii=False, indent=2) + "\n"
        path = os.path.join(OUT, f"{name}.json")
        if check:
            if not os.path.exists(path) or open(path, encoding="utf-8").read() != text:
                drift.append(name)
        else:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
    if drift:
        print("payloads out of date:", ", ".join(drift))
        return 1
    print(f"{'checked' if check else 'wrote'} {len(scenarios)} agent payload files")
    return 0


if __name__ == "__main__":
    sys.exit(main("--check" in sys.argv))
