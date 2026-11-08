# Workflow Routing

> Classify the requested output, add only the stages whose artifacts the job consumes, and run them in one fixed order.

## 1. Classify the Job

Decide the job from the requested output, then confirm it with repository files. Read the request first, then only the files a signal names.

| Job class | Requested output | Example words |
|---|---|---|
| Build | Changed code: a feature, fix, refactor, migration, or adoption; a data model, schema, database migration, tuned query or index, or database operations change; an MCP server, client, or host configuration; a designed or restyled interface or a faux product UI; a user, client, or planner change request applied to existing behavior; one generated or edited image or one image prompt; a readiness verdict, deployment setup, deploy, deployment configuration change, or deployment fix; or a created or refactored skill folder, document, or prompt artifact | 만들어, 추가해, 고쳐, 리팩토링해, 옮겨, 적용해, 연결해, 스키마 설계해, 인덱스 잡아줘, 디자인해, 리디자인해, AI 티 빼줘, 피드백 반영해, 요청대로 바꿔줘, 배포해, 배포 설정해, 배포 실패 고쳐, 점검해, 스킬로 만들어, 문서로 정리해, 프롬프트 만들어, implement, refactor, migrate, connect, redesign, apply this feedback, generate an image, deploy, ship to staging |
| Report | A saved report, audit, review, or plan with no code change | 조사만, 점검만, 리뷰만, 리포트만, 계획만, audit only, just the plan |
| Resume | An earlier run continued | 이어서, 계속, 재개, resume, continue |

A request that is a one-place edit with no plan (a typo, one string, one config value), a commit-only request, a PRD or wireframe package, or a question is out of scope: do not route it.

## 2. Stage Signals

Add a stage only when one of its signals is present. Quote the signal in the route line.

