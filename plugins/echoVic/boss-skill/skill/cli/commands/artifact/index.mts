#!/usr/bin/env node
import * as fs from 'node:fs';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  CliUserError,
  createCliContext,
  describeCommand,
  readJsonInput,
  runMain,
  validatePathInside,
  writeOutput,
} from '../../cli/contract.mts';
import { commandDescriptions } from '../../cli/registry.mts';
import { skillRootFromImportMeta } from '../../infrastructure/paths.mts';

const SKILL_ROOT = skillRootFromImportMeta(import.meta.url);
const DEFAULT_TEMPLATE_DIR = path.join(SKILL_ROOT, 'templates');
const artifactPrepareDescription = commandDescriptions['boss artifact prepare']!;

function showHelp(): void {
  process.stdout.write(
    [
      'Boss Mode - 产物骨架准备',
      '',
      '用法: boss artifact prepare <feature-name> <artifact-name> [template-name]',
      '',
    ].join('\n'),
  );
}

/**
 * 模板的可用引用：项目自带模板回显项目内相对路径，内置模板只回显模板名。
 *
 * 此前一律用 `path.relative(cwd, templatePath)`，内置模板会变成一条从用户项目指向
 * boss 安装位置的穿越路径（实跑见到 `../boss-sched/skill/templates/prd.md.template`），
 * 既打不开也不说明来源。
 */
function describeTemplate(
  cwd: string,
  templatePath: string,
): { template: string; templateSource: 'project' | 'bundled' } {
  const projectRoot = path.join(cwd, '.boss', 'templates');
  if (templatePath.startsWith(projectRoot + path.sep)) {
    return { template: path.relative(cwd, templatePath), templateSource: 'project' };
  }
  return { template: path.basename(templatePath), templateSource: 'bundled' };
}

function resolveTemplate(cwd: string, templateName: string): string {
  const projectTemplate = path.join(cwd, '.boss', 'templates', templateName);
  if (fs.existsSync(projectTemplate)) return projectTemplate;

  const defaultTemplate = path.join(DEFAULT_TEMPLATE_DIR, templateName);
  if (fs.existsSync(defaultTemplate)) return defaultTemplate;

  throw new CliUserError({
    code: 'template_not_found',
    message: `未找到模板文件: ${templateName}`,
    input: { template: templateName },
    retryable: false,
    suggestion: 'Create the project template or use a bundled template name',
  });
}

function renderTemplate(content: string, feature: string): string {
  const replacements: Record<string, string> = {
    '{{FEATURE_NAME}}': feature,
    '{{FEATURE}}': feature,
    '{{PROJECT_NAME}}': feature,
    '{{DATE}}': new Date().toISOString().slice(0, 10),
    '{{VERSION}}': '1.0',
  };
  let rendered = content;
  for (const [token, value] of Object.entries(replacements)) {
    rendered = rendered.split(token).join(value);
  }
  return rendered;
}

function isJsonObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function validateRelativeName(input: string, label: 'artifact' | 'template'): void {
  validatePathInside(input, '/', label);
  if (input.includes('..') || path.isAbsolute(input)) {
    throw new CliUserError({
      code: 'invalid_path',
      message: `Path traversal rejected for ${label}: ${input}`,
      input: { path: input },
      retryable: false,
      suggestion: `Use a relative ${label} name without path traversal`,
    });
  }
}

function validateFeatureName(feature: string): void {
  if (!/^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/.test(feature)) {
    throw new CliUserError({
      code: 'invalid_feature',
      message: '功能名称格式无效（仅允许小写字母、数字和连字符，不能以连字符开头或结尾）',
      input: { feature },
      retryable: false,
      suggestion: 'Use lowercase letters, numbers, and hyphens; do not start or end with a hyphen',
    });
  }
}

