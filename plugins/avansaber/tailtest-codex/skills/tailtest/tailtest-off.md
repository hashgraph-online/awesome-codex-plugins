---
name: tailtest-off
description: Pause tailtest automatic test generation for this session. When the agent needs to (1) stop the Stop hook from queueing files, (2) silence tailtest temporarily without uninstalling it, or (3) respond to "pause tailtest" / "stop tailtest" / "disable tailtest".
---

Pause tailtest for this session.

Set `paused: true` in `.tailtest/session.json`. Respond exactly: "tailtest paused. Type /tailtest on to resume."

The Stop hook reads this flag and returns `decision: continue` without queueing files while paused. No other behaviour changes.
