// Recording and replaying runners. A recording runner wraps a live runner
// and saves each run's request and result as JSON. A replay runner serves
// saved results by run name, so the whole command runs without Java.
//
// The chart mark tag is random per run; recordings store it as TAG_PLACEHOLDER
// and replay substitutes the tag the pipeline uses.

import fs from 'node:fs';
import path from 'node:path';

export const TAG_PLACEHOLDER = '00000000000000000000000000000000';

function runName(req, counter) {
  if (req.kind === 'sany') return 'sany';
  return req.name ?? `run-${counter}`;
}

// Keep only the XML entries the command reads (module nodes, variable
// declarations, and user definitions, without their bodies), so recordings
// of SANY output stay small.
export function trimSanyXml(xml) {
  const root = /<RootModule>.*?<\/RootModule>/.exec(xml)?.[0] ?? '';
  const keep = [];
  for (const chunk of xml.split('<entry>').slice(1)) {
    const m = /^<UID>\d+<\/UID><(OpDeclNode|UserDefinedOpKind|ModuleNode)>/.exec(chunk);
    if (!m) continue;
    let e = chunk.slice(0, chunk.lastIndexOf('</entry>'));
    if (m[1] === 'UserDefinedOpKind') e = e.replace(/<body>[\s\S]*$/, '</UserDefinedOpKind>').replace(/<params>[\s\S]*?<\/params>/, '');
    keep.push(`<entry>${e}</entry>`);
  }
  return `<?xml version="1.0" encoding="UTF-8"?><modules>${root}<context>${keep.join('')}</context></modules>`;
}

export function recordingRunner(inner, dir, tag) {
  fs.mkdirSync(dir, { recursive: true });
  let n = 0;
  return async (req) => {
    const res = await inner(req);
    const name = runName(req, ++n);
    const swap = (s) => (s && tag ? s.split(tag).join(TAG_PLACEHOLDER) : s);
    const saved = {
      request: { kind: req.kind, cfgText: swap(req.cfgText ?? null), wrapper: req.wrapper ? { name: req.wrapper.name, text: swap(req.wrapper.text) } : null },
      exit: res.exit, stdout: req.kind === 'sany' && res.exit === 0 ? trimSanyXml(res.stdout) : swap(res.stdout), stderr: res.stderr, dot: res.dot ?? null,
    };
    fs.writeFileSync(path.join(dir, `${name}.json`), `${JSON.stringify(saved, null, 1)}\n`);
    return res;
  };
}

export function replayRunner(dir, tag = TAG_PLACEHOLDER, log = null) {
  return async (req) => {
    const name = runName(req, 0);
    const file = path.join(dir, `${name}.json`);
    if (!fs.existsSync(file)) throw new Error(`No recorded TLC output for run ${name} in ${dir}.`);
    const saved = JSON.parse(fs.readFileSync(file, 'utf8'));
    log?.push({ name, req });
    if (saved.spawnError) {
      const { ToolchainError } = await import('./toolchain.mjs');
      throw new ToolchainError(saved.spawnError);
    }
    const unswap = (s) => (s ? s.split(TAG_PLACEHOLDER).join(tag) : s);
    return { exit: saved.exit, stdout: unswap(saved.stdout), stderr: saved.stderr, dot: saved.dot };
  };
}
