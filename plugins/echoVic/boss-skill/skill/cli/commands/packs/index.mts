#!/usr/bin/env node
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  CliUserError,
  createCliContext,
  describeCommand,
  runMain,
  validatePathInside,
  writeOutput,
} from '../../cli/contract.mts';
import { commandDescriptions } from '../../cli/registry.mts';
import { detectPipelinePacks } from '../../runtime/application/packs.mts';

const packsDetectDescription = commandDescriptions['boss packs detect']!;

function showHelp(): void {
  process.stdout.write(
    [
      'Boss Harness - Pipeline Pack 自动检测',
      '',
      '用法: boss packs detect [project-dir] [--json]',
      '',
    ].join('\n'),
  );
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss packs detect' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(packsDetectDescription),
      context,
      (data) => `${JSON.stringify(data, null, 2)}\n`,
    );
    return 0;
  }

  if (argv.includes('-h') || argv.includes('--help')) {
    showHelp();
    return 0;
  }

  let projectArg = '.';
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (typeof arg !== 'string') continue;
    if (
      arg === '--json' ||
      arg === '--dry-run' ||
      arg === '--describe' ||
      arg === '--yes' ||
      arg === '-y'
    ) {
      continue;
    }
    if (arg === '--fields' || arg === '--limit' || arg === '--json-input') {
      index += 1;
      continue;
    }
    if (
      arg.startsWith('--fields=') ||
      arg.startsWith('--limit=') ||
      arg.startsWith('--json-input=')
    ) {
      continue;
    }
    if (arg.startsWith('-')) {
      throw new CliUserError({
        code: 'unknown_option',
        message: `未知选项: ${arg}`,
        input: { option: arg },
        retryable: false,
        suggestion: 'Run boss packs detect --describe to verify supported options',
      });
    }
    if (projectArg !== '.') {
      throw new CliUserError({
        code: 'extra_argument',
        message: `多余的参数: ${arg}`,
        input: { argument: arg },
        retryable: false,
        suggestion: 'Pass only one project directory',
      });
    }
    projectArg = arg;
  }

  // biome-ignore lint/suspicious/noControlCharactersInRegex: intentional control character detection
  if (/[\x00-\x1f]/.test(projectArg)) {
    throw new CliUserError({
      code: 'invalid_path',
      message: 'Control characters rejected in project directory',
      input: { path: projectArg },
      retryable: false,
      suggestion: 'Pass a project directory path without control characters',
    });
  }
  const projectDir = path.isAbsolute(projectArg)
    ? projectArg
    : validatePathInside(projectArg, cwd, 'project directory');
  const result = detectPipelinePacks(projectDir);
  if (!context.useJson) {
    for (const pack of result.matched) {
      process.stderr.write(`[PACK-DETECT] 匹配: ${pack.name} (priority=${pack.priority})\n`);
    }
  }

  const payload = {
    detected: result.detected.name,
    detectedPack: result.detected,
    matched: result.matched.map((pack) => pack.name),
    matchedPacks: result.matched,
    reason: result.matched.length === 0 ? 'no pack matched' : undefined,
  };
  writeOutput(payload, context, () => `${result.detected.name}\n`);
  return 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss packs detect',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
