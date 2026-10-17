#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const checks = [];
let allPassed = true;

function addCheck(name, ok, detail) {
  checks.push(detail ? { name, passed: ok, detail } : { name, passed: ok });
  allPassed &&= ok;
}

function walk(dir, visitor, excludes = []) {
  if (!fs.existsSync(dir)) return;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (excludes.includes(entry.name)) continue;
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(fullPath, visitor, excludes);
    } else {
      visitor(fullPath);
    }
  }
}

function scanFiles(patterns, extensions, excludes) {
  const hits = [];
  walk(
    process.cwd(),
    (file) => {
      if (!extensions.some((ext) => file.endsWith(ext))) return;
      let content;
      try {
        content = fs.readFileSync(file, 'utf8');
      } catch {
        return;
      }
      const lines = content.split('\n');
      for (let i = 0; i < lines.length; i++) {
        for (const { pattern, id } of patterns) {
          if (pattern.test(lines[i])) {
            hits.push({ file: path.relative(process.cwd(), file), line: i + 1, rule: id });
          }
        }
      }
    },
    excludes,
  );
  return hits;
}

const excludes = [
  'node_modules',
  '.git',
  'dist',
  'build',
  '.boss',
  '__tests__',
  'test',
  'tests',
  '*.test.*',
  '*.spec.*',
];

