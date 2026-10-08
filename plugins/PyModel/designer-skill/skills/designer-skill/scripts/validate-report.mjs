// Semantic report/evidence validation; structural JSON Schema validation is a
// separate host responsibility. This PASS means report-validation, never UI PASS.
import { createHash } from 'node:crypto';
import { closeSync, constants, fstatSync, openSync, readSync, realpathSync, statSync } from 'node:fs';
import { isAbsolute, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const MAX_BYTES = 2 * 1024 * 1024;
const MODES = new Set(['audit', 'plan', 'refine', 'implement', 'system']);
const KINDS = new Set(['static', 'functional', 'accessibility', 'rendered']);
const STATUSES = new Set(['PASS', 'FAIL', 'NOT_RUN', 'NOT_APPLICABLE']);
const ORIGINS = new Set(['executed', 'observed', 'attested']);
const SHA = /^[a-f0-9]{64}$/;
const record = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const nonempty = value => typeof value === 'string' && value.trim().length > 0;

function readConfined(root, path) {
  if (!nonempty(path) || isAbsolute(path)) throw new Error('Artifact paths must be project-relative.');
  const real = realpathSync(resolve(root, path));
  const rel = relative(root, real);
  if (rel === '..' || rel.startsWith(`..${sep}`) || isAbsolute(rel)) throw new Error('Artifact escapes the authorized root.');
  const fd = openSync(real, constants.O_RDONLY | constants.O_NOFOLLOW | constants.O_NONBLOCK);
  try {
    const stat = fstatSync(fd);
    if (!stat.isFile() || stat.size > MAX_BYTES) throw new Error('Artifact must be a regular file of at most 2 MiB.');
    const bytes = Buffer.alloc(MAX_BYTES + 1);
    let used = 0;
    while (used < bytes.length) {
      const count = readSync(fd, bytes, used, bytes.length - used, null);
      if (!count) break;
      used += count;
    }
    if (used > MAX_BYTES) throw new Error('Artifact exceeded 2 MiB while reading.');
    if (realpathSync(resolve(root, path)) !== real) throw new Error('Artifact path changed while reading.');
    return bytes.subarray(0, used);
  } finally { closeSync(fd); }
}

/** The plan is supplied by the host, never inferred from the report's claims.
 * Structurally validate both against their bundled schemas before calling.
 * artifactRoot must be the host-authorized project/evidence directory. */
export function validateRunReport(report, plan, artifactRoot) {
  const issues = [];
  const result = () => ({ status: issues.length ? 'FAIL' : 'PASS', scope: 'report-validation', issues });
  let root;
  try {
    root = realpathSync(artifactRoot);
    if (!statSync(root).isDirectory()) throw new Error('Not a directory.');
  } catch {
    issues.push('An existing host-authorized artifact directory is required.');
    return result();
  }
  if (!record(report) || !record(plan) || report.schemaVersion !== 2 || plan.schemaVersion !== 1) {
    issues.push('Require report v2 and verification plan v1; legacy reports must be regenerated, not promoted.');
    return result();
  }
  if (!MODES.has(plan.mode) || !MODES.has(report.mode) || !SHA.test(plan.inputHash ?? '') ||
      !['COMPLETE', 'PARTIAL', 'BLOCKED'].includes(report.taskStatus) || !['PASS', 'FAIL', 'NOT_VERIFIED'].includes(report.uiReadiness) ||
      !Array.isArray(report.checks) || !Array.isArray(plan.checks) || !plan.checks.length ||
      report.checks.length > 128 || plan.checks.length > 128 || !Array.isArray(report.findings) || report.findings.length > 256 ||
      !Array.isArray(report.changes) || !Array.isArray(report.limitations)) {
    issues.push('Malformed report or plan; validate the bundled JSON schemas first.');
    return result();
  }
  for (const field of ['runId', 'mode', 'inputRevision', 'outputRevision', 'inputHash']) {
    if (!nonempty(plan[field]) || report[field] !== plan[field]) issues.push(`Report ${field} does not match the host-owned plan.`);
  }
  const requirements = new Map();
  for (const item of plan.checks) {
    if (!record(item) || !nonempty(item.id) || !KINDS.has(item.kind) || typeof item.allowNotApplicable !== 'boolean') {
      issues.push('Malformed planned check.');
      continue;
    }
    if (requirements.has(item.id)) issues.push(`Duplicate planned check: ${item.id}.`);
    requirements.set(item.id, item);
  }
  const checks = new Map();
  function verifyEvidence(evidence, label, current) {
    if (!Array.isArray(evidence) || evidence.length > 16) { issues.push(`${label}: evidence must be an array of at most 16 artifacts.`); return; }
    for (const item of evidence) {
      if (!record(item) || !nonempty(item.artifact) || !nonempty(item.producer) || !nonempty(item.revision) ||
          typeof item.sha256 !== 'string' || !SHA.test(item.sha256) || !ORIGINS.has(item.origin)) {
        issues.push(`${label}: malformed evidence.`);
        continue;
      }
      if (current && item.revision !== plan.outputRevision) issues.push(`${label}: stale evidence revision.`);
      try {
        const bytes = readConfined(root, item.artifact);
        if (createHash('sha256').update(bytes).digest('hex') !== item.sha256) issues.push(`${label}: artifact hash mismatch.`);
      } catch (error) {
        issues.push(`${label}: ${error.message}`);
      }
    }
  }
  for (const check of report.checks) {
    if (!record(check) || !nonempty(check.id) || !KINDS.has(check.kind) || !STATUSES.has(check.status) ||
        typeof check.required !== 'boolean' || !nonempty(check.reason) || !Array.isArray(check.evidence) || check.evidence.length > 16) {
      issues.push('Malformed reported check.');
      continue;
    }
    if (checks.has(check.id)) issues.push(`Duplicate reported check: ${check.id}.`);
    checks.set(check.id, check);
    const requirement = requirements.get(check.id);
    if (check.required && !requirement) issues.push(`${check.id}: required check was not in the host-owned plan.`);
    if (requirement && (!check.required || check.kind !== requirement.kind)) issues.push(`${check.id}: required status/kind differs from the plan.`);
    if (check.status === 'NOT_APPLICABLE' && requirement && !requirement.allowNotApplicable) issues.push(`${check.id}: non-applicability was not authorized.`);
    if (['PASS', 'FAIL'].includes(check.status) && !check.evidence.length) issues.push(`${check.id}: result has no evidence.`);
    if (check.required && check.status === 'PASS' && !check.evidence.some(e => record(e) && ['executed', 'observed'].includes(e.origin))) {
      issues.push(`${check.id}: required PASS relies only on attestation.`);
    }
    verifyEvidence(check.evidence, check.id, Boolean(requirement));
  }
  for (const id of requirements.keys()) if (!checks.has(id)) issues.push(`Missing required check: ${id}.`);
  const claimingReadiness = report.uiReadiness === 'PASS';
  for (const [id, requirement] of requirements) {
    const check = checks.get(id);
    if (!check) continue;
    if (report.taskStatus === 'COMPLETE' && check.status === 'NOT_RUN') issues.push(`${id}: completed task has an unrun required check.`);
    if (claimingReadiness && check.status !== 'PASS' && !(check.status === 'NOT_APPLICABLE' && requirement.allowNotApplicable)) {
      issues.push(`${id}: UI PASS with a nonpassing required check.`);
    }
  }
  if (claimingReadiness) {
    const rendered = [...requirements.values()].some(req => {
      const check = checks.get(req.id);
      return req.kind === 'rendered' && check?.status === 'PASS' && check.required &&
        check.evidence.some(e => record(e) && e.origin === 'observed' && e.revision === plan.outputRevision);
    });
    if (!rendered) issues.push('UI PASS requires planned rendered PASS and observed final-revision evidence.');
    if (report.taskStatus === 'BLOCKED') issues.push('Blocked work cannot claim UI PASS.');
  }
  if (report.taskStatus === 'COMPLETE' && ['refine', 'implement', 'system'].includes(report.mode) && !claimingReadiness) {
    issues.push('Completed UI implementation requires verified UI readiness.');
  }
  if (['audit', 'plan'].includes(report.mode) && report.changes.length) issues.push('Read-only modes cannot report implementation changes.');
  for (const finding of report.findings) {
    if (!record(finding) || typeof finding.blocking !== 'boolean' || typeof finding.resolved !== 'boolean' || !Array.isArray(finding.evidence) || !finding.evidence.length) {
      issues.push('Malformed finding.');
      continue;
    }
    if (claimingReadiness && finding.blocking && !finding.resolved) issues.push('UI PASS with unresolved blocking finding.');
    if (claimingReadiness && finding.blocking && finding.resolved && !finding.evidence.some(e =>
      record(e) && e.revision === plan.outputRevision && ['executed', 'observed'].includes(e.origin))) {
      issues.push('Resolved blocking finding needs executed or observed final-revision resolution evidence.');
    }
    // Historical observations are useful; they cannot alone prove resolution.
    verifyEvidence(finding.evidence, 'finding', false);
  }
  return result();
}

// No network or writes. Run after host JSON Schema validation:
// node validate-report.mjs REPORT.json PLAN.json AUTHORIZED_ROOT
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    if (process.argv.length !== 5) throw new Error('Usage: node validate-report.mjs REPORT.json PLAN.json AUTHORIZED_ROOT');
    const root = realpathSync(process.argv[4]);
    const readJson = path => JSON.parse(readConfined(root, relative(root, resolve(path))).toString('utf8'));
    const result = validateRunReport(readJson(process.argv[2]), readJson(process.argv[3]), root);
    console.log(JSON.stringify(result, null, 2));
    process.exitCode = result.status === 'PASS' ? 0 : 1;
  } catch (error) {
    console.error(JSON.stringify({ status: 'FAIL', scope: 'report-validation', issues: [error.message] }));
    process.exitCode = 1;
  }
}
