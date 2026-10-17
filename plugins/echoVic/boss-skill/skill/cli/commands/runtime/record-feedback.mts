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
import { recordFeedback } from '../../runtime/application/pipeline.mts';
import {
  optionalInputString,
  printRuntimeHelp,
  requireInputString,
  requireOptionValue,
  toFeatureNotFoundError,
  writeActionPlan,
} from './agent-command-utils.mts';

interface RecordFeedbackInput {
  feature: string;
  from: string;
  to: string;
  artifact: string;
  reason: string;
  priority: string;
}

function showHelp(): void {
  printRuntimeHelp('record-feedback', 'boss runtime record-feedback FEATURE [options]');
}

function parseFlatInput(argv: string[]): RecordFeedbackInput {
  let feature = '';
  let from = '';
  let to = '';
  let artifact = '';
  let reason = '';
  let priority = 'recommended';

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    switch (arg) {
      case '--from':
        from = requireOptionValue('--from', argv[index + 1]);
        index += 1;
        continue;
      case '--to':
        to = requireOptionValue('--to', argv[index + 1]);
        index += 1;
        continue;
      case '--artifact':
        artifact = requireOptionValue('--artifact', argv[index + 1]);
        index += 1;
        continue;
      case '--reason':
        reason = requireOptionValue('--reason', argv[index + 1]);
        index += 1;
        continue;
      case '--priority':
        priority = requireOptionValue('--priority', argv[index + 1]);
        index += 1;
        continue;
    }
    const contractOptionEnd = consumeCliContractOption(argv, index);
    if (contractOptionEnd !== null) {
      index = contractOptionEnd;
      continue;
    }
    if (arg.startsWith('-')) throw new Error(`未知选项: ${arg}`);
    if (!feature) feature = arg;
    else throw new Error(`多余的参数: ${arg}`);
  }

  return {
    feature: requireInputString(feature, 'feature'),
    from: requireInputString(from, 'from'),
    to: requireInputString(to, 'to'),
    artifact: requireInputString(artifact, 'artifact'),
    reason: requireInputString(reason, 'reason'),
    priority,
  };
}

function resolveInput(argv: string[], context: CliContext): RecordFeedbackInput {
  const jsonInput = readJsonInput(context.values.jsonInput);
  if (jsonInput) {
    const input = jsonInput as Record<string, unknown>;
    return {
      feature: requireInputString(input.feature, 'feature'),
      from: requireInputString(input.from, 'from'),
      to: requireInputString(input.to, 'to'),
      artifact: requireInputString(input.artifact, 'artifact'),
      reason: requireInputString(input.reason, 'reason'),
      priority: optionalInputString(input.priority) || 'recommended',
    };
  }
  return parseFlatInput(argv);
}

function actionFor(input: RecordFeedbackInput) {
  return {
    type: 'record_feedback',
    feature: input.feature,
    artifact: input.artifact,
    priority: input.priority,
    reason: input.reason,
  };
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss runtime record-feedback' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions['record-feedback']!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions['record-feedback'], null, 2)}\n`,
    );
    return 0;
  }

  if (argv.length === 0 || argv.includes('-h') || argv.includes('--help')) {
    showHelp();
    return argv.length === 0 ? 1 : 0;
  }

  const input = resolveInput(argv, context);
  if (context.values.dryRun) {
    writeActionPlan([actionFor(input)], context, 'medium');
    return 0;
  }

  try {
    const state = recordFeedback(input.feature, {
      from: input.from,
      to: input.to,
      artifact: input.artifact,
      reason: input.reason,
      priority: input.priority,
      cwd,
    });
    const feedbackLoops = state.feedbackLoops || {};
    writeOutput(
      {
        feature: input.feature,
        round: feedbackLoops.currentRound,
        maxRounds: feedbackLoops.maxRounds,
      },
      context,
      () =>
        `${JSON.stringify({ feature: input.feature, round: feedbackLoops.currentRound, maxRounds: feedbackLoops.maxRounds }, null, 2)}\n`,
    );
    return 0;
  } catch (err) {
    throw toFeatureNotFoundError(err, input.feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime record-feedback',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
