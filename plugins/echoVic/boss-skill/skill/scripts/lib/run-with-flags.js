#!/usr/bin/env node
import childProcess from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

import { isHookEnabled } from './hook-flags.js';

const MAX_STDIN = 1024 * 1024;
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function exitCleanly() {
  process.exit(0);
}

function resolvePluginRoot() {
  // 本文件位于 <skill>/scripts/lib/ 内：自定位即 skill 根，安装位置变化无需改代码。
  // 不读取 CLAUDE_PROJECT_DIR / CLAUDE_PLUGIN_ROOT——前者是宿主项目目录，会把脚本相对
  // 路径解析到项目里；后者在复制安装场景下并不存在。SKILL_DIR 保留为显式覆盖。
  return process.env.SKILL_DIR || path.resolve(__dirname, '..', '..');
}

function readStdin() {
  const chunks = [];
  let total = 0;

  try {
    const buf = Buffer.alloc(4096);
    while (true) {
      const bytesRead = fs.readSync(0, buf, 0, buf.length, null);
      if (bytesRead <= 0) {
        break;
      }

      const remaining = MAX_STDIN - total;
      if (remaining <= 0) {
        break;
      }

      if (bytesRead > remaining) {
        chunks.push(Buffer.from(buf.subarray(0, remaining)));
        total += remaining;
        break;
      }

      chunks.push(Buffer.from(buf.subarray(0, bytesRead)));
      total += bytesRead;
    }
  } catch (_e) {
    process.stderr.write('[boss-skill] run-with-flags/readStdin: ' + _e.message + '\n');
  }

  return Buffer.concat(chunks, total);
}

function writeStructuredResult(result, _stdinBuf) {
  if (result && typeof result === 'object' && !Buffer.isBuffer(result)) {
    if (result.stderr) {
      process.stderr.write(String(result.stderr));
    }
    if (result.stdout) {
      process.stdout.write(String(result.stdout));
    }
    process.exit(typeof result.exitCode === 'number' ? result.exitCode : 0);
  }

  if (typeof result === 'string') {
    process.stdout.write(result);
    process.exit(0);
  }

  exitCleanly();
}

async function runModule(scriptAbs, stdinStr, stdinBuf) {
  const mod = await import(pathToFileURL(scriptAbs).href);
  const runner = mod.run || mod.default?.run;
  if (typeof runner === 'function') {
    const result = await runner(stdinStr);
    writeStructuredResult(result, stdinBuf);
  }
}

async function main() {
  const hookId = process.argv[2];
  const scriptRel = process.argv[3];
  const profilesCsv = process.argv[4] || '';

  if (!hookId || !scriptRel) {
    process.stderr.write('Usage: run-with-flags.js <hookId> <scriptRelativePath> [profilesCsv]\n');
    process.exit(1);
  }

  const stdinBuf = readStdin();

  if (!isHookEnabled(hookId, { profiles: profilesCsv })) {
    exitCleanly();
  }

  const pluginRoot = resolvePluginRoot();
  const scriptAbs = path.resolve(pluginRoot, scriptRel);

  const relative = path.relative(pluginRoot, scriptAbs);
  if (relative.startsWith('..') || path.isAbsolute(relative)) {
    process.stderr.write('Path traversal blocked: ' + scriptRel + '\n');
    exitCleanly();
  }

  const stdinStr = stdinBuf.toString('utf8');

  try {
    await runModule(scriptAbs, stdinStr, stdinBuf);
  } catch (_importErr) {
    process.stderr.write('[boss-skill] run-with-flags/import: ' + _importErr.message + '\n');
  }

  try {
    const child = childProcess.spawnSync(process.execPath, [scriptAbs], {
      input: stdinBuf,
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: 30000,
      maxBuffer: MAX_STDIN,
    });

    if (child.stderr && child.stderr.length) {
      process.stderr.write(child.stderr);
    }

    if (child.stdout && child.stdout.length) {
      process.stdout.write(child.stdout);
    } else {
      exitCleanly();
    }

    process.exit(child.status || 0);
  } catch (_spawnErr) {
    process.stderr.write('[boss-skill] run-with-flags/spawn: ' + _spawnErr.message + '\n');
    exitCleanly();
  }
}

await main();
