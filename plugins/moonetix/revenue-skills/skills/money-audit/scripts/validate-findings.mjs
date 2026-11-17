#!/usr/bin/env node
// validate-findings.mjs: check a money-audit findings.json against the project it describes.
// A finding passes only if the code it quotes is really at the file and line it names, and
// if it carries a proof. All ten bug classes must be accounted for.
// Usage: node validate-findings.mjs <findings.json> [--root <project directory>]
import { existsSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

export const CLASSES = [
  'unverified-events',
  'duplicate-credit',
  'balance-races',
  'client-trust',
  'money-arithmetic',
  'refunds-and-reversals',
  'promo-and-referral-abuse',
  'payout-controls',
  'secrets-and-access',
  'ledger-and-audit-trail',
];
export const SEVERITIES = ['critical', 'high', 'medium', 'low'];
const STATUSES = ['finding', 'clear', 'not-applicable'];
const PROOFS = ['probe', 'test', 'trace'];
const LINE_SLACK = 2;
const MIN_SNIPPET = 12;

// The fields each object may carry. assets/findings.schema.json lists the same ones.
export const KEYS = {
  report: ['version', 'project', 'date', 'environment', 'notes', 'findings', 'coverage'],
  finding: ['id', 'class', 'severity', 'title', 'location', 'impact', 'proof', 'fix'],
  quote: ['file', 'line', 'snippet'],
  step: ['file', 'line', 'snippet', 'note'],
  probe: ['kind', 'command', 'result', 'output_file'],
  test: ['kind', 'file', 'command', 'result', 'output_file'],
  trace: ['kind', 'steps'],
  coverage: ['class', 'status', 'examined', 'note'],
};

function checkKeys(value, allowed, label, errors) {
  if (typeof value !== 'object' || value === null) return;
  for (const key of Object.keys(value)) {
    if (!allowed.includes(key)) errors.push(`${label}: unknown field "${key}"`);
  }
}

const squash = (text) => String(text).replace(/\s+/g, ' ').trim();
const isText = (value, min = 1) => typeof value === 'string' && value.trim().length >= min;

function resolveInside(root, file) {
  if (!isText(file)) return null;
  const full = path.resolve(root, file);
  const inside = full === root || full.startsWith(root + path.sep);
  return inside && existsSync(full) && statSync(full).isFile() ? full : null;
}

// The quoted code must appear within a few lines of the stated line.
function checkQuote(root, where, label, errors) {
  if (typeof where !== 'object' || where === null) return errors.push(`${label}: missing`);
  const full = resolveInside(root, where.file);
  if (!full) return errors.push(`${label}: file "${where.file}" does not exist under the project root`);
  const lines = readFileSync(full, 'utf8').split('\n');
  if (!Number.isInteger(where.line) || where.line < 1 || where.line > lines.length) {
    return errors.push(`${label}: line ${where.line} is outside ${where.file} (${lines.length} lines)`);
  }
  const snippet = squash(where.snippet ?? '');
  if (snippet.length < MIN_SNIPPET) {
    return errors.push(`${label}: snippet must quote at least ${MIN_SNIPPET} characters of the code at that line`);
  }
  const from = Math.max(0, where.line - 1 - LINE_SLACK);
  const window = squash(lines.slice(from, where.line + LINE_SLACK).join(' '));
  if (window.includes(snippet)) return undefined;
  const holds = (i) => squash(lines.slice(i, i + 3).join(' ')).includes(snippet);
  let elsewhere = lines.findIndex((_, i) => holds(i));
  while (elsewhere >= 0 && elsewhere + 1 < lines.length && holds(elsewhere + 1)) elsewhere += 1;
  const hint = elsewhere >= 0 ? ` The text is at line ${elsewhere + 1}.` : ' The text is not in that file.';
  return errors.push(`${label}: snippet not found at ${where.file}:${where.line}.${hint}`);
}

function checkProof(root, proof, label, errors) {
  if (typeof proof !== 'object' || proof === null || !PROOFS.includes(proof.kind)) {
    return errors.push(`${label}: proof.kind must be one of ${PROOFS.join(', ')}`);
  }
  checkKeys(proof, KEYS[proof.kind], `${label} proof`, errors);
  if (proof.kind === 'trace') {
    if (!Array.isArray(proof.steps) || proof.steps.length < 2) {
      return errors.push(`${label}: a trace needs at least two steps, from where the value enters to where money moves`);
    }
    proof.steps.forEach((step, i) => {
      checkKeys(step, KEYS.step, `${label} trace step ${i + 1}`, errors);
      checkQuote(root, step, `${label} trace step ${i + 1}`, errors);
      if (!isText(step?.note, 10)) errors.push(`${label} trace step ${i + 1}: note is missing`);
    });
    return undefined;
  }
  if (!isText(proof.command, 5)) errors.push(`${label}: proof.command is missing`);
  if (!isText(proof.result, 20)) errors.push(`${label}: proof.result must say what the run showed`);
  if (proof.kind === 'test' && !resolveInside(root, proof.file)) {
    errors.push(`${label}: test file "${proof.file}" does not exist under the project root`);
  }
  if (proof.output_file !== undefined && !resolveInside(root, proof.output_file)) {
    errors.push(`${label}: output_file "${proof.output_file}" does not exist under the project root`);
  }
  return undefined;
}

export function validate(report, root) {
  const errors = [];
  const warnings = [];
  if (typeof report !== 'object' || report === null) return { errors: ['the file is not a JSON object'], warnings };
  checkKeys(report, KEYS.report, 'report', errors);
  if (report.version !== 1) errors.push('version must be 1');
  if (report.environment !== undefined && !isText(report.environment, 10)) errors.push('environment must say how the app was run');
  if (report.notes !== undefined && !(Array.isArray(report.notes) && report.notes.every((n) => isText(n, 10)))) {
    errors.push('notes must be a list of sentences');
  }
  if (!isText(report.project)) errors.push('project is missing');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(report.date ?? '')) errors.push('date must be YYYY-MM-DD');
  const findings = Array.isArray(report.findings) ? report.findings : (errors.push('findings must be a list'), []);
  const coverage = Array.isArray(report.coverage) ? report.coverage : (errors.push('coverage must be a list'), []);

  const ids = new Set();
  const classesWithFindings = new Set();
  findings.forEach((finding, i) => {
    const label = `finding ${finding?.id ?? `#${i + 1}`}`;
    if (typeof finding !== 'object' || finding === null) return errors.push(`${label}: not an object`);
    checkKeys(finding, KEYS.finding, label, errors);
    checkKeys(finding.location, KEYS.quote, `${label} location`, errors);
    if (!/^MA-\d{2,}$/.test(finding.id ?? '')) errors.push(`${label}: id must look like MA-01`);
    else if (ids.has(finding.id)) errors.push(`${label}: duplicate id`);
    ids.add(finding.id);
    if (!CLASSES.includes(finding.class)) errors.push(`${label}: unknown class "${finding.class}"`);
    else classesWithFindings.add(finding.class);
    if (!SEVERITIES.includes(finding.severity)) errors.push(`${label}: severity must be one of ${SEVERITIES.join(', ')}`);
    if (!isText(finding.title, 10) || finding.title.length > 140) errors.push(`${label}: title must be 10 to 140 characters`);
    if (!isText(finding.impact, 30)) errors.push(`${label}: impact must say what is lost and by whom`);
    if (!isText(finding.fix, 20)) errors.push(`${label}: fix is missing`);
    checkQuote(root, finding.location, `${label} location`, errors);
    checkProof(root, finding.proof, label, errors);
    // A missing ledger is a property of the code as written; there is no request that shows it.
    const runnable = finding.class !== 'ledger-and-audit-trail';
    if (runnable && finding.proof?.kind === 'trace' && ['critical', 'high'].includes(finding.severity)) {
      warnings.push(`${label}: ${finding.severity} severity rests on a code trace only. Run a probe or a test if the app can be started.`);
    }
    return undefined;
  });

  const seen = new Set();
  coverage.forEach((entry, i) => {
    const label = `coverage ${entry?.class ?? `#${i + 1}`}`;
    if (!CLASSES.includes(entry?.class)) return errors.push(`${label}: unknown class`);
    checkKeys(entry, KEYS.coverage, label, errors);
    if (seen.has(entry.class)) errors.push(`${label}: listed twice`);
    seen.add(entry.class);
    if (!STATUSES.includes(entry.status)) return errors.push(`${label}: status must be one of ${STATUSES.join(', ')}`);
    const has = classesWithFindings.has(entry.class);
    if (entry.status === 'finding' && !has) errors.push(`${label}: status is "finding" but no finding has this class`);
    if (entry.status !== 'finding' && has) errors.push(`${label}: there are findings in this class, so status must be "finding"`);
    if (entry.status !== 'not-applicable') {
      if (!Array.isArray(entry.examined) || entry.examined.length === 0) {
        errors.push(`${label}: examined must list the files that were read for this class`);
      } else {
        for (const file of entry.examined) {
          if (!resolveInside(root, file)) errors.push(`${label}: examined file "${file}" does not exist under the project root`);
        }
      }
    }
    if (entry.status !== 'finding' && !isText(entry.note, 20)) {
      errors.push(`${label}: note must say why the class is ${entry.status}`);
    }
    return undefined;
  });
  for (const name of CLASSES) if (!seen.has(name)) errors.push(`coverage: class "${name}" is not accounted for`);

  return { errors, warnings };
}

