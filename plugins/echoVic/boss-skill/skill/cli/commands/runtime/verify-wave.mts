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
import { type VerifyPhase, verifyWave } from '../../runtime/application/wave-verification.mts';
import { printRuntimeHelp } from './agent-command-utils.mts';

function printHelp(): void {
  printRuntimeHelp('verify-wave', 'boss runtime verify-wave FEATURE WAVE_ID [options]');
}

export function parseArgs(argv: string[]) {
  if (argv.length === 0 || argv.includes('-h') || argv.includes('--help')) {
    return { help: true } as const;
  }

  const parsed = {
    feature: '',
    waveId: '',
    phase: 'full' as VerifyPhase,
    dryRun: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    if (arg === '--phase') {
      const value = argv[index + 1];
      if (!value || !['red', 'green', 'full'].includes(value)) {
        throw new Error(`--phase 必须是 red, green 或 full`);
      }
      parsed.phase = value as VerifyPhase;
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
    if (!parsed.waveId) {
      parsed.waveId = arg;
      continue;
    }
    throw new Error(`多余的参数: ${arg}`);
  }

  if (!parsed.feature) throw new Error('缺少 feature 参数');
  if (!parsed.waveId) throw new Error('缺少 waveId 参数');
  return parsed;
}

function renderText(result: ReturnType<typeof verifyWave>): string {
  const lines: string[] = [];
  lines.push(`Wave Verification — ${result.feature} / ${result.waveId} (phase: ${result.phase})`);
  lines.push('─'.repeat(60));

  if (result.redTests) {
    lines.push('Red Tests (should FAIL):');
    for (const r of result.redTests.results) {
      const status = r.passed ? '✓ FAILED as expected' : '✗ PASSED unexpectedly';
      lines.push(`  ${r.command} → exit ${r.exitCode} ${status}`);
    }
    lines.push('');
  }

  if (result.greenGates) {
    lines.push('Green Gates (should PASS):');
    for (const r of result.greenGates.results) {
      const status = r.passed ? '✓ PASSED' : '✗ FAILED';
      lines.push(`  ${r.command} → exit ${r.exitCode} ${status}`);
    }
    lines.push('');
  }

  lines.push(`Result: ${result.verified ? 'VERIFIED' : 'FAILED'}`);
  return `${lines.join('\n')}\n`;
}

function toFeatureNotFoundError(err: unknown, feature: string): unknown {
  const message = err instanceof Error ? err.message : String(err);
  if (message.includes('未找到执行文件') || message.includes('未找到事件文件')) {
    return new CliUserError({
      code: 'feature_not_found',
      message,
      input: { feature },
      retryable: false,
      suggestion: 'Run boss runtime init-pipeline <feature> first',
    });
  }
  return err;
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss runtime verify-wave' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions['verify-wave']!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions['verify-wave'], null, 2)}\n`,
    );
    return 0;
  }

  const parsed = parseArgs(argv);
  if ('help' in parsed) {
    printHelp();
    return 0;
  }

  try {
    const result = verifyWave(parsed.feature, parsed.waveId, parsed.phase, {
      cwd,
      dryRun: parsed.dryRun,
    });

    writeOutput(result, context, (data) => renderText(data as ReturnType<typeof verifyWave>));
    return result.verified ? 0 : 1;
  } catch (err) {
    throw toFeatureNotFoundError(err, parsed.feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime verify-wave',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
