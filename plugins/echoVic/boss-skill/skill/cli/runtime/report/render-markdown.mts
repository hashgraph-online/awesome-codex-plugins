import {
  ARTIFACT_LAYERS,
  type ArtifactLayerId,
  artifactLayer,
} from '../application/artifact-layers.mts';
import type { SummaryModel } from './summary-model.mts';

type SummaryGate = SummaryModel['qualityGates'][string];

function statusIcon(status: string): string {
  switch (status) {
    case 'completed':
      return '✅';
    case 'running':
      return '🔄';
    case 'failed':
      return '❌';
    case 'retrying':
      return '🔁';
    case 'skipped':
      return '⏭️';
    case 'pending':
      return '⏳';
    default:
      return '❓';
  }
}

function gateLabel(name: string): string {
  switch (name) {
    case 'gate0':
      return 'Gate 0 (代码质量)';
    case 'gate1':
      return 'Gate 1 (测试)';
    case 'gate2':
      return 'Gate 2 (性能)';
    default:
      return name;
  }
}

function gateChecks(gate: SummaryGate): unknown[] {
  return Array.isArray(gate.checks) ? gate.checks : [];
}

function gatePassedText(gate: SummaryGate): string {
  return gate.passed == null ? '—' : String(gate.passed);
}

function failedCheckCount(checks: unknown[]): number {
  return checks.filter(
    (check): check is { passed: false } =>
      typeof check === 'object' && check !== null && 'passed' in check && check.passed === false,
  ).length;
}

function gateTableRow(name: string, gate: SummaryGate, includeFailedChecks = false): string {
  const checks = gateChecks(gate);
  const baseColumns = [
    gateLabel(name),
    `${statusIcon(gate.status)} ${gate.status}`,
    gatePassedText(gate),
    String(checks.length),
  ];
  const columns = includeFailedChecks
    ? [...baseColumns, String(failedCheckCount(checks)), gate.executedAt || '—']
    : [...baseColumns, gate.executedAt || '—'];
  return `| ${columns.join(' | ')} |`;
}

