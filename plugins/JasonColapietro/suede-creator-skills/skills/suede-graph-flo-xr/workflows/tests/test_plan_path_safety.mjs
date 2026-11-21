// A 2026-08-23 run against a Next.js App Router repo lost every surviving plan to the
// plan-file validator: PROTECTED_PLAN_SEGMENTS banned the segment "build" anywhere in a
// path, so the tracked route src/app/build/page.tsx read as a generated artifact and all
// seven finalists were pruned as "candidate is structurally unsafe for beam ranking",
// emptying the beam. A later run halted before that: the candidate-audit command inlines
// the whole candidate manifest as base64, and at 10,640 chars the per-spawn clamp refused
// to parse it, failing the attestation closed on a clean worktree. These tests drive the
// real script with stubbed agents and pin the fixes: non-dot artifact segments are banned
// only for paths NOT tracked at the scout's base commit (dot-dirs, node_modules, and .git
// stay banned everywhere), the audit travels as bounded exact-pinned command batches, and
// the plan-producing prompts state the lane-name and file-path constraints that silently
// killed 6 of 8 generated candidates.
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, mkdtempSync, mkdirSync, writeFileSync, symlinkSync, rmSync } from 'node:fs'
import { execFileSync } from 'node:child_process'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = path.dirname(fileURLToPath(import.meta.url))
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor

const REPO = '/tmp/ship-fixture-repo'
const RUN_KEY = 'ship-11111111-2222-3333-4444-555555555555'
const WORKTREE = `${REPO}.worktrees/${RUN_KEY}`
const BASE_SHA = 'a'.repeat(40)
const SCOPE = 'Reconcile the docs\nRefresh the verification date'
const LANE_NAME_PATTERN = '^[A-Za-z0-9][A-Za-z0-9._ -]{0,63}$'

// Two lanes: the lane under test owns targetFile, the second keeps the scope map honest.
const planFor = targetFile => ({
  summary: `touch ${targetFile}`,
  coverage: [targetFile, 'README.md'],
  lanes: [
    { name: 'target-lane', files: [targetFile], tier: 'integration', acceptance: 'npm test' },
    { name: 'readme-lane', files: ['README.md'], tier: 'mechanical', acceptance: 'npm test' },
  ],
  scopeMap: [
    { item: 'Reconcile the docs', lane: 'target-lane', acceptance: 'npm test', source: 'user scope' },
    { item: 'Refresh the verification date', lane: 'readme-lane', acceptance: 'npm test', source: 'user scope' },
  ],
  externalActions: [],
})
const scoreFixture = () => ({
  coverage: 17, evidence: 17, feasibility: 17, safety: 17, efficiency: 17,
  total: 85, rationale: 'verified against the worktree files',
})

