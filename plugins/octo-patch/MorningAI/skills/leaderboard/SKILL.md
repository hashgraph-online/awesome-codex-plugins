---
name: leaderboard
version: "1.3.0"
description: Track AI model leaderboard rankings over time and detect rank/score changes between snapshots
---

# Leaderboard Snapshot Tracker

Track AI model leaderboard rankings over time using SQLite snapshots. Detect new models, removed models, rank changes, and score changes between dates.

## Supported Leaderboards

| Leaderboard | URL | Modality |
|-------------|-----|----------|
| LMSYS Chatbot Arena | https://lmsys.org | Text, Vision |
| LMArena | https://lmarena.ai | Text, Vision |
| HuggingFace Open LLM | https://huggingface.co/spaces/open-llm-leaderboard | Text |
| Artificial Analysis | https://artificialanalysis.ai | Text, Image, Video |
| Scale AI SEAL | https://scale.com/leaderboard | Text |

## Usage

### Save a snapshot

```bash
cd {SKILL_DIR} && python3 skills/leaderboard/scripts/leaderboard_snapshot.py save \
  --leaderboard "chatbot-arena" \
  --date 2026-04-14 \
  --data '[{"model": "claude-4-opus", "rank": 1, "score": 1350}]'
```

Prints the diff against the previous snapshot (new models, rank changes, score changes).

### View latest snapshot

```bash
cd {SKILL_DIR} && python3 skills/leaderboard/scripts/leaderboard_snapshot.py latest \
  --leaderboard "chatbot-arena"
```

## Data Storage

Snapshots are stored in `~/.cache/morning-ai/leaderboard.db` (SQLite). Each entry has:
- `leaderboard` — leaderboard identifier
- `model` — model name
- `rank` — position on the leaderboard
- `score` — numeric score (ELO, accuracy, etc.)
- `snapshot_date` — date of the snapshot

## Integration with Main Workflow

This skill is currently a standalone utility. It can be integrated into the main morning-ai workflow as a Benchmark data source:

1. **As a collector**: Scrape leaderboard pages → save snapshot → diff against previous → generate `TrackerItem` entries for rank changes
2. **As a report section**: Add a "Leaderboard Movement" section to the daily report showing rank/score deltas

To integrate, a collector module (`lib/leaderboard_collector.py`) would:
- Fetch current leaderboard data from supported sites
- Call `save_snapshot()` to persist
- Call `diff_snapshot()` to detect changes
- Convert significant changes (new #1 model, big rank jumps) into `TrackerItem` objects with Benchmark type
