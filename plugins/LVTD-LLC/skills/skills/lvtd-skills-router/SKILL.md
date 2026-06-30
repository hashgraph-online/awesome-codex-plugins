---
name: lvtd-skills-router
description: Use when the user is unsure which LVTD skill fits their problem, asks what skill to use, describes a cross-domain workflow, or needs help choosing between Django, Rust, SEO, B2B sales, writing, product, library, or template skills.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Skills Router
  category: Productivity
  tags: skills,router,workflow,agents
---

# LVTD Skills Router

Use this skill to choose the smallest useful set of LVTD skills for the user's
problem. All skills in this catalog can be model-invoked; this router exists to
reduce selection friction, not to create a separate manual-only command layer.

## Routing Workflow

1. Identify the user's domain, desired outcome, and whether they are asking for
   advice, implementation, review, or troubleshooting.
2. Choose one primary skill. Add secondary skills only when they clearly cover a
   separate concern in the same workflow.
3. If the user asked which skill to use, answer with the recommendation and why.
4. If the user asked for work to be done and the matching skill is available,
   continue by using that skill's workflow.
5. If the matching skill is not installed in the current client, name the skill
   and the marketplace plugin that contains it.

## Skill Map

Use these defaults when the user's request is ambiguous:

- `django-htmx`: HTMX interactions, partial templates, request branching,
  swaps, triggers, redirects, and server-rendered Django UI.
- `alpinejs-django`: Alpine.js behavior in Django templates, especially local
  UI state around HTMX swaps.
- `django-q2`: Django Q2 tasks, schedules, qcluster workers, Redis broker
  setup, and background job debugging.
- `django-test-profiling`: finding the slowest Django tests and runtime
  bottlenecks before optimizing.
- `django-test-performance`: improving slow Django test suites after the
  bottlenecks are known or likely.
- `django-test-data`: cleaning up factories, fixtures, setup methods, and
  database-heavy test data.
- `django-test-parallelization`: enabling or debugging Django parallel test
  execution, pytest-xdist, and shared-resource isolation.
- `django-ci-test-optimization`: tuning Django test jobs in CI, including
  caching, splitting, and command design.
- `django-targeted-mocking`: replacing external services, settings, time,
  stdin/stdout, or HTTP calls in Django tests without broad fragile mocks.
- `fastmcp-django`: FastMCP servers inside Django apps, including ASGI mounting,
  ORM access, auth, and Streamable HTTP deployment.
- `rust-api-test-harness`: Rust HTTP API test harnesses, black-box integration
  tests, random-port app startup, real database isolation, and CI cargo checks.
- `rust-sqlx-postgres-service`: SQLx migrations, compile-time checked queries,
  pool injection, transactions, and Postgres integration tests.
- `rust-domain-boundaries`: newtypes, parse-don't-validate constructors,
  request DTO boundaries, and property tests.
- `rust-error-observability`: typed errors, HTTP adapters, tracing spans,
  redaction, and async failure diagnosis.
- `rust-service-security`: login, password hashing, sessions, route protection,
  and authentication middleware.
- `rust-idempotent-workflows`: retry-safe workflows, duplicate requests,
  queues, side effects, concurrency, and idempotency keys.
- `rust-deployable-service`: Docker, runtime config, secrets, health checks,
  SQLx offline builds, and production startup validation.
- `game-geometry-representation-choice`: choosing between meshes, SDFs,
  voxels, splines, parametric surfaces, fields, and hybrid game-geometry
  workflows before implementation.
- `game-spatial-queries`: raycasts, picking, collision predicates,
  point-in-triangle checks, barycentric constraints, signed distances, and
  geometry query edge cases.
- `game-transform-systems`: coordinate spaces, local/world/view/projection
  transforms, homogeneous coordinates, camera constraints, parent-child
  transforms, and inverse transforms.
- `game-vector-math-primitives`: dot, cross, and triple products for game
  rendering, collision, orientation, normals, projections, signed areas, and
  signed volumes.
- `game-smooth-curves-and-motion`: splines, Bezier curves, interpolation,
  derivative continuity, path parameterization, camera rails, waypoint paths,
  and smooth game motion.
- `game-sdf-and-field-modeling`: SDF primitives, implicit functions, scalar
  fields, vector fields, deformation fields, procedural volumes, and field
  composition.
- `game-mesh-voxel-conversion`: mesh, SDF, voxel, image, contour, and smooth
  curve conversions, including mesh repair, contouring, voxel morphology, and
  attribute preservation.