| Stage | Add it when | Evidence to quote |
|---|---|---|
| `hyper-research` | The job depends on facts outside the repository: choosing between libraries or services, a new major version, an unfamiliar external API, or "최신" / "latest" behavior | The request phrase |
| `hyper-issue` | The request asks to register or record issues ("이슈 등록해줘", "이슈로 남겨줘", "register these as issues"), names issue numbers (`#1~3`, `#4, #7`, `1~3번 이슈`), names a condition over open issues to select and group, or names an issue whose scope or acceptance is missing | The request phrase, plus the tracker and the named numbers, label, or query |
| `hyper-seo` | The job is about search or AI-answer visibility of a named site or page set | The request phrase and the target URL or app path |
| `hyper-google-analytics` | The output is GA4 work: installing or fixing GA4 or the Google tag on a site, auditing a GA4 property or its tag, changing property settings (custom dimensions, key events, retention, filters), analyzing GA4 report data, or finding why GA4 data is missing or wrong | The request phrase, plus the tag file that was read: a file containing `gtag(`, `googletagmanager.com`, a `G-` measurement ID, or `@next/third-parties/google` |
| `hyper-architecture` | The job restructures folders, routes, modules, data or server boundaries, or platform setup; adds a feature that creates a new route, module, or server boundary; sets up or unifies the lint, format, and type tooling (oxlint, Prettier, rustfmt, clippy); or optimizes build or runtime performance | The request phrase plus a stack manifest that was read, such as `package.json` or `Cargo.toml` |
| `hyper-database` | The job designs or reviews a data model or schema, writes or reviews a database migration or backfill, tunes a slow query, an index, a hot key, or a hot partition, chooses a database engine or managed data service, or changes database operations (backup and restore, replication and failover, connection pooling, upgrades, database security, monitoring) | The request phrase, plus the schema, migration, ORM, or driver file that was read when one exists, such as `schema.prisma`, `drizzle.config.ts`, a `migrations/` folder, `pg` or `ioredis` in `package.json`, or a database image in a compose file |
| `hyper-mcp` | The job builds, fixes, migrates, audits, or connects an MCP (Model Context Protocol) server, client, or host MCP configuration, or prepares MCP registry metadata | The request phrase, plus the MCP dependency or configuration file that was read when one exists, such as `@modelcontextprotocol/*` in `package.json`, `mcp` in `pyproject.toml`, `.mcp.json`, or `server.json` |
| `hyper-decision` | The job designs, writes, wires, evaluates, audits, or routes a decision-API call: a model call that returns a typed judgment (a yes/no probability, one option from a closed set, an ordered score, an image box) instead of text, through TypeSafe Jev, OpenAI Decisions, another decision vendor, the Vercel AI SDK or AI Gateway, OpenRouter, or an emulation on a general LLM; or it audits existing LLM calls that only return a label | The request phrase, plus the decision dependency or call that was read when one exists, such as `@typesafe-ai/sdk`, `typesafe-sdk`, `@ai-sdk/typesafe-ai`, `experimental_decide` or `client.decisions.create` in code, or `api.typesafe.ai` in a config file |
| `hyper-design` | The requested output is an interface whose look is the point: a new screen, page, or component designed, an existing UI restyled, faux product UI for a hero, card, or demo, a design brief or `DESIGN.md`, or generic "AI look" patterns audited or removed | The request phrase, plus the target UI path and the styling or design-system file that was read when one exists, such as `DESIGN.md`, a tokens file, or `tailwind.config.*` |
| `hyper-feedback` | The input is a change request in product language against existing behavior: feedback, a complaint, a ticket, meeting notes, a revised spec line, or new wording from the user, a client, or a planner, directly or relayed, and the user wants it worked out and applied ("알아서 파악해서 고쳐", "피드백 반영해", "이 메모대로 반영") | The request phrase, plus the quoted feedback text and its author or relay path |
| `hyper-imagegen` | The whole requested output is one new image, one edit of a supplied image, or one ready-to-use image prompt | The request phrase, plus the supplied edit source or reference path when one exists |
| `hyper-plan` | A Build job touches several files or steps, or a Report job asks for a plan | The request phrase |
| `hyper-execute` | Only as the first stage: a plan file under `.hyper/plans/` already exists and the user wants it run or resumed | The plan path that was read |
| `hyper-mass` | The user asks for a dependency graph, a DAG, "의존성 그래프", "단계별 병렬", or several tasks where some must finish before others start, and no plan file is wanted | The request phrase |
| `hyper-skill` | The requested output is a reusable skill folder: a new skill, or a refactor of an existing skill's trigger, contract, resources, or validation | The request phrase, plus the target `skills/<name>/SKILL.md` when it already exists |
| `hyper-documentation` | The requested output is a documentation artifact, new or refactored: a README, an `AGENTS.md`, an AI-readable document (instruction base, agent guide, runbook, specification, or rule pack), or a reusable prompt artifact (role, system, or agent prompt, prompt template or pack, or prompt eval fixture) | The request phrase, plus the target path when it already exists |
| `hyper-git` | After a tail that does not deliver (`hyper-skill`, `hyper-documentation`, `hyper-feedback`, or `hyper-database`, `hyper-mcp`, `hyper-decision`, `hyper-design`, or `hyper-google-analytics` as the last build stage), when the user asks to commit and push or to merge into named branches and push; after `hyper-skill`, `hyper-documentation`, or `hyper-feedback` also for a pull request. It runs before `hyper-deploy` when the same chain also deploys. Never after `hyper-imagegen`, whose artifact is the delivered image or the gitignored `.hyper/imagegen/` file, and never after `hyper-deploy` | The delivery phrase and the named target branches |
| `hyper-deploy` | The job is a deployment or a deployment finding: a readiness verdict, a first deployment setup, a deploy to a named environment, a change to an existing deployment's settings, or a failed or unhealthy deployment to diagnose and fix | The request phrase, plus the deployment file that was read, such as `Dockerfile`, `compose.yaml`, `wrangler.jsonc`, `.railway/railway.ts`, `railway.toml`, or `config/deploy.yml` |

## 3. Stage Order

Chosen stages always run in this order. Skip the ones that were not chosen.

