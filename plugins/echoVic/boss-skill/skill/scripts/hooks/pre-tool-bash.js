import { normalizeHookInput } from './lib/normalize-input.js';

const DANGEROUS_PATTERNS = [
  {
    pattern: /\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b/,
    reason: 'rm -rf 可能造成不可恢复的数据丢失',
  },
  { pattern: /\bgit\s+push\s+.*(-f|--force)\b/, reason: 'git push --force 可能覆盖远程历史' },
  { pattern: /\bgit\s+reset\s+--hard\b/, reason: 'git reset --hard 会丢弃未提交的更改' },
  { pattern: /\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX)\b/i, reason: 'DROP 操作会删除数据库对象' },
  { pattern: /\bTRUNCATE\s+TABLE\b/i, reason: 'TRUNCATE TABLE 会清空表数据' },
  { pattern: /\bchmod\s+777\b/, reason: 'chmod 777 设置了过于宽泛的权限' },
  { pattern: /\bmkfs\b/, reason: 'mkfs 会格式化磁盘' },
  { pattern: /\bdd\s+.*of=\/dev\//, reason: 'dd 写入设备文件可能造成数据丢失' },
];

function run(rawInput) {
  const input = normalizeHookInput(rawInput);
  if (!input) return '';
  const command = input.command;

  if (!command) return '';

  for (const { pattern, reason } of DANGEROUS_PATTERNS) {
    if (pattern.test(command)) {
      return JSON.stringify({
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          permissionDecision: 'deny',
          permissionDecisionReason: '[boss-skill] 危险命令已拦截: ' + reason,
        },
      });
    }
  }

  return '';
}

export { run };
