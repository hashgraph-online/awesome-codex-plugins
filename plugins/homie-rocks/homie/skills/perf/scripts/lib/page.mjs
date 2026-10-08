/**
 * Is the game page a site serves the page a build made? The site's Worker adds scripts to it: every studio's adds the
 * HOMIE_NET line (the room's address), and a studio's own Worker may add more (a small inline shim, a script of its
 * own). Those are the site's, the same for every build; the game's own page is everything else.
 *
 * So the served page is read as the built page plus scripts: every <script> element of the built page must be there,
 * byte for byte and in order, and so must everything between them (whitespace between tags aside); any other <script>
 * element in the served page is one the site added, and is listed. A stale page or another build's (another bundle's
 * name, a changed inline script, changed markup) never matches; the game's bundle and every other file are compared by
 * SHA-256 apart from this.
 */
import { createHash } from 'node:crypto';

const SCRIPT = /<script\b[^>]*>[\s\S]*?<\/script\s*>/gi;
const sha = (s) => createHash('sha256').update(s).digest('hex');

/** The <script> elements of a page, in order, and the text between them. */
function split(html) {
  const scripts = [];
  const between = [];
  let at = 0;
  for (const m of html.matchAll(SCRIPT)) {
    between.push(html.slice(at, m.index));
    scripts.push(m[0]);
    at = m.index + m[0].length;
  }
  between.push(html.slice(at));
  return { scripts, between };
}

/** Markup with the whitespace between tags (and at either end) taken out: an injected line's newline is not a change. */
const tight = (s) => s.replace(/>\s+</g, '><').replace(/>\s+$/, '>').replace(/^\s+</, '<').trim();

/** What one added script is, for a person: the site's HOMIE_NET line, an inline script, or a script from an address. */
function describe(el) {
  const open = /^<script\b([^>]*)>/i.exec(el)?.[1] ?? '';
  const src = /\bsrc\s*=\s*["']?([^"'\s>]+)/i.exec(open)?.[1] ?? null;
  const body = el.replace(/^<script\b[^>]*>/i, '').replace(/<\/script\s*>$/i, '');
  const kind = /^\s*window\.HOMIE_NET\s*=/.test(body) ? 'homie-net' : src ? 'src' : 'inline';
  return { kind, ...(src ? { src } : {}), bytes: Buffer.byteLength(el), sha256: sha(el).slice(0, 16), starts: body.trim().slice(0, 48) };
}

/**
 * Compare the built page with the served one. Returns { same, added: [{ kind, src?, bytes, sha256, starts }], why }:
 * `added` is every script the site put in the page (HOMIE_NET included); `why` says what differs when it is not the same.
 */
export function gamePageCheck(built, served) {
  const b = split(String(built));
  const s = split(String(served));
  // Walk the served scripts, matching the built ones in order; any served script that is not the next built one is
  // the site's. (A built script the served page lacks is a different page.)
  const added = [];
  const kept = [];
  let k = 0;
  for (const el of s.scripts) {
    if (k < b.scripts.length && el === b.scripts[k]) { kept.push(el); k++; } else added.push(el);
  }
  if (k < b.scripts.length) {
    const missing = b.scripts[k];
    return { same: false, added: added.map(describe), why: `the page lacks the build's script ${describe(missing).src ?? `"${describe(missing).starts}…"`} (${s.scripts.length - added.length} of the build's ${b.scripts.length} scripts there)` };
  }
  // The rest of the page: the served text between its kept scripts must be the built text between the same scripts.
  let rebuilt = '';
  let ki = 0;
  for (let j = 0; j < s.scripts.length; j++) {
    rebuilt += s.between[j];
    if (ki < kept.length && s.scripts[j] === kept[ki]) { rebuilt += `\u0000${ki}\u0000`; ki++; }
  }
  rebuilt += s.between[s.between.length - 1];
  let want = '';
  for (let j = 0; j < b.scripts.length; j++) want += `${b.between[j]}\u0000${j}\u0000`;
  want += b.between[b.between.length - 1];
  if (rebuilt === want || tight(rebuilt) === tight(want)) return { same: true, added: added.map(describe), why: null };
  const x = tight(rebuilt);
  const y = tight(want);
  let at = 0;
  while (at < x.length && at < y.length && x[at] === y[at]) at++;
  const show = (t) => JSON.stringify(t.slice(Math.max(0, at - 24), at + 40).replace(/\u0000\d+\u0000/g, '<script…>'));
  return { same: false, added: added.map(describe), why: `the page's markup differs from the build's at character ${at}: served ${show(x)}, built ${show(y)}` };
}

/**
 * Two lists of added scripts are the same site: the same scripts in the same order. The HOMIE_NET line counts by
 * kind only: its words come from the game's game.json (movement, saves), which a change to the game may touch.
 */
const additionKey = (x) => (x.kind === 'homie-net' ? 'homie-net' : x.sha256);
export const sameAdditions = (a, b) => JSON.stringify((a ?? []).map(additionKey)) === JSON.stringify((b ?? []).map(additionKey));
