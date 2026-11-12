# Workflow Routing

> Classify the requested output, add only the stages whose artifacts the job consumes, and run them in one fixed order.

## 1. Classify the Job

Decide the job from the requested output, then confirm it with repository files. Read the request first, then only the files a signal names.

| Job class | Requested output | Example words |
|---|---|---|
| Build | Changed code: a feature, fix, refactor, migration, or adoption; a data model, schema, database migration, tuned query or index, or database operations change; an MCP server, client, or host configuration; a designed or restyled interface or a faux product UI; a user, client, or planner change request applied to existing behavior; one generated or edited image or one image prompt; a readiness verdict, deployment setup, deploy, deployment configuration change, or deployment fix; or a created or refactored skill folder, document, or prompt artifact | 만들어, 추가해, 고쳐, 리팩토링해, 옮겨, 적용해, 연결해, 스키마 설계해, 인덱스 잡아줘, 디자인해, 리디자인해, AI 티 빼줘, 피드백 반영해, 요청대로 바꿔줘, 배포해, 배포 설정해, 배포 실패 고쳐, 점검해, 스킬로 만들어, 문서로 정리해, 프롬프트 만들어, implement, refactor, migrate, connect, redesign, apply this feedback, generate an image, deploy, ship to staging |
| Report | A saved report, audit, review, or plan with no code change | 조사만, 점검만, 리뷰만, 리포트만, 계획만, audit only, just the plan |
| Resume | An earlier run continued | 이어서, 계속, 재개, resume, continue |

A request that is a one-place edit with no plan (a typo, one string, one config value), a commit-only request, a PRD or wireframe package, a diagram or visual map of a structure, or a question is out of scope: do not route it. A PRD package goes to `hyper-prd` and a diagram to `hyper-diagram`; both are separate skills that this package never uses as stages.

## 2. Stage Signals

Add a stage only when one of its signals is present. Quote the signal in the route line.

