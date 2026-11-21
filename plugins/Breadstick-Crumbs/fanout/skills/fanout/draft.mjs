// Drafts .fanout/plan.md from a goal written as sections ("## name" headings), with no AI call. An agent
// then writes the contracts, and reviews the names the draft flags (`flags`: what a section uses from a file
// another session owns). On the sheet benchmark the planner spent most
// of its minute reading the code and deciding the split; a goal that already names its parts and files
// doesn't need that.
//
// From each section: its name, a one-line task (the first sentence), and the files it mentions in
// backticks. A file goes to the section that adds or changes it ("Add `src/x.mjs`"), or to the only section
// that mentions it. Other sections that mention it build against it (uses/exposes). A file the text before
// the first heading calls generated, with a backticked command next to it, becomes a regen line. Sections
// are merged, smallest first, until there are at most maxSessions; a pair where one builds on the other
// merges sooner, since that removes a contract. Returns null when the goal isn't in that shape.
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { join, basename, dirname, extname } from "node:path";
import { matches } from "./fanout.mjs";

// The names a JS/TS module exports.
export function jsExports(src) {
  const names = [...src.matchAll(/^export\s+(?:default\s+)?(?:async\s+)?(?:function\*?|const|let|var|class)\s+([A-Za-z_$][\w$]*)/gm)].map((m) => m[1]);
  for (const m of src.matchAll(/^export\s*\{([^}]*)\}/gm)) names.push(...m[1].split(",").map((x) => x.trim().split(/\s+as\s+/).pop()).filter(Boolean));
  return names;
}

