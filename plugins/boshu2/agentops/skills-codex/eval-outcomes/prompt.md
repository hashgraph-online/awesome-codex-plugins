# eval-outcomes

Holdout-safe Outcomes grading: project the locked eval substrate into a rubric, grade, then ingest one verdict.

## Instructions

Load and follow the skill instructions from the sibling `SKILL.md` file for this skill. Apply the three-phase workflow — `ao eval outcomes compile` (holdout-safe rubric) → grade locally (Inspect AI dev split or the bushido Qwen grader) → `ao eval outcomes ingest <score.json> --json` (one council verdict record). Never send holdout `target`/`ground_truth`/PII; carry `judge_content_hash`; register a global Dolt burn for holdout grades.
