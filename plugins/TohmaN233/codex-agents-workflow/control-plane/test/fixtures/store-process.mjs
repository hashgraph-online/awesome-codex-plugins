import { ConnectorTaskStore } from '../../connectors/task-store.mjs';
const store = new ConnectorTaskStore({ statePath: process.argv[2] });
try { await store.initialize(); }
catch (error) {
  process.send({ ok: false, code: error.code, message: error.message });
  process.disconnect();
  process.exitCode = 0;
}
if (store.initialized) {
process.send({ ready: true, pid: process.pid });
process.once('message', async fields => {
  try { process.send({ ok: true, task: await store.create(fields) }); }
  catch (error) { process.send({ ok: false, code: error.code, message: error.message }); }
  finally { process.disconnect(); }
});

}