```text
hyper-research -> hyper-issue -> hyper-seo -> hyper-google-analytics -> hyper-architecture -> hyper-database -> hyper-mcp -> hyper-decision -> hyper-design -> hyper-feedback -> (hyper-plan [-> hyper-execute] | hyper-mass | hyper-execute | hyper-skill | hyper-documentation | hyper-imagegen) [-> hyper-git] [-> hyper-deploy]
```

When both delivery brackets are chosen, `hyper-git` runs first and `hyper-deploy` last; nothing runs after `hyper-deploy`.

- Upstream stages (`hyper-research`, `hyper-seo`, `hyper-architecture`) produce evidence for the tail. In a Build job they run in report mode; the tail makes the code change.
- `hyper-google-analytics` is a last build stage: it edits the site code and the property settings itself and proves collection, so `hyper-git` may follow it like `hyper-database`. It runs before `hyper-git` and `hyper-deploy` when the same chain also delivers or deploys, and it never follows `hyper-deploy`. When `hyper-seo` is chosen too, `hyper-seo` runs first and this stage measures the result.
- `hyper-database` is the tail when it is the last chosen stage: it designs the schema, writes the online migration, tunes the query or index, or changes the operations setup and verifies the result itself. When `hyper-plan` or `hyper-mass` follows it, it runs in review mode (design brief, schema or migration review, or engine choice) and its saved report is the plan's input.
- `hyper-mcp` is the tail when it is the last chosen stage: it builds, fixes, migrates, or connects and verifies the result itself. When `hyper-plan` or `hyper-mass` follows it, it runs in audit mode and its report is the plan's input.
- `hyper-decision` is the tail when it is the last chosen stage: it writes the decision artifact (questions, a caller, a template, an eval plan, an audit table, or a route setup) and runs its offline request checker itself. When `hyper-plan` or `hyper-mass` follows it, it runs in `design` or `audit` mode and its saved decision contract or audit table is the plan's input.
- `hyper-design` is the tail when it is the last chosen stage: it designs, restyles, mocks up, or cleans the interface and verifies it itself. When `hyper-plan` or `hyper-mass` follows it, it runs in `brief-only` mode for an interface that does not exist yet or in `audit` mode for an existing one, and its saved brief or report is the plan's input.
- `hyper-feedback` is the tail when it is the last chosen stage: it applies every item within its direct-edit budget and verifies it itself. When its run ends `handoff`, `hyper-plan` is added after it in the same run with `.hyper/feedback/<slug>/brief.md` as required reading; the route line shows that conditional stage as `hyper-feedback [-> hyper-plan]`. When it ends `applied`, no plan stage runs.
- `hyper-issue` produces evidence for the tail, like the other upstream stages: it registers the issues and writes the lane manifest, and `hyper-plan` turns each manifest lane into one parallel lane of its waves. Registration words or issue numbers continue into `hyper-plan` by default, so the run ends only after the lanes are executed and delivered. Only record-only words ("등록만", "이슈만", "작업은 하지 마", "manifest only") make `hyper-issue` the last stage.
- A request handed over by `hyper-issue` itself (it names `.hyper/issues/<slug>/batch.md` and says the issue stage is done) does not run `hyper-issue` again: record it as stage 1 `done` with the manifest path, and start at `hyper-plan`.
- Otherwise the tail is exactly one of: `hyper-plan` (which continues into `hyper-execute` by itself), `hyper-mass`, `hyper-execute` alone for an existing plan, `hyper-skill` for a skill folder, `hyper-documentation` for a document or prompt artifact, or `hyper-imagegen` for one image or one image prompt.
- `hyper-git` is never a tail on its own: it runs after a tail that changed files but owns no delivery. `hyper-plan`, `hyper-execute`, and `hyper-mass` deliver for themselves, so `hyper-git` never follows them.
- `hyper-deploy` is the last stage of a chain: it deploys the result the earlier stages produced, and no stage ever follows it. When the user also asks for commit, push, or merge delivery, `hyper-git` runs before `hyper-deploy`.
- When the request also changes code, the code chain runs first and the `hyper-deploy` stage starts after the execution completion block, so it deploys the finished change rather than a half-built tree.
- In a Report job the chain ends at the last requested stage. A Report job that asks for a plan ends at `hyper-plan` with `--plan-only`.
- At most four stages run, and `hyper-deploy` counts as one of them. A chain that seems to need more is two jobs: run the first and report the second as the next step.
- `hyper-browsing` is a companion, not a stage: it takes no position in this order and does not count toward the four-stage cap. Attach it to the `hyper-research` stage when the research is web-sourced - the question depends on live web sources (search results, vendor, community, or news pages, market or trend data, external documentation, a named URL), signalled by words such as "인터넷 검색", "웹에서", "최신", "동향", "사례", "latest", or a URL. Do not attach it when the research is repository-only (source-code analysis, local files and history), or when no `hyper-research` stage is chosen.

