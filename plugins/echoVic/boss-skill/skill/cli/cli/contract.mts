import { readFileSync } from 'node:fs';
import { isAbsolute, relative, resolve } from 'node:path';
import { parseArgs } from 'node:util';

export type RiskTier = 'low' | 'medium' | 'high';
export type JsonObject = Record<string, unknown>;

export interface CliErrorData {
  code: string;
  message: string;
  input?: JsonObject;
  retryable: boolean;
  suggestion?: string;
}

export class CliUserError extends Error {
  readonly code: string;
  readonly input?: JsonObject;
  readonly retryable: boolean;
  readonly suggestion?: string;

  constructor(data: CliErrorData) {
    super(data.message);
    this.name = 'CliUserError';
    this.code = data.code;
    this.input = data.input;
    this.retryable = data.retryable;
    this.suggestion = data.suggestion;
  }
}

export interface CliContext {
  command: string;
  values: {
    json: boolean;
    yes: boolean;
    dryRun: boolean;
    describe: boolean;
    fields?: string;
    limit: string;
    jsonInput?: string;
  };
  positionals: string[];
  useJson: boolean;
  stdinIsTTY: boolean;
  stdoutIsTTY: boolean;
}

export interface CommandParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  required?: boolean;
  enum?: string[];
  default?: unknown;
}

export interface CommandOption extends CommandParameter {
  short?: string;
}

export interface CommandDescription {
  command: string;
  summary: string;
  parameters: CommandParameter[];
  options: CommandOption[];
  risk_tier: RiskTier;
}

export function createCliContext(
  argv: string[],
  {
    command,
    stdinIsTTY = Boolean(process.stdin.isTTY),
    stdoutIsTTY = Boolean(process.stdout.isTTY),
    validateOptionValues = true,
  }: {
    command: string;
    stdinIsTTY?: boolean;
    stdoutIsTTY?: boolean;
    validateOptionValues?: boolean;
  },
): CliContext {
  if (validateOptionValues) {
    validateCliContractOptionValues(argv);
  }

  const { values, positionals } = parseArgs({
    args: argv,
    allowPositionals: true,
    options: {
      json: { type: 'boolean', default: false },
      yes: { type: 'boolean', short: 'y', default: false },
      'dry-run': { type: 'boolean', default: false },
      fields: { type: 'string' },
      limit: { type: 'string', default: '100' },
      'json-input': { type: 'string' },
      describe: { type: 'boolean', default: false },
    },
    strict: false,
  });

  return {
    command,
    values: {
      json: Boolean(values.json),
      yes: Boolean(values.yes),
      dryRun: Boolean(values['dry-run']),
      describe: Boolean(values.describe),
      fields: typeof values.fields === 'string' ? values.fields : undefined,
      limit: typeof values.limit === 'string' ? values.limit : '100',
      jsonInput: typeof values['json-input'] === 'string' ? values['json-input'] : undefined,
    },
    positionals,
    useJson: Boolean(values.json) || !stdoutIsTTY,
    stdinIsTTY,
    stdoutIsTTY,
  };
}

export function parseLimit(limit: string): number {
  const parsed = Number(limit);
  if (!Number.isInteger(parsed) || parsed < 0 || parsed > 1000) {
    throw new CliUserError({
      code: 'invalid_limit',
      message: `Invalid --limit value: ${limit}`,
      input: { limit },
      retryable: false,
      suggestion: 'Use an integer between 0 and 1000',
    });
  }
  return parsed;
}

export function pickFields<T extends JsonObject>(obj: T, fields?: string): JsonObject {
  if (!fields) return obj;
  const keys = fields
    .split(',')
    .map((key) => key.trim())
    .filter(Boolean);
  return Object.fromEntries(keys.filter((key) => key in obj).map((key) => [key, obj[key]]));
}

export function outputList(items: JsonObject[], context: CliContext): JsonObject[] {
  return items
    .slice(0, parseLimit(context.values.limit))
    .map((item) => pickFields(item, context.values.fields));
}

function isLikelyOptionToken(value: string): boolean {
  return value.startsWith('--') || /^-[A-Za-z]$/.test(value);
}