export function renderMarkdown(model: SummaryModel): string {
  const completedStages = model.stages.filter(
    (stage) => stage.status === 'completed' || stage.status === 'skipped',
  ).length;
  const lines = [
    '# 流水线执行报告',
    '',
    '## 摘要',
    '',
    `- **流水线状态**：${statusIcon(model.status)} ${model.status}`,
    `- **功能名称**：${model.feature}`,
    `- **Pipeline Pack**：${model.pack.name}`,
    `- **阶段进度**：${completedStages} / ${model.stages.length} 已完成`,
    `- **门禁通过率**：${model.metrics.gatePassRate ?? 'N/A'}%`,
    `- **总重试次数**：${model.metrics.retryTotal ?? 0}`,
    `- **Agent 成功/失败**：${model.metrics.agentSuccessCount ?? 0} / ${model.metrics.agentFailureCount ?? 0}`,
    `- **平均阶段重试**：${model.metrics.meanRetriesPerStage ?? 0}`,
    `- **修订循环次数**：${model.metrics.revisionLoopCount ?? 0}`,
    `- **插件失败次数**：${model.metrics.pluginFailureCount ?? 0}`,
    `- **Conversation 打开/收敛/落地**：${model.conversationMetrics.opened} / ${model.conversationMetrics.resolved} / ${model.conversationMetrics.todos}`,
    `- **Conversation huddle / unresolved**：${model.conversationMetrics.huddles} / ${model.conversationMetrics.unresolved}`,
    '',
    '---',
    '',
    '## 执行协作',
    '',
    '| Todo | Owner | Status | Title |',
    '|------|-------|--------|-------|',
  ];

  for (const todo of model.derivedTodos) {
    lines.push(`| ${todo.id} | ${todo.owner} | ${todo.status} | ${todo.title} |`);
  }

  lines.push(
    '',
    '## 证据链',
    '',
    '### 核心用户路径',
    '',
    '- 详见 `qa-report.md`：核心路径必须包含真实浏览器、真实 API、真实 schema 的证据。',
    '- Mock 可辅助定位，但关键路径不能只凭 Mock 通过；缺少真实路径证据时必须标记为未验证。',
    '',
    '### Gate 命令与检查项',
    '',
    '- 当前运行时摘要展示 gate 检查结果与执行时间；精确命令请在可用时查阅 gate output 或 `qa-report.md`。',
    '',
    '| 门禁 | 状态 | 通过 | 检查项 | 失败项 | 执行时间 |',
    '|------|------|------|--------|--------|----------|',
  );

  for (const [name, gate] of Object.entries(model.qualityGates || {})) {
    lines.push(gateTableRow(name, gate, true));
  }

  lines.push(
    '',
    '### 红测转绿证据',
    '',
    '- 详见 `tasks.md`：Evidence Wave 计划、红测命令、绿门禁和 Stop Condition。',
    '- 详见 `qa-report.md`：red-to-green 证据、复跑结果和未覆盖路径说明。',
    '',
    '### Contract Matrix 状态',
    '',
    '- 详见 `tasks.md`：Contract Matrix 对齐 UI / Copy、Client Payload、Server Schema、Persistence、Business Rule 与 Test Evidence。',
    '- 详见 `qa-report.md`：Contract Matrix 验证结果、真实 payload、服务端响应和 schema 证据。',
    '',
    '### 已知失败与遗留风险',
    '',
    `- Gate 通过率：${model.metrics.gatePassRate ?? 'N/A'}%`,
    `- Agent 失败数：${model.metrics.agentFailureCount ?? 0}`,
    `- 插件失败数：${model.metrics.pluginFailureCount ?? 0}`,
    '- 详见 `qa-report.md`：残留风险、未验证核心路径与后续处理建议。',
    '',
    '---',
    '',
    '## 阶段详情',
    '',
    '| 阶段 | 名称 | 状态 | 耗时 | 重试 | 产物数 |',
    '|------|------|------|------|------|--------|',
  );

  for (const stage of model.stages) {
    lines.push(
      `| ${stage.stage} | ${stage.name} | ${statusIcon(stage.status)} ${stage.status} | ${stage.duration == null ? '—' : `${stage.duration}s`} | ${stage.retryCount} | ${stage.artifacts.length} |`,
    );
  }

  lines.push(
    '',
    '## 质量门禁',
    '',
    '| 门禁 | 状态 | 通过 | 检查项数 | 执行时间 |',
    '|------|------|------|----------|----------|',
  );
  for (const [name, gate] of Object.entries(model.qualityGates || {})) {
    lines.push(gateTableRow(name, gate));
  }

  // 产物按生命周期分层：产品资产跨迭代维护，本轮记录下一轮就会被取代，
  // 派生视图可随时重建。平铺成一张清单时，第二次迭代的人分不清哪些还作数。
  lines.push('', '## 产物清单', '');
  const byLayer = new Map<ArtifactLayerId, string[]>();
  for (const stage of model.stages) {
    for (const artifact of stage.artifacts) {
      const layer = artifactLayer(artifact);
      const bucket = byLayer.get(layer) ?? [];
      if (!bucket.includes(artifact)) bucket.push(artifact);
      byLayer.set(layer, bucket);
    }
  }
  for (const layer of ARTIFACT_LAYERS) {
    const artifacts = byLayer.get(layer.id);
    if (!artifacts || artifacts.length === 0) continue;
    lines.push(`### ${layer.title}`, '', `> ${layer.hint}`, '');
    for (const artifact of artifacts.sort()) {
      lines.push(`- \`${artifact}\``);
    }
    lines.push('');
  }

  // 返工与人工介入：事件流里一直有，此前从未出现在报告里。对一份以可审计性为卖点的
  // 产物，「谁要求谁返工、人在哪几步介入过」比任何聚合指标都更能说明这次跑了什么。
  if (model.revisionRequests.length > 0) {
    lines.push(
      '',
      '## 返工记录',
      '',
      '| 发起方 | 接收方 | 产物 | 优先级 | 原因 | 时间 |',
      '|--------|--------|------|--------|------|------|',
    );
    for (const request of model.revisionRequests) {
      lines.push(
        `| ${request.from} | ${request.to} | \`${request.artifact}\` | ${request.priority} | ${request.reason} | ${request.timestamp} |`,
      );
    }
  }

  if (model.humanInterventions.length > 0) {
    lines.push(
      '',
      '## 人工介入',
      '',
      '| 类型 | 选择 | Agent | 阶段 | 时间 |',
      '|------|------|-------|------|------|',
    );
    for (const entry of model.humanInterventions) {
      lines.push(
        `| ${entry.choiceType} | ${entry.selected} | ${entry.agent ?? '-'} | ${entry.stage ?? '-'} | ${entry.timestamp} |`,
      );
    }
  }

  return `${lines.join('\n')}\n`;
}
