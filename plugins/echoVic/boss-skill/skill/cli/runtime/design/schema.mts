export interface UiDesignFrame {
  id: string;
  type: string;
  name?: string;
  layout: 'vertical' | 'horizontal' | 'grid' | 'absolute';
  componentId?: string;
  children: UiDesignFrame[];
}

export interface UiDesignPage {
  id: string;
  name: string;
  route: string;
  viewport: { width: number; height: number };
  frames: UiDesignFrame[];
  states: string[];
}

export interface UiDesignComponent {
  id: string;
  name: string;
  type: string;
}

export interface UiDesignPrototypeLink {
  sourceId: string;
  targetPageId: string;
  interaction?: string;
}

export interface UiDesignArtifact {
  schemaVersion: string;
  artifact: 'ui-design';
  mode: 'wireframe' | 'hifi';
  feature: string;
  updatedAt: string;
  tokens: {
    colors: Record<string, unknown>;
    typography: Record<string, unknown>;
    spacing: Record<string, unknown>;
    radius: Record<string, unknown>;
  };
  pages: UiDesignPage[];
  components: UiDesignComponent[];
  prototype: {
    startPageId: string;
    links: UiDesignPrototypeLink[];
  };
  implementationHints: {
    preferredFramework: string;
    requiredComponents: string[];
    accessibilityNotes: string[];
  };
}

export interface UiDesignValidationResult {
  ok: boolean;
  errors: string[];
}

function isObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function hasKeys(value: Record<string, unknown>): boolean {
  return Object.keys(value).length > 0;
}

function isString(value: unknown): value is string {
  return typeof value === 'string' && value.length > 0;
}

function isNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function isPositiveNumber(value: unknown): value is number {
  return isNumber(value) && value > 0;
}

function hasDesignTokens(value: unknown): boolean {
  if (!isObject(value)) return false;
  return (
    isObject(value.colors) &&
    isObject(value.typography) &&
    isObject(value.spacing) &&
    isObject(value.radius)
  );
}

function collectFrameIds(frames: unknown, ids: string[], errors: string[]): void {
  if (!Array.isArray(frames)) {
    errors.push('page.frames must be an array');
    return;
  }

  for (const frame of frames) {
    if (!isObject(frame)) {
      errors.push('frame id is required');
      continue;
    }

    if (typeof frame.id !== 'string' || frame.id.length === 0) errors.push('frame id is required');
    if (typeof frame.id === 'string') ids.push(frame.id);
    if (!isString(frame.type)) errors.push('frame.type is required');
    if (
      frame.layout !== 'vertical' &&
      frame.layout !== 'horizontal' &&
      frame.layout !== 'grid' &&
      frame.layout !== 'absolute'
    ) {
      errors.push('frame.layout must be vertical, horizontal, grid, or absolute');
    }

    if (!Array.isArray(frame.children)) {
      errors.push('frame.children must be an array');
      continue;
    }
    collectFrameIds(frame.children, ids, errors);
  }
}

export function validateUiDesignArtifact(value: unknown): UiDesignValidationResult {
  const errors: string[] = [];
  if (!isObject(value)) return { ok: false, errors: ['artifact must be an object'] };

  const artifact = value as Partial<UiDesignArtifact>;
  if (!isString(artifact.schemaVersion)) errors.push('schemaVersion is required');
  if (artifact.artifact !== 'ui-design') errors.push('artifact must be ui-design');
  if (artifact.mode !== 'wireframe' && artifact.mode !== 'hifi') {
    errors.push('mode must be wireframe or hifi');
  }
  if (!isString(artifact.feature)) errors.push('feature is required');
  if (!isString(artifact.updatedAt)) errors.push('updatedAt is required');
  if (!hasDesignTokens(artifact.tokens)) {
    errors.push('tokens must define colors, typography, spacing, and radius objects');
  }
  if (!Array.isArray(artifact.pages) || artifact.pages.length === 0) {
    errors.push('pages must contain at least one page');
  }

  const pages = Array.isArray(artifact.pages) ? artifact.pages : [];
  const components = Array.isArray(artifact.components) ? artifact.components : [];
  const prototypeLinks = Array.isArray(artifact.prototype?.links) ? artifact.prototype.links : [];

  if (!Array.isArray(artifact.components)) {
    errors.push('components must be an array');
  }
  if (!isObject(artifact.prototype)) {
    errors.push('prototype must be an object');
    errors.push('prototype.startPageId is required');
  } else {
    if (!isString(artifact.prototype.startPageId)) errors.push('prototype.startPageId is required');
  }
  if (!Array.isArray(artifact.prototype?.links)) {
    errors.push('prototype.links must be an array');
  }
  if (!isObject(artifact.implementationHints)) {
    errors.push('implementationHints must be an object');
  } else {
    if (typeof artifact.implementationHints.preferredFramework !== 'string') {
      errors.push('implementationHints.preferredFramework must be a string');
    }
    if (!Array.isArray(artifact.implementationHints.requiredComponents)) {
      errors.push('implementationHints.requiredComponents must be an array');
    }
    if (!Array.isArray(artifact.implementationHints.accessibilityNotes)) {
      errors.push('implementationHints.accessibilityNotes must be an array');
    }
  }

  const pageIds = new Set<string>();
  const allIds: string[] = [];
  for (const page of pages) {
    if (!isObject(page)) {
      errors.push('page must be an object');
      continue;
    }
    if (!isString(page.id)) errors.push('page.id is required');
    if (!isString(page.name)) errors.push('page.name is required');
    if (typeof page.route !== 'string') errors.push('page.route is required');
    const viewport = page.viewport;
    if (!isObject(viewport) || !isPositiveNumber(viewport.width)) {
      errors.push('page.viewport.width must be a positive number');
    }
    if (!isObject(viewport) || !isPositiveNumber(viewport.height)) {
      errors.push('page.viewport.height must be a positive number');
    }
    if (!Array.isArray(page.states)) errors.push('page.states must be an array');
    if (typeof page.id === 'string') {
      pageIds.add(page.id);
      allIds.push(page.id);
    }
    collectFrameIds(page.frames, allIds, errors);
  }
  for (const component of components) {
    if (!isObject(component)) {
      errors.push('component must be an object');
      continue;
    }
    if (!isString(component.id)) errors.push('component.id is required');
    if (!isString(component.name)) errors.push('component.name is required');
    if (!isString(component.type)) errors.push('component.type is required');
    if (typeof component.id === 'string') allIds.push(component.id);
  }

  const seen = new Set<string>();
  for (const id of allIds.filter(Boolean)) {
    if (seen.has(id)) errors.push(`duplicate id: ${id}`);
    seen.add(id);
  }

  if (artifact.prototype?.startPageId && !pageIds.has(artifact.prototype.startPageId)) {
    errors.push('prototype.startPageId must reference an existing page id');
  }
  for (const [index, link] of prototypeLinks.entries()) {
    if (!isObject(link) || !isString(link.sourceId)) {
      errors.push(`prototype.links[${index}].sourceId is required`);
    }
    if (
      !isObject(link) ||
      typeof link.targetPageId !== 'string' ||
      !pageIds.has(link.targetPageId)
    ) {
      errors.push(`prototype.links[${index}].targetPageId must reference an existing page id`);
    }
  }

  if (artifact.mode === 'hifi') {
    for (const section of ['colors', 'typography', 'spacing', 'radius'] as const) {
      const tokens = artifact.tokens?.[section];
      if (!tokens || !hasKeys(tokens))
        errors.push(`hifi mode requires non-empty tokens.${section}`);
    }
  }

  return { ok: errors.length === 0, errors };
}