function parseArtifactInput(argv: string[]): {
  feature: string;
  artifact: string;
  template?: string;
} {
  const input: { feature: string; artifact: string; template?: string } = {
    feature: '',
    artifact: '',
  };
  const jsonInputArg = createCliContext(argv, { command: 'boss artifact prepare' }).values
    .jsonInput;
  const jsonInput = readJsonInput(jsonInputArg);
  if (jsonInput !== null) {
    if (!isJsonObject(jsonInput)) {
      throw new CliUserError({
        code: 'invalid_json_input',
        message: '--json-input for artifact prepare must be an object',
        input: { jsonInput },
        retryable: false,
        suggestion: 'Use fields: feature, artifact, template',
      });
    }
    if (typeof jsonInput.feature === 'string') input.feature = jsonInput.feature;
    if (typeof jsonInput.artifact === 'string') input.artifact = jsonInput.artifact;
    if (typeof jsonInput.template === 'string') input.template = jsonInput.template;
  }

  const positionals: string[] = [];
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
        suggestion: 'Run boss artifact prepare --describe to verify supported options',
      });
    }
    positionals.push(arg);
  }

  if (positionals[0]) input.feature = positionals[0];
  if (positionals[1]) input.artifact = positionals[1];
  if (positionals[2]) input.template = positionals[2];
  if (positionals.length > 3) {
    throw new CliUserError({
      code: 'extra_argument',
      message: `多余的参数: ${positionals[3]}`,
      input: { argument: positionals[3] },
      retryable: false,
      suggestion: 'Pass feature, artifact, and an optional template name',
    });
  }

  return input;
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss artifact prepare' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(artifactPrepareDescription),
      context,
      (data) => `${JSON.stringify(data, null, 2)}\n`,
    );
    return 0;
  }

  if (argv.includes('-h') || argv.includes('--help')) {
    showHelp();
    return 0;
  }

  const { feature, artifact, template: templateArg } = parseArtifactInput(argv);
  if (!feature || !artifact) {
    throw new CliUserError({
      code: 'missing_argument',
      message: '用法: boss artifact prepare <feature-name> <artifact-name> [template-name]',
      input: { feature, artifact },
      retryable: false,
      suggestion: 'Pass feature and artifact, or provide them with --json-input',
    });
  }

  validateFeatureName(feature);
  validateRelativeName(artifact, 'artifact');
  if (templateArg) validateRelativeName(templateArg, 'template');

  const targetDir = path.join(cwd, '.boss', feature);
  if (!fs.existsSync(targetDir)) {
    throw new CliUserError({
      code: 'feature_not_found',
      message: `目标目录不存在: .boss/${feature}，请先执行 boss project init ${feature}`,
      input: { feature },
      retryable: false,
      suggestion: `Run boss project init ${feature}`,
    });
  }

  const templateName = templateArg ?? `${artifact}.template`;
  validateRelativeName(templateName, 'template');
  const templatePath = resolveTemplate(cwd, templateName);
  const targetPath = path.join(targetDir, artifact);
  const templateRef = describeTemplate(cwd, templatePath);
  const payload = {
    actions: [
      {
        type: 'write_artifact',
        path: path.relative(cwd, targetPath),
        ...templateRef,
      },
    ],
    risk_tier: 'medium',
    requires_approval: false,
  };

  if (context.values.dryRun) {
    const action = payload.actions[0]!;
    writeOutput(
      payload,
      context,
      () =>
        `  [dry-run] write_artifact: ${action.path} <- ${action.template}\nDry-run complete. No files were modified.\n`,
    );
    return 0;
  }

  const content = fs.readFileSync(templatePath, 'utf8');
  fs.writeFileSync(targetPath, renderTemplate(content, feature) + '\n', 'utf8');
  writeOutput(
    {
      path: path.relative(cwd, targetPath),
      ...templateRef,
      written: true,
    },
    context,
    () =>
      `已按模板优先级准备产物骨架: ${path.relative(cwd, targetPath)} <- ${templateRef.template}（${templateRef.templateSource}）\n`,
  );
  return 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss artifact prepare',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
