import readline from 'node:readline';

// A recovery call can spend 30 seconds confirming detached Host cleanup before
// journaling its result. Integration clients must allow that contract plus I/O.
export function makeClient(child, { timeoutMs = 60_000 } = {}) {
  const pending = new Map();
  const lines = readline.createInterface({ input: child.stdout, crlfDelay: Infinity });
  let stderr = '', closedError;
  child.stderr?.on('data', chunk => { stderr = (stderr + chunk.toString()).slice(-4096); });
  const diagnostic = (slot, reason) => new Error(
    `${reason}; request ${slot.id} ${slot.method} after ${Math.round(performance.now() - slot.started)}ms` +
    `; exit=${child.exitCode ?? 'none'} signal=${child.signalCode ?? 'none'}` +
    (stderr ? `; stderr tail: ${stderr}` : ''),
  );
  const failAll = reason => {
    closedError ??= reason;
    for (const slot of pending.values()) {
      clearTimeout(slot.timer); slot.reject(diagnostic(slot, reason));
    }
    pending.clear();
  };
  lines.on('line', line => {
    let message;
    try {
      message = JSON.parse(line);
      if (!message || typeof message !== 'object' || Array.isArray(message)) throw new Error('Expected a JSON-RPC object');
    } catch (error) { failAll(`Invalid MCP response: ${error.message}`); return; }
    const slot = pending.get(message.id);
    if (slot) { pending.delete(message.id); clearTimeout(slot.timer); slot.resolve(message); }
  });
  lines.on('close', () => failAll('MCP stdout closed before a response'));
  child.once('error', error => failAll(`MCP process error: ${error.message}`));
  child.once('close', (code, signal) => failAll(`MCP process closed (${code ?? signal})`));
  child.stdout.on('error', error => failAll(`MCP stdout error: ${error.message}`));
  child.stdin.on('error', error => failAll(`MCP stdin error: ${error.message}`));
  return {
    request(message, { timeoutMs: requestTimeoutMs = timeoutMs } = {}) {
      return new Promise((resolve, reject) => {
        const slot = { id: message.id, method: message.params?.name ?? message.method, started: performance.now(), resolve, reject };
        if (closedError) { reject(diagnostic(slot, closedError)); return; }
        if (pending.has(message.id)) { reject(diagnostic(slot, 'Duplicate pending MCP request ID')); return; }
        if (!Number.isFinite(requestTimeoutMs) || requestTimeoutMs <= 0) { reject(diagnostic(slot, 'Invalid MCP request deadline')); return; }
        slot.timer = setTimeout(() => {
          pending.delete(message.id); reject(diagnostic(slot, `MCP response timeout (${requestTimeoutMs}ms)`));
        }, requestTimeoutMs);
        pending.set(message.id, slot);
        try {
          child.stdin.write(`${JSON.stringify(message)}\n`, error => { if (error) failAll(`MCP request write failed: ${error.message}`); });
        } catch (error) {
          pending.delete(message.id); clearTimeout(slot.timer); reject(diagnostic(slot, `MCP request write failed: ${error.message}`));
        }
      });
    },
  };
}
