import type { SummaryModel } from './summary-model.mts';

interface DiagnosticsEvent {
  type: string;
  timestamp: string;
}

interface DiagnosticsStageRef {
  id: number | string;
  name: string;
  status: string;
}

export interface DiagnosticsModel extends SummaryModel {
  currentStage?: DiagnosticsStageRef | null;
  readyArtifacts?: string[];
  activeAgents?: string[];
  recentFailures?: unknown[];
  recentEvents?: DiagnosticsEvent[];
  progressEvents?: DiagnosticsEvent[];
}

function escapeHtml(value: unknown): string {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderList<T>(items: T[] | undefined, renderItem: (item: T) => string): string {
  if (!Array.isArray(items) || items.length === 0) {
    return '<li class="muted">none</li>';
  }
  return items.map(renderItem).join('');
}

export function renderHtml(model: DiagnosticsModel): string {
  const stageCards = renderList(
    model.stages,
    (stage) => `
    <li class="card">
      <h3>Stage ${stage.stage}: ${escapeHtml(stage.name)}</h3>
      <p>Status: ${escapeHtml(stage.status)}</p>
      <p>Duration: ${stage.duration == null ? '&mdash;' : `${stage.duration}s`}</p>
      <p>Retries: ${stage.retryCount}</p>
    </li>
  `,
  );

  const artifactCards = renderList(
    model.stages.filter((stage) => stage.artifacts.length > 0),
    (stage) => `
    <li class="card">
      <h3>Stage ${stage.stage}</h3>
      <p>${escapeHtml(stage.name)}</p>
      <ul>${renderList(stage.artifacts, (artifact) => `<li>${escapeHtml(artifact)}</li>`)}</ul>
    </li>
  `,
  );

  const eventCards = renderList(
    model.recentEvents,
    (event) => `
    <li class="card">
      <strong>${escapeHtml(event.type)}</strong>
      <p>${escapeHtml(event.timestamp)}</p>
    </li>
  `,
  );

  const progressCards = renderList(
    model.progressEvents,
    (event) => `
    <li class="card">
      <strong>${escapeHtml(event.type)}</strong>
      <p>${escapeHtml(event.timestamp)}</p>
    </li>
  `,
  );

  const todoCards = renderList(
    model.derivedTodos,
    (todo) => `
    <li class="card">
      <strong>${escapeHtml(todo.title)}</strong>
      <p>${escapeHtml(todo.owner)} · ${escapeHtml(todo.status)}</p>
    </li>
  `,
  );

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Boss Diagnostics - ${escapeHtml(model.feature)}</title>
  <style>
    :root {
      --bg: #f5efe5;
      --panel: #fffaf2;
      --ink: #1e2a2f;
      --muted: #6a7478;
      --line: #d8c7aa;
      --accent: #9b4d2f;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Iowan Old Style", "Palatino Linotype", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, #fff9ee 0, #f5efe5 45%, #eadcc6 100%);
    }
    main { padding: 24px; }
    h1, h2, h3 { margin: 0 0 8px; }
    p { margin: 0 0 8px; }
    .hero {
      background: linear-gradient(135deg, rgba(155, 77, 47, 0.12), rgba(30, 42, 47, 0.04));
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 24px;
      margin-bottom: 18px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 16px;
      margin-bottom: 16px;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 18px;
      min-height: 220px;
      box-shadow: 0 8px 24px rgba(30, 42, 47, 0.05);
    }
    .card {
      list-style: none;
      padding: 12px;
      margin-bottom: 10px;
      background: rgba(255, 255, 255, 0.75);
      border: 1px solid rgba(216, 199, 170, 0.9);
      border-radius: 12px;
    }
    .metric-row {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin: 16px 0;
    }
    .metric {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px;
    }
    ul { padding: 0; margin: 0; }
    .muted { color: var(--muted); }
    .flow {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 18px;
    }
    @media (max-width: 900px) {
      .grid, .metric-row { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <h1>${escapeHtml(model.feature)}</h1>
      <p>Status: ${escapeHtml(model.status)}</p>
      <p>Current stage: ${escapeHtml(model.currentStage ? `${model.currentStage.id} (${model.currentStage.name}) ${model.currentStage.status}` : 'none')}</p>
      <p>Pack: ${escapeHtml(model.pack.name)}</p>
    </section>

    <section class="metric-row">
      <div class="metric"><h3>total duration</h3><p>${model.metrics.totalDuration == null ? '&mdash;' : `${model.metrics.totalDuration}s`}</p></div>
      <div class="metric"><h3>gate pass rate</h3><p>${model.metrics.gatePassRate == null ? '&mdash;' : `${model.metrics.gatePassRate}%`}</p></div>
      <div class="metric"><h3>agent outcomes</h3><p>${model.metrics.agentSuccessCount}/${model.metrics.agentFailureCount}</p></div>
      <div class="metric"><h3>plugin failures</h3><p>${model.metrics.pluginFailureCount}</p></div>
    </section>

    <section class="metric-row">
      <div class="metric"><h3>conversations</h3><p>${model.conversationMetrics.opened}/${model.conversationMetrics.resolved}</p></div>
      <div class="metric"><h3>todos</h3><p>${model.conversationMetrics.todos}</p></div>
      <div class="metric"><h3>huddles</h3><p>${model.conversationMetrics.huddles}</p></div>
      <div class="metric"><h3>unresolved</h3><p>${model.conversationMetrics.unresolved}</p></div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>stages</h2>
        <ul>${stageCards}</ul>
      </div>
      <div class="panel">
        <h2>artifacts</h2>
        <ul>${artifactCards}</ul>
      </div>
      <div class="panel">
        <h2>recent events</h2>
        <ul>${eventCards}</ul>
      </div>
    </section>

    <section class="flow">
      <h2>derived todos</h2>
      <ul>${todoCards}</ul>
    </section>

    <section class="flow">
      <h2>progress flow</h2>
      <ul>${progressCards}</ul>
    </section>
  </main>
</body>
</html>
`;
}
