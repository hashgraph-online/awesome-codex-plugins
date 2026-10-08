import { spawnSync } from 'node:child_process';
import * as path from 'node:path';
import { skillRootFromImportMeta } from '../infrastructure/paths.mts';
import {
  CliUserError,
  createCliContext,
  describeCommand,
  validatePathInside,
  writeOutput,
} from './contract.mts';
import {
  ARTIFACT_USAGE,
  DESIGN_USAGE,
  GATE_USAGE,
  HOOKS_USAGE,
  PACKS_USAGE,
  PROJECT_USAGE,
  QA_USAGE,
  showRuntimeHelp,
} from './help.mts';
import {
  artifactDescription,
  commandDescriptions,
  designDescription,
  gateDescription,
  hooksDescription,
  packsDescription,
  projectDescription,
  qaDescription,
  runtimeCommandDescriptions,
  runtimeCommandNames,
  runtimeDescription,
} from './registry.mts';

const SKILL_ROOT = skillRootFromImportMeta(import.meta.url);

type RuntimeModule = {
  main: (argv: string[], options?: { cwd?: string }) => number | Promise<number>;
};

type CommandModule = {
  main: (argv: string[], options?: { cwd?: string }) => number | Promise<number>;
};

const runtimeCommands: Record<string, () => Promise<RuntimeModule>> = {
  'agent-cache': () => import('../commands/runtime/agent-cache.mts'),
  attach: () => import('../commands/runtime/attach.mts'),
  'build-memory-summary': () => import('../commands/runtime/build-memory-summary.mts'),
  'check-stage': () => import('../commands/runtime/check-stage.mts'),
  'evaluate-gates': () => import('../commands/runtime/evaluate-gates.mts'),
  'extract-memory': () => import('../commands/runtime/extract-memory.mts'),
  'generate-summary': () => import('../commands/runtime/generate-summary.mts'),
  'get-ready-artifacts': () => import('../commands/runtime/get-ready-artifacts.mts'),
  'init-pipeline': () => import('../commands/runtime/init-pipeline.mts'),
  launch: () => import('../commands/runtime/launch.mts'),
  'inspect-events': () => import('../commands/runtime/inspect-events.mts'),
  'inspect-pipeline': () => import('../commands/runtime/inspect-pipeline.mts'),
  'inspect-plugins': () => import('../commands/runtime/inspect-plugins.mts'),
  'inspect-progress': () => import('../commands/runtime/inspect-progress.mts'),
  'query-memory': () => import('../commands/runtime/query-memory.mts'),
  'record-artifact': () => import('../commands/runtime/record-artifact.mts'),
  'record-feedback': () => import('../commands/runtime/record-feedback.mts'),
  'record-user-choice': () => import('../commands/runtime/record-user-choice.mts'),
  'open-conversation': () => import('../commands/runtime/open-conversation.mts'),
  pause: () => import('../commands/runtime/pause.mts'),
  resume: () => import('../commands/runtime/resume.mts'),
  'append-conversation-message': () =>
    import('../commands/runtime/append-conversation-message.mts'),
  'resolve-conversation': () => import('../commands/runtime/resolve-conversation.mts'),
  'materialize-todo': () => import('../commands/runtime/materialize-todo.mts'),
  'list-conversations': () => import('../commands/runtime/list-conversations.mts'),
  'list-todos': () => import('../commands/runtime/list-todos.mts'),
  'register-plugins': () => import('../commands/runtime/register-plugins.mts'),
  'render-diagnostics': () => import('../commands/runtime/render-diagnostics.mts'),
  'rebuild-state': () => import('../commands/runtime/rebuild-state.mts'),
  'replay-events': () => import('../commands/runtime/replay-events.mts'),
  'report-agent-status': () => import('../commands/runtime/report-agent-status.mts'),
  'retry-agent': () => import('../commands/runtime/retry-agent.mts'),
  'retry-stage': () => import('../commands/runtime/retry-stage.mts'),
  'run-plugin-hook': () => import('../commands/runtime/run-plugin-hook.mts'),
  'update-agent': () => import('../commands/runtime/update-agent.mts'),
  'update-stage': () => import('../commands/runtime/update-stage.mts'),
  'verify-wave': () => import('../commands/runtime/verify-wave.mts'),
  'verify-requirements': () => import('../commands/runtime/verify-requirements.mts'),
};

