import readline from 'node:readline';

const MAX_JSON_RPC_LINE_BYTES = 2 * 1024 * 1024;

export class JsonRpcPeer {
  constructor({ input, output, defaultTimeoutMs = 15_000 }) {
    this.output = output;
    this.defaultTimeoutMs = defaultTimeoutMs;
    this.nextId = 1;
    this.pending = new Map();
    this.requestHandlers = new Map();
    this.notificationHandlers = new Map();
    this.closed = false;
    this.messageTasks = new Set();
    this.reader = readline.createInterface({ input, crlfDelay: Infinity });
    input.on?.('error', (error) => this.close(error));
    output.on?.('error', (error) => this.close(error));
    this.reader.on('line', (line) => {
      // Correlated responses must be demultiplexed immediately. A human
      // permission/input handler may intentionally remain pending; it must not
      // block a cancellation or completion response that is already on the
      // stream. Durable state transitions are serialized by their stores, not
      // by this transport-wide input queue.
      const task = Promise.resolve()
        .then(() => this.#onLine(line))
        .catch((error) => this.close(error instanceof Error ? error : new Error(String(error))));
      this.messageTasks.add(task);
      task.finally(() => this.messageTasks.delete(task)).catch(() => {});
    });
    this.reader.on('close', () => this.close(new Error('ACP stream closed')));
  }

  onRequest(method, handler) {
    this.requestHandlers.set(method, handler);
    return this;
  }

  onNotification(method, handler) {
    this.notificationHandlers.set(method, handler);
    return this;
  }

  request(method, params = {}, timeoutMs = this.defaultTimeoutMs) {
    if (this.closed) return Promise.reject(Object.assign(new Error('ACP peer is closed'), { code: 'ACP_TRANSPORT_CLOSED' }));
    const id = this.nextId++;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(Object.assign(new Error(`ACP request timed out: ${method}`), { code: 'ACP_REQUEST_TIMEOUT' }));
      }, Math.max(1, Number(timeoutMs) || this.defaultTimeoutMs));
      this.pending.set(id, { resolve, reject, timer, method });
      this.#send({ jsonrpc: '2.0', id, method, params });
    });
  }

  notify(method, params = {}) {
    if (this.closed) throw new Error('ACP peer is closed');
    this.#send({ jsonrpc: '2.0', method, params });
  }

  #send(payload) {
    if (this.closed || this.output.destroyed || this.output.writableEnded) {
      throw new Error('ACP output stream is closed');
    }
    this.output.write(`${JSON.stringify(payload)}\n`);
  }

  async #onLine(line) {
    if (Buffer.byteLength(line, 'utf8') > MAX_JSON_RPC_LINE_BYTES) {
      throw new Error(`ACP JSON-RPC message exceeds ${MAX_JSON_RPC_LINE_BYTES} bytes`);
    }
    let message;
    try {
      message = JSON.parse(line);
    } catch {
      return;
    }
    if (Object.hasOwn(message, 'id') && !message.method) {
      const pending = this.pending.get(message.id);
      if (!pending) return;
      this.pending.delete(message.id);
      clearTimeout(pending.timer);
      if (message.error) pending.reject(new Error(message.error.message || 'ACP request failed'));
      else pending.resolve(message.result);
      return;
    }
    if (message.method && Object.hasOwn(message, 'id')) {
      const handler = this.requestHandlers.get(message.method);
      if (!handler) {
        this.#send({
          jsonrpc: '2.0',
          id: message.id,
          error: { code: -32601, message: `Unsupported ACP client request: ${message.method}` },
        });
        return;
      }
      try {
        const result = await handler(message.params || {}, message.id);
        this.#send({ jsonrpc: '2.0', id: message.id, result });
      } catch (error) {
        this.#send({
          jsonrpc: '2.0',
          id: message.id,
          error: { code: -32000, message: error instanceof Error ? error.message : String(error) },
        });
      }
      return;
    }
    if (message.method) {
      const handler = this.notificationHandlers.get(message.method);
      if (handler) await handler(message.params || {});
    }
  }

  close(error = new Error('ACP peer closed')) {
    if (this.closed) return;
    this.closed = true;
    this.reader.close();
    for (const pending of this.pending.values()) {
      clearTimeout(pending.timer);
      pending.reject(Object.assign(new Error(error?.message || 'ACP transport closed'), { code: 'ACP_TRANSPORT_CLOSED', cause: error }));
    }
    this.pending.clear();
  }
}