function missingValueError(option: string): CliUserError {
  return new CliUserError({
    code: 'missing_option_value',
    message: `${option} requires a value`,
    input: { option },
    retryable: false,
    suggestion: `Pass a value after ${option}`,
  });
}

export function validateCliContractOptionValues(argv: string[]): void {
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    if (arg !== '--fields' && arg !== '--limit' && arg !== '--json-input') {
      continue;
    }

    const nextValue = argv[index + 1];
    if (
      nextValue === undefined ||
      (isLikelyOptionToken(nextValue) && !(arg === '--json-input' && nextValue === '-'))
    ) {
      throw missingValueError(arg);
    }

    index += 1;
  }
}

export function consumeCliContractOption(argv: string[], index: number): number | null {
  const arg = argv[index]!;
  if (
    arg === '--json' ||
    arg === '--describe' ||
    arg === '--dry-run' ||
    arg === '--yes' ||
    arg === '-y'
  ) {
    return index;
  }

  if (arg === '--fields' || arg === '--limit' || arg === '--json-input') {
    const nextValue = argv[index + 1];
    if (
      nextValue === undefined ||
      (isLikelyOptionToken(nextValue) && !(arg === '--json-input' && nextValue === '-'))
    ) {
      throw missingValueError(arg);
    }
    return index + 1;
  }

  if (
    arg.startsWith('--fields=') ||
    arg.startsWith('--limit=') ||
    arg.startsWith('--json-input=')
  ) {
    return index;
  }

  return null;
}

function isJsonObject(value: unknown): value is JsonObject {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

export function writeOutput(
  data: unknown,
  context: CliContext,
  renderText: (data: unknown) => string,
): void {
  if (!context.useJson) {
    process.stdout.write(renderText(data));
    return;
  }

  const payload = Array.isArray(data)
    ? data
        .slice(0, parseLimit(context.values.limit))
        .map((item) => (isJsonObject(item) ? pickFields(item, context.values.fields) : item))
    : isJsonObject(data)
      ? pickFields(data, context.values.fields)
      : data;

  process.stdout.write(`${JSON.stringify(payload)}\n`);
}

export function readJsonInputText(raw: string, stdinText: string): unknown {
  const text = raw === '-' ? stdinText : raw;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    throw new CliUserError({
      code: 'invalid_json_input',
      message: 'Invalid JSON supplied to --json-input',
      input: { jsonInput: raw === '-' ? '<stdin>' : raw },
      retryable: false,
      suggestion: 'Pass valid JSON or use --json-input=- with JSON on stdin',
    });
  }
}

export function readJsonInput(raw: string | undefined): unknown | null {
  if (raw === undefined) return null;
  return readJsonInputText(raw, raw === '-' ? readFileSync(0, 'utf8') : '');
}

export function assertConfirmed(context: CliContext, action: string): void {
  if (!context.stdinIsTTY && !context.values.yes) {
    throw new CliUserError({
      code: 'confirmation_required',
      message: '--yes required in non-interactive mode',
      input: { action },
      retryable: false,
      suggestion: `Re-run ${context.command} with --yes after reviewing --dry-run output`,
    });
  }
}

export function validatePathInside(input: string, baseDir: string, label: string): string {
  // biome-ignore lint/suspicious/noControlCharactersInRegex: intentional control character detection
  if (/[\x00-\x1f]/.test(input)) {
    throw new CliUserError({
      code: 'invalid_path',
      message: `Control characters rejected in ${label}`,
      input: { path: input },
      retryable: false,
      suggestion: `Pass a ${label} path without control characters`,
    });
  }

  const resolvedBaseDir = resolve(baseDir);
  const resolvedPath = resolve(resolvedBaseDir, input);
  const relativePath = relative(resolvedBaseDir, resolvedPath);

  if (
    relativePath === '..' ||
    relativePath.startsWith('../') ||
    relativePath.startsWith('..\\') ||
    isAbsolute(relativePath)
  ) {
    throw new CliUserError({
      code: 'invalid_path',
      message: `Path traversal rejected for ${label}: ${input}`,
      input: { path: input },
      retryable: false,
      suggestion: `Use a ${label} path inside the current project directory`,
    });
  }

  return resolvedPath;
}

