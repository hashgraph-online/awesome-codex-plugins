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
import { recordArtifact, recordArtifacts } from '../../runtime/application/pipeline.mts';
import { renderArtifactHtml } from '../../runtime/report/render-artifact-html.mts';
import {
  printRuntimeHelp,
  requireInputString,
  toFeatureNotFoundError,
  writeActionPlan,
} from './agent-command-utils.mts';

interface RecordArtifactInput {
  feature: string;
  artifact: string;
  stage: string;
  noOpen: boolean;
}

function showHelp(): void {
  printRuntimeHelp(
    'record-artifact',
    'boss runtime record-artifact FEATURE ARTIFACT STAGE [options]',
  );
}

function parseFlatInput(argv: string[]): RecordArtifactInput {
  let feature = '';
  let artifact = '';
  let stage = '';
  let noOpen = false;
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    const contractOptionEnd = consumeCliContractOption(argv, index);
    if (contractOptionEnd !== null) {
      index = contractOptionEnd;
      continue;
    }
    if (arg === '--no-open') {
      noOpen = true;
      continue;
    }
    if (arg.startsWith('-')) throw new Error(`未知选项: ${arg}`);
    if (!feature) feature = arg;
    else if (!artifact) artifact = arg;
    else if (!stage) stage = arg;
    else throw new Error(`多余的参数: ${arg}`);
  }
  return {
    feature: requireInputString(feature, 'feature'),
    artifact: requireInputString(artifact, 'artifact'),
    stage: requireInputString(stage, 'stage'),
    noOpen,
  };
}

function resolveInput(argv: string[], context: CliContext): RecordArtifactInput {
  const jsonInput = readJsonInput(context.values.jsonInput);
  if (jsonInput) {
    const input = jsonInput as Record<string, unknown>;
    return {
      feature: requireInputString(input.feature, 'feature'),
      artifact: requireInputString(input.artifact, 'artifact'),
      stage: requireInputString(input.stage, 'stage'),
      noOpen: input.noOpen === true || input['no-open'] === true,
    };
  }
  return parseFlatInput(argv);
}

function parseStageNumber(stage: string): number {
  const stageNumber = Number(stage);
  if (!Number.isInteger(stageNumber)) {
    throw new Error('stage 必须是整数');
  }
  if (stageNumber < 1 || stageNumber > 4) {
    throw new Error('stage 必须是 1-4');
  }
  return stageNumber;
}

function actionFor(input: RecordArtifactInput, stageNumber: number) {
  return {
    type: 'record_artifact',
    feature: input.feature,
    artifact: input.artifact,
    stage: stageNumber,
  };
}

function isMarkdownArtifact(artifact: string): boolean {
  return artifact.endsWith('.md');
}

function htmlArtifactFor(markdownArtifact: string): string {
  return markdownArtifact.replace(/\.md$/, '.html');
}

function validateMarkdownArtifactName(artifact: string): void {
  if (
    !isMarkdownArtifact(artifact) ||
    artifact !== path.basename(artifact) ||
    artifact.includes('/') ||
    artifact.includes('\\') ||
    artifact.includes('..')
  ) {
    throw new Error(`无效 Markdown 产物: ${artifact}`);
  }
}

function isInsideDirectory(child: string, parent: string): boolean {
  const relative = path.relative(parent, child);
  return (
    relative === '' || Boolean(relative && !relative.startsWith('..') && !path.isAbsolute(relative))
  );
}

function resolveFeatureDir(cwd: string, feature: string): string {
  const bossDir = path.resolve(cwd, '.boss');
  const featureDir = path.resolve(bossDir, feature);
  if (featureDir === bossDir || !isInsideDirectory(featureDir, bossDir)) {
    throw new Error(`无效 feature 路径: ${feature}`);
  }
  return featureDir;
}

function markdownPathFor(input: RecordArtifactInput, cwd: string): string {
  validateMarkdownArtifactName(input.artifact);
  const featureDir = resolveFeatureDir(cwd, input.feature);
  const markdownPath = path.resolve(featureDir, input.artifact);
  if (path.dirname(markdownPath) !== featureDir) {
    throw new Error(`无效 Markdown 产物: ${input.artifact}`);
  }
  return markdownPath;
}

