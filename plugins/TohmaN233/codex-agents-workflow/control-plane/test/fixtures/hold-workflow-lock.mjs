import { WorkflowStore } from '../../lib/workflow-store.mjs';
const store = await new WorkflowStore(process.argv[2]).initialize();
setInterval(() => {}, 1000); // Keep the fixture process alive until its parent kills it.
await store.withWriter(async () => {
  process.send({ locked: true });
  await new Promise(() => {});
});