export function describeGroup(description: typeof runtimeDescription, commands: readonly string[]) {
  return {
    ...describeCommand(description),
    commands: [...commands],
  };
}

export function describeRegisteredCommand(command: string) {
  const description = commandDescriptions[command];
  if (!description) {
    throw new Error(`Missing command description for ${command}`);
  }
  return describeCommand(description);
}

export function writeDescription(
  data: unknown,
  context = createCliContext([], { command: 'boss' }),
): void {
  writeOutput(data, context, () => `${JSON.stringify(data, null, 2)}\n`);
}

export function removeFirstPositional(argv: string[], positional: string | undefined): string[] {
  if (!positional) return argv;
  const index = argv.indexOf(positional);
  if (index === -1) return argv;
  return [...argv.slice(0, index), ...argv.slice(index + 1)];
}

/** 真实命令表，用于给未知命令找最接近的候选。 */
const KNOWN_COMMANDS = [
  'install',
  'uninstall',
  'path',
  'doctor',
  'status',
  'continue',
  'gate',
  'qa attack',
  'runtime',
  'design preview',
  'project init',
  'artifact prepare',
  'packs detect',
  'hooks run',
];

/** 用户最可能的直觉说法 → 真实命令。`init` 是想开始时的第一直觉。 */
const COMMAND_INTENTS: Record<string, string> = {
  init: 'project init',
  start: 'project init',
  new: 'project init',
  create: 'project init',
  run: '/boss（在你的 coding agent 里输入，而不是这个 CLI）',
  review: '/boss:review（在你的 coding agent 里输入）',
  test: 'qa attack',
  check: 'doctor',
  diagnose: 'doctor',
};

function editDistance(left: string, right: string): number {
  const rows = Array.from({ length: left.length + 1 }, (_, i) => [
    i,
    ...Array(right.length).fill(0),
  ]);
  for (let j = 0; j <= right.length; j += 1) rows[0]![j] = j;
  for (let i = 1; i <= left.length; i += 1) {
    for (let j = 1; j <= right.length; j += 1) {
      const cost = left[i - 1] === right[j - 1] ? 0 : 1;
      rows[i]![j] = Math.min(
        rows[i - 1]![j]! + 1,
        rows[i]![j - 1]! + 1,
        rows[i - 1]![j - 1]! + cost,
      );
    }
  }
  return rows[left.length]![right.length]!;
}

/**
 * 未知命令时给出最接近的真实命令。
 *
 * 「Run --describe to list available commands」把排查成本推回给用户，而 `init` 这类
 * 直觉说法其实有确定的对应项（`project init`）。先查意图表，再按编辑距离找最近的命令。
 */
export function suggestCommand(command: string | undefined): string | null {
  if (!command) return null;
  const intent = COMMAND_INTENTS[command.toLowerCase()];
  if (intent) return intent;

  let best: { name: string; distance: number } | null = null;
  for (const name of KNOWN_COMMANDS) {
    const distance = editDistance(command.toLowerCase(), name.split(' ')[0] as string);
    if (!best || distance < best.distance) best = { name, distance };
  }
  // 距离过远时不硬猜，避免给出误导性的建议
  if (!best || best.distance > Math.max(2, Math.floor(command.length / 2))) return null;
  return best.name;
}

export function throwUnknownCommand(scope: string, command: string | undefined): never {
  const closest = suggestCommand(command);
  throw new CliUserError({
    code: 'unknown_command',
    message: `Unknown command: ${command}`,
    input: { command },
    retryable: false,
    suggestion: closest
      ? `你是想用 \`${closest}\` 吗？完整列表：${scope} --help`
      : `Run ${scope} --help to list available commands`,
  });
}

function ensureHookScriptInsideScripts(scriptRelativePath: string): void {
  const scriptAbs = validatePathInside(scriptRelativePath, SKILL_ROOT, 'hook script');
  const scriptsRoot = path.join(SKILL_ROOT, 'scripts');
  const relativeToScripts = path.relative(scriptsRoot, scriptAbs);
  if (
    relativeToScripts === '..' ||
    relativeToScripts.startsWith('../') ||
    relativeToScripts.startsWith('..\\') ||
    path.isAbsolute(relativeToScripts)
  ) {
    throw new CliUserError({
      code: 'invalid_path',
      message: `Path traversal rejected for hook script: ${scriptRelativePath}`,
      input: { path: scriptRelativePath },
      retryable: false,
      suggestion: 'Use a script-relative-path inside the scripts directory',
    });
  }
}

