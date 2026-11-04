// Reads TLC's -tool output: splits it into nested messages, renders it the way
// plain TLC prints it, and extracts verdict facts and counterexample traces.

const START_RE = /@!@!@STARTMSG (\d+):(\d+) @!@!@$/;
const END_RE = /^@!@!@ENDMSG (\d+) @!@!@$/;

export const LEVEL = { NONE: 0, ERROR: 1, BUG: 2, WARNING: 3, STATE: 4 };

export const CODE = {
  INVARIANT_INITIAL: 2107,
  PROPERTY_INITIAL: 2108,
  INVARIANT_VIOLATED: 2110,
  ACTION_PROPERTY: 2112,
  DEADLOCK: 2114,
  TEMPORAL: 2116,
  BEHAVIOR_HEADER: 2121,
  BACK_TO_STATE: 2122,
  STATE: 2217,
  STUTTER: 2218,
  COUNTEREXAMPLE_HEADER: 2264,
  INIT_DONE: 2190,
  STATS: 2199,
  PROGRESS: 2200,
  FINISHED: 2186,
  SANY_START: 2220,
  SANY_END: 2219,
};

// Parse output text into a tree. Each node is either a string (one text line)
// or {code, level, body:[nodes], closed}. A text node may carry a `glue` flag
// meaning a message started on the same line right after it.
export function parseMessages(text) {
  const root = { body: [] };
  const stack = [root];
  const lines = text.split('\n');
  const endsWithNewline = text.endsWith('\n');
  if (endsWithNewline) lines.pop();
  for (const line of lines) {
    const top = stack[stack.length - 1];
    const end = END_RE.exec(line);
    if (end && stack.length > 1) {
      top.closed = true;
      stack.pop();
      continue;
    }
    const start = START_RE.exec(line);
    if (start) {
      const before = line.slice(0, start.index);
      if (before !== '') top.body.push({ text: before, glue: true });
      const msg = { code: Number(start[1]), level: Number(start[2]), body: [], closed: false };
      top.body.push(msg);
      stack.push(msg);
      continue;
    }
    top.body.push(line);
  }
  return { body: root.body, cut: stack.length > 1, endsWithNewline };
}

function isMsg(n) {
  return typeof n === 'object' && n !== null && 'code' in n;
}

export function messageText(msg) {
  const out = [];
  for (const n of msg.body) {
    if (typeof n === 'string') out.push(n);
    else if (isMsg(n)) out.push(messageText(n));
    else out.push(n.text);
  }
  return out.join('\n');
}

const PREFIX = { 1: 'Error: ', 2: 'TLC Bug: ', 3: 'Warning: ', 4: 'State ' };
const WARNING_HINT = '(Use the -nowarning option to disable this warning.)';

function pad2(n) {
  return String(n).padStart(2, '0');
}

// TLC's human duration for a millisecond count.
export function formatDuration(ms) {
  const totalSeconds = Math.floor(ms / 1000);
  const s = totalSeconds % 60;
  const totalMinutes = Math.floor(totalSeconds / 60);
  const m = totalMinutes % 60;
  const totalHours = Math.floor(totalMinutes / 60);
  const h = totalHours % 24;
  const d = Math.floor(totalHours / 24);
  if (totalSeconds < 60) return `${pad2(s)}s`;
  if (totalMinutes < 60) return `${pad2(m)}min ${pad2(s)}s`;
  if (totalHours < 24) return `${pad2(h)}h ${pad2(m)}min`;
  return `${d}d ${pad2(h)}h`;
}

// Render a parsed tree as plain TLC output.
export function renderPlain(tree) {
  const state = { warned: false };
  const lines = renderNodes(tree.body, state, true);
  let text = '';
  for (const l of lines) text += l.glue ? l.text : `${l.text}\n`;
  if (!tree.endsWithNewline && text.endsWith('\n')) text = text.slice(0, -1);
  return text;
}

// Returns [{text, glue}] where glue means "no newline after this piece".
function renderNodes(nodes, state, topLevel) {
  const out = [];
  for (let i = 0; i < nodes.length; i++) {
    const n = nodes[i];
    if (typeof n === 'string') { out.push({ text: n }); continue; }
    if (!isMsg(n)) { out.push({ text: n.text, glue: true }); continue; }
    if (n.code === CODE.SANY_START || n.code === CODE.SANY_END) continue;
    if (topLevel && n.code === CODE.PROGRESS && n.closed) {
      const next = nodes.slice(i + 1).find((x) => typeof x !== 'string' || x !== '');
      if (next && isMsg(next) && next.code === CODE.STATS) continue;
    }
    const body = renderMessageBody(n, state);
    const prefix = n.code === CODE.BACK_TO_STATE ? '' : PREFIX[n.level] ?? '';
    if (body.length === 0) body.push({ text: '' });
    body[0] = { ...body[0], text: prefix + body[0].text };
    out.push(...body);
    if (n.level === LEVEL.WARNING && !state.warned && n.closed) {
      state.warned = true;
      out.push({ text: WARNING_HINT });
    }
  }
  return out;
}

