// Run wf_c67e116f-f61 lost two of three Improve candidates to "API Error: Connection lost
// mid-response" and recorded nothing about either loss. The harness resolves agent() with
// null on a terminal transport failure rather than throwing, so a dead scorer read as a
// score of nothing: the candidate was pruned as unscored, Aggregate fell under its
// two-survivor minimum, and Select was handed a single finalist — with 160 of 200 agent
// calls unspent. These tests drive the real script with stubbed agents and prove the
// transport death is retried, that a run out of headroom still refuses to retry, and that
// the halt line names which of the several ways the search can come back empty happened.
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = path.dirname(fileURLToPath(import.meta.url))
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor

const REPO = '/tmp/ship-fixture-repo'
const RUN_KEY = 'ship-11111111-2222-3333-4444-555555555555'
const WORKTREE = `${REPO}.worktrees/${RUN_KEY}`
const BASE_SHA = 'a'.repeat(40)
const SCOPE = 'Reconcile the docs\nRefresh the verification date'

const LANES = [
  { name: 'docs-lane', files: ['index.md'], tier: 'integration', acceptance: 'npm test' },
  { name: 'readme-lane', files: ['README.md'], tier: 'mechanical', acceptance: 'npm test' },
]
const planFixture = (summary = 'reconcile the docs') => ({
  summary,
  coverage: ['index.md', 'README.md'],
  lanes: LANES,
  scopeMap: [
    { item: 'Reconcile the docs', lane: 'docs-lane', acceptance: 'npm test', source: 'user scope' },
    { item: 'Refresh the verification date', lane: 'readme-lane', acceptance: 'npm test', source: 'user scope' },
  ],
  externalActions: [],
})
// Deliberately non-canonical: a scopeMap item that is not a line of SCOPE is exactly what
// planEligibility rejected in the real run, and it is a different failure from a lost score.
const ineligiblePlanFixture = () => ({
  ...planFixture('plan with an off-checklist mapping'),
  scopeMap: [{ item: 'something nobody asked for', lane: 'docs-lane', acceptance: 'npm test', source: 'user scope' }],
})
const scoreFixture = (total = 85) => ({
  coverage: 17, evidence: 17, feasibility: 17, safety: 17, efficiency: total - 68,
  total, rationale: 'verified against the worktree files',
})

// A transport death as the harness actually delivers it: agent() resolves with null.
const TRANSPORT_NULL = Symbol('transport-null')
// The same failure delivered as a throw, which the harness also does.
const TRANSPORT_THROW = Symbol('transport-throw')

function runShip ({
  source,
  agentBudget = 'deep',
  scoreScript = () => scoreFixture(),
  planScript = () => planFixture(),
  budgetTotal = null,
} = {}) {
  const calls = []
  const logs = []
  let scoreSeq = 0

  const fixture = (opts) => {
    const label = opts.label || ''
    switch (opts.phase) {
      case 'Scout':
        return {
          worktreePath: WORKTREE, tempRoot: `/private/tmp/${RUN_KEY}`, baseSha: BASE_SHA,
          dirtyFiles: [], candidateFiles: [`${WORKTREE}/index.md`, `${WORKTREE}/README.md`],
          siblingClaims: [], liveCwds: [], manifestOverflow: false,
          hazards: [{ kind: 'secret', blocking: false, detail: 'no secrets found' }],
        }
      case 'ScoutVerify':
        return {
          repoRoot: REPO, worktreePath: WORKTREE, commonDir: `${REPO}/.git`,
          registered: true, commonDirMatches: true, headSha: BASE_SHA,
          headMatchesOriginMain: true, clean: true, realPathWithinAllowedFamily: true,
          unsafeCandidateFiles: [], trackedCandidateFiles: [],
        }
      case 'Research':
        return { lens: label, facts: [], constraints: [], unread: [] }
      case 'Gaps':
        if (label.startsWith('gap:')) return { lens: label, facts: [], constraints: [], unread: [] }
        if (label === 'skeptic:constraints') return { audited: [] }
        return { gaps: [] }
      case 'Generate':
        return planScript(label)
      case 'Score':
        return scoreScript(label, scoreSeq++)
      case 'RefutePlan':
        return { defects: [], notes: 'no defect reproduced' }
      case 'Aggregate':
        return planScript('aggregate')
      case 'Improve':
        return planScript(label)
      default:
        return null
    }
  }

  const agent = async (prompt, opts = {}) => {
    calls.push({ phase: opts.phase, label: opts.label })
    const value = fixture(opts)
    if (value === TRANSPORT_NULL) return null
    if (value === TRANSPORT_THROW) {
      throw Object.assign(new Error('API Error: Connection lost mid-response.'), { code: null })
    }
    return value
  }
  const parallel = (thunks) => Promise.all(thunks.map((t) => t()))
  const pipeline = async (items, ...stages) =>
    Promise.all(items.map(async (item, i) => {
      let value = item
      for (const stage of stages) value = await stage(value, item, i)
      return value
    }))

  const body = source.replace('export const meta', 'const meta')
  const run = new AsyncFunction(
    'agent', 'parallel', 'pipeline', 'phase', 'log', 'args', 'budget', 'workflow', body)

  return run(
    agent, parallel, pipeline, () => {}, (m) => logs.push(m),
    { repo: REPO, scope: SCOPE, deploys: false, agentBudget, agentNamespace: '', helperDir: '/tmp/ship-fixture-helpers' },
    { total: budgetTotal, spent: () => 0, remaining: () => budgetTotal === null ? Infinity : budgetTotal },
    async () => {},
  ).then((result) => ({ result, calls, logs }))
}

