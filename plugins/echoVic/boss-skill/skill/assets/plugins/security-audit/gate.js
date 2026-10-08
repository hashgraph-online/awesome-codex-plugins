#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const checks = [];
let passed = true;

function addCheck(name, ok, detail) {
  checks.push(detail ? { name, passed: ok, detail } : { name, passed: ok });
  passed &&= ok;
}

function walk(dir, visitor) {
  if (!fs.existsSync(dir)) return;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === '.git' || entry.name === 'node_modules') continue;
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(fullPath, visitor);
    } else {
      visitor(fullPath);
    }
  }
}

function containsAny(patterns, extensions) {
  let count = 0;
  for (const pattern of patterns) {
    let found = false;
    walk(process.cwd(), (file) => {
      if (found || !extensions.some((ext) => file.endsWith(ext))) return;
      try {
        found = pattern.test(fs.readFileSync(file, 'utf8'));
      } catch {
        found = false;
      }
    });
    if (found) count += 1;
  }
  return count;
}

const secretHits = containsAny(
  [
    /AKIA[0-9A-Z]{16}/,
    /(api[_-]?key|apikey|secret[_-]?key|access[_-]?token)\s*[:=]\s*['"][a-zA-Z0-9/+]{20,}/i,
    /-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----/,
    /ghp_[a-zA-Z0-9]{36}/,
    /sk-[a-zA-Z0-9]{48}/,
  ],
  ['.ts', '.js', '.py', '.go', '.json', '.env', '.yaml', '.yml'],
);
addCheck(
  'secrets-scan',
  secretHits === 0,
  secretHits > 0 ? `发现 ${secretHits} 类敏感信息模式` : undefined,
);

if (fs.existsSync('package.json')) {
  const audit = spawnSync(process.platform === 'win32' ? 'npm.cmd' : 'npm', ['audit', '--json'], {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'ignore'],
  });
  let severe = 0;
  try {
    const parsed = JSON.parse(audit.stdout || '{}');
    severe =
      Number(parsed.metadata?.vulnerabilities?.high ?? 0) +
      Number(parsed.metadata?.vulnerabilities?.critical ?? 0);
  } catch {
    severe = 0;
  }
  addCheck(
    'dependency-vulnerabilities',
    severe === 0,
    severe > 0 ? `${severe} 个高危漏洞` : undefined,
  );
} else {
  addCheck('dependency-vulnerabilities', true, '跳过：无 package.json');
}

const unsafeHits = containsAny(
  [/eval\(/, /dangerouslySetInnerHTML/, /innerHTML\s*=/],
  ['.js', '.ts', '.jsx', '.tsx'],
);
addCheck(
  'unsafe-patterns',
  unsafeHits === 0,
  unsafeHits > 0 ? `发现 ${unsafeHits} 类不安全模式` : undefined,
);

process.stdout.write(`${JSON.stringify(checks)}\n`);
process.exit(passed ? 0 : 1);