export function loadReport(file) {
  let report;
  try {
    report = JSON.parse(readFileSync(file, 'utf8'));
  } catch (err) {
    throw new Error(`Cannot read ${file}: ${err.message}`);
  }
  return report;
}

export function parseCli(argv) {
  const args = argv.slice();
  const options = {};
  for (const flag of ['--root', '--out']) {
    const at = args.indexOf(flag);
    if (at >= 0) options[flag.slice(2)] = args.splice(at, 2)[1];
  }
  options.file = args[0];
  options.root = path.resolve(options.root || '.');
  return options;
}

function main() {
  const { file, root } = parseCli(process.argv.slice(2));
  if (!file) {
    console.error('Usage: node validate-findings.mjs <findings.json> [--root <project directory>]');
    process.exitCode = 2;
    return;
  }
  let report;
  try {
    report = loadReport(file);
  } catch (err) {
    console.error(err.message);
    process.exitCode = 2;
    return;
  }
  const { errors, warnings } = validate(report, root);
  for (const warning of warnings) console.log(`warning: ${warning}`);
  if (errors.length) {
    for (const error of errors) console.log(`error: ${error}`);
    console.log(`\nINVALID: ${errors.length} problem${errors.length === 1 ? '' : 's'}. Fix the report, do not delete the check.`);
    process.exitCode = 1;
    return;
  }
  const counts = SEVERITIES.map((s) => `${report.findings.filter((f) => f.severity === s).length} ${s}`).join(', ');
  console.log(`VALID: ${report.findings.length} findings (${counts}), all ${CLASSES.length} classes accounted for.`);
}

if (import.meta.url === pathToFileURL(process.argv[1] || '').href) main();