const CURRENT = readFileSync(path.join(HERE, '..', 'suede-graph-flo-xr.js'), 'utf8')
const scoreCalls = (calls) => calls.filter((c) => c.phase === 'Score')

// Two scorers die on their first call and succeed on the retry — the shape of the real
// incident, where 2 of 40 agents died and the rest of the run was healthy.
const flakyOnce = (limit = 2) => {
  const seen = new Set()
  return (label) => {
    if (!seen.has(label) && seen.size < limit) { seen.add(label); return TRANSPORT_NULL }
    return scoreFixture()
  }
}
// Kills the nth and mth distinct score of the run. On a deep budget the first eight
// distinct scores are the generated plans and the next three are Improve round 1, so
// [9, 10] reproduces the real failure: the flake lands inside the beam, not outside it.
const flakeDistinct = (ordinals) => {
  const order = new Map()
  return (label) => {
    if (!order.has(label)) {
      order.set(label, order.size + 1)
      if (ordinals.includes(order.get(label))) return TRANSPORT_NULL
    }
    return scoreFixture()
  }
}

test('a scorer that dies on a null transport result is retried instead of silently pruned', async () => {
  const { result, calls } = await runShip({ source: CURRENT, scoreScript: flakyOnce() })
  // Asserted before anything about the new bookkeeping: the user-visible cost of the bug
  // was candidates leaving the beam, and that has to be what fails first if this regresses.
  const scored = result.graph.thoughts.filter(
    (t) => t.operationId === 'score-generated' && t.score)
  assert.equal(scored.length, 8,
    `all 8 generated plans must still carry a score after a recovered flake; got ${scored.length}`)
  const retries = result.graph.scoreRetries
  assert.ok(retries.used > 0,
    'a null agent() result is a transport death; it must be retried, not read as "no score"')
  assert.ok(retries.attempts.some((a) => a.outcome === 'retried'),
    `every retry must be recorded; got ${JSON.stringify(retries.attempts)}`)
  assert.ok(retries.attempts.some((a) => a.outcome === 'recovered'),
    'a retry that succeeds must be recorded as recovered, so a clean-looking run still shows the flake')
  // The whole point: the candidates survive, so the run is not starved of finalists.
  assert.ok(scoreCalls(calls).length > result.graph.scoreRetries.used,
    'retries must be extra calls on top of the original scores, not replacements')
})

test('a flake inside the beam no longer starves Aggregate of survivors', async () => {
  // This is the real run, reproduced. Two of the three Improve-round-1 scores die, the
  // beam collapses to one, and Aggregate — which needs two survivors — emits nothing, so
  // Select is handed a single candidate. With the retry the beam holds and Aggregate runs.
  const { result } = await runShip({ source: CURRENT, scoreScript: flakeDistinct([9, 10]) })
  const kept = result.graph.thoughts.filter((t) => t.operationId === 'keep-improved-1' && t.status === 'kept')
  assert.equal(kept.length, 3,
    `a recovered flake must not shrink the beam; kept ${kept.length} of 3`)
  const aggregate = result.graph.operations.find((o) => o.id === 'aggregate-plans')
  assert.equal(aggregate.outputThoughtIds.length, 1,
    'Aggregate needs two survivors to run at all; losing them to a flake silently skips the stage')
})

test('a transport death delivered as a throw is retried on the same terms', async () => {
  const seen = new Set()
  const { result } = await runShip({
    source: CURRENT,
    scoreScript: (label) => {
      if (!seen.has(label)) { seen.add(label); return TRANSPORT_THROW }
      return scoreFixture()
    },
  })
  assert.ok(result.graph.scoreRetries.used > 0,
    'the harness throws for some transport failures and resolves null for others; both are retriable')
})

