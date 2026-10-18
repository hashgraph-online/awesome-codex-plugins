import { createCodexToolBroker } from './codex-tool-broker.mjs';
import { join } from 'node:path';
import {readPinnedObject} from '../pinned-object-reader.mjs';

export async function loadNodeSkillSnapshots(runtime, runId, envelope) {
  const snapshots = [];
  for (const pin of envelope.allowed_skills ?? []) {
    const files = Object.create(null);
    for (const resource of pin.resources) {
      const bytes = await readPinnedObject(join(runtime.runs.directory(runId),'objects'),resource);
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