| Stage | Add it when | Evidence to quote |
|---|---|---|
| `hyper-research` | The job depends on facts outside the repository: choosing between libraries or services, a new major version, an unfamiliar external API, or "최신" / "latest" behavior | The request phrase |
| `hyper-issue` | The request asks to register or record issues ("이슈 등록해줘", "이슈로 남겨줘", "register these as issues"), names issue numbers (`#1~3`, `#4, #7`, `1~3번 이슈`), names a condition over open issues to select and group, or names an issue whose scope or acceptance is missing | The request phrase, plus the tracker and the named numbers, label, or query |
| `hyper-seo` | The job is about search or AI-answer visibility of a named site or page set | The request phrase and the target URL or app path |
| `hyper-google-analytics` | The output is GA4 work: installing or fixing GA4 or the Google tag on a site, auditing a GA4 property or its tag, changing property settings (custom dimensions, key events, retention, filters), analyzing GA4 report data, or finding why GA4 data is missing or wrong | The request phrase, plus the tag file that was read: a file containing `gtag(`, `googletagmanager.com`, a `G-` measurement ID, or `@next/third-parties/google` |
| `hyper-google-tagmanager` | The output is Google Tag Manager work on a website: installing GTM, auditing a GTM install or a container export, changing container tags, triggers, variables, templates, consent settings, or the dataLayer, verifying that tags fire, diagnosing missing or duplicate tracking that passes through GTM, or analyzing a container | The request phrase, plus the file that was read: a file containing a `GTM-` container ID, `googletagmanager.com/gtm.js`, a `dataLayer` push, or `GoogleTagManager` from `@next/third-parties/google`, or a container export JSON |
| `hyper-architecture` | The job restructures folders, routes, modules, data or server boundaries, or platform setup; adds a feature that creates a new route, module, or server boundary; sets up or unifies the lint, format, and type tooling (oxlint, Prettier, rustfmt, clippy); or optimizes build or runtime performance | The request phrase plus a stack manifest that was read, such as `package.json` or `Cargo.toml` |
| `hyper-database` | The job designs or reviews a data model or schema, writes or reviews a database migration or backfill, tunes a slow query, an index, a hot key, or a hot partition, chooses a database engine or managed data service, or changes database operations (backup and restore, replication and failover, connection pooling, upgrades, database security, monitoring) | The request phrase, plus the schema, migration, ORM, or driver file that was read when one exists, such as `schema.prisma`, `drizzle.config.ts`, a `migrations/` folder, `pg` or `ioredis` in `package.json`, or a database image in a compose file |
| `hyper-mcp` | The job builds, fixes, migrates, audits, or connects an MCP (Model Context Protocol) server, client, or host MCP configuration, or prepares MCP registry metadata | The request phrase, plus the MCP dependency or configuration file that was read when one exists, such as `@modelcontextprotocol/*` in `package.json`, `mcp` in `pyproject.toml`, `.mcp.json`, or `server.json` |
| `hyper-decision` | The job designs, writes, wires, evaluates, audits, or routes a decision-API call: a model call that returns a typed judgment (a yes/no probability, one option from a closed set, an ordered score, an image box) instead of text, through TypeSafe Jev, OpenAI Decisions, another decision vendor, the Vercel AI SDK or AI Gateway, OpenRouter, or an emulation on a general LLM; or it audits existing LLM calls that only return a label | The request phrase, plus the decision dependency or call that was read when one exists, such as `@typesafe-ai/sdk`, `typesafe-sdk`, `@ai-sdk/typesafe-ai`, `experimental_decide` or `client.decisions.create` in code, or `api.typesafe.ai` in a config file |
| `hyper-design` | The requested output is an interface whose look is the point: a new screen, page, or component designed, an existing UI restyled, faux product UI for a hero, card, or demo, a design brief or `DESIGN.md`, or generic "AI look" patterns audited or removed | The request phrase, plus the target UI path and the styling or design-system file that was read when one exists, such as `DESIGN.md`, a tokens file, or `tailwind.config.*` |
| `hyper-frontend` | The requested output is working frontend behavior or layout inside a defined look: a component, page, or form built, a layout, overflow, responsive, state, or animation defect fixed, an interface matched to a screenshot, mockup, or live page, or existing UI checked in a real browser, with words such as "레이아웃 깨져", "반응형", "스크롤이 이상해", "상태마다 흔들려", "스크린샷대로 똑같이", "브라우저에서 확인", "fix the overflow", "match this mockup" | The request phrase, plus the target UI path and the framework manifest that was read, such as `package.json` with `react`, `vue`, `svelte`, or `astro` |
| `hyper-feedback` | The input is a change request in product language against existing behavior: feedback, a complaint, a ticket, meeting notes, a revised spec line, or new wording from the user, a client, or a planner, directly or relayed, and the user wants it worked out and applied ("알아서 파악해서 고쳐", "피드백 반영해", "이 메모대로 반영") | The request phrase, plus the quoted feedback text and its author or relay path |
| `hyper-debug` | The input is a runtime failure to explain or fix outside a deployment: a stack trace, a failing or intermittent test, a crash, or wrong output, with words such as "왜 실패하는지", "에러 원인", "flaky test", "why does this fail" | The request phrase, plus the failing command, test name, or trace excerpt that was read |
| `hyper-cleanup` | The requested output is a behavior-preserving cleanup of code that already works: remove, simplify, deduplicate, or consolidate code, comments, or tests while the observable behavior and the public surface stay the same, with words such as "정리해줘", "군더더기 지워줘", "clean up", "remove dead code", "deduplicate" | The request phrase, plus the file set that was read when one is named |
| `hyper-data` | The requested output is an answer computed from a dataset (a CSV, Parquet, or JSON file, a spreadsheet export, or a database export): a count, a total, a trend, a comparison, or a chart the user asked for, with words such as "이 CSV에서", "데이터 분석해서", "집계해줘", "how many rows" | The request phrase, plus the dataset path that was read |
| `hyper-review` | The requested output is a verdict on a change that already exists, with no edit requested: a named diff, commit range, branch, pull request, or the working tree, signalled by words such as "리뷰만", "판정만", "고치지는 마", "review this diff", "review the PR", "can this merge" | The request phrase, plus the diff, branch, PR number, or working-tree state that was read |
| `hyper-handoff` | The requested output is a continuation memo, a check of one, or a session that resumes from one: the context is nearly full, a compaction or a switch of session, agent, or machine is pending, or the user asks for a handoff, a continuation note, or to continue from a memo, with words such as "핸드오프 써줘", "write a handoff". A resume needs a named memo path, an open memo under `.hyper/handoff/` that matches the current branch or worktree, or an open run to continue; "이어서 해줘" with none of those is not this stage | The request phrase, plus the memo path when one is named |
| `hyper-imagegen` | The whole requested output is one new image, one edit of a supplied image, or one ready-to-use image prompt | The request phrase, plus the supplied edit source or reference path when one exists |
| `hyper-plan` | A Build job touches several files or steps, or a Report job asks for a plan, with no explicit adversarial opt-in | The request phrase |
| `hyper-debate` | The user explicitly asks for adversarial, multi-perspective, or devil's-advocate planning: "여러 관점으로 따져보고 계획", "찬반으로 붙여서 계획", "반대 의견까지 붙여서 계획", "adversarial planning", "devil's advocate plan", "red team this plan", "debate it then plan". The opt-in must be in the user's own words in this turn; a hard problem described without those words is an ordinary plan | The request phrase that carries the opt-in |
| `hyper-execute` | Only as the first stage: a plan file under `.hyper/plans/` already exists and the user wants it run or resumed | The plan path that was read |
| `hyper-mass` | The user asks for a dependency graph, a DAG, "의존성 그래프", "단계별 병렬", or several tasks where some must finish before others start, and no plan file is wanted | The request phrase |
| `hyper-loop` | The request is several goals that depend on each other and must all be finished, each with its own acceptance criteria that need fresh evidence ("목표 여러 개 끝까지", "이 목표들 다 끝날 때까지 돌려", "keep going until every goal passes"), or a stopped loop under `.hyper/loop/<slug>/` is resumed | The request phrase, or the `.hyper/loop/<slug>/goals.json` path that was read |
| `hyper-skill` | The requested output is a reusable skill folder: a new skill, or a refactor of an existing skill's trigger, contract, resources, or validation | The request phrase, plus the target `skills/<name>/SKILL.md` when it already exists |
| `hyper-documentation` | The requested output is a documentation artifact, new or refactored: a README, an `AGENTS.md`, an AI-readable document (instruction base, agent guide, runbook, specification, or rule pack), or a reusable prompt artifact (role, system, or agent prompt, prompt template or pack, or prompt eval fixture) | The request phrase, plus the target path when it already exists |
| `hyper-git` | After a tail that does not deliver (`hyper-skill`, `hyper-documentation`, `hyper-feedback`, `hyper-debug`, `hyper-loop`, or `hyper-database`, `hyper-mcp`, `hyper-decision`, `hyper-design`, `hyper-frontend`, `hyper-google-analytics`, or `hyper-google-tagmanager` as the last build stage), when the user asks to commit and push or to merge into named branches and push; after any of those tails (a debug stage that ended `fixed` or a loop stage that ended `complete` included) also for a pull request, except `hyper-database`, `hyper-mcp`, `hyper-decision`, `hyper-design`, and `hyper-frontend`, which route a PR through `hyper-plan`. It runs before `hyper-deploy` when the same chain also deploys. Never after `hyper-imagegen`, whose artifact is the delivered image or the gitignored `.hyper/imagegen/` file, and never after `hyper-deploy` | The delivery phrase and the named target branches |
| `hyper-deploy` | The job is a deployment or a deployment finding: a readiness verdict, a first deployment setup, a deploy to a named environment, a change to an existing deployment's settings, or a failed or unhealthy deployment to diagnose and fix | The request phrase, plus the deployment file that was read, such as `Dockerfile`, `compose.yaml`, `wrangler.jsonc`, `.railway/railway.ts`, `railway.toml`, or `config/deploy.yml` |

## 3. Stage Order

Chosen stages always run in this order. Skip the ones that were not chosen.

```text
hyper-research -> hyper-issue -> hyper-seo -> hyper-google-analytics -> hyper-google-tagmanager -> hyper-architecture -> hyper-database -> hyper-mcp -> hyper-decision -> hyper-design -> hyper-frontend -> hyper-feedback -> hyper-debug -> hyper-review -> hyper-cleanup -> (hyper-plan [-> hyper-execute] | hyper-debate [-> hyper-execute] | hyper-mass | hyper-loop | hyper-execute | hyper-data | hyper-handoff (write | check) | hyper-skill | hyper-documentation | hyper-imagegen) [-> hyper-git] [-> hyper-deploy]
resume re-entry, no chain position: hyper-handoff (resume) -> the first unfinished stage of the open run
```