export function describeCommand(description: CommandDescription): CommandDescription {
  return {
    command: description.command,
    summary: description.summary,
    parameters: description.parameters,
    options: description.options,
    risk_tier: description.risk_tier,
  };
}

function optionValuePlaceholder(option: CommandOption): string {
  if (option.name === 'json-input') return ' <json|->';
  if (option.type === 'boolean') return '';
  return ` <${option.type}>`;
}

function optionDetails(option: CommandOption): string {
  const parts: string[] = [];
  if (option.enum && option.enum.length > 0) {
    parts.push(`(${option.enum.join('|')})`);
  }
  if (option.default !== undefined && option.default !== false) {
    parts.push(`[default: ${String(option.default)}]`);
  }
  return parts.join(' ');
}

function renderOption(option: CommandOption): string {
  const longFlag = `--${option.name}${optionValuePlaceholder(option)}`;
  const flag = option.short ? `-${option.short}, ${longFlag}` : longFlag;
  const details = optionDetails(option);
  return details ? `  ${flag}  ${details}` : `  ${flag}`;
}

export function renderHelp(description: CommandDescription, usage: string): string {
  const lines = [
    `Usage: ${usage}`,
    '',
    'Options:',
    ...description.options.map(renderOption),
    '  -h, --help          Show help',
    '',
  ];
  return lines.join('\n');
}

export function exitCodeForError(err: unknown): number {
  return err instanceof CliUserError && err.retryable ? 2 : 1;
}

