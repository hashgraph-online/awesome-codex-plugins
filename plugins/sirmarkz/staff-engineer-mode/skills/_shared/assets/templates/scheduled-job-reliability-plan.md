# Scheduled Job Reliability Plan

| Field | Value |
| --- | --- |
| Job / trigger | <name, schedule or event, time-zone basis> |
| Run contract | <what one successful run guarantees; acceptable lateness> |
| Idempotency | <dedup key / window; partial-progress checkpoint> |
| Overlap policy | <singleton / leader / bounded; skip-or-queue on overlap> |
| Fencing Token/Generation | <resource-enforced stale-holder rejection, or equivalent proof> |
| Stale-Holder Test | <paused old holder resumes after reassignment and is rejected> |
| Time basis | <time zone; daylight-saving and leap handling> |
| Deadline | <per-run deadline; overrun behavior> |
| Missed/stuck detection | <expected-by alert; stuck-run alert> |
| Catch-up policy | <backfill / collapse / skip; rate bound> |
| Completion evidence | <run/generation/start/end/outcome/window record> |
| Run-record safety | <prohibited sensitive fields; redaction; access; retention; disposal> |
| Owner | <owner; review cadence> |