const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const ticks = (s) => [...s.matchAll(/`([^`\n]+)`/g)].map((m) => m[1]);
const sentences = (s) => s.split(/(?<=[.!?])\s+|\n+/).filter(Boolean);

export function draftPlan({ goal, root, maxSessions = 4 }) {
  if (!goal) return null;
  const parts = goal.split(/^#{2,3}[ \t]+(.+)$/m);
  const preamble = parts[0].replace(/^#[^#].*$/m, "").trim();
  const sections = [];
  for (let i = 1; i < parts.length; i += 2) sections.push({ name: slug(parts[i]), heading: parts[i].trim(), text: parts[i + 1].trim() });
  if (sections.length < 2 || sections.some((s) => !s.name) || new Set(sections.map((s) => s.name)).size < sections.length) return null;

  const files = new Set(spawnSync("git", ["ls-files"], { cwd: root, encoding: "utf8" }).stdout.split("\n").filter(Boolean));
  const isPath = (t) => /^[\w.\-/]+\.[A-Za-z][A-Za-z0-9]*$/.test(t) && (t.includes("/") || files.has(t));

  // Generated files: a sentence before the first heading that says "generated" and names a path (a glob is
  // fine: `css/f-*-rtl.css`) and a command. The test command: a sentence that says "test" and names a command.
  const regen = [];
  let goalTest = null;
  for (const sen of sentences(preamble)) {
    const t = ticks(sen), cmd = t.find((x) => /\s/.test(x));
    if (/generated/i.test(sen)) {
      const paths = t.filter((x) => isPath(x) || (/^[\w.\-/*]+\.[A-Za-z][A-Za-z0-9]*$/.test(x) && x.includes("*") && x.includes("/")));
      if (paths.length && cmd) regen.push({ paths, cmd });
    } else if (/\btests?\b/i.test(sen) && cmd && !goalTest) goalTest = cmd;
  }
  const isGenerated = (p) => regen.some((r) => r.paths.some((g) => matches(g, p)));

  // Who owns each mentioned file.
  const mentions = new Map();
  for (const s of sections) {
    s.paths = [...new Set(ticks(s.text).filter(isPath))].filter((p) => !isGenerated(p));
    for (const p of s.paths) (mentions.get(p) ?? mentions.set(p, []).get(p)).push(s);
  }
  const owner = new Map();
  for (const [p, ss] of mentions) {
    const esc = p.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    // "Add `src/x.mjs`", "change `src/x.mjs`", or "Add `f()` in `src/x.mjs`".
    const adds = new RegExp(`\\b(add|create|change|update|edit|rewrite|extend)\\s+\`${esc}\`|\\b(add|create)\\b[^.\\n]*\\bin\\s+\`${esc}\``, "i");
    const adder = ss.find((s) => adds.test(s.text));
    if (adder) owner.set(p, adder);
    else if (ss.length === 1) owner.set(p, ss[0]);
    else if (!files.has(p)) return null; // a new file several sections mention and none adds: can't tell whose
  }
  // Each section's own tests, next to the project's existing ones (test/<module>.test.mjs).
  const testFile = [...files].find((f) => /\.test\.[A-Za-z]+$/.test(f));
  for (const s of sections) {
    s.owns = [...owner].filter(([, o]) => o === s).map(([p]) => p);
    if (!s.owns.length) return null;
    if (testFile) {
      const suffix = testFile.slice(testFile.indexOf(".test.")), dir = dirname(testFile);
      for (const p of s.owns.filter((p) => !files.has(p))) {
        const t = `${dir}/${basename(p, extname(p))}${suffix}`;
        if (!files.has(t) && !owner.has(t) && !s.owns.includes(t)) s.owns.push(t);
      }
    }
    s.task = sentences(s.text)[0].replace(/(\s+with)?[:.]?$/, "").slice(0, 160);
  }
  // With node's test runner, each session can check its own test files on the merged code.
  // A test command the goal names wins over package.json's.
  let test = goalTest, nodeTest = false;
  try {
    const t = JSON.parse(readFileSync(join(root, "package.json"), "utf8")).scripts?.test;
    if (t && !test) { test = "npm test"; nodeTest = /^node\s+--test\b/.test(t); }
  } catch { /* no package.json */ }

  // Merge down to maxSessions: the pair with the least spec text, a pair with a dependency counting as less.
  const groups = sections.map((s) => ({ members: [s] }));
  const size = (g) => g.members.reduce((n, s) => n + s.text.length, 0);
  const owned = (g) => new Set(g.members.flatMap((s) => s.owns));
  const linked = (a, b) => { const oa = owned(a), ob = owned(b); return a.members.some((s) => s.paths.some((p) => ob.has(p))) || b.members.some((s) => s.paths.some((p) => oa.has(p))); };
  while (groups.length > Math.max(1, maxSessions)) {
    let best = null;
    for (let i = 0; i < groups.length; i++) for (let j = i + 1; j < groups.length; j++) {
      const cost = (size(groups[i]) + size(groups[j])) * (linked(groups[i], groups[j]) ? 0.75 : 1);
      if (!best || cost < best.cost) best = { i, j, cost };
    }
    groups[best.i].members.push(...groups[best.j].members);
    groups.splice(best.j, 1);
  }

  const sessions = groups.map((g) => {
    const name = g.members.map((s) => s.name).join("-"), own = owned(g);
    const uses = [...new Set(g.members.flatMap((s) => s.paths).filter((p) => !own.has(p) && owner.has(p)))];
    return { name, members: g.members, owns: [...own], uses, task: g.members.map((s) => s.task).join("; ") };
  });
  for (const s of sessions) s.exposes = s.owns.filter((p) => sessions.some((o) => o !== s && o.uses.includes(p)));

  // Names a session's sections mention (`createStore`, `f(x)`) that an existing file another session owns
  // defines, when the session doesn't build on that file: the goal may need it changed without naming the
  // file (library benchmark: fines needs `createStore` to start with `payments: []`, and holds owns
  // src/store.mjs). Only these need an agent to look; a draft with none skips the review.
  // JS/TS exports, and PHP functions (global, so every top-level one counts: a WordPress theme's shared code).
  const defs = new Map();
  for (const f of files) {
    const php = f.endsWith(".php");
    if ((!php && !/\.(m?[jt]sx?|cjs)$/.test(f)) || isGenerated(f)) continue;
    let src = "";
    try { src = readFileSync(join(root, f), "utf8"); } catch { continue; }
    const names = php ? [...src.matchAll(/^function\s+&?\s*([A-Za-z_]\w*)\s*\(/gm)].map((m) => m[1]) : jsExports(src);
    for (const n of names) (defs.get(n) ?? defs.set(n, new Set()).get(n)).add(f);
  }
  const flags = [];
  for (const s of sessions) for (const t of s.members.flatMap((m) => ticks(m.text))) {
    const id = t.match(/^([A-Za-z_$][\w$]*)\s*(?:\(.*\))?$/)?.[1];
    for (const f of defs.get(id) ?? []) {
      const o = sessions.find((x) => x !== s && x.owns.includes(f));
      if (o && !s.uses.includes(f) && !flags.some((x) => x.session === s.name && x.name === id)) flags.push({ session: s.name, name: id, file: f, owner: o.name });
    }
  }

  for (const s of sessions) {
    const tests = s.owns.filter((p) => /\.test\.[A-Za-z]+$/.test(p));
    s.check = nodeTest && tests.length ? `node --test ${tests.join(" ")}` : "";
  }
  const text = [
    test ? `test: ${test}` : "",
    ...regen.map((r) => `regen: ${r.paths.join(", ")} via ${r.cmd}`),
    "",
    ...sessions.map((s) => [`## ${s.name}`, `owns: ${s.owns.join(", ")}`, `task: ${s.task}`, s.check ? `check: ${s.check}` : "",
      s.exposes.length ? `exposes: ${s.exposes.join(", ")}` : "", s.uses.length ? `uses: ${s.uses.join(", ")}` : "", ""].filter((l, i, a) => l || i === a.length - 1).join("\n")),
  ].filter((l, i) => l || i > 0).join("\n");
  // Each session's brief gets its own sections in full, after the goal's opening text.
  const specs = Object.fromEntries(sessions.map((s) => [s.name, [preamble, ...s.members.map((m) => `## ${m.heading}\n${m.text}`)].filter(Boolean).join("\n\n")]));
  return { text, specs, contracts: sessions.some((s) => s.exposes.length), flags };
}
