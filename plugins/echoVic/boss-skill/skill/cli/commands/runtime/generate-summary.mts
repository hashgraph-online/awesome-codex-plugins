#!/usr/bin/env node
import * as fs from 'node:fs';
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
import { renderArtifactHtml } from '../../runtime/report/render-artifact-html.mts';
import { renderJson } from '../../runtime/report/render-json.mts';
import { renderMarkdown } from '../../runtime/report/render-markdown.mts';
import { buildSummaryModel } from '../../runtime/report/summary-model.mts';
import { printRuntimeHelp } from './agent-command-utils.mts';

function printHelp(): void {
  printRuntimeHelp('generate-summary', 'boss runtime generate-summary FEATURE [options]');
}

export function parseArgs(argv: string[]) {
  if (argv.length === 0 || argv.includes('-h') || argv.includes('--help')) {
    return { help: true } as const;
  }

  const parsed = {
    feature: '',
    json: false,
    stdout: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    if (arg === '--json') {
      parsed.json = true;
      continue;
    }
    if (arg === '--stdout') {
      parsed.stdout = true;
      continue;
    }
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

  if (!parsed.feature) {
    throw new Error('缺少 feature 参数');
  }
  return parsed;
}

function toFeatureNotFoundError(err: unknown, feature: string): unknown {
  const message = err instanceof Error ? err.message : String(err);
  if (message.includes('未找到执行文件')) {
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

function isInsideDirectory(child: string, parent: string): boolean {
  const relative = path.relative(parent, child);
  return (
    relative === '' || Boolean(relative && !relative.startsWith('..') && !path.isAbsolute(relative))
  );
}

function resolveFeatureDir(
  cwd: string,
  feature: string,
): { featureDir: string; safeFeature: string } {
  const bossDir = path.resolve(cwd, '.boss');
  const featureDir = path.resolve(bossDir, feature);
  if (featureDir === bossDir || !isInsideDirectory(featureDir, bossDir)) {
    throw new Error(`无效 feature 路径: ${feature}`);
  }
  return {
    featureDir,
    safeFeature: path.relative(bossDir, featureDir).split(path.sep).join('/'),
  };
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss runtime generate-summary' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions['generate-summary']!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions['generate-summary'], null, 2)}\n`,
    );
    return 0;
  }

  const parsed = parseArgs(argv);
  if ('help' in parsed) {
    printHelp();
    return 0;
  }

  try {
    const { featureDir, safeFeature } = resolveFeatureDir(cwd, parsed.feature);
    const format = parsed.json ? 'json' : 'markdown';
    const outputArtifact = parsed.json ? 'summary-report.json' : 'summary-report.md';
    const relativeOutputPath = `.boss/${safeFeature}/${outputArtifact}`;
    const relativeHtmlOutputPath = `.boss/${safeFeature}/summary-report.html`;
    const outputPath = path.join(featureDir, outputArtifact);
    const htmlOutputPath = path.join(featureDir, 'summary-report.html');

    if (context.values.dryRun && !parsed.stdout) {
      const actions = [{ type: 'write_file', path: relativeOutputPath, format }];
      if (!parsed.json) {
        actions.push({ type: 'write_file', path: relativeHtmlOutputPath, format: 'html' });
      }
      writeOutput(
        {
          actions,
          risk_tier: 'medium',
          requires_approval: false,
        },
        context,
        () => `would write ${relativeOutputPath}\n`,
      );
      return 0;
    }

    const model = buildSummaryModel(safeFeature, { cwd });
    const rendered = parsed.json ? renderJson(model) : renderMarkdown(model);

    if (parsed.stdout) {
      process.stdout.write(rendered);
      return 0;
    }

    if (!parsed.json) {
      const html = renderArtifactHtml({
        cwd,
        feature: safeFeature,
        sourceArtifact: 'summary-report.md',
        markdown: rendered,
      });
      fs.writeFileSync(outputPath, rendered, 'utf8');
      fs.writeFileSync(htmlOutputPath, html, 'utf8');
    } else {
      fs.writeFileSync(outputPath, rendered, 'utf8');
    }
    writeOutput(
      {
        feature: safeFeature,
        outputPath: relativeOutputPath,
        ...(parsed.json ? {} : { htmlOutputPath: relativeHtmlOutputPath }),
        format,
      },
      context,
      () => `报告已生成: ${outputPath}\n`,
    );
    return 0;
  } catch (err) {
    throw toFeatureNotFoundError(err, parsed.feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime generate-summary',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