export function errorPayload(err: unknown): { error: CliErrorData } {
  if (err instanceof CliUserError) {
    return {
      error: {
        code: err.code,
        message: err.message,
        input: err.input,
        retryable: err.retryable,
        suggestion: err.suggestion,
      },
    };
  }

  const message = err instanceof Error ? err.message : String(err);
  const unknownOptionMatch = message.match(/^(?:未知选项|Unknown option):\s*(.+)$/);
  if (unknownOptionMatch) {
    return {
      error: {
        code: 'unknown_option',
        message,
        input: { option: unknownOptionMatch[1] },
        retryable: false,
        suggestion: 'Run this command with --describe to verify supported options',
      },
    };
  }
  // feature 尚未初始化：runtime 层裸抛「未找到执行文件/事件文件」，在此统一映射为
  // 带恢复指引的 not_initialized，避免各命令重复包装。
  const notInitializedMatch = message.match(/^未找到(?:执行文件|事件文件):\s*(.+)$/);
  if (notInitializedMatch) {
    return {
      error: {
        code: 'pipeline_not_initialized',
        message,
        input: { path: notInitializedMatch[1] },
        retryable: false,
        suggestion:
          '该 feature 尚未初始化或路径不对；先运行 `boss runtime init-pipeline <feature>`，或用 `boss doctor` 检查已有 feature',
      },
    };
  }
  // 领域条件不是内部故障：下面每一条调用方都有明确的下一步，归到 internal_error
  // 会让人以为是工具坏了，而附带的「--describe 确认参数」建议也毫无帮助。
  const domainErrors: Array<{
    pattern: RegExp;
    code: string;
    suggestion: (match: RegExpMatchArray) => string;
  }> = [
    {
      pattern: /^Agent (\S+) 已达最大重试次数/,
      code: 'retry_budget_exhausted',
      suggestion: (m) =>
        `Agent ${m[1]} 的重试预算已用尽；按编排循环升级到 \`boss runtime retry-stage <feature> <stage>\`，它会重置该阶段所有 agent 的预算`,
    },
    {
      pattern: /^阶段 (\S+) 已达最大重试次数/,
      code: 'retry_budget_exhausted',
      suggestion: (m) =>
        `阶段 ${m[1]} 的重试预算已用尽；需要人工介入排查失败原因，或重新初始化该 feature`,
    },
    {
      pattern: /^无效的状态转换: (\S+) → (\S+)/,
      code: 'invalid_state_transition',
      suggestion: (m) =>
        `当前状态是 ${m[1]}，不能直接转到 ${m[2]}；合法路径见 \`boss runtime update-stage --describe\`（pending→running→completed/failed，failed→retrying→running）`,
    },
    {
      pattern: /^fromRunId does not match active runId: (\S+)/,
      code: 'run_id_mismatch',
      suggestion: () =>
        '该 feature 的当前 runId 不是这个值；用 `boss status <feature> --json` 查看 parameters.runId 后重试',
    },
    {
      pattern: /^产物 (\S+) 的反馈循环已达上限/,
      code: 'feedback_budget_exhausted',
      suggestion: (m) =>
        `产物 ${m[1]} 的返工轮次已用尽；继续返工前应由人判断是否该改需求或架构，而不是再发一轮修订`,
    },
    {
      pattern:
        /^(?:Expected property name|Unexpected token|Unexpected end of JSON input|Expected ',' or)/,
      code: 'state_unreadable',
      suggestion: () =>
        '某个 JSON 文件无法解析。若是 .boss/<feature>/.meta/execution.json，它只是事件流的投影，可用 `boss runtime rebuild-state <feature>` 从 events.jsonl 重建',
    },
    {
      pattern: /^门禁脚本未找到: (\S+)/,
      code: 'gate_not_found',
      suggestion: (m) =>
        `未找到门禁 ${m[1]}；内置门禁为 gate0 / gate1 / gate2，自定义门禁需放在 .boss/plugins/<name>/ 并先跑 \`boss runtime register-plugins <feature>\``,
    },
    {
      pattern: /^多余的参数: (\S+)/,
      code: 'invalid_usage',
      suggestion: (m) =>
        `多出一个位置参数 ${m[1]}；若想传布尔值，注意本 CLI 用成对旗标（如 --gate-passed / --gate-failed）而不是 --flag <value>。用 --describe 查看该命令支持的选项`,
    },
    {
      pattern: /^阶段 (\S+) 状态为 \S+，只有 failed 状态可以重试/,
      code: 'invalid_state_transition',
      suggestion: (m) =>
        `只有 failed 状态的阶段可以重试；先用 \`boss runtime update-stage <feature> ${m[1]} failed --reason <原因>\` 记录失败`,
    },
  ];
  for (const entry of domainErrors) {
    const match = message.match(entry.pattern);
    if (match) {
      return {
        error: {
          code: entry.code,
          message,
          retryable: false,
          suggestion: entry.suggestion(match),
        },
      };
    }
  }

  // 缺少必填参数属于用法错误：调用方有明确的处置动作（照 usage 补参数），
  // 归到 internal_error 会让人以为是工具坏了。
  const usageMatch = message.match(/^Usage:\s*(.+)$/);
  if (usageMatch) {
    return {
      error: {
        code: 'invalid_usage',
        message,
        input: { usage: usageMatch[1] },
        retryable: false,
        suggestion: `按用法补齐参数：${usageMatch[1]}`,
      },
    };
  }

  // 计划文件与落盘哈希不一致：恢复被拒。这不是内部故障，调用方有明确的处置动作，
  // 因此单列错误码而不是落到 internal_error。
  const planMismatchMatch = message.match(
    /^workflow-plan\.json 与落盘时的 workflowHash 不一致，拒绝恢复：(.+)$/m,
  );
  if (planMismatchMatch) {
    return {
      error: {
        code: 'workflow_plan_mismatch',
        message,
        input: { path: planMismatchMatch[1] },
        retryable: false,
        suggestion:
          '计划文件已被修改或损坏；从版本控制恢复 workflow-plan.json，或用 `boss runtime init-pipeline <feature>` 重新编译计划后再恢复',
      },
    };
  }
  return {
    error: {
      code: 'internal_error',
      message,
      retryable: false,
      suggestion: 'Re-run with --describe to verify command parameters',
    },
  };
}

export function writeError(err: unknown, context: Pick<CliContext, 'useJson'>): void {
  const payload = errorPayload(err);
  if (context.useJson) {
    process.stderr.write(`${JSON.stringify(payload)}\n`);
    return;
  }

  process.stderr.write(`Error [${payload.error.code}]: ${payload.error.message}\n`);
  if (payload.error.suggestion) {
    process.stderr.write(`Hint: ${payload.error.suggestion}\n`);
  }
}

export function runMain(
  fn: () => number | Promise<number>,
  context: Pick<CliContext, 'useJson'>,
): Promise<number> {
  return Promise.resolve()
    .then(fn)
    .catch((err) => {
      writeError(err, context);
      return exitCodeForError(err);
    });
}
