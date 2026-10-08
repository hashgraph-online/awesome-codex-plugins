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
import { recordUserChoice } from '../../runtime/application/pipeline.mts';
import {
  optionalInputString,
  printRuntimeHelp,
  requireInputString,
  requireOptionValue,
  toFeatureNotFoundError,
  writeActionPlan,
} from './agent-command-utils.mts';

interface RecordUserChoiceInput {
  feature: string;
  choiceType: string;
  selected: string;
  options?: string[];
  reason?: string;
  agent?: string;
  stage?: number;
}

function showHelp(): void {
  printRuntimeHelp(
    'record-user-choice',
    'boss runtime record-user-choice FEATURE --choice-type <type> --selected <value> [options]',
  );
}

function parseFlatInput(argv: string[]): RecordUserChoiceInput {
  let feature = '';
  let choiceType = '';
  let selected = '';
  let options: string[] | undefined;
  let reason: string | undefined;
  let agent: string | undefined;
  let stage: number | undefined;

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    switch (arg) {
      case '--choice-type':
        choiceType = requireOptionValue('--choice-type', argv[index + 1]);
        index += 1;
        continue;
      case '--selected':
        selected = requireOptionValue('--selected', argv[index + 1]);
        index += 1;
        continue;
      case '--options':
        options = requireOptionValue('--options', argv[index + 1])
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean);
        index += 1;
        continue;
      case '--reason':
        reason = requireOptionValue('--reason', argv[index + 1]);
        index += 1;
        continue;
      case '--agent':
        agent = requireOptionValue('--agent', argv[index + 1]);
        index += 1;
        continue;
      case '--stage': {
        const raw = requireOptionValue('--stage', argv[index + 1]);
        const parsed = Number(raw);
        if (!Number.isInteger(parsed)) throw new Error('--stage 必须是整数');
        stage = parsed;
        index += 1;
        continue;
      }
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
    choiceType: requireInputString(choiceType, 'choiceType'),
    selected: requireInputString(selected, 'selected'),
    options,
    reason,
    agent,
    stage,
  };
}

function resolveInput(argv: string[], context: CliContext): RecordUserChoiceInput {
  const jsonInput = readJsonInput(context.values.jsonInput);
  if (jsonInput) {
    const input = jsonInput as Record<string, unknown>;
    return {
      feature: requireInputString(input.feature, 'feature'),
      choiceType: requireInputString(input.choiceType, 'choiceType'),
      selected: requireInputString(input.selected, 'selected'),
      options: Array.isArray(input.options)
        ? input.options.filter(
            (item): item is string => typeof item === 'string' && item.length > 0,
          )
        : undefined,
      reason: optionalInputString(input.reason),
      agent: optionalInputString(input.agent),
      stage: typeof input.stage === 'number' ? input.stage : undefined,
    };
  }
  return parseFlatInput(argv);
}

function actionFor(input: RecordUserChoiceInput) {
  return {
    type: 'record_user_choice',
    feature: input.feature,
    choice_type: input.choiceType,
    selected: input.selected,
  };
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss runtime record-user-choice' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions['record-user-choice']!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions['record-user-choice'], null, 2)}\n`,
    );
    return 0;
  }

  if (argv.length === 0 || argv.includes('-h') || argv.includes('--help')) {
    showHelp();
    return argv.length === 0 ? 1 : 0;
  }

  const input = resolveInput(argv, context);
  if (context.values.dryRun) {
    writeActionPlan([actionFor(input)], context, 'low');
    return 0;
  }

  try {
    recordUserChoice(input.feature, {
      choiceType: input.choiceType,
      selected: input.selected,
      options: input.options,
      reason: input.reason,
      agent: input.agent,
      stage: input.stage,
      cwd,
    });
    writeOutput(
      {
        feature: input.feature,
        choiceType: input.choiceType,
        selected: input.selected,
      },
      context,
      () => `记录用户选择：${input.choiceType} -> ${input.selected}\n`,
    );
    return 0;
  } catch (err) {
    throw toFeatureNotFoundError(err, input.feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime record-user-choice',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