`hyper-handoff` in write or check mode is a tail on its own and nothing follows it. In resume mode it is a re-entry step, not a tail: it runs first, takes no chain position, and does not count toward the four-stage cap. After its three-line restatement the router resumes the open workflow record at its first unfinished stage, or the run the memo's `Where` names through that run's own stage, or routes the remaining work as a normal request when no record exists. Delivery stages follow only on delivery words in the user's current request, never on words quoted inside the memo.

When both delivery brackets are chosen, `hyper-git` runs first and `hyper-deploy` last; nothing runs after `hyper-deploy`.

- Upstream stages (`hyper-research`, `hyper-seo`, `hyper-architecture`) produce evidence for the tail. In a Build job they run in report mode; the tail makes the code change.
- `hyper-google-analytics` is a last build stage: it edits the site code and the property settings itself and proves collection, so `hyper-git` may follow it like `hyper-database`. It runs before `hyper-git` and `hyper-deploy` when the same chain also delivers or deploys, and it never follows `hyper-deploy`. When `hyper-seo` is chosen too, `hyper-seo` runs first and this stage measures the result.
- `hyper-google-tagmanager` is a last build stage like `hyper-google-analytics`: it edits the site code that loads GTM, drafts container changes or publishes them after approval, and proves firing itself, so `hyper-git` may follow it. When `hyper-google-analytics` is chosen too, the property settings run first and this stage sends data to them. It runs before `hyper-git` and `hyper-deploy` and never follows `hyper-deploy`.
- `hyper-database` is the tail when it is the last chosen stage: it designs the schema, writes the online migration, tunes the query or index, or changes the operations setup and verifies the result itself. When `hyper-plan` or `hyper-mass` follows it, it runs in review mode (design brief, schema or migration review, or engine choice) and its saved report is the plan's input.
- `hyper-mcp` is the tail when it is the last chosen stage: it builds, fixes, migrates, or connects and verifies the result itself. When `hyper-plan` or `hyper-mass` follows it, it runs in audit mode and its report is the plan's input.
- `hyper-decision` is the tail when it is the last chosen stage: it writes the decision artifact (questions, a caller, a template, an eval plan, an audit table, or a route setup) and runs its offline request checker itself. When `hyper-plan` or `hyper-mass` follows it, it runs in `design` or `audit` mode and its saved decision contract or audit table is the plan's input.
- `hyper-design` is the tail when it is the last chosen stage: it designs, restyles, mocks up, or cleans the interface and verifies it itself. When `hyper-plan` or `hyper-mass` follows it, it runs in `brief-only` mode for an interface that does not exist yet or in `audit` mode for an existing one, and its saved brief or report is the plan's input.
- `hyper-frontend` is the tail when it is the last chosen stage: it builds, fixes, matches, or checks the frontend and proves it in a rendered browser itself. When `hyper-plan` or `hyper-mass` follows it, it runs in `verify` mode and its saved report is the plan's input. When `hyper-design` is chosen too, `hyper-design` runs first in `brief-only` mode and `hyper-frontend` builds inside that brief.
- `hyper-feedback` is the tail when it is the last chosen stage: it applies every item within its direct-edit budget and verifies it itself. When its run ends `handoff`, `hyper-plan` is added after it in the same run with `.hyper/feedback/<slug>/brief.md` as required reading; the route line shows that conditional stage as `hyper-feedback [-> hyper-plan]`. When it ends `applied`, no plan stage runs.
- `hyper-debug` is the tail when it is the last chosen stage: it reproduces the failure, proves the cause with a toggle, and, only when the user asked for a fix, applies the minimal fix with red-to-green proof. When its run ends `handoff` (the confirmed fix spans several files), `hyper-plan` is added after it in the same run with `.hyper/debug/<slug>.md` as required reading; the route line shows that conditional stage as `hyper-debug [-> hyper-plan]`. When it ends `confirmed`, `fixed`, or `unconfirmed`, no plan stage runs.
- `hyper-debate` replaces `hyper-plan` when the user explicitly opts into adversarial, multi-perspective, or devil's-advocate planning, and it continues into `hyper-execute` by itself like the plan stage. Never chain both: the debate writes the plan, so a chain that names both is the debate chain with the plan stage dropped. A request with no adversarial opt-in in the user's own words stays on `hyper-plan`, and the debate never becomes the default because a problem is hard.
- `hyper-issue` produces evidence for the tail, like the other upstream stages: it registers the issues and writes the lane manifest, and `hyper-plan` turns each manifest lane into one parallel lane of its waves. Registration words or issue numbers continue into `hyper-plan` by default, so the run ends only after the lanes are executed and delivered. Only record-only words ("등록만", "이슈만", "작업은 하지 마", "manifest only") make `hyper-issue` the last stage.
- A request handed over by `hyper-issue` itself (it names `.hyper/issues/<slug>/batch.md` and says the issue stage is done) does not run `hyper-issue` again: record it as stage 1 `done` with the manifest path, and start at `hyper-plan`.
- Otherwise the tail is exactly one of: `hyper-plan` (which continues into `hyper-execute` by itself, and which `hyper-debate` replaces on an explicit adversarial opt-in), `hyper-mass`, `hyper-loop` for several dependent goals with criteria, `hyper-cleanup` for a behavior-preserving cleanup, `hyper-data` for an answer computed from a dataset, `hyper-execute` alone for an existing plan, `hyper-skill` for a skill folder, `hyper-documentation` for a document or prompt artifact, `hyper-handoff` in write or check mode for a continuation memo, or `hyper-imagegen` for one image or one image prompt. A resume from a memo is not a tail: it re-enters the open run first (§3).
- `hyper-loop` is the tail when it is chosen: it keeps `.hyper/loop/<slug>/` (`brief.md`, `goals.json`, `ledger.jsonl`, `final-gate.json`), runs the goals in dependency order, and finishes only when `final-gate.json` has `status` `complete`. It may commit inside goals but never pushes, merges, or opens a pull request, so delivery words add `hyper-git` after it.
- `hyper-git` is never a tail on its own: it runs after a tail that changed files but owns no delivery. `hyper-plan`, `hyper-execute`, and `hyper-mass` deliver for themselves, so `hyper-git` never follows them.
- `hyper-deploy` is the last stage of a chain: it deploys the result the earlier stages produced, and no stage ever follows it. When the user also asks for commit, push, or merge delivery, `hyper-git` runs before `hyper-deploy`.
- When the request also changes code, the code chain runs first and the `hyper-deploy` stage starts after the execution completion block, so it deploys the finished change rather than a half-built tree.
- In a Report job the chain ends at the last requested stage. A Report job that asks for a plan ends at `hyper-plan` with `--plan-only`.
- At most four distinct core stages run, counted this way:
  - Each stage in the route line counts once, including a stage that is also the initial selection and including a stage added by the one allowed re-route (§6 of `rules/stage-handoff.md`).
  - `hyper-deploy` counts as one of the four.
  - A retry of a stage, a resumed run, and a stage that is re-entered after its own stop all count as the stage that already counted, not as a new one.
  - `hyper-plan` and `hyper-debate` are one decision stage: a chain names one of them, never both, so the pair never spends two slots.
  - `hyper-plan` continuing into `hyper-execute` counts as two stages, because the plan and the run are separate stages even though one session runs them.
  - `hyper-execute` chosen alone for an existing plan counts as its own stage, with no plan stage before it.
  - `hyper-git` never counts, and the companion skill below never counts either.
  - `hyper-handoff` in resume mode takes no chain position and does not count; in write or check mode it is the tail and counts.
  - A chain that seems to need a fifth counted stage is two jobs: run the first, and report the second as the next step.
