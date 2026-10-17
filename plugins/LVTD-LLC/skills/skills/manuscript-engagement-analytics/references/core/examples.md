# Manuscript Engagement Analytics Examples

Synthetic examples for engagement audits.

## Value Map

| Section | Words | Cumulative | Takeaway | Risk |
|---------|-------|------------|----------|------|
| Introduction | 1,800 | 1,800 | Why the topic matters | Slow start, low action |
| Why people fail backups | 900 | 2,700 | Failure model | Useful but late |
| Make your first backup | 650 | 3,350 | Reader creates backup | First concrete payoff |
| Restore drill | 1,100 | 4,450 | Reader proves backup works | Strong value |

**Diagnosis**: The first concrete payoff arrives after about 3,350 words. Move a small backup exercise into the introduction or cut the setup.

## Heading Rewrite

| Weak Heading | Stronger Takeaway Heading |
|--------------|---------------------------|
| Networking Basics | Know Which Port Your Service Actually Uses |
| Backups | Restore Once Before You Trust A Backup |
| Security | Decide What You Are Willing To Expose |
| Docker | Keep App Data Out Of Disposable Containers |

## Comment Dropoff Interpretation

| Reader Data | Possible Meaning | Inspect |
|-------------|------------------|---------|
| Comments stop after Chapter 2 for most readers | Boredom or confusion before Chapter 3 | End of Ch. 1 and all of Ch. 2 |
| Comments cluster on one paragraph | Confusing claim or missing proof | That paragraph and surrounding setup |
| Readers skip a long background section | Value enabler placed too early | Whether the background can move later |
| Readers finish but do not apply advice | Effective reading, weak transfer | Add exercises, follow-up, or implementation examples |

## Script Output Interpretation

```text
| Line | Lvl | Heading | Words | Cumulative | Flags |
| 42 | 1 | Introduction | 2100 | 2100 | long-section,no-value-marker |
| 210 | 2 | Install The First Service | 780 | 2880 | value-marker |
```

**Interpretation**:
- The script found a long opening with no obvious value marker.
- The recommendation should inspect whether the introduction can deliver a concrete result earlier.
- Do not assume the heading has no value only because the heuristic flagged it.

## Revision Actions

| Risk | Better Action |
|------|---------------|
| Slow start | Open with a useful diagnostic, checklist, or small win. |
| Long theory run | Add a worked example after the first concept. |
| Vague headings | Rename headings as reader outcomes. |
| Comment dropoff | Cut preceding setup and add verification or payoff. |
| Hidden value | Promote the useful insight into heading and opening sentence. |

## Beta Data Table

```text
Reader | Last commented section | Stated reason | Follow-up needed
A | Ch. 2 DNS basics | None | Ask what made them stop.
B | Ch. 3 proxy lab | Command failed | Verify lab and add troubleshooting.
C | Ch. 2 DNS basics | "Got busy" | Inspect Ch. 2 value density anyway.
```
