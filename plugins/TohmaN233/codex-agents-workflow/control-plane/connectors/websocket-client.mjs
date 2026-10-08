import { createHash, randomBytes } from 'node:crypto';
import net from 'node:net';
import { EventEmitter } from 'node:events';

const MAX_FRAME_BYTES = 16 * 1024 * 1024;
const MAX_HANDSHAKE_BYTES = 64 * 1024;

function encodeFrame(payload, opcode = 0x1) {
  const data = Buffer.isBuffer(payload) ? payload : Buffer.from(String(payload), 'utf8');
  const mask = randomBytes(4);
  let header;
  if (data.length < 126) {
    header = Buffer.alloc(2);
    header[1] = 0x80 | data.length;
  } else if (data.length <= 0xffff) {
    header = Buffer.alloc(4);
    header[1] = 0x80 | 126;
    header.writeUInt16BE(data.length, 2);
  } else {
    header = Buffer.alloc(10);
    header[1] = 0x80 | 127;
    header.writeBigUInt64BE(BigInt(data.length), 2);
  }
  header[0] = 0x80 | opcode;
  const masked = Buffer.alloc(data.length);
  for (let index = 0; index < data.length; index += 1) {
    masked[index] = data[index] ^ mask[index % 4];
  }
  return Buffer.concat([header, mask, masked]);
}

function parseFrames(buffer) {
  const frames = [];
  let offset = 0;
  while (buffer.length - offset >= 2) {
    const first = buffer[offset];
    const second = buffer[offset + 1];
    let length = second & 0x7f;
    let cursor = offset + 2;
    if (length === 126) {
      if (buffer.length - cursor < 2) break;
      length = buffer.readUInt16BE(cursor);
      cursor += 2;
    } else if (length === 127) {
      if (buffer.length - cursor < 8) break;
      const longLength = buffer.readBigUInt64BE(cursor);
      if (longLength > BigInt(Number.MAX_SAFE_INTEGER)) throw new Error('WebSocket frame is too large');
      length = Number(longLength);
      cursor += 8;
    }
    if (length > MAX_FRAME_BYTES) throw new Error(`WebSocket frame exceeds ${MAX_FRAME_BYTES} bytes`);
    const masked = Boolean(second & 0x80);
    let mask = null;
    if (masked) {
      if (buffer.length - cursor < 4) break;
      mask = buffer.subarray(cursor, cursor + 4);
      cursor += 4;
    }
    if (buffer.length - cursor < length) break;
    const payload = Buffer.from(buffer.subarray(cursor, cursor + length));
    if (mask) {
      for (let index = 0; index < payload.length; index += 1) {
        payload[index] ^= mask[index % 4];
      }
    }
    frames.push({ fin: Boolean(first & 0x80), opcode: first & 0x0f, payload });
    offset = cursor + length;
  }
  return { frames, rest: buffer.subarray(offset) };
}

export class LoopbackWebSocket extends EventEmitter {
  constructor(url, { origin, timeoutMs = 10_000 } = {}) {
    super();
    const parsed = new URL(url);
    if (parsed.protocol !== 'ws:') throw new Error('Only loopback ws:// URLs are supported');
    if (!['127.0.0.1', 'localhost', '::1', '[::1]'].includes(parsed.hostname)) {
      throw new Error('WebSocket target must be loopback');
    }
    this.url = parsed;
    this.origin = origin || `http://${parsed.host}`;
    this.timeoutMs = timeoutMs;
    this.socket = null;
    this.open = false;
    this.closed = false;
    this.buffer = Buffer.alloc(0);
    this.fragmentOpcode = null;
    this.fragments = [];
    this.fragmentBytes = 0;
  }

