import type {
  UiDesignArtifact,
  UiDesignFrame,
  UiDesignPage,
  UiDesignValidationResult,
} from './schema.mts';

const DEFAULT_VIEWPORT_WIDTH = 1440;
const DEFAULT_VIEWPORT_HEIGHT = 960;

function escapeHtml(value: unknown): string {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function escapeAttribute(value: unknown): string {
  return escapeHtml(value);
}

function coerceViewportDimension(value: unknown, fallback: number): number {
  return typeof value === 'number' && Number.isFinite(value) && value > 0
    ? Math.round(value)
    : fallback;
}

function buildPrototypeTargets(design: UiDesignArtifact): Map<string, string> {
  const targets = new Map<string, string>();
  for (const link of design.prototype.links) {
    targets.set(link.sourceId, link.targetPageId);
  }
  return targets;
}

function renderFrame(
  frame: UiDesignFrame,
  prototypeTargets: Map<string, string>,
  depth = 0,
): string {
  const targetPageId = prototypeTargets.get(frame.id);
  const targetAttribute = targetPageId
    ? ` data-target-page="${escapeAttribute(targetPageId)}"`
    : '';
  const childFrames = frame.children
    .map((child) => renderFrame(child, prototypeTargets, depth + 1))
    .join('');
  const displayName = frame.name || frame.type;
  const depthStyle = `--depth:${depth}`;

  return `
    <section class="frame frame-${escapeAttribute(frame.type)} layout-${escapeAttribute(frame.layout)}" data-frame-id="${escapeAttribute(frame.id)}" data-frame-type="${escapeAttribute(frame.type)}" style="${depthStyle}"${targetAttribute}>
      <div class="frame-label">
        <span>${escapeHtml(displayName)}</span>
        <small>${escapeHtml(frame.type)}</small>
      </div>
      ${childFrames ? `<div class="frame-children">${childFrames}</div>` : ''}
    </section>
  `;
}

function renderPageNav(pages: UiDesignPage[], activePageId: string): string {
  return pages
    .map((page) => {
      const activeClass = page.id === activePageId ? ' is-active' : '';
      return `<button class="page-tab${activeClass}" type="button" data-page-id="${escapeAttribute(page.id)}">${escapeHtml(page.name)}</button>`;
    })
    .join('');
}

function renderPage(
  page: UiDesignPage,
  prototypeTargets: Map<string, string>,
  isActive: boolean,
): string {
  const activeClass = isActive ? ' is-active' : '';
  const frameHtml = page.frames.map((frame) => renderFrame(frame, prototypeTargets)).join('');
  const viewportWidth = coerceViewportDimension(page.viewport.width, DEFAULT_VIEWPORT_WIDTH);
  const viewportHeight = coerceViewportDimension(page.viewport.height, DEFAULT_VIEWPORT_HEIGHT);

  return `
    <article class="page-canvas${activeClass}" data-page="${escapeAttribute(page.id)}" aria-label="${escapeAttribute(page.name)}">
      <header class="canvas-header">
        <div>
          <p>${escapeHtml(page.route)}</p>
          <h2>${escapeHtml(page.name)}</h2>
        </div>
        <span>${viewportWidth} x ${viewportHeight}</span>
      </header>
      <main class="viewport-shell" style="--viewport-width:${viewportWidth}px;--viewport-height:${viewportHeight}px">
        ${frameHtml || '<p class="empty-state">No frames defined for this page.</p>'}
      </main>
    </article>
  `;
}

function renderValidationErrors(errors: string[]): string {
  const errorItems = errors.map((error) => `<li>${escapeHtml(error)}</li>`).join('');

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>UI Design Preview Error</title>
  <style>
    body { margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f6f7f9; color: #17202a; }
    main { max-width: 840px; margin: 12vh auto; padding: 32px; background: #fff; border: 1px solid #d9dee7; border-radius: 8px; box-shadow: 0 16px 40px rgba(23, 32, 42, 0.08); }
    h1 { margin: 0 0 12px; font-size: 24px; }
    p { margin: 0 0 20px; color: #536170; }
    li { margin: 8px 0; }
  </style>
</head>
<body>
  <main>
    <h1>UI Design JSON validation failed</h1>
    <p>The preview could not render the artifact because the schema check reported errors.</p>
    <ul>${errorItems}</ul>
  </main>
</body>
</html>`;
}

export function renderUiDesignHtml(
  design: UiDesignArtifact,
  validation: UiDesignValidationResult,
): string {
  if (!validation.ok) return renderValidationErrors(validation.errors);

  const startPage =
    design.pages.find((page) => page.id === design.prototype.startPageId) ?? design.pages[0];
  if (!startPage) return renderValidationErrors(['pages must contain at least one page']);

  const prototypeTargets = buildPrototypeTargets(design);
  const pageNav = renderPageNav(design.pages, startPage.id);
  const pages = design.pages
    .map((page) => renderPage(page, prototypeTargets, page.id === startPage.id))
    .join('');
  const components = design.components
    .map(
      (component) =>
        `<li><strong>${escapeHtml(component.name)}</strong><span>${escapeHtml(component.type)}</span></li>`,
    )
    .join('');
  const accessibilityNotes = design.implementationHints.accessibilityNotes
    .map((note) => `<li>${escapeHtml(note)}</li>`)
    .join('');

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(design.feature)} UI Design Preview</title>
  <style>
    :root { color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; background: #edf1f5; color: #18212f; }
    button { font: inherit; }
    .app-shell { display: grid; grid-template-columns: 248px minmax(0, 1fr) 300px; min-height: 100vh; }
    .sidebar, .inspector { background: #fbfcfe; border-color: #d7dde7; padding: 20px; }
    .sidebar { border-right: 1px solid #d7dde7; }
    .inspector { border-left: 1px solid #d7dde7; }
    .brand h1 { margin: 0; font-size: 18px; line-height: 1.3; }
    .brand p, .canvas-header p, .meta-label { margin: 4px 0 0; color: #617083; font-size: 13px; }
    .page-list { display: grid; gap: 8px; margin-top: 24px; }
    .page-tab, .viewport-control { border: 1px solid #cbd3df; background: #fff; color: #18212f; border-radius: 6px; padding: 10px 12px; cursor: pointer; text-align: left; }
    .page-tab.is-active, .viewport-control.is-active { border-color: #1f6feb; box-shadow: inset 0 0 0 1px #1f6feb; }
    .workspace { display: grid; grid-template-rows: auto minmax(0, 1fr); min-width: 0; }
    .toolbar { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 14px 20px; background: #fff; border-bottom: 1px solid #d7dde7; }
    .viewport-controls { display: flex; gap: 8px; }
    .viewport-control { text-align: center; min-width: 82px; }
    .canvas-scroll { overflow: auto; padding: 28px; }
    .canvas-scroll.viewport-desktop .page-canvas { max-width: min(100%, 1120px); }
    .canvas-scroll.viewport-tablet .page-canvas { max-width: min(100%, 820px); }
    .canvas-scroll.viewport-mobile .page-canvas { max-width: min(100%, 390px); }
    .page-canvas { display: none; margin: 0 auto; transition: max-width 120ms ease; }
    .page-canvas.is-active { display: block; }
    .canvas-header { display: flex; justify-content: space-between; align-items: end; gap: 16px; margin-bottom: 14px; }
    .canvas-header h2 { margin: 0; font-size: 22px; }
    .canvas-header span { color: #617083; font-size: 13px; }
    .viewport-shell { min-height: 560px; background: #fff; border: 1px solid #cbd3df; border-radius: 8px; padding: 18px; box-shadow: 0 20px 50px rgba(24, 33, 47, 0.10); }
    .frame { border: 1px solid #b9c4d2; border-radius: 6px; background: rgba(255, 255, 255, 0.86); margin: 10px 0; padding: 12px; box-shadow: inset 3px 0 0 hsl(calc(210 + var(--depth) * 22), 58%, 54%); }
    .frame[data-target-page] { border-color: #1f6feb; cursor: pointer; }
    .frame-label { display: flex; align-items: center; justify-content: space-between; gap: 12px; color: #1d2735; font-weight: 700; }
    .frame-label small { color: #617083; font-size: 12px; font-weight: 500; text-transform: uppercase; }
    .frame-children { display: grid; gap: 10px; margin-top: 12px; }
    .layout-horizontal > .frame-children { grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); }
    .layout-grid > .frame-children { grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }
    .frame-button { background: #f2f7ff; }
    .inspector h2 { margin: 0 0 16px; font-size: 16px; }
    .inspector-section { border-top: 1px solid #d7dde7; padding: 16px 0; }
    .inspector-section:first-of-type { border-top: 0; padding-top: 0; }
    .inspector ul { list-style: none; padding: 0; margin: 0; display: grid; gap: 10px; }
    .inspector li { display: flex; justify-content: space-between; gap: 12px; color: #3d4a5c; font-size: 13px; }
    .inspector li span { color: #617083; }
    .empty-state { margin: 0; color: #617083; }
    @media (max-width: 980px) {
      .app-shell { grid-template-columns: 1fr; }
      .sidebar, .inspector { border: 0; border-bottom: 1px solid #d7dde7; }
      .toolbar { align-items: stretch; flex-direction: column; }
      .viewport-controls { flex-wrap: wrap; }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <h1>${escapeHtml(design.feature)}</h1>
        <p>${escapeHtml(design.mode)} preview</p>
      </div>
      <nav class="page-list" aria-label="Pages">${pageNav}</nav>
    </aside>
    <section class="workspace">
      <header class="toolbar">
        <div>
          <strong>Prototype</strong>
          <p class="meta-label">Updated ${escapeHtml(design.updatedAt)}</p>
        </div>
        <div class="viewport-controls" aria-label="Viewport presets">
          <button class="viewport-control is-active" type="button" data-viewport="desktop">Desktop</button>
          <button class="viewport-control" type="button" data-viewport="tablet">Tablet</button>
          <button class="viewport-control" type="button" data-viewport="mobile">Mobile</button>
        </div>
      </header>
      <div class="canvas-scroll viewport-desktop" data-current-viewport="desktop">${pages}</div>
    </section>
    <aside class="inspector">
      <h2>Inspector</h2>
      <section class="inspector-section">
        <p class="meta-label">Framework</p>
        <strong>${escapeHtml(design.implementationHints.preferredFramework)}</strong>
      </section>
      <section class="inspector-section">
        <p class="meta-label">Components</p>
        <ul>${components || '<li>No components defined</li>'}</ul>
      </section>
      <section class="inspector-section">
        <p class="meta-label">Accessibility</p>
        <ul>${accessibilityNotes || '<li>No accessibility notes</li>'}</ul>
      </section>
    </aside>
  </div>
  <script>
    function switchPage(pageId) {
      document.querySelectorAll('.page-tab').forEach(function (tab) {
        tab.classList.toggle('is-active', tab.dataset.pageId === pageId);
      });
      document.querySelectorAll('.page-canvas').forEach(function (page) {
        page.classList.toggle('is-active', page.dataset.page === pageId);
      });
    }

    function switchViewport(viewport) {
      var canvas = document.querySelector('.canvas-scroll');
      if (!canvas) return;
      canvas.classList.remove('viewport-desktop', 'viewport-tablet', 'viewport-mobile');
      canvas.classList.add('viewport-' + viewport);
      canvas.dataset.currentViewport = viewport;
      document.querySelectorAll('.viewport-control').forEach(function (control) {
        control.classList.toggle('is-active', control.dataset.viewport === viewport);
      });
    }

    document.querySelectorAll('.page-tab').forEach(function (tab) {
      tab.addEventListener('click', function () {
        if (tab.dataset.pageId) switchPage(tab.dataset.pageId);
      });
    });

    document.querySelectorAll('[data-target-page]').forEach(function (frame) {
      frame.addEventListener('click', function (event) {
        event.stopPropagation();
        if (frame.dataset.targetPage) switchPage(frame.dataset.targetPage);
      });
    });

    document.querySelectorAll('.viewport-control').forEach(function (control) {
      control.addEventListener('click', function () {
        if (control.dataset.viewport) switchViewport(control.dataset.viewport);
      });
    });
  </script>
</body>
</html>`;
}
