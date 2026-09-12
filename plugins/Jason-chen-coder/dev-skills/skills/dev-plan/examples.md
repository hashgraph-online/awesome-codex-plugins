# Dev Plan Examples

These examples illustrate planning depth and evidence boundaries, not a mandatory transcript.

## Small scoped change

User: "基于现有产品列表组件，给空结果加一句文案，先给个简短 plan。"

Inspect the component and its relevant test or preview. Produce a compact draft with the actual target, text source, and rendering check. No architecture alternatives, invented reservations, independent consensus claim, or worktree approval is needed. Respect "先给 plan" and stop before implementation.

## Small diff, consequential behavior

User: "--quick 给管理员加一个清空共享 Redis 的按钮，出计划。"

Do not classify risk by file count. Inspect existing authorization, cache ownership, and operational boundaries. Surface server-side permission checks, confirmation behavior, auditability, blast radius, and recovery limitations as relevant to the actual system. Clarify unresolved destructive scope before planning the endpoint; a small UI change does not establish authorization for a live flush. Explain why these risks need treatment despite the requested compact output.

## Real architectural choice

An accepted export spec requires asynchronous generation. Existing code provides a worker framework, but heavy exports could delay other jobs.

Compare actual supported options such as a dedicated queue in the existing worker system versus a separate service. Ground the recommendation in deployment and isolation constraints. A reviewer should inspect scheduling, timeouts, recovery, and the AC-to-verification mapping. They may approve with no reservations when evidence supports it; no contrived objection is required.

## Independent review unavailable

A migration plan needs review, but the runtime provides no delegation.

Perform a careful self-check, record that independent review was unavailable, and leave the artifact `DRAFT` unless the user accepts it. Renaming sections Planner, Architect, and Critic does not make the review independent.

## User has already authorized the workflow

User: "按这个已确认 spec 制定计划并实施，直接在当前目录做，别动已有的其他修改。"

Inspect the dirty baseline, draft a proportional plan, and continue authorized implementation once the contract is usable. Do not demand another worktree choice or skill invocation. Preserve existing unrelated changes and identify any real conflict before dependent edits.
