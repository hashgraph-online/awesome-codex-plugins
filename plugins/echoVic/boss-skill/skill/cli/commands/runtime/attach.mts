#!/usr/bin/env node
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  type CliContext,
  consumeCliContractOption,
  createCliContext,
  describeCommand,
  readJsonInput,
  runMain,
  writeOutput,
} from '../../cli/contract.mts';
import { runtimeCommandDescriptions } from '../../cli/registry.mts';
import { inspectPipeline } from '../../runtime/application/inspection.mts';
import {
  printRuntimeHelp,
  requireInputString,
  toFeatureNotFoundError,
} from './agent-command-utils.mts';

interface AttachInput {
  feature: string;
}

function showHelp(): void {
  printRuntimeHelp('attach', 'boss runtime attach FEATURE [options]');
}

function parseFlatInput(argv: string[]): AttachInput {
  let feature = '';
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    const contractOptionEnd = consumeCliContractOption(argv, index);
    if (contractOptionEnd !== null) {
      index = contractOptionEnd;
      continue;
    }
    if (arg.startsWith('-')) throw new Error(`未知选项: ${arg}`);
    if (!feature) feature = arg;
    else throw new Error(`多余的参数: ${arg}`);
  }
  return { feature: requireInputString(feature, 'feature') };
}

function resolveInput(argv: string[], context: CliContext): AttachInput {
  const jsonInput = readJsonInput(context.values.jsonInput);
  if (jsonInput) {
    return {
      feature: requireInputString((jsonInput as Record<string, unknown>).feature, 'feature'),
    };
  }
  return parseFlatInput(argv);
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss runtime attach' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions.attach!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions.attach, null, 2)}\n`,
    );
    return 0;
  }

  if (argv.length === 0 || argv.includes('-h') || argv.includes('--help')) {
    showHelp();
    return argv.length === 0 ? 1 : 0;
  }

  const input = resolveInput(argv, context);
  try {
    const summary = inspectPipeline(input.feature, { cwd });
    writeOutput(
      {
        feature: input.feature,
        runId: summary.runId,
        handle: summary.runId ? `${input.feature}:${summary.runId}` : input.feature,
        status: summary.status,
        currentStage: summary.currentStage,
        activeAgents: summary.activeAgents,
        readyArtifacts: summary.readyArtifacts,
        pause: summary.pause,
        artifactDag: summary.artifactDag,
      },
      context,
      () => `Pipeline ${input.feature}: ${summary.status}\n`,
    );
    return 0;
  } catch (err) {
    throw toFeatureNotFoundError(err, input.feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime attach',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
