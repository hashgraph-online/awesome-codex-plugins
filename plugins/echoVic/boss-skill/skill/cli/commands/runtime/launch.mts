#!/usr/bin/env node
import * as fs from 'node:fs';
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
import { initPipeline } from '../../runtime/application/pipeline.mts';
import { readExecutionView } from '../../runtime/application/state.mts';
import { printRuntimeHelp, requireInputString, writeActionPlan } from './agent-command-utils.mts';

interface LaunchInput {
  feature: string;
}

function showHelp(): void {
  printRuntimeHelp('launch', 'boss runtime launch FEATURE [options]');
}

function parseFlatInput(argv: string[]): LaunchInput {
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

function resolveInput(argv: string[], context: CliContext): LaunchInput {
  const jsonInput = readJsonInput(context.values.jsonInput);
  if (jsonInput) {
    return {
      feature: requireInputString((jsonInput as Record<string, unknown>).feature, 'feature'),
    };
  }
  return parseFlatInput(argv);
}

function toHandle(feature: string, execution: ReturnType<typeof readExecutionView>) {
  const runId = typeof execution.parameters?.runId === 'string' ? execution.parameters.runId : '';
  return {
    feature,
    runId,
    handle: runId ? `${feature}:${runId}` : feature,
    status: execution.status,
    commands: {
      status: `boss status ${feature}`,
      attach: `boss attach ${feature}`,
    },
  };
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss runtime launch' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions.launch!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions.launch, null, 2)}\n`,
    );
    return 0;
  }

  if (argv.length === 0 || argv.includes('-h') || argv.includes('--help')) {
    showHelp();
    return argv.length === 0 ? 1 : 0;
  }

  const input = resolveInput(argv, context);
  if (context.values.dryRun) {
    writeActionPlan([{ type: 'launch_pipeline', feature: input.feature }], context, 'medium');
    return 0;
  }

  let execution: ReturnType<typeof readExecutionView>;
  const execPath = path.join(cwd, '.boss', input.feature, '.meta', 'execution.json');
  if (fs.existsSync(execPath)) {
    execution = readExecutionView(cwd, input.feature);
  } else {
    execution = initPipeline(input.feature, { cwd });
  }

  writeOutput(toHandle(input.feature, execution), context, (data) => {
    const payload = data as ReturnType<typeof toHandle>;
    return `Pipeline ${payload.feature}: ${payload.handle}\n`;
  });
  return 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime launch',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