  async connect() {
    if (this.open) return this;
    const key = randomBytes(16).toString('base64');
    const expectedAccept = createHash('sha1')
      .update(`${key}258EAFA5-E914-47DA-95CA-C5AB0DC85B11`)
      .digest('base64');
    const host = this.url.hostname === 'localhost' ? '127.0.0.1' : this.url.hostname.replace(/^\[|\]$/g, '');
    const port = Number(this.url.port || 80);
    const path = `${this.url.pathname || '/'}${this.url.search || ''}`;
    const socket = net.createConnection({ host, port });
    this.socket = socket;
    await new Promise((resolve, reject) => {
      let timer = null;
      let header = Buffer.alloc(0);
      const fail = (error) => {
        if (timer) clearTimeout(timer);
        socket.destroy();
        reject(error instanceof Error ? error : new Error(String(error)));
      };
      timer = setTimeout(() => fail(new Error(`WebSocket handshake timed out after ${this.timeoutMs}ms`)), this.timeoutMs);
      socket.once('error', fail);
      socket.once('connect', () => {
        socket.write([
          `GET ${path} HTTP/1.1`,
          `Host: ${this.url.host}`,
          'Upgrade: websocket',
          'Connection: Upgrade',
          `Sec-WebSocket-Key: ${key}`,
          'Sec-WebSocket-Version: 13',
          `Origin: ${this.origin}`,
          '\r\n',
        ].join('\r\n'));
      });
      const onData = (chunk) => {
        header = Buffer.concat([header, chunk]);
        if (header.length > MAX_HANDSHAKE_BYTES) return fail(new Error('WebSocket handshake headers are too large'));
        const boundary = header.indexOf('\r\n\r\n');
        if (boundary < 0) return;
        socket.off('data', onData);
        const head = header.subarray(0, boundary).toString('utf8');
        const rest = header.subarray(boundary + 4);
        const lines = head.split('\r\n');
        if (!/^HTTP\/1\.1 101\b/.test(lines[0] || '')) return fail(new Error(`WebSocket upgrade rejected: ${lines[0] || 'empty response'}`));
        const headers = Object.fromEntries(lines.slice(1).map((line) => {
          const colon = line.indexOf(':');
          return colon < 0 ? [line.toLowerCase(), ''] : [line.slice(0, colon).trim().toLowerCase(), line.slice(colon + 1).trim()];
        }));
        if (headers['sec-websocket-accept'] !== expectedAccept) return fail(new Error('WebSocket accept key mismatch'));
        clearTimeout(timer);
        socket.off('error', fail);
        this.open = true;
        this.#attachSocket();
        if (rest.length) this.#onData(rest);
        resolve();
      };
      socket.on('data', onData);
    });
    return this;
  }

  sendText(value) {
    if (!this.open || this.closed || !this.socket?.writable) throw new Error('WebSocket is not open');
    this.socket.write(encodeFrame(value, 0x1));
  }

  close() {
    if (this.closed) return;
    this.closed = true;
    this.open = false;
    try { this.socket?.write(encodeFrame(Buffer.alloc(0), 0x8)); } catch {}
    this.socket?.destroy();
  }

  #attachSocket() {
    this.socket.on('data', (chunk) => this.#onData(chunk));
    this.socket.on('error', (error) => this.#finish(error));
    this.socket.on('close', () => this.#finish(new Error('WebSocket connection closed')));
  }

  #onData(chunk) {
    this.buffer = Buffer.concat([this.buffer, chunk]);
    let parsed;
    try { parsed = parseFrames(this.buffer); }
    catch (error) {
      this.socket?.destroy();
      this.#finish(error);
      return;
    }
    this.buffer = parsed.rest;
    for (const frame of parsed.frames) {
      if (frame.opcode === 0x8) {
        this.close();
        this.emit('close');
        continue;
      }
      if (frame.opcode === 0x9) {
        if (this.socket?.writable) this.socket.write(encodeFrame(frame.payload, 0xA));
        continue;
      }
      if (frame.opcode === 0xA) continue;
      if (frame.opcode === 0x1 || frame.opcode === 0x2) {
        if (frame.fin) this.emit('message', frame.payload);
        else {
          this.fragmentOpcode = frame.opcode;
          this.fragments = [frame.payload];
          this.fragmentBytes = frame.payload.length;
        }
        continue;
      }
      if (frame.opcode === 0x0 && this.fragmentOpcode !== null) {
        this.fragmentBytes += frame.payload.length;
        if (this.fragmentBytes > MAX_FRAME_BYTES) {
          this.socket?.destroy();
          this.#finish(new Error(`Fragmented WebSocket message exceeds ${MAX_FRAME_BYTES} bytes`));
          return;
        }
        this.fragments.push(frame.payload);
        if (frame.fin) {
          this.emit('message', Buffer.concat(this.fragments, this.fragmentBytes));
          this.fragmentOpcode = null;
          this.fragments = [];
          this.fragmentBytes = 0;
        }
      }
    }
  }

  #finish(error) {
    if (this.closed) return;
    this.closed = true;
    this.open = false;
    if (this.listenerCount('error') > 0) this.emit('error', error);
    this.emit('close', error);
  }
}

export { encodeFrame, parseFrames };