function runHookScript(argv: string[], context: ReturnType<typeof createCliContext>): number {
  const [hook, script] = context.positionals;
  if (!hook || !script) {
    throw new CliUserError({
      code: 'missing_argument',
      message: 'Usage: boss hooks run <hook-id> <script-relative-path> [profiles-csv]',
      input: { hook, script },
      retryable: false,
      suggestion: 'Run boss hooks run --describe to verify command parameters',
    });
  }

  ensureHookScriptInsideScripts(script);
  const scriptPath = path.join(SKILL_ROOT, 'scripts', 'lib', 'run-with-flags.js');
  const result = spawnSync(process.execPath, [scriptPath, ...argv], {
    cwd: process.cwd(),
    env: process.env,
    stdio: ['inherit', 'pipe', 'pipe'],
  });
  if (result.error) {
    throw result.error;
  }

  if (result.stdout.length > 0) {
    process.stdout.write(result.stdout);
  }
  if (result.stderr.length > 0) {
    process.stderr.write(result.stderr);
  }
  return result.status ?? 0;
}

export async function runRuntimeCommand(argv: string[]): Promise<number> {
  const context = createCliContext(argv, { command: 'boss runtime' });
  const runtimeCommand = context.positionals[0];
  if (context.values.describe && context.positionals.length === 0) {
    writeDescription(
      {
        ...describeGroup(runtimeDescription, runtimeCommandNames),
        runtime_commands: runtimeCommandNames,
      },
      context,
    );
    return 0;
  }

  if (!runtimeCommand || runtimeCommand === '-h' || runtimeCommand === '--help') {
    showRuntimeHelp();
    return 0;
  }

  const commandArgv = removeFirstPositional(argv, runtimeCommand);
  const commandContext = createCliContext(commandArgv, {
    command: `boss runtime ${runtimeCommand}`,
  });
  if (commandContext.values.describe) {
    const description = runtimeCommandDescriptions[runtimeCommand];
    if (!description) {
      throwUnknownCommand('boss runtime', runtimeCommand);
    }
    writeDescription(describeCommand(description), commandContext);
    return 0;
  }

  const load = runtimeCommands[runtimeCommand];
  if (!load) {
    throwUnknownCommand('boss runtime', runtimeCommand);
  }

  const mod = await load();
  return mod.main(commandArgv, { cwd: process.cwd() });
}

export async function runDesignCommand(argv: string[]): Promise<number> {
  const context = createCliContext(argv, { command: 'boss design' });
  const subcommand = context.positionals[0];
  if (context.values.describe && context.positionals.length === 0) {
    writeDescription(describeGroup(designDescription, ['preview']), context);
    return 0;
  }

  if (!subcommand || subcommand === '-h' || subcommand === '--help') {
    process.stdout.write(DESIGN_USAGE);
    return 0;
  }

  if (subcommand !== 'preview') {
    throwUnknownCommand('boss design', subcommand);
  }

  const commandArgv = removeFirstPositional(argv, subcommand);
  const commandContext = createCliContext(commandArgv, { command: 'boss design preview' });
  if (commandContext.values.describe) {
    writeDescription(describeRegisteredCommand('boss design preview'), commandContext);
    return 0;
  }

  const mod: CommandModule = await import('../commands/design/preview.mts');
  return mod.main(commandArgv, { cwd: process.cwd() });
}

export async function runGateCommand(argv: string[]): Promise<number> {
  const context = createCliContext(argv, { command: 'boss gate' });
  const subcommand = context.positionals[0];
  if (context.values.describe && context.positionals.length === 0) {
    writeDescription(describeGroup(gateDescription, ['final']), context);
    return 0;
  }

  if (argv.includes('-h') || argv.includes('--help')) {
    process.stdout.write(GATE_USAGE);
    return 0;
  }

  const commandKey = subcommand === 'final' ? 'boss gate final' : 'boss gate';
  const commandArgv = subcommand === 'final' ? removeFirstPositional(argv, subcommand) : argv;
  const normalizedArgv = subcommand === 'final' ? [subcommand, ...commandArgv] : argv;
  const commandContext = createCliContext(commandArgv, { command: commandKey });
  if (commandContext.values.describe) {
    writeDescription(describeRegisteredCommand(commandKey), commandContext);
    return 0;
  }

  const mod: CommandModule = await import('../commands/gate/index.mts');
  return mod.main(normalizedArgv, { cwd: process.cwd() });
}

