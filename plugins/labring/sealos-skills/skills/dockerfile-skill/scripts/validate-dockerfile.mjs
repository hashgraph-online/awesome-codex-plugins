#!/usr/bin/env node

/**
 * Dockerfile Validation Script
 *
 * Checks generated Dockerfile for common issues before build.
 * Exit code 0 = valid, exit code 1 = has errors.
 *
 * Usage: node validate-dockerfile.mjs <dockerfile-path> [--port=3000] [--json]
 */

import fs from 'fs';
import path from 'path';

function validate(dockerfilePath, opts = {}) {
  const content = fs.readFileSync(dockerfilePath, 'utf-8');
  const lines = content.split('\n');
  const issues = [];

  // 1. No :latest tags
  for (let i = 0; i < lines.length; i++) {
    if (/^FROM\s+\S+:latest/i.test(lines[i])) {
      issues.push({ severity: 'error', line: i + 1, rule: 'no-latest', msg: `Using :latest tag: ${lines[i].trim()}` });
    }
  }

  // 2. Has non-root USER
  if (!/^USER\s+(?!root)/m.test(content)) {
    issues.push({ severity: 'warn', rule: 'non-root-user', msg: 'No non-root USER instruction found' });
  }

  // 3. Multi-stage build (when build step likely needed)
  const fromCount = (content.match(/^FROM\s/gm) || []).length;
  if (fromCount < 2 && /RUN\s+.*\b(build|compile)\b/i.test(content)) {
    issues.push({ severity: 'warn', rule: 'multi-stage', msg: 'Single-stage build detected with build step — consider multi-stage' });
  }

  // 4. COPY . before dependency install (cache busting)
  const copyAllIdx = lines.findIndex(l => /^COPY\s+\.\s+\./.test(l));
  const installIdx = lines.findIndex(l => /npm ci|npm install|pnpm install|yarn install|pip install|go mod download/.test(l));
  if (copyAllIdx !== -1 && installIdx !== -1 && copyAllIdx < installIdx) {
    issues.push({ severity: 'error', rule: 'copy-before-install', msg: 'COPY . . before dependency install breaks Docker cache' });
  }

  // 5. EXPOSE matches expected port
  if (opts.port) {
    const exposeMatch = content.match(/^EXPOSE\s+(\d+)/m);
    if (exposeMatch && exposeMatch[1] !== String(opts.port)) {
      issues.push({ severity: 'warn', rule: 'port-mismatch', msg: `EXPOSE ${exposeMatch[1]} doesn't match expected port ${opts.port}` });
    }
    if (!exposeMatch) {
      issues.push({ severity: 'warn', rule: 'no-expose', msg: 'No EXPOSE instruction found' });
    }
  }

  // 6. -dev packages in runtime stage (after last FROM)
  const lastFromIdx = lines.reduce((acc, l, i) => /^FROM\s/.test(l) ? i : acc, 0);
  const runtimeSection = lines.slice(lastFromIdx).join('\n');
  const devPkgs = runtimeSection.match(/(lib\w+-dev|python3-dev|gcc|g\+\+|make|build-essential)/g);
  if (devPkgs && fromCount > 1) {
    issues.push({ severity: 'warn', rule: 'dev-in-runtime', msg: `Build-time packages in runtime stage: ${[...new Set(devPkgs)].join(', ')}` });
  }

  // 7. Has CMD or ENTRYPOINT
  if (!/^(CMD|ENTRYPOINT)\s/m.test(content)) {
    issues.push({ severity: 'error', rule: 'no-cmd', msg: 'No CMD or ENTRYPOINT instruction found' });
  }

  // 8. .dockerignore exists
  const dir = path.dirname(dockerfilePath);
  if (!fs.existsSync(path.join(dir, '.dockerignore'))) {
    issues.push({ severity: 'warn', rule: 'no-dockerignore', msg: 'No .dockerignore file found' });
  }

  const errors = issues.filter(i => i.severity === 'error');
  const warnings = issues.filter(i => i.severity === 'warn');

  return {
    valid: errors.length === 0,
    errors: errors.length,
    warnings: warnings.length,
    issues,
  };
}

// ─── CLI ────────────────────────────────────────────────────
const args = process.argv.slice(2);
const dockerfilePath = args.find(a => !a.startsWith('--'));
const portFlag = args.find(a => a.startsWith('--port='));
const jsonFlag = args.includes('--json');
const port = portFlag ? parseInt(portFlag.split('=')[1]) : null;

if (dockerfilePath) {
  const absPath = path.resolve(dockerfilePath);
  if (!fs.existsSync(absPath)) {
    console.error(`File not found: ${absPath}`);
    process.exit(1);
  }
  const result = validate(absPath, { port });
  if (jsonFlag) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    if (result.errors > 0) console.log(`✗ ${result.errors} error(s), ${result.warnings} warning(s)`);
    else if (result.warnings > 0) console.log(`⚠ ${result.warnings} warning(s), no errors`);
    else console.log('✓ Dockerfile validation passed');
    for (const i of result.issues) {
      const icon = i.severity === 'error' ? '✗' : '⚠';
      const loc = i.line ? `:${i.line}` : '';
      console.log(`  ${icon} [${i.rule}]${loc} ${i.msg}`);
    }
  }
  process.exit(result.valid ? 0 : 1);
}

export { validate };
