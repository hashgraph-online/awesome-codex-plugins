---
name: toil-mining
description: Mine caller-supplied usage history for
---
# Toil Mining — rank repeated friction

Mine explicitly supplied session, shell, RTK, or CASS history without modifying
the sources. The result is evidence for a caller; this skill does not file work,
schedule automation, or mutate a tracker.

## Procedure

1. Record the input sources, time window, filters, and query.
2. Normalize repeated human actions while excluding documented machine echoes
   and generated repetitions. For caller-supplied Codex JSONL, use the
   deterministic helper below rather than an ad hoc transcript scan.
3. Cluster equivalent actions and preserve representative evidence references.
4. Score each cluster from measured frequency and observed pain such as elapsed
   time, failure count, interruption, or token cost.
5. Emit a ranked report and stop.

Each candidate must contain a measured count, source references, confidence in
the clustering, pain evidence, and the smallest plausible automation shape.
Separate observations from recommendations.

## Repetition threshold: measured, not remembered

A cluster qualifies as toil only above a measured floor: at least three
occurrences in the supplied window, each resolvable to a source reference. Two
occurrences are a coincidence; a vivid memory of "doing this constantly" with
one resolvable instance is an anecdote. The named failure mode is
salience mining — ranking by how annoying the last occurrence felt rather than
by count, which surfaces yesterday's irritation over the quiet weekly drain.
If the supplied history cannot establish the count, report the candidate as
below-threshold with its actual measured count; never round an impression up
to a frequency.

## Weighted priority: frequency x cost x error-proneness

Rank clusters by the product of three measured factors, not by any single one:

- **frequency** — occurrences per window, from the cluster count;
- **cost** — median elapsed time or token cost per occurrence, from the
  evidence, not from recall;
- **error-proneness** — fraction of occurrences showing a failure, retry, or
  correction in the source.

Score each factor from cited evidence and show the three inputs next to every
composite score so the caller can re-weigh them. A factor the history cannot
support is reported as unmeasured — scored at the floor, never guessed at the
midpoint. The named failure mode is frequency-only ranking: a daily two-second
nuisance outranking a weekly half-hour error-prone ritual because only one
axis was measured. The product form exists precisely so that a high-frequency,
near-zero-cost, never-fails cluster ranks where it belongs: low.

### Deterministic recent-human extraction (Codex JSONL)

The helper accepts only explicit session paths and requires an explicit,
timezone-qualified window:

```bash
python3 skills/toil-mining/scripts/recent_human.py --since 2026-07-12T00:00:00Z \
  --until 2026-07-16T00:00:00Z /path/to/session-a.jsonl /path/to/session-b.jsonl \
  > /tmp/recent-human.json
```

It extracts `event_msg` / `user_message` records with `source_path`, one-based
`line`, normalized UTC `timestamp`, and request `text`. Codex attachment and IDE
wrappers are normalized by keeping the text after `# My request for Codex:`.
Restored or forked copies are deduplicated by `client_id`, with the earliest
occurrence retained.

The extractor treats a nonempty `client_id` as the high-confidence UI-origin
boundary. Records without it are reported as `missing_client_id`, not guessed to
be human. It also excludes these narrow generated envelope families and reports
their counts: internal context tags (`codex_internal_context`, environment,
permissions, skill/app/plugin instructions), fresh-context cross-family refuter
prompts, and agent `Message Type:` envelopes. This is deliberately conservative:
a directly typed message from a client that omits `client_id` remains unchecked.

The JSON result includes input/parsed/candidate/emitted counts, exclusions by
reason, checked facts, and not-checked facts. Malformed records are counted, not
silently discarded. The helper reads only the supplied JSONL and writes only to
stdout; it does not read attachment contents, discover more sessions, cluster
meaning, score toil, file work, or schedule automation. It is
retrieval/report-only.

## Output

Write `.agents/toil-mining/YYYY-MM-DD-candidates.md` only when the caller asks for
a local artifact; otherwise return the report inline. Include checked and
not-checked sources. Do not include owners, priorities, claims, queues, or a next
action.

## References

- [Automation shape routing](../automation-shape-routing/SKILL.md)
- [CASS](../cass/SKILL.md)