- `cookiecutter`: Cookiecutter templates, Jinja rendering, hooks, options,
  generated project validation, and template cleanup.
- `developer-docs-technical-research`: researching feature behavior, source
  owners, SMEs, hands-on validation, contradictions, and doc-ready evidence
  before planning or drafting technical documentation.
- `developer-docs-audience-research`: mapping developer audiences, learning
  objectives, user goals, prerequisites, and audience-specific docs needs.
- `developer-docs-planning`: choosing developer documentation content types,
  outlines, scope, source of truth, scenario plans, and launch plans.
- `developer-docs-drafting`: drafting READMEs, getting-started docs,
  tutorials, how-to guides, concepts, API guides, troubleshooting pages,
  migration guides, SaaS topics, and release documentation.
- `developer-docs-editing-review`: editing, reviewing, technically verifying,
  and improving developer documentation drafts.
- `code-sample-documentation`: writing and reviewing code samples in developer
  docs, including runnable examples, snippets, comments, and API guide samples.
- `visual-docs-diagrams`: planning or reviewing diagrams, screenshots, flows,
  visuals, and accessibility for technical documentation.
- `documentation-information-architecture`: auditing and reorganizing docs
  navigation, inventories, landing pages, hierarchies, sequences, redirects,
  and findability.
- `documentation-platform-selection`: choosing docs platforms or authoring
  tools, comparing docs-as-code, CMS, wiki, static-site, DITA, API reference,
  help-center, or custom tooling, and planning migrations or pilots.
- `docs-agile-integration`: integrating documentation with Agile planning,
  scrum boards, definitions of done, release gates, review timing, and
  cross-sprint docs work.
- `saas-documentation`: planning and writing SaaS or managed-service docs,
  responsibility boundaries, release notes, support enablement, and operations
  runbooks.
- `docs-release-maintenance`: publishing, maintaining, refreshing,
  deprecating, deleting, and release-aligning developer documentation.
- `docs-feedback-triage`: triaging docs feedback from readers, support,
  community, field teams, analytics, and review channels.
- `documentation-quality-metrics`: measuring developer documentation quality,
  success signals, feedback loops, and docs health.
- `seo-opportunity-research`: finding organic growth opportunities from
  customer demand, search behavior, communities, and competitive gaps.
- `seo-persona-intent-mapping`: mapping personas, search intent, funnel stage,
  formats, CTAs, and localization needs into SEO plans.
- `product-led-seo-strategy`: turning product value, page architecture,
  taxonomy, and scalable experiences into a product-led SEO strategy.
- `seo-roadmap-prioritization`: scoring SEO initiatives, sequencing roadmap
  work, and framing cross-functional SEO asks.
- `technical-seo-triage`: diagnosing traffic drops, indexing failures,
  canonicals, redirects, crawlability, and migration risk.
- `link-building-strategy`: designing sustainable link-building campaigns
  around business outcomes, assets, publisher ecosystems, metrics, and scope.
- `linkable-asset-planning`: planning or auditing link-worthy assets from
  market pains, existing strengths, competitor evidence, and linker audiences.
- `link-prospecting-research`: researching link opportunity types, queries,
  competitor backlink angles, list sources, and autocomplete seed expansions.
- `link-prospect-qualification`: scoring link prospects for relevance, trust,
  editorial quality, authority, outreach fit, spam risk, and asset readiness.
- `link-outreach-acquisition`: drafting and operating link outreach with
  personalization, subject lines, response handling, tracking, and guardrails.
- `broken-link-building`: finding dead-resource opportunities, qualifying
  dead backlinks, preparing replacement outreach, and salvaging old owned URLs.
- `guest-post-placement`: planning citation-justified guest post placements,
  publisher quality checks, pitch titles, and placement tracking.
- `local-sponsorship-link-building`: planning local sponsorship campaigns for
  local visibility, relationships, fulfillment, measurement, and links.
- `book-toc-lab`: planning or restructuring useful nonfiction books around a
  promise, scope, reader outcome, and takeaway-first table of contents.
- `reader-experience-edit`: revising practical nonfiction for usefulness,
  pacing, front-loaded insight, and beta-readiness.
- `beta-reader-feedback`: planning beta rounds and turning reader feedback into
  manuscript revisions.
- `book-seed-marketing`: choosing first-reader channels and seed marketing for
  useful nonfiction books.