- `hyper-browsing` is a companion, not a stage: it takes no position in this order and does not count toward the four-stage cap. Attach it to the `hyper-research` stage when the research is web-sourced - the question depends on live web sources (search results, vendor, community, or news pages, market or trend data, external documentation, a named URL), signalled by words such as "인터넷 검색", "웹에서", "최신", "동향", "사례", "latest", or a URL. Do not attach it when the research is repository-only (source-code analysis, local files and history), or when no `hyper-research` stage is chosen.

## 4. Chain Recipes

| Job | Chain |
|---|---|
| Architecture review only | `hyper-architecture` |
| Lint, format, or type tooling set up or unified, or build or runtime performance optimized | `hyper-architecture` alone, as the last stage that makes the edits |
| Refactor or restructure | `hyper-architecture` -> `hyper-plan` |
| Feature or fix across several files | `hyper-plan` |
| Feature or fix with an explicit adversarial opt-in ("찬반으로 붙여서 계획", "red team this plan", "debate it then plan") | `hyper-debate` |
| Feature that adds a route, module, or server boundary | `hyper-architecture` -> `hyper-plan` |
| Library or technology choice, then adoption | `hyper-research` -> `hyper-plan` |
| Issue record only, or a batch manifest only ("등록만", "명세만") | `hyper-issue` |
| Issues registered, or issue numbers named, then the lanes implemented ("이슈 등록해줘", "#1~3 작업해줘") | `hyper-issue` -> `hyper-plan` |
| Hand-off from `hyper-issue` with a manifest | `hyper-plan`, with `hyper-issue` recorded as `done` |
| Unfamiliar external facts behind the issue's fix | `hyper-research` -> `hyper-issue` -> `hyper-plan` |
| Framework or major-version migration | `hyper-research` -> `hyper-architecture` -> `hyper-plan` |
| Schema designed, migration written, query or index tuned, or database operations changed | `hyper-database` |
| Database review, engine choice, or design brief only | `hyper-database` in review or choose mode, alone |
| Engine or data service the repository does not use yet ("Valkey로 옮겨", "DynamoDB 도입") | `hyper-research` -> `hyper-database` |
| Database change delivered as a PR or ship, or one that also changes application code | `hyper-database` (review) -> `hyper-plan` |
| MCP server or client built, fixed, migrated, or connected | `hyper-mcp` |
| MCP audit or report only | `hyper-mcp` in audit mode, alone |
| MCP server that wraps an unfamiliar external API ("Notion API를 MCP로") | `hyper-research` -> `hyper-mcp` |
| MCP change delivered as a PR or ship, or one that also changes non-MCP modules | `hyper-mcp` (audit) -> `hyper-plan` |
| Decision-API questions, caller, template, eval plan, audit, or route setup ("결정 모델로 바꿔", "Jev 질문 설계", "OpenAI Decisions 호출 코드") | `hyper-decision` |
| Decision-API route or vendor that its references do not cover ("새로 나온 결정 모델 붙여줘") | `hyper-research` -> `hyper-decision` |
| Decision-API change delivered as a PR or ship, or one that rewires calls across the application ("라벨만 돌려주는 LLM 호출 전부 바꾸고 PR까지") | `hyper-decision` (`design` or `audit`) -> `hyper-plan` |
| Interface designed, restyled, mocked up, or cleaned of generic patterns | `hyper-design` |
| Interface audit or design direction only | `hyper-design` in `audit` or `brief-only` mode, alone |
| Interface work delivered as a PR or ship, or one that also needs API, data, or route changes | `hyper-design` (`audit` or `brief-only`) -> `hyper-plan` |
| Interface that depends on current external guidance ("최신 가이드라인 확인해서") | `hyper-research` -> `hyper-design` |
| Frontend built, fixed, matched to a screenshot or live page, or checked in a browser ("레이아웃 깨져", "스크린샷대로 똑같이", "check it at phone width") | `hyper-frontend` |
| Frontend check only ("확인만 해줘", "don't edit") | `hyper-frontend` in `verify` mode, alone |
| New look plus a frontend build whose states, responsive behavior, or motion must be proven in a browser | `hyper-design` (`brief-only`) -> `hyper-frontend` |
| Frontend work delivered as a PR or ship, or one that also needs API, data, or route changes | `hyper-frontend` (`verify`) -> `hyper-plan` |
| Change request from the user, a client, or a planner applied to existing behavior | `hyper-feedback` |
| Same, with items over the direct-edit budget (a new route, a schema change, an API contract) | `hyper-feedback` -> `hyper-plan`, the plan stage added when the feedback stage ends `handoff` |
| Change request that depends on current external facts ("최신 정책에 맞게 바꿔달래") | `hyper-research` -> `hyper-feedback` |
| Runtime failure explained, cause only ("원인만 찾아줘", "why does this test fail") | `hyper-debug` in findings-only mode |
| Runtime failure explained and fixed ("에러 원인 찾아서 고쳐줘", "flaky test 잡아줘") | `hyper-debug`, with `hyper-plan` added when the debug stage ends `handoff` |
| Runtime failure in an unfamiliar library or service whose current behavior must be checked first | `hyper-research` -> `hyper-debug` |
| Finished change reviewed with a verdict only ("리뷰만 해줘", "이 브랜치 판정만", "review PR #412") | `hyper-review` in review-only mode, alone |
| Finished change reviewed and the confirmed blockers fixed ("리뷰하고 확인된 것만 고쳐줘") | `hyper-review` in review-and-fix mode, alone; `hyper-git` only on commit-and-push words in the same request |
| One image created, one supplied image edited, or one image prompt written | `hyper-imagegen` |
| Image that depends on current external guidance or references ("최신 프롬프트 가이드 참고해서") | `hyper-research` -> `hyper-imagegen` |
| Research report only | `hyper-research` |
| Behavior-preserving cleanup of working code, tests, or comments ("군더더기 정리해줘", "remove dead code and prove it") | `hyper-cleanup`, alone; a change that moves a public API, a signature, a dependency, or behavior is a different stage |
| Question answered from a dataset ("이 CSV에서 월별 매출 집계해줘", "how many orders per region in this export") | `hyper-data` |
| Continuation memo written or checked ("핸드오프 써줘", "컨텍스트 거의 찼어, 새 세션에서 이어서") | `hyper-handoff` in write or check mode, alone |
| Continue from a memo ("memo.md 읽고 이어서 해줘", "continue from the memo") | `hyper-handoff` in resume mode first, then the open run at its first unfinished stage; a delivery stage only when the current request carries delivery words |
| SEO audit or report only | `hyper-seo` |
| SEO score loop ("최대 점수까지", "keep improving the score") | `hyper-seo` in its optimize mode, alone |
| SEO fixes implemented as a planned change | `hyper-seo` -> `hyper-plan` |
| GA4 installed or fixed on a site ("사이트에 GA4 달아줘") | `hyper-google-analytics` |
| GA4 installed or fixed, then merged and pushed ("GA4 달고 dev에 머지·푸시") | `hyper-google-analytics` -> `hyper-git` |
| Search-visibility audit, then GA4 measurement set up ("SEO 점검하고 GA4 측정까지 세팅해줘") | `hyper-seo` -> `hyper-google-analytics` |
| GA4 report data analyzed for the last month ("지난달 GA 유입 데이터 분석해서 리포트 줘") | `hyper-google-analytics` in `analyze` mode, alone |
| GTM installed, audited, configured, verified, or diagnosed ("GTM 달아줘", "태그가 두 번 잡혀", "audit our GTM container") | `hyper-google-tagmanager` |
| GA4 property settings changed, then the GTM container wired to send them ("맞춤 측정기준 만들고 GTM 태그도 고쳐줘") | `hyper-google-analytics` -> `hyper-google-tagmanager` |
| GTM work, then merged and pushed ("GTM 달고 dev에 머지·푸시") | `hyper-google-tagmanager` -> `hyper-git` |
| Dependency-ordered multi-agent phase | `hyper-mass`, with upstream stages before it when their signals are present |
| Several dependent goals to finish, each with criteria that need fresh evidence ("이 목표들 다 끝날 때까지", "finish all of these goals") | `hyper-loop`, with upstream stages before it when their signals are present |
| Stopped multi-goal loop resumed ("루프 이어서") | `hyper-loop`, resuming from `.hyper/loop/<slug>/` |
| Existing plan run or resumed | `hyper-execute` |
| Skill folder created or refactored | `hyper-skill` |
| Skill folder that depends on current provider docs ("최신 규격", "latest spec") | `hyper-research` -> `hyper-skill` |
| README, `AGENTS.md`, document, rule pack, reusable prompt, template, pack, prompt eval fixture, or agent memory files (`MEMORY.md`, memory bank, lessons file) created or refactored | `hyper-documentation` |
| Document or prompt that depends on current external sources or provider guidance | `hyper-research` -> `hyper-documentation` |
| Skill folder, document, MCP, decision-API, interface, frontend, database, GA4 analytics, GTM, feedback, debug, or loop change, then commit and push ("커밋하고 푸시까지") | that chain -> `hyper-git` in commit mode |
| Same, then merge into named branches ("dev, main에 머지하고 푸시") | that chain -> `hyper-git` in commit mode with `&& <branch>` targets for this run's commits, or workflow mode when a whole work branch must be merged |
| Change from a non-delivering tail other than a database, MCP, decision-API, interface, or frontend job, then a pull request ("PR까지") | that chain -> `hyper-git` in workflow mode; an MCP, decision-API, interface, frontend, or database job with "PR까지" or "ship" keeps the review or audit -> `hyper-plan` route above |
| Deploy to a named environment ("배포해줘", "staging에 올려줘", "deploy it to staging") | `hyper-deploy` in `deploy` mode |
| Fix a failed, crashing, or unhealthy deployment ("배포 실패 고쳐줘", "로그 보고 원인 찾아서 고쳐줘") | `hyper-deploy` in `diagnose` mode |
| Pre-deploy readiness check ("배포 전 점검", "배포 전 검사만") | `hyper-deploy` in `preflight` mode, with validate-only when the user says "고치지 말고" |
| First deployment configuration for a repository that has none, then a non-production deploy | `hyper-deploy` in `setup` mode, then its `deploy` phases |
| Change an existing deployment's variables, health check, or platform settings, then redeploy | `hyper-deploy` in `change` mode, then its `deploy` phases |
| Deployment on a platform the repository and the skill's target guides do not cover | `hyper-research` -> `hyper-deploy` |
| Code change and then deploy ("기능 고치고 배포까지", "Fix the bug and deploy it to staging") | `hyper-plan` -> `hyper-deploy`; the plan stage continues into `hyper-execute` itself, and the deploy stage starts after its execution completion block |

