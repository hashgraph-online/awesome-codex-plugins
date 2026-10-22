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
  writeOutput,
} from '../../cli/contract.mts';
import { commandDescriptions } from '../../cli/registry.mts';
import { skillRootFromImportMeta } from '../../infrastructure/paths.mts';
import { initPipeline } from '../../runtime/application/pipeline.mts';

const SKILL_ROOT = skillRootFromImportMeta(import.meta.url);
const DEFAULT_TEMPLATE_DIR = path.join(SKILL_ROOT, 'templates');
const PROJECT_TEMPLATE_DIR = path.join('.boss', 'templates');
const projectInitDescription = commandDescriptions['boss project init']!;

const PLACEHOLDERS: Array<{ file: string; title: string; infoTitle: string; agent: string }> = [
  { file: 'prd.md', title: '产品需求文档 (PRD)', infoTitle: '文档信息', agent: 'PM Agent' },
  {
    file: 'architecture.md',
    title: '系统架构文档',
    infoTitle: '文档信息',
    agent: 'Architect Agent',
  },
  {
    file: 'ui-spec.md',
    title: 'UI/UX 规范文档',
    infoTitle: '文档信息',
    agent: 'UI Designer Agent',
  },
  {
    file: 'ui-design.json',
    title: 'UI Design JSON',
    infoTitle: 'Artifact Info',
    agent: 'UI Designer Agent',
  },
  {
    file: 'tech-review.md',
    title: '技术评审报告',
    infoTitle: '文档信息',
    agent: 'Tech Lead Agent',
  },
  {
    file: 'tasks.md',
    title: '开发任务规格文档',
    infoTitle: '文档信息',
    agent: 'Scrum Master Agent',
  },
  { file: 'qa-report.md', title: 'QA 测试报告', infoTitle: '报告信息', agent: 'QA Agent' },
  { file: 'deploy-report.md', title: '部署报告', infoTitle: '报告信息', agent: 'DevOps Agent' },
];

function showHelp(): void {
  process.stdout.write(
    [
      'Boss Mode - 项目初始化',
      '',
      '用法: boss project init <feature-name> [options]',
      '',
      '选项:',
      '  -h, --help      显示帮助信息',
      '  -t, --template  初始化项目级模板目录（.boss/templates）',
      '  -f, --force     强制覆盖已存在的目录',
      '',
    ].join('\n'),
  );
}

