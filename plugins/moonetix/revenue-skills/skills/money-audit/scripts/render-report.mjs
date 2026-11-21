#!/usr/bin/env node
// render-report.mjs: turn a valid findings.json into a Markdown report.
// Usage: node render-report.mjs <findings.json> [--root <project directory>] [--out REPORT.md]
import { writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { CLASSES, SEVERITIES, loadReport, parseCli, validate } from './validate-findings.mjs';

const plural = (n) => `${n} finding${n === 1 ? '' : 's'}`;

const CLASS_TITLES = {
  'unverified-events': 'Unverified inbound events',
  'duplicate-credit': 'Duplicate credit',
  'balance-races': 'Races on a balance',
  'client-trust': 'Amounts trusted from the client',
  'money-arithmetic': 'Money arithmetic',
  'refunds-and-reversals': 'Refunds and reversals',
  'promo-and-referral-abuse': 'Promo, trial and referral abuse',
  'payout-controls': 'Payout controls',
  'secrets-and-access': 'Secrets and access on the money path',
  'ledger-and-audit-trail': 'Ledger and audit trail',
};
const PROOF_LABELS = { probe: 'Demonstrated with a live request', test: 'Demonstrated with a test', trace: 'Traced in code, not run' };

const cell = (text) => String(text).replace(/\|/g, '\\|').replace(/\s+/g, ' ').trim();
const fence = (text) => `\`\`\`\n${String(text).replace(/```/g, "'''").trimEnd()}\n\`\`\``;

export function render(report) {
  const findings = [...report.findings].sort(
    (a, b) => SEVERITIES.indexOf(a.severity) - SEVERITIES.indexOf(b.severity) || a.id.localeCompare(b.id),
  );
  const out = [`# Money audit: ${report.project}`, '', `Date: ${report.date}`, ''];
  const counts = SEVERITIES.map((s) => `${findings.filter((f) => f.severity === s).length} ${s}`).join(', ');
  out.push(findings.length ? `**${plural(findings.length)}:** ${counts}.` : '**No findings.**', '');
  if (report.environment) out.push(`**How the app was run.** ${report.environment.trim()}`, '');

  if (findings.length) {
    out.push('## Summary', '', '| ID | Severity | Class | Finding | Where | Proof |', '| --- | --- | --- | --- | --- | --- |');
    for (const f of findings) {
      out.push(
        `| ${f.id} | ${f.severity} | ${CLASS_TITLES[f.class]} | ${cell(f.title)} | \`${f.location.file}:${f.location.line}\` | ${f.proof.kind} |`,
      );
    }
    out.push('', '## Findings', '');
    for (const f of findings) {
      out.push(`### ${f.id}: ${f.title}`, '');
      out.push(`- **Severity:** ${f.severity}`, `- **Class:** ${CLASS_TITLES[f.class]}`);
      out.push(`- **Where:** \`${f.location.file}:${f.location.line}\``, '', fence(f.location.snippet), '');
      out.push(`**Impact.** ${f.impact.trim()}`, '', `**Proof.** ${PROOF_LABELS[f.proof.kind]}.`, '');
      if (f.proof.kind === 'trace') {
        f.proof.steps.forEach((step, i) => {
          out.push(`${i + 1}. \`${step.file}:${step.line}\` ${step.note.trim()}`, '', fence(step.snippet), '');
        });
      } else {
        out.push(fence(f.proof.command), '', f.proof.result.trim(), '');
      }
      out.push(`**Fix.** ${f.fix.trim()}`, '');
    }
  }

  out.push('## Coverage', '', '| Class | Result | Files read | Note |', '| --- | --- | --- | --- |');
  for (const name of CLASSES) {
    const entry = report.coverage.find((c) => c.class === name);
    const files = (entry.examined || []).map((f) => `\`${f}\``).join(', ') || 'none';
    const result = entry.status === 'finding' ? plural(findings.filter((f) => f.class === name).length) : entry.status;
    out.push(`| ${CLASS_TITLES[name]} | ${result} | ${files} | ${cell(entry.note || '')} |`);
  }
  out.push('');
  if (report.notes?.length) {
    out.push('## Notes', '', ...report.notes.map((note) => `- ${note.trim()}`), '');
  }
  return out.join('\n');
}

function main() {
  const { file, root, out } = parseCli(process.argv.slice(2));
  if (!file) {
    console.error('Usage: node render-report.mjs <findings.json> [--root <project directory>] [--out REPORT.md]');
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
  const { errors } = validate(report, root);
  if (errors.length) {
    console.error(`Not rendering: the findings file has ${errors.length} problem${errors.length === 1 ? '' : 's'}. Run validate-findings.mjs.`);
    process.exitCode = 1;
    return;
  }
  const text = render(report);
  if (out) writeFileSync(out, text);
  else process.stdout.write(text);
}

if (import.meta.url === pathToFileURL(process.argv[1] || '').href) main();
