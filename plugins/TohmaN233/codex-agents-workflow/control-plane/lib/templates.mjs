import { ALLOWED_TEMPLATE_FIELDS } from './config.mjs';

const DEFAULT_EMPTY = '(not provided)';
const FIELD_LIMITS = {
  task: 30_000,
  context: 30_000,
  constraints: 20_000,
  verification: 20_000,
  task_type_id: 128,
  stage_id: 128,
  provider_name: 256,
};

function normalizeValue(value) {
  if (value === undefined || value === null || value === '') return DEFAULT_EMPTY;
  if (typeof value === 'string') return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch (error) {
    throw new Error(`template input is not JSON-serializable: ${error.message}`);
  }
}

function boundValue(name, value) {
  const normalized = normalizeValue(value);
  const max = FIELD_LIMITS[name] || 20_000;
  if (normalized.length > max) {
    throw new Error(`template field ${name} exceeds ${max} characters`);
  }
  return normalized;
}

export function renderTemplate(template, variables, maxPromptChars = 80_000) {
  const values = {};
  const rendered = template.replace(/{{\s*([a-zA-Z0-9_]+)\s*}}/g, (_match, name) => {
    if (!ALLOWED_TEMPLATE_FIELDS.has(name)) {
      throw new Error(`unsupported template field: ${name}`);
    }
    return values[name] ??= boundValue(name, variables[name]);
  });
  if (rendered.includes('{{') || rendered.includes('}}')) {
    throw new Error('rendered template contains unresolved braces');
  }
  if (rendered.length > maxPromptChars) {
    throw new Error(`compiled prompt exceeds ${maxPromptChars} characters`);
  }
  return rendered;
}