Each `hyper-plan` row continues into `hyper-execute` unless the job is a Report job.

## 5. Tie-Breaks

- A stage the user names inside a longer request ("hyper-research로 조사하고 바로 적용해") is chosen, and the other stages still follow the signals.
- A request whose whole output is one blocked page's content ("이 403 페이지 본문만 가져와") is not a `hyper` job: `hyper-browsing` handles it alone. A blocked source met while researching stays inside the `hyper-research` stage as its companion.
- `hyper-issue` never runs with `hyper-skill` or `hyper-documentation`; an issue record or a manifest is its own deliverable, and a skill folder or general document goes to its own stage.
- `hyper-issue` runs before `hyper-plan` whenever issues are registered or numbers are named, unless the user used record-only words; then the chain ends at `hyper-issue`.
- `hyper-mass` and `hyper-plan` never run in one chain. Choose `hyper-mass` only on its explicit signal; otherwise choose `hyper-plan`.
- `hyper-loop` never runs with `hyper-plan`, `hyper-mass`, or `hyper-execute` in one chain. Choose `hyper-loop` when the request names several goals that must all finish with per-goal criteria; one deliverable goes to `hyper-plan`, and an explicit dependency-graph phase goes to `hyper-mass`.
- Delivery words on a loop job go to `hyper-git` after the loop stage ends `complete`; a loop that ends `blocked` or `paused` does not start `hyper-git`.
- `hyper-skill` and `hyper-plan` never run in one chain. When the requested output is a skill folder, choose `hyper-skill`; a plan file is not its input.
- `hyper-documentation` never runs with `hyper-plan`. Choose by the primary deliverable: a README, `AGENTS.md`, document, or reusable prompt artifact goes to `hyper-documentation`, which picks its own mode, and a skill folder goes to `hyper-skill`.
- `hyper-mcp` and `hyper-skill` never run in one chain. When the requested output is a skill folder, even one about MCP, choose `hyper-skill`.
- `hyper-decision` and `hyper-skill` never run in one chain. When the requested output is a skill folder, even one about decision models, choose `hyper-skill`. A moderation policy, a classifier prompt, or a document about decision models goes to `hyper-documentation`.
- A request to train a classifier, fine-tune a model, or build a dataset pipeline is not a `hyper-decision` job; it routes by the existing rows. Add `hyper-decision` only when a model call that returns a typed judgment is the deliverable or the audit target.
- Delivery words ("PR까지", "ship") on a decision-API job put `hyper-decision` in `design` or `audit` mode before `hyper-plan`, because only the plan and execute stages own delivery.
- `hyper-mcp` and `hyper-architecture` both run only when the job also restructures non-MCP folders, routes, or modules; an MCP-only job routes to `hyper-mcp` without the architecture stage.
- Delivery words ("PR까지", "ship") on an MCP job put `hyper-mcp` in audit mode before `hyper-plan`, because only the plan and execute stages own delivery.
- `hyper-design` never runs with `hyper-skill` or `hyper-documentation` in one chain. A skill folder, a general document, or a prompt about design goes to its own stage; a project's `DESIGN.md` that records the product's visual system goes to `hyper-design`.
- A feature whose main output is behavior (a new API, a data flow, a fix) routes by the existing rows even when it has a screen; add `hyper-design` only when the request asks for the look itself ("디자인 신경 써서", "AI 티 안 나게", "redesign").
- Delivery words ("PR까지", "ship") on an interface job put `hyper-design` in `audit` or `brief-only` mode before `hyper-plan`, because only the plan and execute stages own delivery.
- `hyper-frontend` and `hyper-design` are decided by what the request asks for. The look itself, the direction, a craft floor, or a generic-pattern audit goes to `hyper-design`; layout mechanics, state and responsive behavior, motion safety, matching a concrete reference, or a rendered-browser check goes to `hyper-frontend`. Both run only when the request asks for a new look and also names behavior to build and prove in a browser, and then `hyper-design` runs first in `brief-only` mode.
- `hyper-frontend` never runs with `hyper-skill`, `hyper-documentation`, or `hyper-imagegen` in one chain; a skill folder, a document, or one image goes to its own stage. Native app UI (SwiftUI, UIKit, Compose) is not a `hyper-frontend` job and routes by the `hyper-design` and existing rows.
- A defect seen in the browser as a broken layout, an overflow, a shifting control, or a janky animation goes to `hyper-frontend`; a stack trace, a failing test, or a crash goes to `hyper-debug`; a product-language change request about wording or behavior goes to `hyper-feedback`.
- Delivery words ("PR까지", "ship") on a frontend job put `hyper-frontend` in `verify` mode before `hyper-plan`, because only the plan and execute stages own delivery. Commit-and-push words add `hyper-git` after the frontend stage.
- `hyper-imagegen` never runs with `hyper-plan`, `hyper-mass`, `hyper-skill`, `hyper-documentation`, or `hyper-design` in one chain. Choose by the primary deliverable: one image or one image prompt goes to `hyper-imagegen`; an interface that contains a picture goes to `hyper-design`; a reusable prompt pack or template for images goes to `hyper-documentation`; image analysis or critique is not a `hyper` job.
- A `hyper-imagegen` stage that ends `awaiting_input` asked its one question; the chain stops there and resumes on the answer.
- `hyper-feedback` never runs with `hyper-skill`, `hyper-documentation`, `hyper-imagegen`, `hyper-mass`, or `hyper-design` in one chain. A request whose look is the point ("리디자인", "AI 티 안 나게") goes to `hyper-design`; a change request about a skill folder or a document goes to that stage; an explicit dependency-graph request goes to `hyper-mass`.
- A product-language change request routes to `hyper-feedback` even when one item needs a schema, route, or API change: the stage applies the in-budget items and its `brief.md` carries the rest into `hyper-plan`. Add `hyper-architecture` or `hyper-database` before it only when the user asks for that review by name or words.
- A one-place edit that already names its location and new value ("이 버튼 문구 하나만 바꿔줘") is not a `hyper` job; a request with several items, an unknown location, or feeling-level wording ("복잡하대", "불편하대") routes to `hyper-feedback`.
- Delivery words on a feedback job go to `hyper-git` when the feedback stage ends `applied`; when it ends `handoff`, they pass to the added `hyper-plan` as its delivery flag and `hyper-git` is dropped, because the plan and execute stages deliver for themselves.
- A `hyper-feedback` stage that ends `awaiting_input` asked its one question; the chain stops there and resumes on the answer.
- A failed, crashing, or unhealthy deployment goes to `hyper-deploy`; a runtime failure reproduced in code, tests, or a local run goes to `hyper-debug`. `hyper-debug` and `hyper-deploy` run in one chain only when the user asks to deploy the fix, and then `hyper-deploy` follows the delivered fix.
- `hyper-debug` never runs with `hyper-feedback`, `hyper-skill`, `hyper-documentation`, `hyper-imagegen`, or `hyper-mass` in one chain. A stack trace, a failing test, or a crash goes to `hyper-debug`; a product-language change request goes to `hyper-feedback`.
- Delivery words on a debug job go to `hyper-git` when the debug stage ends `fixed`; when it ends `handoff`, they pass to the added `hyper-plan` as its delivery flag and `hyper-git` is dropped. A debug stage that ends `awaiting_input` asked its one question; the chain stops there and resumes on the answer.
- A change that already exists and only needs a verdict goes to `hyper-review`; a change that does not exist yet goes to `hyper-plan`, and a runtime failure to explain goes to `hyper-debug`. `hyper-review` never runs with `hyper-plan` or `hyper-execute` in one chain, and its review-and-fix mode owns the repair itself.
- A question answered by computing over a dataset goes to `hyper-data`; a schema, migration, slow query, index, or database setting goes to `hyper-database`; GA4 property report data goes to `hyper-google-analytics`; a dashboard interface goes to `hyper-design`. `hyper-data` writes `.hyper/data/<slug>/report.md` and changes no tracked file, so `hyper-git` never follows it.
- A `hyper-data` stage that ends `awaiting_input` asked its one question; one that ends `prerequisite_missing` reports the missing engine and its install command and installs nothing. The chain stops at either and resumes on the answer or after the install.
- On "이어서" / "continue" the router looks for a run in this order: a memo path named in the request; an open memo under `.hyper/handoff/` that matches the current branch or worktree; the open workflow record; the open execution state. An open memo is read first in resume mode, and then the record or run it points to is resumed. A closed memo is ignored unless the user names it. A plain "이어서 해줘" with no memo, no open workflow record, and no execution state is not a handoff trigger. A memo written in the middle of a chain records the workflow record path in `Where`; the record stays as it is and the memo is what the next session reads first.
- A continuation memo, a check of one, or a resume from one goes to `hyper-handoff`; a durable agent memory file goes to `hyper-documentation`; a plan file goes to `hyper-plan`; stopping a plan run or a goal loop belongs to that run's own stage, and the memo only points to its state directory. Write mode and check mode are a tail on their own and nothing follows them. Resume mode is a re-entry step, so it takes no chain position and does not count toward the four-stage cap: it runs first, and after its three-line restatement the router resumes the open workflow record at its first unfinished stage, or the run the memo names through that run's own stage, or routes the remaining work as a normal request when no record exists. The stage writes only under `.hyper/handoff/` and changes no tracked file, whatever the mode: it edits no code, commits nothing, and pushes nothing. Delivery stages follow only on delivery words in the user's current request, never on words quoted inside the memo, and the stage's `confirm-first` gate is the stage's own, so the router never approves on the user's behalf.
- A `hyper-handoff` stage that ends with the check line `unverified-standalone` is `done` with the failed question numbers carried into the report. One that ends `self: fail: <question numbers>` is `done` the same way: the failed question numbers go into the closing report, and no delivery stage is added on its account. One that cannot find a fact it needs asks for that one fact and the chain stops there, resuming on the answer.
- `hyper-database` never runs with `hyper-skill` or `hyper-documentation` in one chain. A skill folder or a document about databases goes to its own stage.
- A document about GA ("GA 운영 가이드 문서 써줘") goes to `hyper-documentation`; building the GA skill folder itself goes to `hyper-skill`; a search-visibility audit stays with `hyper-seo` even when it lists GA4 as one measurement row.
- Approval questions for property writes - creating a property, activating a filter, lowering retention, changing consent defaults on a live site, archiving or deleting - belong to the `hyper-google-analytics` stage, not to `hyper`. This orchestrator passes the property ID or site URL from the request unchanged and never approves on the user's behalf.
- A Google Tag Manager container (a `GTM-` ID, container tags, triggers, variables, or the dataLayer) goes to `hyper-google-tagmanager`; a direct Google tag (`gtag(` with a `G-` ID and no container), GA4 property settings, or GA4 report data goes to `hyper-google-analytics`. A `googletagmanager.com` file alone does not decide it: `gtm.js` with a `GTM-` ID is GTM, and `gtag/js` with a `G-` ID is the direct Google tag. Both stages run only when the request also asks for GA4 property work, and then `hyper-google-analytics` runs first.
- Approval questions for publishing a container version, deleting container items, changing user permissions, or changing live consent behavior belong to the `hyper-google-tagmanager` stage. This orchestrator passes the container ID and site URL from the request unchanged and never approves on the user's behalf.
- A tracking plan written as a document goes to `hyper-documentation`; an ad campaign or an analytics library installed without GTM is not a `hyper-google-tagmanager` job and routes by the existing rows.
- A diagram, flowchart, ERD, or other visual map of a structure ("구조도 그려줘", "draw the sequence diagram") is not a `hyper` job, like a PRD package: the drawing goes to `hyper-diagram` and the PRD to `hyper-prd`; an architecture review stays with `hyper-architecture` and does not add a drawing.
- An MCP server that queries a database ("사내 DB 조회하는 MCP 서버") routes to `hyper-mcp`; add `hyper-database` only when the job also changes the schema, a migration, an index, or a database setting.
- `hyper-architecture` and `hyper-database` both run only when the job restructures folders or modules and also changes the schema or queries; persistence-layer placement alone ("repository 레이어 정리") stays with `hyper-architecture`.
- When `hyper-database` and another build tail (`hyper-mcp`, `hyper-decision`, `hyper-design`, or `hyper-frontend`) are both chosen, the job spans modules: run each of them in its report mode (review, audit, `design`, `brief-only`, or `verify`) and end the chain at `hyper-plan`.
- Delivery words ("PR까지", "ship") on a database job put `hyper-database` in review mode before `hyper-plan`, because only the plan and execute stages own delivery.
- `hyper-git` never runs with `hyper-plan`, `hyper-execute`, or `hyper-mass` in one chain; their delivery flags carry the same words. A Git-only request with no other stage (commit, worktree, or merge alone) is not a `hyper` job; recording an issue goes to `hyper-issue`.
- `hyper-deploy` never runs before the tail that changes the code it deploys, and no stage follows it: it is the last stage in the order. A request that also asks for commit, push, or merge delivery puts `hyper-git` immediately before `hyper-deploy`.
- `hyper-deploy` and `hyper-documentation` are decided by the primary deliverable: a deployment that runs, or a fix to one, goes to `hyper-deploy`; a deployment runbook, guide, or checklist written as a document goes to `hyper-documentation`.
- `hyper-deploy` and `hyper-skill` never run in one chain. A skill folder about deploying goes to `hyper-skill`.
- A CI workflow file edit that only changes one place and deploys nothing is not a `hyper` job: it is a one-place edit outside this chain. A request to make CI deploy goes to `hyper-deploy`, which owns the platform configuration and the deploy command.
- Approval questions for a production deploy, a rollback, a data or volume operation, a deletion, a cost change, a DNS or firewall change, or a credential belong to the `hyper-deploy` stage: the stage asks them, with its own gate and its own exact command. This orchestrator never approves or answers them on the user's behalf.
- On a `hyper-git` delivery stage, merges into `main`, `master`, the default branch, or a deploy branch happen only when the user named that branch.
- An existing plan file wins over a new plan only when the user points at it or says to resume. A new Build request with an unrelated old plan gets a new plan.
- When the stack is outside the architecture stage's supported set, keep the stage anyway: it decides support from files and stops with a reason, and `rules/stage-handoff.md` §4 records that stop as a skip.

