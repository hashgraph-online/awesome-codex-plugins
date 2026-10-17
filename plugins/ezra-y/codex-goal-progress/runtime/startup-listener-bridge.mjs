export class StartupListenerBridge {
  #pendingPid = null;
  #pendingConnection = null;
  #queuedResponse = null;
  #pendingTimer = null;
  #continueProcess;
  #setTimer;
  #clearTimer;

  constructor(options = {}) {
    this.#continueProcess = options.continueProcess ?? (() => undefined);
    this.#setTimer = options.setTimer ?? setTimeout;
    this.#clearTimer = options.clearTimer ?? clearTimeout;
  }

  get pendingPid() {
    return this.#pendingPid;
  }

  acceptConnection(connection) {
    if (this.#pendingConnection && this.#pendingConnection !== connection) {
      this.#pendingConnection.destroy();
    }
    this.#pendingConnection = connection;
    connection.on?.("error", () => undefined);
    if (this.#queuedResponse) {
      this.#deliver(this.#queuedResponse);
    }
  }

  acceptLaunch(pid, timeoutMs = 21_000) {
    if (!Number.isSafeInteger(pid) || pid <= 1 || this.#pendingPid !== null) {
      return false;
    }
    this.#pendingPid = pid;
    this.#pendingTimer = this.#setTimer(() => this.release(), timeoutMs);
    return true;
  }

  acceptResponse(response) {
    if (!response || typeof response !== "object") {
      return false;
    }
    if (!Number.isSafeInteger(response.pid) || response.pid !== this.#pendingPid) {
      return false;
    }
    if (response.action !== "continue" && response.action !== "complete") {
      this.release();
      return false;
    }
    this.#deliver(response);
    return true;
  }

  release() {
    if (Number.isSafeInteger(this.#pendingPid) && this.#pendingPid > 1) {
      this.#continueProcess(this.#pendingPid);
    }
    this.#reset(true);
  }

  close() {
    this.release();
  }

  #deliver(response) {
    if (!this.#pendingConnection) {
      this.#queuedResponse = response;
      return;
    }
    this.#pendingConnection.end(`${JSON.stringify(response)}\n`);
    this.#reset(false);
  }

  #reset(destroyConnection) {
    this.#pendingPid = null;
    this.#queuedResponse = null;
    if (this.#pendingTimer) {
      this.#clearTimer(this.#pendingTimer);
      this.#pendingTimer = null;
    }
    if (this.#pendingConnection) {
      if (destroyConnection) {
        this.#pendingConnection.destroy();
      }
      this.#pendingConnection = null;
    }
  }
}
