// Finds Java and tla2tools.jar, fetching the pinned jar into a cache folder
// (through release.mjs) when TLA2TOOLS is not set, and runs TLC or SANY with
// output streamed to files.

import { spawn, spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { TLA2TOOLS_VERSION, TLA2TOOLS_SHA256, INSTALL_HINT, downloadJar } from './release.mjs';

export { TLA2TOOLS_VERSION, TLA2TOOLS_SHA256 };

export class ToolchainError extends Error {}

export function cacheDir(env = process.env) {
  if (env.STATECHART_CACHE) return env.STATECHART_CACHE;
  const base = env.XDG_CACHE_HOME || path.join(os.homedir(), '.cache');
  return path.join(base, 'endostack', 'statechart');
}

function sha256File(file) {
  return createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}

export function javaMajor(javaBin, env = process.env) {
  const r = spawnSync(javaBin, ['-version'], { encoding: 'utf8', env: javaEnv(env) });
  if (r.error || r.status !== 0) return null;
  const m = /version "(\d+)(?:\.(\d+))?/.exec(`${r.stderr}${r.stdout}`);
  if (!m) return null;
  const major = Number(m[1]);
  return major === 1 ? Number(m[2]) : major;
}

// Returns { java, jar }. Throws ToolchainError with install guidance.
export async function resolveToolchain(env = process.env) {
  const java = env.JAVA || 'java';
  const major = javaMajor(java, env);
  if (major === null) {
    throw new ToolchainError(`Cannot run Java (${java}). TLC needs Java 11 or later.\n${INSTALL_HINT}`);
  }
  if (major < 11) throw new ToolchainError(`${java} is Java ${major}; TLC needs Java 11 or later.\n${INSTALL_HINT}`);
  if (env.TLA2TOOLS) {
    if (!fs.existsSync(env.TLA2TOOLS)) throw new ToolchainError(`TLA2TOOLS points at ${env.TLA2TOOLS}, which does not exist.`);
    return { java, jar: env.TLA2TOOLS };
  }
  const dir = cacheDir(env);
  const jar = path.join(dir, `tla2tools-${TLA2TOOLS_VERSION}.jar`);
  if (fs.existsSync(jar) && sha256File(jar) === TLA2TOOLS_SHA256) return { java, jar };
  if (env.STATECHART_NO_DOWNLOAD) {
    throw new ToolchainError(`TLA2TOOLS is not set and downloads are disabled (STATECHART_NO_DOWNLOAD).\n${INSTALL_HINT}`);
  }
  let tmp;
  try {
    fs.mkdirSync(dir, { recursive: true });
    process.stderr.write(`Downloading tla2tools ${TLA2TOOLS_VERSION} into ${dir}\n`);
    tmp = await downloadJar(jar);
    const sum = sha256File(tmp);
    if (sum !== TLA2TOOLS_SHA256) throw new Error(`checksum mismatch: got ${sum}, expected ${TLA2TOOLS_SHA256}`);
    fs.renameSync(tmp, jar);
    return { java, jar };
  } catch (e) {
    if (tmp) fs.rmSync(tmp, { force: true });
    throw new ToolchainError(`Could not download tla2tools.jar: ${e.message}\n${INSTALL_HINT}`);
  }
}

// Java gets only the variables it needs to start, never the caller's whole
// environment, so tokens and keys in the shell never reach the model checker.
const JAVA_ENV_KEYS = ['PATH', 'HOME', 'USERPROFILE', 'JAVA_HOME', 'SystemRoot', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'LANG', 'LC_ALL', 'LC_CTYPE'];

export function javaEnv(base = process.env) {
  const env = {};
  for (const name of JAVA_ENV_KEYS) if (base[name] !== undefined) env[name] = base[name];
  return env;
}

function runEnv(base, tmpDir) {
  const env = { ...javaEnv(base), TMPDIR: tmpDir };
  if (process.platform !== 'darwin') env.LC_ALL = 'C.UTF-8';
  return env;
}

// Spawn Java with stdout and stderr streamed into files. Resolves to
// { exit, signal, stdoutFile, stderrFile } or rejects when Java cannot start.
export function runJava({ java, jar, args, cwd, outPrefix, env = process.env, onSpawn }) {
  const stdoutFile = `${outPrefix}.out`;
  const stderrFile = `${outPrefix}.err`;
  const out = fs.openSync(stdoutFile, 'w');
  const err = fs.openSync(stderrFile, 'w');
  const tmpDir = `${outPrefix}.tmp`;
  fs.mkdirSync(tmpDir, { recursive: true });
  const fullArgs = ['-XX:+UseParallelGC', `-Djava.io.tmpdir=${tmpDir}`, ...args.jvm ?? [], '-cp', jar, ...args.main];
  return new Promise((resolve, reject) => {
    let settled = false;
    const finish = (fn, v) => {
      if (settled) return;
      settled = true;
      fs.closeSync(out);
      fs.closeSync(err);
      fn(v);
    };
    let child;
    try {
      child = spawn(java, fullArgs, { cwd, stdio: ['ignore', out, err], env: runEnv(env, tmpDir) });
    } catch (e) {
      finish(reject, new ToolchainError(`Java could not start (${java}): ${e.message}`));
      return;
    }
    onSpawn?.(child);
    child.on('error', (e) => finish(reject, new ToolchainError(`Java could not start (${java}): ${e.message}`)));
    child.on('exit', (code, signal) => {
      // Some runtimes report a failed spawn only through exit code 127 / ENOENT.
      if (code === null && signal === null) { finish(reject, new ToolchainError(`Java could not start (${java}).`)); return; }
      finish(resolve, { exit: code ?? 128, signal, stdoutFile, stderrFile });
    });
  });
}

// A runner turns a run request into { exit, stdout, stderr, dot }.
// Requests: { name, kind:'sany', spec } or
//           { name, kind:'tlc', spec, cfgText, specDir, dump:boolean, tag }.
export function liveRunner({ java, jar, workDir, env = process.env }) {
  let n = 0;
  return async function run(req) {
    const dir = path.join(workDir, `${String(++n).padStart(2, '0')}-${req.name}`);
    fs.mkdirSync(dir, { recursive: true });
    if (req.kind === 'sany') {
      const res = await runJava({
        java, jar, cwd: dir, outPrefix: path.join(dir, 'sany'), env,
        args: { main: ['tla2sany.xml.XMLExporter', '-o', '-I', path.dirname(req.spec), req.spec] },
      });
      return { exit: res.exit, stdout: fs.readFileSync(res.stdoutFile, 'utf8'), stderr: fs.readFileSync(res.stderrFile, 'utf8') };
    }
    let spec = req.spec;
    if (req.wrapper) {
      spec = path.join(dir, `${req.wrapper.name}.tla`);
      fs.writeFileSync(spec, req.wrapper.text);
    }
    const cfg = path.join(dir, 'run.cfg');
    fs.writeFileSync(cfg, `${req.cfgText}\n`);
    const dot = path.join(dir, 'graph.dot');
    // TLC 1.7.4 resolves -config against the checked module's folder, so pass
    // the config path relative to that folder.
    const cfgArg = path.relative(path.dirname(spec), cfg);
    const main = ['tlc2.TLC', '-tool', '-workers', '1', '-fp', '0', '-lncheck', 'final', '-metadir', path.join(dir, 'meta'), '-config', cfgArg];
    if (req.dump) main.push('-dump', 'dot,actionlabels', dot);
    main.push(spec);
    const res = await runJava({
      java, jar, cwd: dir, outPrefix: path.join(dir, 'tlc'), env,
      args: { jvm: [`-DTLA-Library=${req.specDir}`], main },
    });
    return {
      exit: res.exit,
      stdout: fs.readFileSync(res.stdoutFile, 'utf8'),
      stderr: fs.readFileSync(res.stderrFile, 'utf8'),
      dot: req.dump && fs.existsSync(dot) ? fs.readFileSync(dot, 'utf8') : null,
      cfgText: req.cfgText,
    };
  };
}
