export type BootstrapResponse = { body: unknown; status: number };

export type BootstrapInbox = {
  receive(result: unknown): void;
  request(path: string, method: string, body: unknown, fallback: (path: string, method: string, body: unknown) => Promise<BootstrapResponse>): Promise<unknown>;
  ready: Promise<void>;
};

export function createBootstrapInbox(): BootstrapInbox;