// A01: Injection (SQL, Command, NoSQL)
const injectionPatterns = [
  {
    pattern: /`\s*(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\b[^`]*\$\{/i,
    id: 'sql-template-injection',
  },
  { pattern: /(?:query|execute|raw)\s*\(\s*['"`][^'"`]*\s*\+\s*/i, id: 'sql-concat' },
  { pattern: /exec\(\s*(?:`[^`]*\$\{|['"][^'"]*\s*\+\s*)/i, id: 'command-injection' },
  {
    pattern: /child_process.*exec\(\s*(?:`[^`]*\$\{|[^,]*\+\s*(?:req|input|param|arg|user))/i,
    id: 'command-injection-req',
  },
  { pattern: /\$where\s*:\s*['"`].*\+/i, id: 'nosql-injection' },
];
const injectionHits = scanFiles(
  injectionPatterns,
  ['.ts', '.js', '.tsx', '.jsx', '.py', '.go'],
  excludes,
);
addCheck(
  'owasp-a01-injection',
  injectionHits.length === 0,
  injectionHits.length > 0
    ? `${injectionHits.length} 处注入风险: ${injectionHits
        .slice(0, 3)
        .map((h) => `${h.file}:${h.line}(${h.rule})`)
        .join(', ')}`
    : undefined,
);

// A02: Broken Authentication
const authPatterns = [
  {
    pattern: /(?:jwt|token).*(?:secret|key)\s*[:=]\s*['"][^'"]{3,}['"]/i,
    id: 'hardcoded-jwt-secret',
  },
  { pattern: /httpOnly\s*:\s*false/i, id: 'cookie-no-httponly' },
  { pattern: /secure\s*:\s*false/i, id: 'cookie-no-secure' },
  { pattern: /sameSite\s*:\s*['"]none['"]/i, id: 'cookie-samesite-none' },
  { pattern: /bcrypt.*(?:rounds?|salt)\s*[:=]\s*(?:[1-7])\b/i, id: 'weak-bcrypt-rounds' },
];
const authHits = scanFiles(authPatterns, ['.ts', '.js', '.tsx', '.jsx'], excludes);
addCheck(
  'owasp-a02-broken-auth',
  authHits.length === 0,
  authHits.length > 0
    ? `${authHits.length} 处认证风险: ${authHits
        .slice(0, 3)
        .map((h) => `${h.file}:${h.line}(${h.rule})`)
        .join(', ')}`
    : undefined,
);

// A03: Sensitive Data Exposure
const sensitivePatterns = [
  { pattern: /(?:password|passwd|pwd)\s*[:=]\s*['"][^'"]+['"]/i, id: 'hardcoded-password' },
  {
    pattern: /localStorage\.setItem\(\s*['"](?:token|auth|session|jwt|password)/i,
    id: 'sensitive-localstorage',
  },
  {
    pattern: /console\.log\(.*(?:password|token|secret|key|credential)/i,
    id: 'log-sensitive-data',
  },
];
const sensitiveHits = scanFiles(sensitivePatterns, ['.ts', '.js', '.tsx', '.jsx', '.py'], excludes);
addCheck(
  'owasp-a03-sensitive-data',
  sensitiveHits.length === 0,
  sensitiveHits.length > 0
    ? `${sensitiveHits.length} 处敏感数据暴露: ${sensitiveHits
        .slice(0, 3)
        .map((h) => `${h.file}:${h.line}(${h.rule})`)
        .join(', ')}`
    : undefined,
);

// A05: Broken Access Control
const accessPatterns = [
  { pattern: /cors\(\s*\{[^}]*origin\s*:\s*(?:true|['"][*]['"])/i, id: 'cors-wildcard' },
  { pattern: /Access-Control-Allow-Origin['"]\s*[:=,]\s*['"][*]['"]/i, id: 'cors-header-wildcard' },
  { pattern: /\.\.\/.*req\.(params|query|body)/i, id: 'path-traversal' },
];
const accessHits = scanFiles(
  accessPatterns,
  ['.ts', '.js', '.tsx', '.jsx', '.py', '.go'],
  excludes,
);
addCheck(
  'owasp-a05-broken-access',
  accessHits.length === 0,
  accessHits.length > 0
    ? `${accessHits.length} 处访问控制风险: ${accessHits
        .slice(0, 3)
        .map((h) => `${h.file}:${h.line}(${h.rule})`)
        .join(', ')}`
    : undefined,
);

// A06: Security Misconfiguration
const misconfigPatterns = [
  { pattern: /debug\s*[:=]\s*(?:true|1|['"]true['"])/i, id: 'debug-enabled' },
  { pattern: /NODE_ENV.*(?:!==?|!=)\s*['"]production['"]/i, id: 'env-check-inverted' },
  { pattern: /helmet\s*\(\s*\{[^}]*contentSecurityPolicy\s*:\s*false/i, id: 'csp-disabled' },
  { pattern: /x-powered-by/i, id: 'x-powered-by-exposed' },
];
const misconfigHits = scanFiles(
  misconfigPatterns,
  ['.ts', '.js', '.json', '.yaml', '.yml'],
  excludes,
);
addCheck(
  'owasp-a06-misconfig',
  misconfigHits.length === 0,
  misconfigHits.length > 0
    ? `${misconfigHits.length} 处配置风险: ${misconfigHits
        .slice(0, 3)
        .map((h) => `${h.file}:${h.line}(${h.rule})`)
        .join(', ')}`
    : undefined,
);

// A07: XSS (Cross-Site Scripting)
const xssPatterns = [
  { pattern: /innerHTML\s*=\s*(?!['"]<)/, id: 'innerHTML-assignment' },
  {
    pattern: /dangerouslySetInnerHTML\s*=\s*\{\s*\{\s*__html\s*:\s*(?!['"])/i,
    id: 'react-dangerous-html',
  },
  { pattern: /document\.write\s*\(/, id: 'document-write' },
  { pattern: /\$\(\s*['"`].*\)\.html\s*\(\s*(?!['"])/i, id: 'jquery-html-injection' },
  { pattern: /v-html\s*=\s*["'](?!['"])/i, id: 'vue-v-html' },
];
const xssHits = scanFiles(xssPatterns, ['.ts', '.js', '.tsx', '.jsx', '.vue', '.html'], excludes);
addCheck(
  'owasp-a07-xss',
  xssHits.length === 0,
  xssHits.length > 0
    ? `${xssHits.length} 处 XSS 风险: ${xssHits
        .slice(0, 3)
        .map((h) => `${h.file}:${h.line}(${h.rule})`)
        .join(', ')}`
    : undefined,
);

// A08: Insecure Deserialization
const deserPatterns = [
  {
    pattern: /JSON\.parse\(\s*(?:req\.body|request\.body|ctx\.request\.body)/,
    id: 'unvalidated-json-parse',
  },
  { pattern: /pickle\.loads?\s*\(/i, id: 'python-pickle' },
  { pattern: /yaml\.load\(\s*[^,)]+\s*\)(?!\s*,\s*Loader)/i, id: 'yaml-unsafe-load' },
  { pattern: /unserialize\s*\(\s*\$_(GET|POST|REQUEST|COOKIE)/i, id: 'php-unserialize' },
];
const deserHits = scanFiles(deserPatterns, ['.ts', '.js', '.py', '.php', '.go'], excludes);
addCheck(
  'owasp-a08-insecure-deserialization',
  deserHits.length === 0,
  deserHits.length > 0
    ? `${deserHits.length} 处反序列化风险: ${deserHits
        .slice(0, 3)
        .map((h) => `${h.file}:${h.line}(${h.rule})`)
        .join(', ')}`
    : undefined,
);

// A09: Insecure Cryptography
const cryptoPatterns = [
  { pattern: /createHash\(\s*['"](?:md5|sha1)['"]\s*\)/i, id: 'weak-hash-algorithm' },
  { pattern: /createCipher\(\s*['"](?:des|rc4|aes-128-ecb)['"]/i, id: 'weak-cipher' },
  {
    pattern: /Math\.random\(\).*(?:token|secret|key|password|id|session)/i,
    id: 'math-random-security',
  },
  { pattern: /crypto.*randomBytes\(\s*(?:[1-9]|1[0-5])\s*\)/i, id: 'insufficient-entropy' },
];
const cryptoHits = scanFiles(cryptoPatterns, ['.ts', '.js', '.py', '.go'], excludes);
addCheck(
  'owasp-a09-insecure-crypto',
  cryptoHits.length === 0,
  cryptoHits.length > 0
    ? `${cryptoHits.length} 处加密风险: ${cryptoHits
        .slice(0, 3)
        .map((h) => `${h.file}:${h.line}(${h.rule})`)
        .join(', ')}`
    : undefined,
);

// A10: Insufficient Logging & Monitoring
const loggingPatterns = [
  { pattern: /catch\s*\([^)]*\)\s*\{\s*\}/, id: 'empty-catch' },
  { pattern: /catch\s*\([^)]*\)\s*\{\s*\/\//i, id: 'catch-only-comment' },
  { pattern: /\.catch\(\s*\(\s*\)\s*=>\s*\{\s*\}\s*\)/, id: 'empty-promise-catch' },
];
const loggingHits = scanFiles(loggingPatterns, ['.ts', '.js', '.tsx', '.jsx'], excludes);
addCheck(
  'owasp-a10-insufficient-logging',
  loggingHits.length === 0,
  loggingHits.length > 0
    ? `${loggingHits.length} 处日志不足: ${loggingHits
        .slice(0, 3)
        .map((h) => `${h.file}:${h.line}(${h.rule})`)
        .join(', ')}`
    : undefined,
);

process.stdout.write(`${JSON.stringify(checks)}\n`);
process.exit(allPassed ? 0 : 1);
