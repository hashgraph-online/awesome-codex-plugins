#!/usr/bin/env node
import { spawn } from 'node:child_process';
import { readdir } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(fileURLToPath(import.meta.url));
const names = [
  'node-input-materials.test.mjs',
  'owned-workflow-wait.test.mjs','owned-workflow-authority.test.mjs','direct-tool-catalog.test.mjs',
  'managed-item-identity.test.mjs',
  'owned-native-integration.test.mjs',
  'native-handoff-delivery.test.mjs',
  'i18n.test.mjs',
  'thread-protocol.test.mjs',
  'thread-handoff.test.mjs',
  'thread-source-options.test.mjs',
  'execution-envelope-resources.test.mjs',
  'prompt-input-projection.test.mjs',
  'release-defaults.test.mjs',
  'native-binding.test.mjs',
  'native-provider-identity.test.mjs',
  'native-agent-bridge.test.mjs',
  'native-agent-observer.test.mjs',
  'config.test.mjs',
  'local-client-discovery.test.mjs',
  'generation-progress.test.mjs',
  'review-checklist.test.mjs',
  'connector-integration.test.mjs',
  'connectors.test.mjs',
  'attempt-admission.test.mjs',
  'workspace-snapshot.test.mjs',
  'connector-process.test.mjs',
  'run-refresh.test.mjs',
  'skill-generation-recovery.test.mjs',
  'launch-edited-workflow.test.mjs',
  'cache-cleanup.test.mjs',
  'task-inputs.test.mjs',
  'console.test.mjs',
  'mcp.test.mjs',
  'mcp-app.test.mjs',
  'mcp-app-bootstrap.test.mjs',
  'workflow-wait.test.mjs',
  'conversation-control-recovery.test.mjs',
  'mcp-startup.test.mjs',
  'plugin-bootstrap.test.mjs',
  'run-absolute-scope.test.mjs',
  'runtime-dependency-boundary.test.mjs',
  'runtime-environment.test.mjs',
  'runtime-registry.test.mjs',
  'runtime-registration-flow.test.mjs',
  'open-console.test.mjs',
  'providers.test.mjs',
  'workflow-store.test.mjs',
  'workflow-editor.test.mjs',
  'workflow-validator.test.mjs',
  'workflow-migration.test.mjs',
  'workflow-runtime.test.mjs',
  'workflow-loops.test.mjs',
  'workflow-loop-runtime.test.mjs',
  'workspace-source-locations.test.mjs',
  'workflow-routing.test.mjs',
  'workflow-pins.test.mjs',
  'workflow-subworkflow.test.mjs',
  'parallel-planner.test.mjs',
  'parallel-worktrees.test.mjs',
  'parallel-runtime.test.mjs',
  'workflow-execution-contracts.test.mjs',
  'managed-native-pool.test.mjs',
  'host-main-manager.test.mjs',
  'main-model-selection.test.mjs',
  'main-orchestration.test.mjs',
  'run-history-retention.test.mjs',
  'workflow-resource-program.test.mjs',
  'workflow-service.test.mjs',
  'workflow-input-file.test.mjs',
  'native-continuation-regression.test.mjs',
  'legacy-conversion-certificate.test.mjs',
  'strict-execution.test.mjs',
  'codex-command-broker.test.mjs',
  'codex-tool-broker.test.mjs',
  'codex-managed-login.test.mjs',
  'codex-model-catalog.test.mjs',
  'codex-host-auth.test.mjs',
  'codex-auth-rpc.test.mjs',
  'strict-manager.test.mjs',
  'strict-session-view.test.mjs',
  'display-data.test.mjs',
  'skill-routing-contract.test.mjs',
  'skill-import.test.mjs',
  'authoring.test.mjs',
  'authoring-loops.test.mjs',
  'authoring-dependency-lifecycle.test.mjs',
  'authoring-preparation-approval.test.mjs',
  'authoring-upgrade-efficiency.test.mjs',
  'authoring-runtime-input-boundary.test.mjs',
];

const discovered=(await readdir(root)).filter(name=>name.endsWith('.test.mjs')).sort();
const declared=[...names].sort();
if(JSON.stringify(discovered)!==JSON.stringify(declared)){
  console.error('TEST_MANIFEST_INCOMPLETE',JSON.stringify({missing:discovered.filter(name=>!declared.includes(name)),stale:declared.filter(name=>!discovered.includes(name))}));
  process.exit(1);
}
const files=names.map((name) => join(root, name));

const child = spawn(process.execPath, ['--test', '--test-concurrency=1', ...files], {
  stdio: 'inherit',
  windowsHide: true,
  env: process.env,
});
child.once('error', (error) => {
  console.error(error);
  process.exitCode = 1;
});
child.once('exit', (code, signal) => {
  if (signal) console.error(`test runner terminated by ${signal}`);
  process.exitCode = Number.isInteger(code) ? code : 1;
});