export async function runQaCommand(argv: string[]): Promise<number> {
  const context = createCliContext(argv, { command: 'boss qa' });
  const subcommand = context.positionals[0];
  if (context.values.describe && context.positionals.length === 0) {
    writeDescription(describeGroup(qaDescription, ['attack']), context);
    return 0;
  }

  if (argv.includes('-h') || argv.includes('--help')) {
    process.stdout.write(QA_USAGE);
    return 0;
  }

  if (subcommand && subcommand !== 'attack') {
    throwUnknownCommand('boss qa', subcommand);
  }

  const commandKey = subcommand === 'attack' ? 'boss qa attack' : 'boss qa';
  const commandArgv = subcommand === 'attack' ? removeFirstPositional(argv, subcommand) : argv;
  const normalizedArgv = subcommand === 'attack' ? [subcommand, ...commandArgv] : argv;
  const commandContext = createCliContext(commandArgv, { command: commandKey });
  if (commandContext.values.describe) {
    writeDescription(describeRegisteredCommand(commandKey), commandContext);
    return 0;
  }

  const mod: CommandModule = await import('../commands/qa/index.mts');
  return mod.main(normalizedArgv, { cwd: process.cwd() });
}

export async function runProjectCommand(argv: string[]): Promise<number> {
  const context = createCliContext(argv, { command: 'boss project' });
  const subcommand = context.positionals[0];
  if (context.values.describe && context.positionals.length === 0) {
    writeDescription(describeGroup(projectDescription, ['init']), context);
    return 0;
  }

  if (!subcommand || subcommand === '-h' || subcommand === '--help') {
    process.stdout.write(PROJECT_USAGE);
    return 0;
  }

  if (subcommand !== 'init') {
    throwUnknownCommand('boss project', subcommand);
  }

  const mod: CommandModule = await import('../commands/project/index.mts');
  return mod.main(removeFirstPositional(argv, subcommand), { cwd: process.cwd() });
}

export async function runArtifactCommand(argv: string[]): Promise<number> {
  const context = createCliContext(argv, { command: 'boss artifact' });
  const subcommand = context.positionals[0];
  if (context.values.describe && context.positionals.length === 0) {
    writeDescription(describeGroup(artifactDescription, ['prepare']), context);
    return 0;
  }

  if (!subcommand || subcommand === '-h' || subcommand === '--help') {
    process.stdout.write(ARTIFACT_USAGE);
    return 0;
  }

  if (subcommand !== 'prepare') {
    throwUnknownCommand('boss artifact', subcommand);
  }

  const mod: CommandModule = await import('../commands/artifact/index.mts');
  return mod.main(removeFirstPositional(argv, subcommand), { cwd: process.cwd() });
}

export async function runPacksCommand(argv: string[]): Promise<number> {
  const context = createCliContext(argv, { command: 'boss packs' });
  const subcommand = context.positionals[0];
  if (context.values.describe && context.positionals.length === 0) {
    writeDescription(describeGroup(packsDescription, ['detect']), context);
    return 0;
  }

  if (!subcommand || subcommand === '-h' || subcommand === '--help') {
    process.stdout.write(PACKS_USAGE);
    return 0;
  }

  if (subcommand !== 'detect') {
    throwUnknownCommand('boss packs', subcommand);
  }

  const mod: CommandModule = await import('../commands/packs/index.mts');
  return mod.main(removeFirstPositional(argv, subcommand), { cwd: process.cwd() });
}

export function runHooksCommand(argv: string[]): number {
  const context = createCliContext(argv, { command: 'boss hooks' });
  const subcommand = context.positionals[0];
  if (context.values.describe && context.positionals.length === 0) {
    writeDescription(describeGroup(hooksDescription, ['run']), context);
    return 0;
  }

  if (!subcommand || subcommand === '-h' || subcommand === '--help') {
    process.stdout.write(HOOKS_USAGE);
    return 0;
  }

  if (subcommand !== 'run') {
    throwUnknownCommand('boss hooks', subcommand);
  }

  const commandArgv = removeFirstPositional(argv, subcommand);
  const commandContext = createCliContext(commandArgv, { command: 'boss hooks run' });
  if (commandContext.values.describe) {
    writeDescription(describeRegisteredCommand('boss hooks run'), commandContext);
    return 0;
  }

  return runHookScript(commandArgv, commandContext);
}
