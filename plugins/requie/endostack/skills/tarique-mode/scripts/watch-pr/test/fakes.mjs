// Test doubles: a scripted GitHub reader and a manual clock.

import { emptyConfig } from '../lib/config.mjs';
import { QueryError } from '../lib/errors.mjs';

// Same values as the documented flag defaults.
const TIMING_DEFAULTS = { maxQueryErrors: 5, timeout: 0, sweepInterval: 300, interval: 60 };

export function fakeClock(start = 1_700_000_000) {
  const clock = {
    t: start,
    sleeps: [],
    now: () => clock.t,
    sleep: async (s) => {
      clock.sleeps.push(s);
      clock.t += s;
    },
  };
  return clock;
}

export function cfg(overrides = {}) {
  return { ...emptyConfig(), ...overrides };
}

export function prFields(over = {}) {
  return {
    state: 'OPEN',
    isDraft: false,
    mergedAt: null,
    baseRefName: 'main',
    headRefName: 'feature',
    headRefOid: 'a'.repeat(40),
    mergeable: 'MERGEABLE',
    mergeStateStatus: 'CLEAN',
    reviewDecision: 'APPROVED',
    ...over,
  };
}

export const passCheck = (name = 'build') => ({ name, state: 'SUCCESS', bucket: 'pass', description: '', link: '', workflow: 'ci' });
export const pendCheck = (name = 'build') => ({ name, state: 'IN_PROGRESS', bucket: 'pending', description: '', link: '', workflow: 'ci' });
export const failCheck = (name = 'build') => ({ name, state: 'FAILURE', bucket: 'fail', description: 'tests failed', link: 'https://ci/1', workflow: 'ci' });

// A PR's state at one poll: { fields, threads: [threadNodes], checks, commits }
// `script` maps PR number -> array of states (the last one repeats) or a
// single state. A state may be an Error to make prFields throw.
export function fakeReader({ script = {}, origin = 'https://github.com/acme/widgets.git', lookup, openPrs = [], calls = [] } = {}) {
  const cursorPos = new Map();
  const stateFor = (n) => {
    const s = script[n];
    if (!Array.isArray(s)) return s;
    const i = cursorPos.get(n) ?? 0;
    return s[Math.min(i, s.length - 1)];
  };
  const reader = {
    calls,
    async originUrl() {
      calls.push(['originUrl']);
      return origin;
    },
    async lookupPr(n) {
      calls.push(['lookupPr', n]);
      if (lookup instanceof Error) throw lookup;
      return lookup ?? { number: n ?? 1, url: `https://github.com/acme/widgets/pull/${n ?? 1}` };
    },
    async listOpenPrs() {
      calls.push(['listOpenPrs']);
      return openPrs;
    },
    async prFields(o, r, n) {
      calls.push(['prFields', n]);
      const st = stateFor(n);
      // advance this PR's script on each prFields read
      cursorPos.set(n, (cursorPos.get(n) ?? 0) + 1);
      if (st instanceof Error) throw st;
      if (!st) throw new QueryError('command-failed', `no script for #${n}`);
      reader._current = st;
      return st.fields ?? prFields();
    },
    async threadPage(o, r, n, cursor) {
      calls.push(['threadPage', n, cursor]);
      const st = reader._current;
      const pages = st.threadPages ?? [{ nodes: st.threads ?? [], pageInfo: { hasNextPage: false, endCursor: null } }];
      const idx = cursor === null ? 0 : Number(cursor.replace('c', ''));
      return pages[idx];
    },
    async checksFast(o, r, n) {
      calls.push(['checksFast', n]);
      const st = reader._current;
      if (st.fast) return st.fast;
      const list = st.checks ?? [passCheck()];
      return { code: 0, stdout: JSON.stringify(list), stderr: '' };
    },
    async rollupPage(o, r, n, cursor) {
      calls.push(['rollupPage', n, cursor]);
      const st = reader._current;
      const pages = st.rollupPages ?? [{ nodes: [], pageInfo: { hasNextPage: false, endCursor: null } }];
      const idx = cursor === null ? 0 : Number(cursor.replace('r', ''));
      return pages[idx];
    },
    async commitRollups(o, r, n) {
      calls.push(['commitRollups', n]);
      const st = reader._current;
      return st.commits ?? [{ oid: (st.fields ?? prFields()).headRefOid, state: 'SUCCESS' }];
    },
  };
  return reader;
}

export function thread({ id = 'T1', resolved = false, author = 'alice', body = 'please fix', path = 'src/a.js', line = 3 } = {}) {
  return {
    id,
    isResolved: resolved,
    comments: { nodes: [{ author: { login: author }, body, path, line, createdAt: '2026-10-01T00:00:00Z' }] },
  };
}

export function baseOpts(over = {}) {
  return {
    help: false,
    owner: 'acme',
    repo: 'widgets',
    pr: 1,
    mode: 'single',
    stackPrs: null,
    ...TIMING_DEFAULTS,
    statusOnly: false,
    allowDraft: false,
    reviewBots: [],
    approvalChecks: [],
    configPath: null,
    pretty: false,
    ...over,
  };
}

export function collector() {
  const out = [];
  return { out, write: (v) => out.push(v) };
}
