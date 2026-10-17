import { LoopbackWebSocket } from './websocket-client.mjs';

export class CdpClient {
  constructor({ webSocketDebuggerUrl, origin, timeoutMs = 30_000 }) {
    this.socket = new LoopbackWebSocket(webSocketDebuggerUrl, { origin, timeoutMs });
    this.timeoutMs = timeoutMs;
    this.nextId = 1;
    this.pending = new Map();
    this.closed = false;
  }

  async connect() {
    await this.socket.connect();
    if (this.socket.closed) throw new Error('WebSocket closed during CDP connection setup');
    this.socket.on('message', (payload) => this.#onMessage(payload));
    this.socket.on('error', (error) => this.close(error));
    this.socket.on('close', (error) => this.close(error instanceof Error ? error : new Error('WebSocket connection closed')));
    return this;
  }

  send(method, params = {}, timeoutMs = this.timeoutMs) {
    if (this.closed) return Promise.reject(new Error('CDP connection is closed'));
    const id = this.nextId++;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`CDP command timed out: ${method}`));
      }, Math.max(1, Number(timeoutMs) || this.timeoutMs));
      this.pending.set(id, { resolve, reject, timer });
      try {
        this.socket.sendText(JSON.stringify({ id, method, params }));
      } catch (error) {
        clearTimeout(timer);
        this.pending.delete(id);
        reject(error);
      }
    });
  }

  async evaluate(expression, timeoutMs) {
    const result = await this.send('Runtime.evaluate', {
      expression,
      returnByValue: true,
      includeCommandLineAPI: true,
    }, timeoutMs);
    if (result?.exceptionDetails) {
      throw new Error(result.exceptionDetails?.exception?.description || result.exceptionDetails?.text || 'Cursor page evaluation failed');
    }
    return result?.result?.value;
  }

  async key(key, code, windowsVirtualKeyCode, modifiers = 0) {
    await this.send('Input.dispatchKeyEvent', {
      type: 'keyDown', modifiers, key, code,
      windowsVirtualKeyCode, nativeVirtualKeyCode: windowsVirtualKeyCode,
    });
    await this.send('Input.dispatchKeyEvent', {
      type: 'keyUp', modifiers, key, code,
      windowsVirtualKeyCode, nativeVirtualKeyCode: windowsVirtualKeyCode,
    });
  }

  close(error = new Error('CDP connection closed')) {
    if (this.closed) return;
    this.closed = true;
    this.socket.close();
    for (const pending of this.pending.values()) {
      clearTimeout(pending.timer);
      pending.reject(error);
    }
    this.pending.clear();
  }

  #onMessage(payload) {
    let message;
    try { message = JSON.parse(payload.toString('utf8')); } catch { return; }
    if (!Object.hasOwn(message, 'id')) return;
    const pending = this.pending.get(message.id);
    if (!pending) return;
    this.pending.delete(message.id);
    clearTimeout(pending.timer);
    if (message.error) pending.reject(new Error(message.error.message || JSON.stringify(message.error)));
    else pending.resolve(message.result);
  }
}