## 4. Chain Recipes

| Job | Chain |
|---|---|
| Architecture review only | `hyper-architecture` |
| Lint, format, or type tooling set up or unified, or build or runtime performance optimized | `hyper-architecture` alone, as the last stage that makes the edits |
| Refactor or restructure | `hyper-architecture` -> `hyper-plan` |
| Feature or fix across several files | `hyper-plan` |
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
| Change request from the user, a client, or a planner applied to existing behavior | `hyper-feedback` |
| Same, with items over the direct-edit budget (a new route, a schema change, an API contract) | `hyper-feedback` -> `hyper-plan`, the plan stage added when the feedback stage ends `handoff` |
| Change request that depends on current external facts ("최신 정책에 맞게 바꿔달래") | `hyper-research` -> `hyper-feedback` |
| One image created, one supplied image edited, or one image prompt written | `hyper-imagegen` |
| Image that depends on current external guidance or references ("최신 프롬프트 가이드 참고해서") | `hyper-research` -> `hyper-imagegen` |
| Research report only | `hyper-research` |
| SEO audit or report only | `hyper-seo` |
| SEO score loop ("최대 점수까지", "keep improving the score") | `hyper-seo` in its optimize mode, alone |
| SEO fixes implemented as a planned change | `hyper-seo` -> `hyper-plan` |
| GA4 installed or fixed on a site ("사이트에 GA4 달아줘") | `hyper-google-analytics` |
| GA4 installed or fixed, then merged and pushed ("GA4 달고 dev에 머지·푸시") | `hyper-google-analytics` -> `hyper-git` |
| Search-visibility audit, then GA4 measurement set up ("SEO 점검하고 GA4 측정까지 세팅해줘") | `hyper-seo` -> `hyper-google-analytics` |
| GA4 report data analyzed for the last month ("지난달 GA 유입 데이터 분석해서 리포트 줘") | `hyper-google-analytics` in `analyze` mode, alone |
| Dependency-ordered multi-agent phase | `hyper-mass`, with upstream stages before it when their signals are present |
| Existing plan run or resumed | `hyper-execute` |
| Skill folder created or refactored | `hyper-skill` |
| Skill folder that depends on current provider docs ("최신 규격", "latest spec") | `hyper-research` -> `hyper-skill` |
| README, `AGENTS.md`, document, rule pack, reusable prompt, template, pack, or prompt eval fixture created or refactored | `hyper-documentation` |
| Document or prompt that depends on current external sources or provider guidance | `hyper-research` -> `hyper-documentation` |
| Skill folder, document, MCP, decision-API, interface, database, GA4 analytics, or feedback change, then commit and push ("커밋하고 푸시까지") | that chain -> `hyper-git` in commit mode |
| Same, then merge into named branches ("dev, main에 머지하고 푸시") | that chain -> `hyper-git` in commit mode with `&& <branch>` targets for this run's commits, or workflow mode when a whole work branch must be merged |
| Skill folder, document, or feedback change, then a pull request ("PR까지") | that chain -> `hyper-git` in workflow mode; an MCP, decision-API, interface, or database job with "PR까지" or "ship" keeps the review or audit -> `hyper-plan` route above |
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
- `hyper-imagegen` never runs with `hyper-plan`, `hyper-mass`, `hyper-skill`, `hyper-documentation`, or `hyper-design` in one chain. Choose by the primary deliverable: one image or one image prompt goes to `hyper-imagegen`; an interface that contains a picture goes to `hyper-design`; a reusable prompt pack or template for images goes to `hyper-documentation`; image analysis or critique is not a `hyper` job.
- A `hyper-imagegen` stage that ends `awaiting_input` asked its one question; the chain stops there and resumes on the answer.
- `hyper-feedback` never runs with `hyper-skill`, `hyper-documentation`, `hyper-imagegen`, `hyper-mass`, or `hyper-design` in one chain. A request whose look is the point ("리디자인", "AI 티 안 나게") goes to `hyper-design`; a change request about a skill folder or a document goes to that stage; an explicit dependency-graph request goes to `hyper-mass`.
- A product-language change request routes to `hyper-feedback` even when one item needs a schema, route, or API change: the stage applies the in-budget items and its `brief.md` carries the rest into `hyper-plan`. Add `hyper-architecture` or `hyper-database` before it only when the user asks for that review by name or words.
- A one-place edit that already names its location and new value ("이 버튼 문구 하나만 바꿔줘") is not a `hyper` job; a request with several items, an unknown location, or feeling-level wording ("복잡하대", "불편하대") routes to `hyper-feedback`.
- Delivery words on a feedback job go to `hyper-git` when the feedback stage ends `applied`; when it ends `handoff`, they pass to the added `hyper-plan` as its delivery flag and `hyper-git` is dropped, because the plan and execute stages deliver for themselves.
- A `hyper-feedback` stage that ends `awaiting_input` asked its one question; the chain stops there and resumes on the answer.
- `hyper-database` never runs with `hyper-skill` or `hyper-documentation` in one chain. A skill folder or a document about databases goes to its own stage.
- A document about GA ("GA 운영 가이드 문서 써줘") goes to `hyper-documentation`; building the GA skill folder itself goes to `hyper-skill`; a search-visibility audit stays with `hyper-seo` even when it lists GA4 as one measurement row.
- Approval questions for property writes - creating a property, activating a filter, lowering retention, changing consent defaults on a live site, archiving or deleting - belong to the `hyper-google-analytics` stage, not to `hyper`. This orchestrator passes the property ID or site URL from the request unchanged and never approves on the user's behalf.
- An MCP server that queries a database ("사내 DB 조회하는 MCP 서버") routes to `hyper-mcp`; add `hyper-database` only when the job also changes the schema, a migration, an index, or a database setting.
- `hyper-architecture` and `hyper-database` both run only when the job restructures folders or modules and also changes the schema or queries; persistence-layer placement alone ("repository 레이어 정리") stays with `hyper-architecture`.
- When `hyper-database` and another build tail (`hyper-mcp`, `hyper-decision`, or `hyper-design`) are both chosen, the job spans modules: run each of them in its report mode (review, audit, `design`, or `brief-only`) and end the chain at `hyper-plan`.
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
| "PR까지" after `hyper-skill`, `hyper-documentation`, or `hyper-feedback` | `hyper-git` delivery stage in workflow mode (pull request) |

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

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| The eighteen stage skills, the companion skill, and the orchestrator role | user instruction, 2026-11-06 (orchestrator role); the stage set extended to fifteen with `hyper-deploy` by user instruction, 2026-11-07, to sixteen with `hyper-feedback` by user instruction, 2026-11-07, to seventeen with `hyper-decision` by user instruction, 2026-11-08, and to the current eighteen with `hyper-google-analytics` by user instruction, 2026-11-08; `hyper-browsing` attached to web-sourced research by user instruction, 2026-11-07 |
| Each stage's trigger, output, and exclusions, including `hyper-mass` excluding plan-file execution and `hyper-execute` requiring an existing plan | each stage skill's own `SKILL.md` in this repository, 2026-11-06 |
| The delivery words, the plan-only and approval-hold words, and the plan-to-execute auto-continue | the plan skill's handoff rule in this repository, 2026-11-06 |
| The stage order, the four-stage cap, the recipes, and the tie-breaks | this package's chosen design, not a validated optimum |