test('a malformed score is never retried — the schema is not a connection to redial', async () => {
  const { result } = await runShip({
    source: CURRENT,
    // Present, well-formed JSON, but not a valid score. This is a judgment, not a flake.
    scoreScript: () => ({ coverage: 1, evidence: 1, feasibility: 1, safety: 1, efficiency: 1, total: 5, rationale: '' }),
  })
  assert.equal(result.graph.scoreRetries.used, 0,
    'retrying a schema-valid-but-rejected score just burns budget re-asking a settled question')
})

test('retries stop at the reserved-budget floor instead of eating the run', async () => {
  // Every score dies forever. Retries must be bounded by attempts, the run-wide cap, and
  // the floor of budget held back for the phases after the search.
  const { result } = await runShip({ source: CURRENT, scoreScript: () => TRANSPORT_NULL })
  const retries = result.graph.scoreRetries
  assert.ok(retries.used <= retries.cap,
    `run-wide retries (${retries.used}) must not exceed the cap (${retries.cap})`)
  assert.ok(result.graph.budget.remaining >= 0, 'the ceiling still holds')
  assert.ok(
    retries.attempts.some((a) => a.outcome === 'attempts-exhausted' || a.outcome === 'run-retry-cap-reached' || a.outcome === 'reserved-budget-floor'),
    `a refused retry must say which bound refused it; got ${JSON.stringify(retries.attempts.map((a) => a.outcome))}`)
})

test('an unrecovered score failure is recorded, not silently dropped from the beam', async () => {
  const { result } = await runShip({ source: CURRENT, scoreScript: () => TRANSPORT_NULL })
  const failures = result.graph.dropped.filter(
    (d) => d.operation === 'Score' && d.reason === 'candidate agent failure')
  assert.ok(failures.length > 0,
    'a dead scorer must leave an entry in graph.dropped; the old code left no trace anywhere')
  assert.ok(result.graph.callLedger.some((c) => c.status === 'empty'),
    'the call ledger must distinguish an empty result from a healthy one')
  assert.equal(result.scoreReliability.degraded, true,
    'scoreReliability must ride out in the result so degradation is visible without parsing the graph')
})

test('losing every finalist to infrastructure is named as that, not as "no safe graph winner"', async () => {
  const { result } = await runShip({ source: CURRENT, scoreScript: () => TRANSPORT_NULL })
  assert.equal(result.halted, true)
  assert.notEqual(result.reason, 'no safe graph winner',
    'an infrastructure flake and a genuine evidence conflict must not print the same line')
  assert.match(result.reason, /score/i,
    `the halt reason must name the lost scores; got ${JSON.stringify(result.reason)}`)
  assert.equal(result.haltDetail.infrastructureDegraded, true)
  assert.ok(result.haltDetail.scoreAgentFailures > 0)
})

test('a finalist rejected on plan eligibility is named as that, with the flake reported alongside', async () => {
  // Both were true at once in the real run: two scores died AND the one finalist that
  // reached Select failed deterministic eligibility. The operator has to be able to read
  // both facts off the result without hand-parsing the journal.
  const { result } = await runShip({
    source: CURRENT,
    planScript: () => ineligiblePlanFixture(),
    scoreScript: flakyOnce(),
  })
  assert.equal(result.halted, true)
  assert.match(result.reason, /eligibility/i,
    `a plan rejected by planEligibility must say so; got ${JSON.stringify(result.reason)}`)
  assert.ok(result.haltDetail.eligibilityRejections.length > 0,
    'the deterministic reasons must ride out with the halt, not only inside graph.dropped')
  assert.ok(result.haltDetail.budgetRemaining >= 0)
})

test('Select is no more willing to pick than it was — an ineligible plan still loses', async () => {
  const { result } = await runShip({ source: CURRENT, planScript: () => ineligiblePlanFixture() })
  assert.equal(result.halted, true, 'refusing an ineligible plan is correct and must not regress')
  assert.equal(result.selectedPlan, null)
})

test('a clean run still selects a winner and reports undegraded scoring', async () => {
  // The fixture stops stubbing after Select, so this run halts in Build. That is the
  // point: the graph search must reach a winner, and the search is all these changes
  // touch. What matters here is that Select emitted one and that a healthy run reports
  // itself as healthy rather than quietly carrying a degraded flag.
  const { result } = await runShip({ source: CURRENT })
  const select = result.graph.operations.find((o) => o.id === 'select-plan')
  assert.equal(select.outputThoughtIds.length, 1, 'Select must still pick a winner on a healthy run')
  assert.ok(result.selectedPlan, `a fully healthy run must still pick a plan; halted with ${JSON.stringify(result.reason)}`)
  assert.equal(result.scoreReliability.degraded, false)
  assert.equal(result.scoreReliability.retriesUsed, 0)
  assert.equal(result.scoreReliability.unrecoveredFailures, 0)
})
