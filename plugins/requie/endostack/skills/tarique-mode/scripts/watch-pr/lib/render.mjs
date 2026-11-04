import { draftLabel } from './proof.mjs';

// Human-readable rendering of verdict objects for --pretty. Works only
// from the verdict object, so pretty and JSON output never disagree.

function cell(text) {
  return String(text).replace(/\\/g, '\\\\').replace(/\|/g, '\\|').replace(/[\r\n]+/g, ' ');
}

function ciCell(r) {
  if (r.status !== 'open') return '-';
  const c = r.ci;
  const green = c.wasGreenBefore ? ' (was green before)' : '';
  if (c.state === 'clean') return `clean${green}`;
  if (c.state === 'pending') return `${c.pending.length} pending${green}`;
  if (c.state === 'failing') {
    const pend = c.pending.length ? `, ${c.pending.length} pending` : '';
    return `${c.failed.length} failed${pend}${green}`;
  }
  return `GitHub-reported failure (head rollup ${c.headRollup})${green}`;
}

function reviewCell(r) {
  if (r.status !== 'open') return '-';
  const parts = [`${r.threads} open thread${r.threads === 1 ? '' : 's'}`];
  if (r.reviewAutomationRunning) parts.push('review automation running');
  return parts.join(', ');
}

function mergeCell(r) {
  return { ok: 'ok', merged: 'merged', closed: 'closed', draft: 'draft', 'changes-requested': 'changes requested', conflict: 'conflict', 'approval-check': 'awaiting approval check' }[r.merge] ?? r.merge;
}

export function statusTable(rows) {
  const header = ['PR', 'Checks', 'Threads', 'Mergeability'];
  const lines = [`| ${header.join(' | ')} |`, `|${header.map(() => ' --- |').join('')}`];
  for (const r of rows) {
    lines.push(`| [#${r.pr}](${r.url}) | ${cell(ciCell(r))} | ${cell(reviewCell(r))} | ${cell(mergeCell(r))} |`);
  }
  return lines.join('\n');
}

function oneLine(text, max) {
  const first = String(text ?? '').split(/\r?\n/).find((l) => l.trim() !== '') ?? '';
  const t = first.trim();
  return t.length > max ? `${t.slice(0, max)}...` : t;
}

function renderBlocker(v) {
  const out = [];
  const titles = {
    conflict: 'merge conflicts',
    threads: 'unresolved review threads',
    checks: 'failing checks',
    gate: 'merge gate',
    'status-query': 'GitHub status could not be read',
  };
  out.push(`BLOCKER: ${titles[v.blocker] ?? v.blocker}${v.pr ? ` on #${v.pr}` : ''} (exit ${v.exitCode})`);
  if (v.pr) out.push(`pr=${v.pr}`);
  if (v.blocker === 'conflict') {
    out.push(`mergeable=${v.mergeable}`, `merge_state=${v.mergeState}`);
  } else if (v.blocker === 'threads') {
    out.push(`threads=${v.threadCount}`, `bot_passes=${v.botPasses}`);
    for (const t of v.threads) {
      out.push(
        `thread id=${t.id} path=${t.path ?? '-'} line=${t.line ?? '-'} author=${t.author ?? '-'} bot=${t.bot} passes=${t.botPasses} body=${JSON.stringify(oneLine(t.body, 180))}`,
      );
    }
  } else if (v.blocker === 'checks') {
    out.push(`failed=${v.failed.length}`, `pending=${v.pending.length}`);
    for (const c of v.failed) {
      out.push(`check name=${JSON.stringify(c.name)} state=${c.state ?? '-'} description=${JSON.stringify(oneLine(c.description, 180))} link=${c.link || '-'}`);
    }
    if (v.github?.refuses) {
      out.push(
        `github_refuses=true merge_state=${v.github.mergeState} head_rollup=${v.github.headRollup} was_green_before=${v.github.wasGreenBefore}`,
      );
    }
  } else if (v.blocker === 'gate') {
    out.push(`reason=${v.reason}`, `draft=${v.draft}`, `review_decision=${v.reviewDecision ?? 'none'}`);
    for (const c of v.approvalChecks) out.push(`approval_check name=${JSON.stringify(c.name)} state=${c.state ?? '-'}`);
  } else if (v.blocker === 'status-query') {
    out.push(`failures=${v.failures}`, `error=${v.error.kind}`, `detail=${JSON.stringify(v.error.detail)}`);
    if (v.error.raw !== undefined) out.push(`raw=${JSON.stringify(v.error.raw)}`);
  }
  out.push(`action=${v.action}`);
  return out.join('\n');
}

function renderReady(v) {
  const head = v.mode === 'single' ? `READY: #${v.prs[0].pr}` : `READY: ${v.prs.map((p) => `#${p.pr}`).join(' ')}`;
  const lines = [`${head}: no conflicts, no unresolved threads, no failing or pending checks.`];
  if (v.prs.length === 1 && !v.prs[0].merged) {
    const p = v.prs[0];
    lines.push(`merge_state=${p.mergeState} review_decision=${p.reviewDecision ?? 'none'} draft=${p.draft}`);
    if (p.draft === draftLabel(true)) lines.push('note: the PR is a draft and --allow-draft was set; leave it as a draft.');
  }
  return lines.join('\n');
}

export function render(v) {
  switch (v.kind) {
    case 'STATUS':
      return `STATUS ${v.rows.length} PR${v.rows.length === 1 ? '' : 's'}\n${statusTable(v.rows)}`;
    case 'BLOCKER':
      return renderBlocker(v);
    case 'READY':
      return renderReady(v);
    case 'QUEUE':
      return `QUEUE: watching ${v.prs.length} PRs bottom to top: ${v.prs.map((n) => `#${n}`).join(' ')}`;
    case 'WAITING':
      return v.reason === 'merge-queue'
        ? `WAITING: #${v.pr} is blocker-free, waiting for the merge queue (${v.unmerged} unmerged)`
        : `WAITING: #${v.pr} has ${v.pending.length} pending check${v.pending.length === 1 ? '' : 's'}: ${v.pending.join(', ')}`;
    case 'ADVANCE':
      return `ADVANCE: merged ${v.merged.map((n) => `#${n}`).join(' ')}; frontier is now #${v.frontier}; ${v.remaining} remaining`;
    case 'RETRY':
      return `RETRY: read failed (${v.error.kind}: ${v.error.detail}); failure ${v.failures}; retrying in ${v.backoffSeconds}s`;
    case 'COMPLETE':
      return `COMPLETE: all ${v.merged.length} queued PRs merged: ${v.merged.map((n) => `#${n}`).join(' ')}`;
    case 'TIMEOUT':
      if (v.reason === 'status-unavailable') return `TIMEOUT: deadline passed while GitHub status was unavailable (${v.failures} failures)`;
      if (v.mode === 'queued') return `TIMEOUT: deadline passed with frontier #${v.pr} and ${v.unmerged} unmerged`;
      return `TIMEOUT: deadline passed waiting on #${v.pr}: ${v.pending.join(', ') || 'no pending checks recorded'}`;
    default:
      return JSON.stringify(v);
  }
}