function writeHtmlWithRollback(outputPath: string, html: string): () => void {
  const previous = fs.existsSync(outputPath) ? fs.readFileSync(outputPath) : null;
  fs.writeFileSync(outputPath, html, 'utf8');
  return () => {
    if (previous) {
      fs.writeFileSync(outputPath, previous);
      return;
    }
    fs.rmSync(outputPath, { force: true });
  };
}

function actionsFor(input: RecordArtifactInput, cwd: string, stageNumber: number) {
  if (!isMarkdownArtifact(input.artifact)) {
    return [actionFor(input, stageNumber)];
  }
  validateMarkdownArtifactName(input.artifact);
  resolveFeatureDir(cwd, input.feature);
  const htmlArtifact = htmlArtifactFor(input.artifact);
  return [
    actionFor(input, stageNumber),
    {
      type: 'write_file',
      path: path.posix.join('.boss', input.feature, htmlArtifact),
      format: 'html',
    },
    {
      type: 'record_artifact',
      feature: input.feature,
      artifact: htmlArtifact,
      stage: stageNumber,
    },
  ];
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss runtime record-artifact' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions['record-artifact']!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions['record-artifact'], null, 2)}\n`,
    );
    return 0;
  }

  if (argv.length === 0 || argv.includes('-h') || argv.includes('--help')) {
    showHelp();
    return argv.length === 0 ? 1 : 0;
  }

  const input = resolveInput(argv, context);
  const stageNumber = parseStageNumber(input.stage);
  if (context.values.dryRun) {
    writeActionPlan(actionsFor(input, cwd, stageNumber), context, 'medium');
    return 0;
  }

  try {
    let htmlArtifact: string | undefined;
    let htmlPath: string | undefined;
    let markdown: string | undefined;
    let html: string | undefined;
    let htmlOutputPath: string | undefined;

    if (isMarkdownArtifact(input.artifact)) {
      const markdownPath = markdownPathFor(input, cwd);
      if (!fs.existsSync(markdownPath)) {
        throw new Error(`未找到 Markdown 产物: ${path.relative(cwd, markdownPath)}`);
      }
      markdown = fs.readFileSync(markdownPath, 'utf8');
      htmlArtifact = htmlArtifactFor(input.artifact);
      htmlPath = path.posix.join('.boss', input.feature, htmlArtifact);
      htmlOutputPath = path.join(resolveFeatureDir(cwd, input.feature), htmlArtifact);
      html = renderArtifactHtml({
        cwd,
        feature: input.feature,
        sourceArtifact: input.artifact,
        markdown,
      });
    }

    let execution: ReturnType<typeof recordArtifact>;

    if (markdown !== undefined && htmlArtifact && html !== undefined && htmlOutputPath) {
      execution = recordArtifacts(input.feature, [input.artifact, htmlArtifact], stageNumber, {
        cwd,
        beforeAppend: () => writeHtmlWithRollback(htmlOutputPath, html),
      });
    } else {
      execution = recordArtifact(input.feature, input.artifact, stageNumber, { cwd });
    }

    const stageKey = String(stageNumber);
    const artifacts =
      execution.stages && execution.stages[stageKey] ? execution.stages[stageKey]!.artifacts : [];
    const previewCommand =
      input.artifact === 'ui-design.json'
        ? `boss design preview ${input.feature}${input.noOpen ? ' --no-open' : ''}`
        : undefined;
    const payload = {
      feature: input.feature,
      artifact: input.artifact,
      stage: stageNumber,
      artifacts,
      previewCommand,
      ...(htmlArtifact ? { htmlArtifact, htmlPath } : {}),
    };
    writeOutput(
      payload,
      context,
      () =>
        `${JSON.stringify(payload, null, 2)}\n${previewCommand ? `Preview: ${previewCommand}\n` : ''}`,
    );
    return 0;
  } catch (err) {
    throw toFeatureNotFoundError(err, input.feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime record-artifact',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