- `book-sales-optimization`: improving book product pages, retailer funnels,
  pricing, formats, reviews, and post-launch sales.
- `self-publishing-production`: final production sequencing for editing,
  proofreading, layout, cover, print-on-demand, ISBNs, and launch readiness.
- `customer-discovery-conversations`: planning or auditing customer discovery
  conversations so they produce concrete evidence instead of compliments,
  opinions, hypotheticals, or feature-request noise.
- `customer-commitment-validation`: evaluating whether customer, sales,
  investor, partner, or product meetings created real commitment and
  advancement.
- `customer-segment-slicing`: narrowing broad markets, audiences, or personas
  into specific, reachable who-where customer segments.
- `customer-conversation-access`: finding and framing customer conversations
  through warm intros, communities, casual chats, events, advisors, landing-page
  replies, or meeting requests.
- `customer-learning-notes`: synthesizing raw customer notes, transcripts, call
  summaries, or CRM snippets into shared team learning and next questions.
- `b2b-sales-constraint-diagnosis`: diagnosing the one sales bottleneck limiting
  current pipeline or revenue: reach, resonance, timing, or trust.
- `b2b-reach-engineering`: building named-account reach systems, target buyer
  lists, controlled delivery channels, and first-touch saturation plans.
- `b2b-resonance-audit`: auditing and rewriting B2B messaging around buyer
  pain, concrete outcome, and mechanism so the right buyers remember it.
- `b2b-timing-engine`: designing 4-6 week buyer-presence cadences so known
  buyers remember the company when pain becomes urgent.
- `b2b-trust-engineering`: reducing perceived buying risk with relevant proof,
  clear next steps, layered familiarity, and confirmatory sales calls.
- `traction-bullseye`: choosing and focusing startup traction channels.
- `traction-channel-research`: researching comparable growth paths and channel
  options before Bullseye ranking.
- `traction-test-planner`: designing cheap, measurable channel tests and
  success criteria.
- `traction-review`: reviewing traction experiment results and deciding whether
  to double down, iterate, or pivot.
- `traction-critical-path`: setting traction goals and deciding what not to do.
- `traction-seo-content`, `traction-email-marketing`,
  `traction-paid-acquisition`, `traction-events-community`,
  `traction-partnership-sales`, `traction-pr-playbook`, and
  `traction-viral-engineering`: channel-specific traction test planning.
- `make-product-viral`: improving a product, landing page, pricing page, launch
  page, free tool, or social preview for clarity, memorability, and sharing.
- `calibredb`: managing Calibre libraries through the `calibredb` CLI.

## Marketplace Plugins

- `router`: `lvtd-skills-router`
- `django`: Django server-rendered UI, jobs, FastMCP, and test optimization
  skills.
- `rust`: Rust API testing, persistence, domain, observability, security,
  idempotency, and deployment skills.
- `game-geometry`: game geometry representation choice, spatial queries,
  transforms, vector primitives, smooth curves, SDFs, fields, mesh and voxel
  conversion.
- `developer-docs`: developer documentation research, planning, drafting,
  review, code samples, visuals, SaaS docs, Agile integration, platform
  selection, feedback, metrics, information architecture, release, and
  maintenance skills.
- `seo`: `seo-opportunity-research`, `seo-persona-intent-mapping`,
  `product-led-seo-strategy`, `seo-roadmap-prioritization`,
  `technical-seo-triage`, `link-building-strategy`,
  `linkable-asset-planning`, `link-prospecting-research`,
  `link-prospect-qualification`, `link-outreach-acquisition`,
  `broken-link-building`, `guest-post-placement`,
  `local-sponsorship-link-building`
- `nonfiction-book-writing`: nonfiction planning, editing, beta feedback,
  seed marketing, sales optimization, and production skills.
- `customer-discovery`: customer interviews, segment slicing, access,
  commitment validation, and notes synthesis.
- `b2b-sales`: constraint diagnosis, reach engineering, resonance audits,
  timing engines, and trust engineering for B2B sales.
- `traction`: startup traction, channel research, test planning, and
  channel-specific growth skills.
- `cookiecutter`: `cookiecutter`

`calibredb` and `make-product-viral` may be direct-install skills when they are
not present in a generated marketplace plugin.

## Avoid

- Do not load every candidate skill just to browse. Route from the user's
  current request first.
- Do not continue routing once a specific skill clearly fits.
- Do not force a planning/execution taxonomy onto the catalog. Pick by domain,
  outcome, and evidence needed for the current request.
