/**
 * Wave 的结构化定义。
 *
 * 取代从 `tasks.md` Markdown 表格解析 wave 与验证命令：
 * - 命令以 argv 数组表达，执行时不经 shell，消除注入面。
 * - Markdown 退化为渲染视图；结构化 JSON 是真相源。
 */

export interface StructuredCommand {
  /** 可执行文件名。不经 shell，故不支持管道/重定向/变量展开。 */
  command: string;
  args: string[];
}

export interface StructuredWave {
  id: string;
  title: string;
  scope: string;
  writeSet: string[];
  redTests: StructuredCommand[];
  greenGates: StructuredCommand[];
  contractRows: string[];
  stopCondition: string;
  status: string;
}

/** shell 元字符：出现在 argv 元素里通常意味着调用方误以为能用 shell 语法。 */
const SHELL_METACHARACTERS = /[;&|`$><\n\r(){}[\]!*?~#]/;

export class InvalidCommandError extends Error {
  readonly field: string;
  readonly value: string;

  constructor(field: string, value: string, message: string) {
    super(message);
    this.name = 'InvalidCommandError';
    this.field = field;
    this.value = value;
  }
}

function assertNoShellSyntax(field: string, value: string): void {
  const match = value.match(SHELL_METACHARACTERS);
  if (match) {
    throw new InvalidCommandError(
      field,
      value,
      `命令片段包含 shell 元字符 ${JSON.stringify(match[0])}：${JSON.stringify(value)}。` +
        '命令以 argv 数组直接执行，不经 shell，因此不支持管道、重定向、变量展开或命令串联。' +
        '如需组合多步，请拆成多条命令。',
    );
  }
}

/**
 * 规范化并校验一条结构化命令。
 *
 * 同时接受两种输入形态：
 * - `{ command, args }` —— 推荐形态
 * - `["cmd", "arg1", ...]` —— argv 数组简写
 *
 * 明确拒绝裸字符串：那正是需要 shell 切分的旧形态。
 */
export function normalizeCommand(input: unknown, field: string): StructuredCommand {
  if (typeof input === 'string') {
    throw new InvalidCommandError(
      field,
      input,
      `命令必须是 argv 数组或 { command, args } 对象，不能是字符串：${JSON.stringify(input)}。` +
        '字符串形态需要 shell 切分，已不再支持。',
    );
  }

  if (Array.isArray(input)) {
    const parts = input.filter(
      (item): item is string => typeof item === 'string' && item.length > 0,
    );
    if (parts.length === 0) {
      throw new InvalidCommandError(field, JSON.stringify(input), '命令数组为空');
    }
    const [command, ...args] = parts;
    for (const part of parts) assertNoShellSyntax(field, part);
    return { command: command!, args };
  }

  if (input && typeof input === 'object') {
    const record = input as Record<string, unknown>;
    const command = record.command;
    if (typeof command !== 'string' || command.length === 0) {
      throw new InvalidCommandError(field, JSON.stringify(input), '命令缺少 command 字段');
    }
    const args = Array.isArray(record.args)
      ? record.args.filter((item): item is string => typeof item === 'string')
      : [];
    assertNoShellSyntax(field, command);
    for (const arg of args) assertNoShellSyntax(field, arg);
    return { command, args };
  }

  throw new InvalidCommandError(field, String(input), '命令格式无法识别');
}

export function normalizeCommands(input: unknown, field: string): StructuredCommand[] {
  if (input == null) return [];
  if (!Array.isArray(input)) {
    throw new InvalidCommandError(field, String(input), `${field} 必须是数组`);
  }
  return input.map((entry, index) => normalizeCommand(entry, `${field}[${index}]`));
}

/** 用于展示与事件记录的可读形式。仅作显示，不用于执行。 */
export function formatCommand(command: StructuredCommand): string {
  return [command.command, ...command.args].join(' ');
}
