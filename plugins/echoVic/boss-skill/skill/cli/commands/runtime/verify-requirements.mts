#!/usr/bin/env node
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  CliUserError,
  consumeCliContractOption,
  createCliContext,
  describeCommand,
  runMain,
  writeOutput,
} from '../../cli/contract.mts';
import { runtimeCommandDescriptions } from '../../cli/registry.mts';
import {
  type RequirementsVerificationResult,
  verifyRequirements,
} from '../../runtime/application/requirements-verification.mts';
import { printRuntimeHelp } from './agent-command-utils.mts';

function printHelp(): void {
  printRuntimeHelp('verify-requirements', 'boss runtime verify-requirements FEATURE [options]');
}

export function parseArgs(argv: string[]) {
  if (argv.length === 0 || argv.includes('-h') || argv.includes('--help')) {
    return { help: true } as const;
  }

  const parsed = {
    feature: '',
    testDir: '',
    dryRun: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    if (arg === '--test-dir') {
      const value = argv[index + 1];
      if (!value || value.startsWith('-')) {
        throw new Error(`--test-dir 需要一个路径参数`);
      }
      parsed.testDir = value;
      index += 1;
      continue;
    }
    if (arg === '--dry-run') {
      parsed.dryRun = true;
      continue;
    }
    if (arg === '--json') continue;
    const contractOptionEnd = consumeCliContractOption(argv, index);
    if (contractOptionEnd !== null) {
      index = contractOptionEnd;
      continue;
    }
    if (arg.startsWith('-')) {
      throw new Error(`未知选项: ${arg}`);
    }
    if (!parsed.feature) {
      parsed.feature = arg;
      continue;
    }
    throw new Error(`多余的参数: ${arg}`);
  }

  if (!parsed.feature) throw new Error('缺少 feature 参数');
  return parsed;
}

function renderText(result: RequirementsVerificationResult): string {
  const lines: string[] = [];
  lines.push(`Requirements Traceability Matrix — ${result.feature}`);
  lines.push('═'.repeat(60));

  for (const row of result.matrix) {
    const status = row.covered ? '[COVERED]' : '[MISSING]';
    const files = row.covered ? ` ${row.testFiles.join(', ')}` : '';
    lines.push(`${row.ac}: ${row.description}  ${status}${files}`);
  }

  lines.push('─'.repeat(60));
  lines.push(`Coverage: ${result.coveredACs}/${result.totalACs} (${result.coveragePercent}%)`);
  return `${lines.join('\n')}\n`;
}

function toFeatureNotFoundError(err: unknown, feature: string): unknown {
  const message = err instanceof Error ? err.message : String(err);
  if (message.includes('未找到') || message.includes('feature')) {
    return new CliUserError({
      code: 'feature_not_found',
      message,
      input: { feature },
      retryable: false,
      suggestion: 'Ensure .boss/<feature>/prd.md exists with AC-N acceptance criteria',
    });
  }
  return err;
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss runtime verify-requirements' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions['verify-requirements']!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions['verify-requirements'], null, 2)}\n`,
    );
    return 0;
  }

  const parsed = parseArgs(argv);
  if ('help' in parsed) {
    printHelp();
    return 0;
  }

  try {
    const result = verifyRequirements(parsed.feature, {
      cwd,
      testDir: parsed.testDir || undefined,
      dryRun: parsed.dryRun,
    });

    writeOutput(result, context, (data) => renderText(data as RequirementsVerificationResult));
    return result.verified ? 0 : 1;
  } catch (err) {
    throw toFeatureNotFoundError(err, parsed.feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime verify-requirements',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