## 6. Delivery and Report-Only Words

Pass these through to the stage that owns them; never pick one the user did not say.

| User words | Passed to |
|---|---|
| none | local delivery (the stage's default) |
| "PR까지", "PR만", "make a PR", `--make-pr` | `--make-pr` |
| "머지까지", "배포까지", "ship", `--ship` | `--ship` |
| "계획만", "실행하지 말고", "plan only", `--plan-only` | `--plan-only`; the chain ends after the plan |
| "승인은 내가 할게", "I'll approve" | The approval hold, passed as said; the chain ends after the plan |
| "커밋하고 푸시", "commit and push", after a non-delivering tail | `hyper-git` delivery stage in commit mode |
| "<branch>, <branch>에 머지하고 푸시", "merge into dev and main", after a non-delivering tail | `hyper-git` delivery stage with those targets, in the named order |
| "PR까지" after a non-delivering tail other than a database, MCP, decision-API, or interface job | `hyper-git` delivery stage in workflow mode (pull request) |

Tie-break for "배포까지" on a code-change chain: "배포까지" carries two meanings at once, so it resolves to both. The plan stage receives `--ship` (merge delivery) and the chain gains `hyper-deploy` after the tail; the deploy stage starts only after the execution completion block, so the ship delivery finishes first and the deploy then runs against the merged result. When the user means only the ship delivery ("머지까지" with no platform mention), route `--ship` alone and skip `hyper-deploy`. When the user means only the deployment and no merge ("배포만"), run `hyper-deploy` alone without `--ship`.

## 7. Ambiguity

- When the files and the request decide the chain, route without asking.
- Ask one question only when two chains are equally supported and the wrong one would redo most of the work, such as "구조 바꿔줘" in a repository with two supported apps and no path named. Name the candidate chains, recommend one, and say that the run continues with the recommendation if no answer comes.
- When the request contradicts the repository (the user names a stack the manifests do not show), ask once with both pieces of evidence.

## 8. Route Line

Print one Korean line before the first stage:

```text
워크플로: <stage> -> <stage> -> ... (전달: local|make-pr|ship|plan-only|git:<mode> <targets>) / 근거: <stage>=<signal>; <stage>=<signal>
```

A run that stops before the first stage prints the same line with the stop reason in place of the chain.

A `hyper-research` stage with its companion is written `hyper-research(+hyper-browsing)`, and its signal names the web-sourcing word: `근거: hyper-research(+hyper-browsing)="인터넷 검색으로 동향 조사"`.

## Sources

> Checked 2026-11-10.

| Claim | Source |
|---|---|
| The stage skills, the companion skill, and the orchestrator role | user instruction, 2026-11-06 (orchestrator role); `hyper-deploy` added by user instruction, 2026-11-07; `hyper-feedback` added by user instruction, 2026-11-07; `hyper-decision` added by user instruction, 2026-11-08; `hyper-google-analytics` added by user instruction, 2026-11-08; `hyper-debug` added by user instruction, 2026-11-09 (issue #22); `hyper-loop` added by user instruction, 2026-11-09 (issue #21); `hyper-data` added by user instruction, 2026-11-09 (issue #25); `hyper-google-tagmanager` added by user instruction, 2026-11-09 (hyper routing refresh); `hyper-frontend` added by user instruction, 2026-11-09 (issue #46); `hyper-handoff` added by user instruction, 2026-11-10; `hyper-debate` added by user instruction, 2026-11-10 (issue #26); `hyper-review` added by user instruction, 2026-11-10 (issue #23); `hyper-cleanup` added by user instruction, 2026-11-10 (issue #24); `hyper-browsing` attached to web-sourced research by user instruction, 2026-11-07 |
| Each stage's trigger, output, and exclusions, including `hyper-mass` excluding plan-file execution and `hyper-execute` requiring an existing plan | each stage skill's own `SKILL.md` in this repository, 2026-11-06 |
| The delivery words, the plan-only and approval-hold words, and the plan-to-execute auto-continue | the plan skill's handoff rule in this repository, 2026-11-06 |
| The stage order, the four-stage cap, the recipes, and the tie-breaks | this package's chosen design, not a validated optimum |
| Handoff write and check modes as a tail with nothing after them, resume mode as a re-entry step outside the chain and the four-stage cap, the resume lookup order (named memo, open memo, workflow record, execution state), and delivery stages gated on the current request's words only | this package's chosen design, not a validated optimum |
