# Accreditation Frameworks — Generic Structures (Orientation Only)

> **⚠️ Version warning — read before using anything below.** These are *generic shapes*
> for orientation, so agents can ask the right questions. Accreditation bodies revise
> criteria, renumber outcomes, and change evidence expectations between cycles; what is
> sketched here may be outdated for the professor's review cycle the day it is read.
> **The mapping target is always the actual current verbatim text the professor
> supplies** — from their accreditation office or the body's published criteria for the
> relevant cycle. Nothing in this file is ever quoted into a register, matrix, or
> self-study as if it were the standard.

## Generic shape: ABET EAC (engineering programs)

- **Student outcomes**: a numbered set (the long-standing structure is outcomes 1–7:
  problem solving, design, communication, ethical/professional responsibility,
  teamwork, experimentation, lifelong learning — *shape only; verify numbering and
  text for the cycle*).
- **Continuous improvement expectation**: documented assessment processes, results,
  and evidence that results drive program changes — not one-time snapshots.
- **Evidence expectation**: direct measures of student work tied to each outcome;
  indirect measures (surveys, exit interviews) supplement, never substitute.
- Mapping is usually course-level → student outcome, with attainment data at the
  program level.

## Generic shape: AACSB (business schools)

- Organized around an **Assurance of Learning (AoL) cycle**:
  goals → measures → results → improvements, repeated and documented.
- Learning goals are the school's own (not a fixed national list), so the register
  depends entirely on professor-supplied program goals.
- Reviewers look for **closed loops**: a result that triggered a change, and evidence
  the change was made — exactly what the passport's `iteration_history[]` records.

## Generic shape: regional / institutional program review

- Periodic self-study against institution-defined criteria: program outcomes, curriculum
  map, assessment results, improvement actions, resource narrative.
- The template, attainment thresholds, and calculation method are institutional —
  always `[NEEDS PROFESSOR INPUT]`.

## Generic shape: 中国工程教育专业认证 (Chinese engineering education accreditation)

- **OBE orientation** (成果导向): 培养目标 → 毕业要求 → 课程体系, audited top-down.
- **毕业要求**: 12 generic categories (工程知识、问题分析、设计/开发解决方案、研究、
  使用现代工具、工程与社会、环境和可持续发展、职业规范、个人和团队、沟通、项目管理、
  终身学习 — *shape only; verify against the current 认证标准*). Each is decomposed by
  the institution into **指标点** (indicator points) — the 指标点 are
  institution-specific and are usually the actual mapping target.
- **课程目标达成评价**: per-course attainment evaluation against 课程目标, rolled up
  to 毕业要求 attainment; calculation methods are institutional.
- **持续改进**: documented evaluate → improve → re-evaluate loops; the same closed-loop
  logic as AACSB AoL, with heavier emphasis on quantified attainment (达成度).

## Common vocabulary

| Term | Meaning |
|------|---------|
| Direct measure | Evaluation of actual student work against the outcome (exam items, rubric-scored projects, 课程考核) |
| Indirect measure | Perception or proxy data (surveys, exit interviews, employment data, 问卷) |
| Triangulation | Multiple measures converging on the same outcome claim |
| Closing the loop / 持续改进 | Results → change → re-measurement, documented |
| Attainment / 达成度 | Proportion or score level at which a cohort meets an outcome threshold (calculation method is institutional) |
| Curriculum map / 课程矩阵 | The course × outcome matrix this skill builds |

## Evidence-type taxonomy (used by this skill)

| Type | What it is | Examples |
|------|-----------|----------|
| **Direct** | Student work measured against the outcome | tagged exam items + distributions, rubric-scored project results |
| **Indirect** | Perceptions and proxies | course surveys, alumni/employer feedback |
| **Process** | Evidence the system works | assessment plans, meeting records, `iteration_history` change records |

A criterion's register entry records which type(s) it demands; the evidence index
records which type each item actually is. A type mismatch is a finding, not a fit.

## Mapping anti-patterns (and the honest alternative)

| Anti-pattern | What it looks like | Why it fails | Honest practice |
|--------------|-------------------|--------------|-----------------|
| **Over-mapping** | Every LO claims to support nearly every criterion | An all-X matrix carries no information; reviewers discount it wholesale | Map each LO to the 1–3 criteria it genuinely serves; empty cells are fine |
| **Level inflation** | Every cell marked "Master"; every attainment "excellent" | Implausible uniformity invites the hardest scrutiny | Use the I/R/M spread honestly — Introduce cells are expected and credible |
| **Evidence theater** | Retro-tagging instruments that never measured the outcome; relabeling indirect as direct | Collapses the first time a reviewer pulls the thread | A gap finding plus a real fix (tag next term's items properly) — `gap` mode exists for this |
| **Last-minute retrofitting** | Building the whole map the month before the visit, from memory | Memory-built maps are hollow by construction; no loop evidence exists | Map while teaching is current; let `iteration_history` accumulate the loop evidence as it happens |

The pattern behind all four: documentation drifting from teaching. This skill's
CLAIMED / EVIDENCED / HOLLOW labels exist to keep the drift visible — documentation of
real teaching, not theater about imagined teaching.