function runShip ({
  source,
  agentBudget = 'light',
  candidateFiles,
  trackedCandidateFiles = [],
  planScript,
} = {}) {
  const calls = []
  const logs = []

  const fixture = (opts) => {
    const label = opts.label || ''
    switch (opts.phase) {
      case 'Scout':
        return {
          worktreePath: WORKTREE, tempRoot: `/private/tmp/${RUN_KEY}`, baseSha: BASE_SHA,
          dirtyFiles: [], candidateFiles,
          siblingClaims: [], liveCwds: [], manifestOverflow: false,
          hazards: [{ kind: 'secret', blocking: false, detail: 'no secrets found' }],
        }
      case 'ScoutVerify':
        return {
          repoRoot: REPO, worktreePath: WORKTREE, commonDir: `${REPO}/.git`,
          registered: true, commonDirMatches: true, headSha: BASE_SHA,
          headMatchesOriginMain: true, clean: true, realPathWithinAllowedFamily: true,
          unsafeCandidateFiles: [], trackedCandidateFiles,
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
        return scoreFixture()
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
    calls.push({ phase: opts.phase, label: opts.label, prompt, opts })
    return fixture(opts)
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
    { total: null, spent: () => 0, remaining: () => Infinity },
    async () => {},
  ).then((result) => ({ result, calls, logs }))
}

const CURRENT = readFileSync(path.join(HERE, '..', 'suede-graph-flo-xr.js'), 'utf8')
const STRUCTURAL_PRUNE = 'candidate is structurally unsafe for beam ranking'
const structuralPrunes = result => result.graph.pruned
  .filter(thought => thought.state && thought.state.pruning === STRUCTURAL_PRUNE)

test('a tracked src/app/build/page.tsx route survives beam ranking and can be selected', async () => {
  const route = 'src/app/build/page.tsx'
  const { result } = await runShip({
    source: CURRENT,
    candidateFiles: [route, 'README.md'],
    trackedCandidateFiles: [route, 'README.md'],
    planScript: () => planFor(route),
  })
  assert.equal(structuralPrunes(result).length, 0,
    'a tracked App Router build route is source, not an artifact; it must not be pruned as structurally unsafe')
  assert.ok(result.selectedPlan,
    `a plan touching the tracked build route must reach Select; run ended with ${JSON.stringify(result.reason)}`)
  assert.ok(result.selectedPlan.lanes.some(lane => lane.files.includes(route)),
    'the selected plan must still own the build route file')
})

test('untracked artifact paths are still rejected at every artifact-root shape', async () => {
  // Repo-root build output, a Gradle module build dir, and a dist bundle: none tracked,
  // all still artifacts. The tracked-file exemption must not have widened past git.
  for (const artifact of ['build/output.js', 'module/build/Output.class', 'dist/index.js']) {
    const { result } = await runShip({
      source: CURRENT,
      candidateFiles: [artifact, 'README.md'],
      trackedCandidateFiles: ['README.md'],
      planScript: () => planFor(artifact),
    })
    assert.ok(structuralPrunes(result).length > 0,
      `every plan touching untracked ${artifact} must still be pruned as structurally unsafe`)
    assert.equal(result.halted, true, `a run whose plans all touch untracked ${artifact} must halt`)
    assert.equal(result.selectedPlan, null, `untracked ${artifact} must never reach Select`)
  }
})

test('tracked-ness never exempts .git, node_modules, or dot-directory segments', async () => {
  // The attestation is a model response; even one that (falsely or truly) claims these
  // paths are tracked must not unlock them — the hard bans are unconditional.
  for (const hard of ['node_modules/escape.ts', '.next/server/page.js', '.git/hooks/pre-commit.sample']) {
    const { result } = await runShip({
      source: CURRENT,
      candidateFiles: [hard, 'README.md'],
      trackedCandidateFiles: [hard, 'README.md'],
      planScript: () => planFor(hard),
    })
    assert.equal(result.selectedPlan, null, `${hard} must never reach Select even when attested tracked`)
    assert.equal(result.halted, true, `a run whose plans all touch ${hard} must halt`)
  }
})

test('an attestation claiming tracked paths outside the candidate list fails closed', async () => {
  const { result } = await runShip({
    source: CURRENT,
    candidateFiles: ['src/a.ts', 'README.md'],
    trackedCandidateFiles: ['src/invented.ts'],
    planScript: () => planFor('src/a.ts'),
  })
  assert.equal(result.halted, true)
  assert.equal(result.reason, 'invalid scout worktree',
    'a tracked claim for a path the scout never nominated is a fabricated attestation and must halt the run')
})

test('the candidate audit travels as bounded command batches instead of one unparseable inline payload', async () => {
  // 58 long paths plus the two plan files: the legacy single-command form carried the
  // whole manifest inline and blew past the clamp parse ceiling (10,640 chars denied in
  // run wf_c7c670cf-77d), which halted a clean run as "invalid scout worktree".
  const longCandidates = Array.from({ length: 58 }, (_, index) =>
    `src/features/deeply/nested/section-${String(index).padStart(2, '0')}/${'x'.repeat(120)}-component.tsx`)
  const candidateFiles = [...longCandidates, 'index.md', 'README.md']
  const legacyInlineLength = Buffer.from(JSON.stringify(candidateFiles), 'utf8').toString('base64').length
  assert.ok(legacyInlineLength > 10000,
    `test premise: the legacy inline payload must exceed the observed denial length; got ${legacyInlineLength}`)

  const { calls } = await runShip({
    source: CURRENT,
    candidateFiles,
    trackedCandidateFiles: ['index.md', 'README.md'],
    planScript: () => planFor('index.md'),
  })
  const verify = calls.find(call => call.phase === 'ScoutVerify')
  assert.ok(verify, 'the attestation stage must still run')
  const auditRules = verify.opts.bashCommandClamp.filter(rule => rule.includes('candidate-audit.cjs'))
  assert.ok(auditRules.length >= 2,
    `a manifest this large must be split across multiple audit commands; got ${auditRules.length}`)
  for (const rule of auditRules) {
    assert.ok(rule.length <= 2060,
      `every audit command must stay far under the clamp parse ceiling; got ${rule.length} chars`)
  }
  const decoded = auditRules.flatMap(rule => {
    const match = rule.match(/candidate-audit\.cjs' '[^']*' '[^']*' '([A-Za-z0-9+/=]+)'\)$/)
    assert.ok(match, `audit command must carry an exact-pinned base64 slice: ${rule.slice(0, 120)}…`)
    return JSON.parse(Buffer.from(match[1], 'base64').toString('utf8'))
  })
  assert.deepEqual(decoded, candidateFiles,
    'the batched payloads must reassemble to exactly the scout candidate list — no path dropped or reordered')
  assert.match(verify.prompt, /union/i,
    'the verifier must be told to union the batch outputs rather than copy one of them')
})

test('plan-producing prompts state the lane-name and file-path constraints that discard candidates', async () => {
  const { calls, result } = await runShip({
    source: CURRENT,
    agentBudget: 'standard',
    candidateFiles: ['src/a.ts', 'README.md'],
    trackedCandidateFiles: [],
    planScript: () => planFor('src/a.ts'),
  })
  assert.ok(result.selectedPlan, 'the healthy fixture must still select a winner')
  for (const phase of ['Generate', 'Improve', 'Aggregate']) {
    const call = calls.find(c => c.phase === phase)
    assert.ok(call, `${phase} must run in this fixture`)
    assert.ok(call.prompt.includes(LANE_NAME_PATTERN),
      `${phase} prompt must state the exact lane-name pattern; 6 of 8 real candidates died on em-dashes and colons`)
    assert.ok(call.prompt.includes('copied verbatim from the candidate file list'),
      `${phase} prompt must state that lane files are verbatim candidate paths`)
  }
  const generate = calls.find(c => c.phase === 'Generate')
  assert.equal(generate.opts.schema.properties.lanes.items.properties.name.pattern, LANE_NAME_PATTERN,
    'the PLAN schema must enforce the lane-name pattern at the tool layer so violations retry in-flight instead of wasting the candidate')
})

test('candidate-audit.cjs reports tracked-at-base candidates and still flags unsafe paths', async (t) => {
  let gitAvailable = true
  try {
    execFileSync('git', ['--version'], { encoding: 'utf8' })
  } catch {
    gitAvailable = false
  }
  if (!gitAvailable) return t.skip('git is not available on this host')

  const repo = mkdtempSync(path.join(os.tmpdir(), 'gfx-candidate-audit-'))
  t.after(() => rmSync(repo, { recursive: true, force: true }))
  const git = (...args) => {
    try {
      return execFileSync('git', ['-C', repo, ...args], { encoding: 'utf8' })
    } catch (error) {
      assert.fail(`git ${args.join(' ')} failed: ${error.stderr || error}`)
    }
  }
  git('init', '-q')
  mkdirSync(path.join(repo, 'src/app/build'), { recursive: true })
  writeFileSync(path.join(repo, 'src/app/build/page.tsx'), 'export default function BuildPage() {}\n')
  writeFileSync(path.join(repo, 'README.md'), '# fixture\n')
  git('add', '.')
  git('-c', 'user.email=fixture@example.com', '-c', 'user.name=Fixture', 'commit', '-q', '-m', 'fixture')
  // Untracked artifacts and a symlink, created after the commit — a real run's worktree
  // is a clean checkout, but the audit must not depend on that to classify correctly.
  mkdirSync(path.join(repo, 'build'), { recursive: true })
  writeFileSync(path.join(repo, 'build/output.js'), 'artifact\n')
  mkdirSync(path.join(repo, 'module/build'), { recursive: true })
  writeFileSync(path.join(repo, 'module/build/Output.class'), 'artifact\n')
  symlinkSync('/', path.join(repo, 'evil-link'))

  const candidates = [
    'src/app/build/page.tsx', 'README.md', 'build/output.js',
    'module/build/Output.class', 'src/brand-new-file.ts', 'evil-link',
  ]
  const helper = path.join(HERE, '..', 'helpers', 'candidate-audit.cjs')
  const payload = Buffer.from(JSON.stringify(candidates), 'utf8').toString('base64')
  let audit
  try {
    audit = execFileSync('node', [helper, repo, repo, payload], { encoding: 'utf8' })
  } catch (error) {
    assert.fail(`candidate-audit failed: ${error.stderr || error}`)
  }
  const report = JSON.parse(audit)
  assert.deepEqual(report.unsafeCandidateFiles, ['evil-link'],
    'the symlink audit must be unchanged by the tracked-ness addition')
  assert.deepEqual(report.trackedCandidateFiles, ['src/app/build/page.tsx', 'README.md'],
    'exactly the committed files are tracked — untracked artifacts, new files, and unsafe paths are not')
})

test('diff-digest.cjs rejects a file reached through a symlinked worktree ancestor', async (t) => {
  let gitAvailable = true
  try {
    execFileSync('git', ['--version'], { encoding: 'utf8' })
  } catch {
    gitAvailable = false
  }
  if (!gitAvailable) return t.skip('git is not available on this host')

  const repo = mkdtempSync(path.join(os.tmpdir(), 'gfx-diff-digest-'))
  const outside = mkdtempSync(path.join(os.tmpdir(), 'gfx-diff-digest-outside-'))
  t.after(() => rmSync(repo, { recursive: true, force: true }))
  t.after(() => rmSync(outside, { recursive: true, force: true }))

  execFileSync('git', ['init', '-q', repo], { encoding: 'utf8' })
  writeFileSync(path.join(repo, 'README.md'), '# fixture\n')
  execFileSync('git', ['-C', repo, 'add', 'README.md'], { encoding: 'utf8' })
  execFileSync('git', [
    '-C', repo, '-c', 'user.email=fixture@example.com', '-c', 'user.name=Fixture',
    'commit', '-q', '-m', 'fixture',
  ], { encoding: 'utf8' })

  writeFileSync(path.join(outside, 'secret.txt'), 'outside\n')
  symlinkSync(outside, path.join(repo, 'outside'), 'dir')

  const helper = path.join(HERE, '..', 'helpers', 'diff-digest.cjs')
  const payload = Buffer.from(JSON.stringify(['outside/secret.txt']), 'utf8').toString('base64')
  assert.throws(
    () => execFileSync('node', [helper, repo, 'HEAD', payload], { encoding: 'utf8' }),
    error => {
      assert.match(String(error.stderr), /reported file resolves outside worktree/)
      return true
    },
  )
})

// Run wf_13062fd6-bf3 (2026-09-04, seven-line scope, three finalists): every finalist
// mapped each checklist line to its owning lane two or three times — one scopeMap
// entry per cited source — and Select rejected all of them for "a duplicate item-lane
// pair", ending the run with zero mutations. A repeated pair is one mapping with more
// sources, not a defect; every entry still has to name the lane's acceptance and a
// known source.
const planWithRepeatedPair = (target, extra) => {
  const plan = planFor(target)
  plan.scopeMap.push({ item: 'Reconcile the docs', lane: 'target-lane', acceptance: 'npm test', source: 'user scope', ...extra })
  return plan
}

test('a scopeMap that repeats an item-lane pair with a second source is still selectable', async () => {
  const route = 'src/a.ts'
  const { result } = await runShip({
    source: CURRENT,
    candidateFiles: [route, 'README.md'],
    trackedCandidateFiles: [route, 'README.md'],
    planScript: () => planWithRepeatedPair(route),
  })
  assert.ok(result.selectedPlan,
    `a repeated (item, lane) mapping is one mapping cited twice and must reach Select; run ended with ${JSON.stringify(result.reason)} ${JSON.stringify(result.haltDetail && result.haltDetail.eligibilityRejections)}`)
})

test('folding repeated pairs does not skip the per-entry acceptance check', async () => {
  const route = 'src/a.ts'
  const { result } = await runShip({
    source: CURRENT,
    candidateFiles: [route, 'README.md'],
    trackedCandidateFiles: [route, 'README.md'],
    planScript: () => planWithRepeatedPair(route, { acceptance: 'npm run build' }),
  })
  assert.equal(result.selectedPlan, null,
    'a repeated entry naming an acceptance the lane does not run must still reject the plan')
  assert.ok((result.haltDetail.eligibilityRejections || []).some(r => /does not name an existing lane acceptance/.test(r)),
    `the rejection must be the acceptance mismatch; got ${JSON.stringify(result.haltDetail.eligibilityRejections)}`)
})
