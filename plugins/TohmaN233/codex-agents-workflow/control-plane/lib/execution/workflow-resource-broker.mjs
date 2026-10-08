import { createCodexToolBroker } from './codex-tool-broker.mjs';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { digest } from '../workflow-revisions.mjs';
import { requireValue } from '../workflow-paths.mjs';

export async function loadNodeSkillSnapshots(runtime, runId, envelope) {
  const snapshots = [];
  for (const pin of envelope.allowed_skills ?? []) {
    const files = Object.create(null);
    for (const resource of pin.resources) {
      requireValue(/^[a-f0-9]{64}$/.test(resource.sha256), 'SKILL_PIN', 'Invalid pinned Skill object');
      const bytes = await readFile(join(runtime.runs.directory(runId), 'objects', resource.sha256));
      requireValue(digest(bytes) === resource.sha256, 'SKILL_PIN_CHANGED', 'Pinned Skill resource changed');
      files[resource.path] = bytes;
    }
    snapshots.push({source_path:pin.path, source_hash:pin.source_hash, name:pin.name, files});
  }
  return snapshots;
}

// Workflow resources supplement Codex's native tools; they do not replace them.
export async function createWorkflowResourceBroker({ workspace, access, allowedPaths, resources, authorize, onOperation }) {
  const broker = await createCodexToolBroker({ workspace, access, allowedPaths, resources, authorize, onOperation, recoverToolErrors: true });
  const tools = broker.tools().filter(tool => /^(read_workflow_resource(?:_chunk|_range)?|materialize_workflow_resource)$/.test(tool.name));
  const names = new Set(tools.map(tool => tool.name));
  return {
    ...broker,
    tools: () => structuredClone(tools),
    call(name, args, callId) {
      if (!names.has(name)) throw Object.assign(new Error(`Unknown Workflow resource tool: ${name}`), { code: 'WORKFLOW_RESOURCE_TOOL' });
      return broker.call(name, args, callId);
    },
  };
}
