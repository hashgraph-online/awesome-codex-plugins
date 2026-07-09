# Compounding-mode scheduled tick — design

How `--compounding` runs unattended: a host scheduler fires a headless worker
on a cadence, the worker runs one mining sweep, and the results land in durable
artifacts (a findings ledger + bead candidates) instead of a chat transcript.

## ⛔ Dispatch constraint (LAW 0)

The tick dispatches **`codex exec`** — NEVER `claude -p` / `claude --print`.
That path bills the Anthropic API and/or burns the Claude Max weekly quota, is
mechanically blocked on this host (`~/.claude/hooks/no-claude-p-guard.sh`),
and a scheduler would re-commit the violation on every fire. Acceptable
headless lanes: `codex exec` (default), the local llama endpoint for cheap
pre-filtering. There is no third option; do not reason past this.

## Shape

```
scheduler (launchd | systemd user timer)
  └─> tick script (thin shell wrapper)
        └─> codex exec "<compounding-mode prompt>"
              ├─> reads sources (cass, rtk history, shell history, ritual scans)
              ├─> diffs clusters against the previous findings entry
              ├─> appends a dated section to .agents/toil-mining/findings.md
              └─> emits bead-candidate stanzas for new/grown clusters
```

The tick is idempotent per day: re-firing overwrites nothing, it appends one
dated section keyed by date. The worker gets a fresh context every fire — all
continuity lives in the findings ledger it diffs against, not in the session.

## Cadence

Weekly is the default. Daily is wasteful (rituals take days to form); monthly
lets a new ritual hit dozens of pastes before it is caught. Tune per host
activity, not per enthusiasm.

## Mac — launchd

`~/Library/LaunchAgents/com.bo.toil-mining-tick.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.bo.toil-mining-tick</string>
  <key>ProgramArguments</key><array>
    <string>/bin/zsh</string><string>-lc</string>
    <string>codex exec "Run the toil-mining skill in --compounding mode over this host's usage history; append findings to .agents/toil-mining/findings.md and emit bead candidates for new clusters." &gt;&gt; "$HOME/.local/state/toil-mining/tick.log" 2&gt;&amp;1</string>
  </array>
  <key>StartCalendarInterval</key><dict>
    <key>Weekday</key><integer>1</integer>
    <key>Hour</key><integer>7</integer>
    <key>Minute</key><integer>30</integer>
  </dict>
</dict></plist>
```

Load with `launchctl bootstrap gui/$(id -u) <plist>`; verify with
`launchctl print gui/$(id -u)/com.bo.toil-mining-tick`.

## bushido (WSL) — systemd user timer

`~/.config/systemd/user/toil-mining-tick.service`:

```ini
[Unit]
Description=toil-mining compounding sweep (codex exec; never claude -p)

[Service]
Type=oneshot
ExecStart=/usr/bin/env zsh -lc 'codex exec "Run the toil-mining skill in --compounding mode over this host's usage history; append findings to .agents/toil-mining/findings.md and emit bead candidates for new clusters."'
```

`~/.config/systemd/user/toil-mining-tick.timer`:

```ini
[Unit]
Description=weekly toil-mining sweep

[Timer]
OnCalendar=Mon 07:30
Persistent=true

[Install]
WantedBy=timers.target
```

Enable with `systemctl --user enable --now toil-mining-tick.timer`; inspect
with `systemctl --user list-timers` and `journalctl --user -u
toil-mining-tick.service`.

## Output routing

| Artifact | Path | Contract |
|---|---|---|
| Findings ledger | `.agents/toil-mining/findings.md` | Append-only dated sections; each section = sources consulted, new clusters, grown clusters (with previous→current counts), echo-filter note |
| Candidate report | `.agents/toil-mining/YYYY-MM-DD-candidates.md` | Same ranked-table format as on-demand mode |
| Bead candidates | tracker (`ao beads exec create`, P3 by default) | One bead per new candidate above the ranking threshold, body citing the findings section; dedupe against open toil beads before creating |

The tick never auto-builds an automation and never escalates a candidate past
"bead created" — shape decisions stay with `/automation-shape-routing`, and
anything external stays gated on the operator.

## Failure behavior

- Worker failure: log to the tick log and exit non-zero; the next fire retries. No partial ledger writes — build the section in a temp file, append atomically.
- Missing source (no rtk, no ritual scan that week): note it in the section and continue with the rest; an empty sweep is a valid, cheap result.
- Quota/rate pressure on the codex lane: skip the fire (log "skipped: lane unavailable") rather than falling back to any Claude headless path — the fallback that "just this once" uses `claude -p` is the exact failure LAW 0 exists to stop.