function renderMessageBody(msg, state) {
  if (msg.code === CODE.BACK_TO_STATE) {
    const lines = renderNodes(msg.body, state, false);
    if (lines.length) {
      const m = /^(\d+): Back to state: (.*)$/.exec(lines[0].text);
      if (m) lines[0] = { text: `Back to state ${m[1]}: ${m[2]}` };
    }
    return lines;
  }
  if (msg.code === CODE.FINISHED) {
    const lines = renderNodes(msg.body, state, false);
    if (lines.length) {
      const m = /^Finished in (\d+)ms at (.*)$/.exec(lines[0].text);
      if (m) lines[0] = { text: `Finished in ${formatDuration(Number(m[1]))} at ${m[2]}` };
    }
    return lines;
  }
  return renderNodes(msg.body, state, false);
}

export function renderPlainText(text) {
  return renderPlain(parseMessages(text));
}

// ---- verdict facts ----

function topMessages(tree) {
  return tree.body.filter(isMsg);
}

const NAMED = [
  [CODE.INVARIANT_VIOLATED, /^Invariant (.+) is violated\.?/, 'invariant'],
  [CODE.INVARIANT_INITIAL, /^Invariant (.+) is violated by the initial state/, 'invariant'],
  [CODE.PROPERTY_INITIAL, /^Property (.+) is violated by the initial state/, 'property'],
  [CODE.ACTION_PROPERTY, /^Action property (.+) is violated\.?/, 'property'],
];

// Facts from one run: first broken rule, counts, error messages.
export function runFacts(tree) {
  const facts = { broken: null, distinct: null, initial: null, errors: [], temporal: false };
  for (const m of topMessages(tree)) {
    const first = messageText(m).split('\n')[0];
    if (!facts.broken) {
      if (m.code === CODE.DEADLOCK) facts.broken = { kind: 'deadlock', code: m.code };
      else if (m.code === CODE.TEMPORAL) { facts.broken = { kind: 'temporal', code: m.code }; facts.temporal = true; }
      else {
        for (const [code, re, kind] of NAMED) {
          if (m.code !== code) continue;
          const r = re.exec(first);
          if (r) facts.broken = { kind, name: r[1], code };
        }
      }
    }
    if (m.code === CODE.INIT_DONE) {
      const r = /: (\d+) distinct states? generated/.exec(first);
      if (r) facts.initial = Number(r[1]);
    }
    if (m.code === CODE.STATS || m.code === CODE.PROGRESS) {
      const r = /([\d,]+) distinct states found/.exec(first);
      if (r) facts.distinct = Math.max(facts.distinct ?? 0, Number(r[1].replace(/,/g, '')));
    }
  }
  return facts;
}

// Error, bug, and state messages as plain lines (for exit-2 explanations).
export function errorExcerpt(tree, maxLines = 40) {
  const lines = [];
  for (const m of topMessages(tree)) {
    if (m.level === LEVEL.ERROR || m.level === LEVEL.BUG || m.level === LEVEL.STATE) {
      const rendered = renderPlain({ body: [m], endsWithNewline: true }).replace(/\n+$/, '');
      lines.push(...rendered.split('\n'));
    }
  }
  if (lines.length) return lines.slice(0, maxLines).join('\n');
  const plain = renderPlain(tree).replace(/\n+$/, '').split('\n');
  return plain.slice(-30).join('\n');
}

// Pull the action name out of "<Name line 5, col 8 to line 5, col 36 of module M>".
export function actionName(header) {
  const m = /^<(.*?) line \d+, col \d+ to line \d+, col \d+ of module [^>]*>$/.exec(header);
  if (m) return m[1];
  const inner = /^<(.*)>$/.exec(header);
  return inner ? inner[1] : header;
}

// The counterexample of a run: [{action, text}] plus lasso info.
// action is null for the initial state. text is the state printout.
export function trace(tree) {
  const states = [];
  let loopBack = null;
  let stutter = false;
  for (const m of topMessages(tree)) {
    if (m.code === CODE.STATE) {
      const text = messageText(m);
      const nl = text.indexOf('\n');
      const head = nl < 0 ? text : text.slice(0, nl);
      const body = nl < 0 ? '' : text.slice(nl + 1);
      const r = /^(\d+): (.*)$/.exec(head);
      if (!r) continue;
      const header = r[2];
      states.push({ action: header === '<Initial predicate>' ? null : actionName(header), text: body.replace(/\n+$/, '') });
    } else if (m.code === CODE.BACK_TO_STATE) {
      const r = /^(\d+): Back to state: (.*)$/.exec(messageText(m).split('\n')[0]);
      if (r) loopBack = { index: Number(r[1]) - 1, action: actionName(r[2]) };
    } else if (m.code === CODE.STUTTER) {
      stutter = true;
    } else if (m.code === CODE.INVARIANT_INITIAL || m.code === CODE.PROPERTY_INITIAL) {
      const text = messageText(m);
      const nl = text.indexOf('\n');
      states.push({ action: null, text: (nl < 0 ? '' : text.slice(nl + 1)).replace(/\n+$/, '') });
    }
  }
  return { states, loopBack, stutter };
}

// Plain stdout text lines outside any message (spec output, PrintT marks).
export function plainLines(tree) {
  const out = [];
  for (const n of tree.body) {
    if (typeof n === 'string') out.push(n);
    else if (!isMsg(n)) out.push(n.text);
    else out.push(null); // a message boundary
  }
  return out;
}