function validateFeatureName(feature: string): void {
  if (!feature) {
    throw new CliUserError({
      code: 'missing_feature',
      message: '请提供功能名称',
      input: { feature },
      retryable: false,
      suggestion: 'Pass a feature name, or provide {"feature":"name"} with --json-input',
    });
  }
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

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

function writePlaceholder(
  targetDir: string,
  feature: string,
  date: string,
  item: (typeof PLACEHOLDERS)[number],
): void {
  if (item.file.endsWith('.json')) {
    fs.writeFileSync(
      path.join(targetDir, item.file),
      `${JSON.stringify(
        {
          schemaVersion: '1.0.0',
          artifact: 'ui-design',
          mode: 'wireframe',
          feature,
          updatedAt: `${date}T00:00:00Z`,
          tokens: { colors: {}, typography: {}, spacing: {}, radius: {} },
          pages: [
            {
              id: 'main',
              name: feature,
              route: '/',
              viewport: { width: 1440, height: 960 },
              frames: [
                {
                  id: 'main-page',
                  type: 'page',
                  name: feature,
                  layout: 'vertical',
                  children: [],
                },
              ],
              states: [],
            },
          ],
          components: [],
          prototype: { startPageId: 'main', links: [] },
          implementationHints: {
            preferredFramework: '',
            requiredComponents: [],
            accessibilityNotes: [],
          },
        },
        null,
        2,
      )}\n`,
      'utf8',
    );
    return;
  }

  const content = [
    `# ${item.title}`,
    '',
    `## ${item.infoTitle}`,
    `- **功能名称**：${feature}`,
    `- **创建日期**：${date}`,
    '- **状态**：待填充',
    '',
    '---',
    '',
    `> 此文件将由 ${item.agent} 自动填充`,
    '',
  ].join('\n');
  fs.writeFileSync(path.join(targetDir, item.file), content, 'utf8');
}

function copyTemplates(cwd: string, force: boolean): void {
  if (!fs.existsSync(DEFAULT_TEMPLATE_DIR)) {
    throw new CliUserError({
      code: 'template_dir_missing',
      message: `未找到内置模板目录: ${DEFAULT_TEMPLATE_DIR}`,
      input: { path: DEFAULT_TEMPLATE_DIR },
      retryable: false,
      suggestion: 'Rebuild or reinstall boss-skill so bundled templates are present',
    });
  }

  const projectTemplateDir = path.join(cwd, PROJECT_TEMPLATE_DIR);
  if (fs.existsSync(projectTemplateDir)) {
    if (!force) {
      throw new CliUserError({
        code: 'template_dir_exists',
        message: `模板目录已存在: '${PROJECT_TEMPLATE_DIR}'. 为避免覆盖，已停止初始化。`,
        input: { path: PROJECT_TEMPLATE_DIR },
        retryable: false,
        suggestion: 'Use --force after reviewing --dry-run output',
      });
    }
    fs.rmSync(projectTemplateDir, { recursive: true, force: true });
  }

  fs.mkdirSync(projectTemplateDir, { recursive: true });
  for (const file of fs
    .readdirSync(DEFAULT_TEMPLATE_DIR)
    .filter((name) => name.endsWith('.template'))
    .sort()) {
    fs.copyFileSync(path.join(DEFAULT_TEMPLATE_DIR, file), path.join(projectTemplateDir, file));
  }

  fs.writeFileSync(
    path.join(projectTemplateDir, 'README.md'),
    [
      '# Boss 项目模板说明',
      '',
      '此目录中的模板会覆盖 Skill 内置模板。',
      '',
      '模板查找优先级：',
      '1. `.boss/templates/<name>.template`',
      '2. Skill 内置 `templates/<name>.template`',
      '',
      '说明：',
      '- `boss project init` 只负责初始化轻量占位文件',
      '- Boss 在真正生成某个产物前，会调用 `boss artifact prepare` 按相同优先级准备当前文档骨架',
      '',
    ].join('\n'),
    'utf8',
  );
}

function readProjectPackageJson(cwd: string): Record<string, unknown> | null {
  const packageJsonPath = path.join(cwd, 'package.json');
  if (!fs.existsSync(packageJsonPath)) return null;
  try {
    return JSON.parse(fs.readFileSync(packageJsonPath, 'utf8')) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function projectDependencyVersion(pkg: Record<string, unknown>, name: string): string {
  const dependencyGroups = [
    'dependencies',
    'devDependencies',
    'peerDependencies',
    'optionalDependencies',
  ];
  for (const groupName of dependencyGroups) {
    const group = pkg[groupName];
    if (group && typeof group === 'object' && !Array.isArray(group)) {
      const version = (group as Record<string, unknown>)[name];
      if (typeof version === 'string') return version;
    }
  }
  return '';
}

function isTailwindV4Version(version: string): boolean {
  const match = version.match(/\d+/);
  return match ? Number(match[0]) >= 4 : false;
}

function cssUsesTailwind(content: string): boolean {
  return (
    /@import\s+["']tailwindcss["']/.test(content) ||
    /@tailwind\s+(base|components|utilities)/.test(content)
  );
}

function isTailwindV4Project(cwd: string, cssFiles: string[]): boolean {
  const pkg = readProjectPackageJson(cwd);
  if (pkg && isTailwindV4Version(projectDependencyVersion(pkg, 'tailwindcss'))) return true;
  return cssFiles.some((file) =>
    /@import\s+["']tailwindcss["']/.test(fs.readFileSync(file, 'utf8')),
  );
}

function findTailwindCssFiles(cwd: string): string[] {
  const candidates = [
    'app/globals.css',
    'src/app/globals.css',
    'styles/globals.css',
    'src/styles/globals.css',
    'src/index.css',
    'src/main.css',
    'app.css',
    'src/app.css',
  ].map((name) => path.join(cwd, name));

  const found = candidates.filter(
    (file) => fs.existsSync(file) && cssUsesTailwind(fs.readFileSync(file, 'utf8')),
  );
  if (found.length > 0) return found;

  const ignoredDirs = new Set(['.boss', '.git', 'node_modules', 'dist', 'build', 'coverage']);
  const results: string[] = [];
  function walk(dir: string): void {
    if (results.length >= 5) return;
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (results.length >= 5) return;
      if (entry.isDirectory()) {
        if (!ignoredDirs.has(entry.name)) walk(path.join(dir, entry.name));
        continue;
      }
      if (!entry.name.endsWith('.css')) continue;
      const file = path.join(dir, entry.name);
      if (cssUsesTailwind(fs.readFileSync(file, 'utf8'))) results.push(file);
    }
  }
  walk(cwd);
  return results;
}

function posixRelative(fromDir: string, toPath: string): string {
  const relativePath = path.relative(fromDir, toPath).split(path.sep).join('/');
  return relativePath.startsWith('.') ? relativePath : `./${relativePath}`;
}

function ensureBossArtifactsExcludedFromSourceScanners(cwd: string): string[] {
  const cssFiles = findTailwindCssFiles(cwd);
  if (cssFiles.length === 0 || !isTailwindV4Project(cwd, cssFiles)) return [];

  const updated: string[] = [];
  const bossDir = path.join(cwd, '.boss');
  for (const cssFile of cssFiles) {
    const content = fs.readFileSync(cssFile, 'utf8');
    if (/@source\s+not\s+["'][^"']*\.boss\/?["']/.test(content)) continue;

    const bossSourcePath = posixRelative(path.dirname(cssFile), bossDir);
    const addition = [
      '',
      '/* Boss orchestration artifacts are not application source. */',
      `@source not "${bossSourcePath}";`,
      '',
    ].join('\n');
    fs.writeFileSync(cssFile, `${content.replace(/\s*$/, '\n')}${addition}`, 'utf8');
    updated.push(path.relative(cwd, cssFile));
  }
  return updated;
}

interface ProjectInitInput {
  feature: string;
  template: boolean;
  force: boolean;
}

function isJsonObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function parseProjectInitInput(argv: string[]): ProjectInitInput {
  const input: ProjectInitInput = { feature: '', template: false, force: false };
  const jsonInputArg = createCliContext(argv, { command: 'boss project init' }).values.jsonInput;
  const jsonInput = readJsonInput(jsonInputArg);
  if (jsonInput !== null) {
    if (!isJsonObject(jsonInput)) {
      throw new CliUserError({
        code: 'invalid_json_input',
        message: '--json-input for project init must be an object',
        input: { jsonInput },
        retryable: false,
        suggestion: 'Use fields: feature, template, force',
      });
    }
    if (typeof jsonInput.feature === 'string') input.feature = jsonInput.feature;
    if (typeof jsonInput.template === 'boolean') input.template = jsonInput.template;
    if (typeof jsonInput.force === 'boolean') input.force = jsonInput.force;
  }

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
    if (arg === '-f' || arg === '--force') {
      input.force = true;
    } else if (arg === '-t' || arg === '--template') {
      input.template = true;
    } else if (arg.startsWith('-')) {
      throw new CliUserError({
        code: 'unknown_option',
        message: `未知选项: ${arg}`,
        input: { option: arg },
        retryable: false,
        suggestion: 'Run boss project init --describe to verify supported options',
      });
    } else if (!input.feature) {
      input.feature = arg;
    } else {
      throw new CliUserError({
        code: 'extra_argument',
        message: `多余的参数: ${arg}`,
        input: { argument: arg },
        retryable: false,
        suggestion: 'Pass only one feature name',
      });
    }
  }

  return input;
}

function buildProjectInitPlan(
  feature: string,
  initTemplates: boolean,
  force: boolean,
): {
  actions: Array<{ type: string; path: string; overwrite: boolean }>;
  risk_tier: 'medium' | 'high';
  requires_approval: boolean;
} {
  const actions = [
    {
      type: 'create_feature_workspace',
      path: path.join('.boss', feature),
      overwrite: force,
    },
  ];
  if (initTemplates) {
    actions.push({
      type: 'copy_project_templates',
      path: PROJECT_TEMPLATE_DIR,
      overwrite: force,
    });
  }
  return {
    actions,
    risk_tier: force ? 'high' : 'medium',
    requires_approval: force,
  };
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss project init' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(projectInitDescription),
      context,
      (data) => `${JSON.stringify(data, null, 2)}\n`,
    );
    return 0;
  }

  if (argv.includes('-h') || argv.includes('--help')) {
    showHelp();
    return 0;
  }

  const { feature, force, template: initTemplates } = parseProjectInitInput(argv);

  validateFeatureName(feature);
  const plan = buildProjectInitPlan(feature, initTemplates, force);

  if (context.values.dryRun) {
    writeOutput(plan, context, () => {
      const lines = plan.actions.map((action) => `  [dry-run] ${action.type}: ${action.path}`);
      return `${lines.join('\n')}\nDry-run complete. No files were modified.\n`;
    });
    return 0;
  }

  const targetDir = path.join(cwd, '.boss', feature);
  const relativeTarget = path.join('.boss', feature);

  if (initTemplates) {
    copyTemplates(cwd, force);
    if (!context.useJson) {
      process.stdout.write(`模板目录：\n  ${PROJECT_TEMPLATE_DIR}/\n`);
    }
  }

  const skipFeatureBootstrap = fs.existsSync(targetDir) && initTemplates && !force;
  if (fs.existsSync(targetDir) && !skipFeatureBootstrap) {
    if (!force) {
      throw new CliUserError({
        code: 'feature_dir_exists',
        message: `目录已存在: ${relativeTarget}（使用 --force 覆盖）`,
        input: { path: relativeTarget },
        retryable: false,
        suggestion: 'Use --force after reviewing --dry-run output',
      });
    }
    fs.rmSync(targetDir, { recursive: true, force: true });
  }

  if (!skipFeatureBootstrap) {
    fs.mkdirSync(path.join(targetDir, '.meta'), { recursive: true });
    const date = today();
    for (const item of PLACEHOLDERS) {
      writePlaceholder(targetDir, feature, date, item);
    }
    initPipeline(feature, { cwd });
    const sourceIsolationPaths = ensureBossArtifactsExcludedFromSourceScanners(cwd);
    writeOutput(
      {
        feature,
        path: relativeTarget,
        templatesPath: initTemplates ? PROJECT_TEMPLATE_DIR : undefined,
        sourceIsolationPaths,
        created: true,
        skipped: false,
      },
      context,
      () => `Boss Mode 项目目录初始化完成: ${relativeTarget}\n`,
    );
  } else {
    const sourceIsolationPaths = ensureBossArtifactsExcludedFromSourceScanners(cwd);
    writeOutput(
      {
        feature,
        path: relativeTarget,
        templatesPath: initTemplates ? PROJECT_TEMPLATE_DIR : undefined,
        sourceIsolationPaths,
        created: false,
        skipped: true,
      },
      context,
      () => `跳过 feature 初始化，继续保留现有目录内容: ${relativeTarget}\n`,
    );
  }

  if (!context.useJson) {
    process.stdout.write(
      initTemplates
        ? '下一步：先修改 .boss/templates/ 中的模板，再运行 /boss 开始开发流程\n'
        : '下一步：运行 /boss 开始开发流程\n',
    );
  }
  return 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss project init',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
