---
name: tailtest-on
description: Resume tailtest automatic test generation after a pause. When the agent needs to (1) re-enable the Stop hook after tailtest-off, (2) restart automatic test generation for this session, or (3) respond to "resume tailtest" / "unpause tailtest" / "enable tailtest".
---

Resume tailtest for this session.

Set `paused: false` in `.tailtest/session.json`. Respond exactly: "tailtest resumed."
