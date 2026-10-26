// Provider routes bind a client protocol to its configured destination. Local URLs contain only an opaque id;
// credentials stay in the client's request. Bindings survive engine replacement and are immutable once registered.
import { createHmac, randomBytes } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { dataDir } from "./paths.ts";

export type Platform = "codex" | "claude";
export type ProviderRoute = { id: string; platform: Platform; baseUrl: string };
const ID = /^[a-f0-9]{32}$/;

export const routingPort = (enginePort: number): number => {
  if (!Number.isInteger(enginePort) || enginePort < 1 || enginePort > 65534) throw new Error("invalid engine port");
  return enginePort + 1;
};

export function validateBaseUrl(value: string, enginePort?: number): URL {
  const invalid = () => Object.assign(new Error("invalid provider URL"), { key: "conflict.endpointUrl" });
  if (typeof value !== "string" || /[\r\n\t]/.test(value)) throw invalid();
  let url: URL;
  try { url = new URL(value); } catch { throw invalid(); }
  if (!["http:", "https:"].includes(url.protocol) || !url.hostname || url.username || url.password || url.hash || url.pathname.startsWith("/__cam/")) throw invalid();
  if (enginePort !== undefined && ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname) && [enginePort, routingPort(enginePort)].includes(Number(url.port || (url.protocol === "https:" ? 443 : 80)))) {
    throw Object.assign(new Error("provider endpoint points to the engine"), { key: "conflict.proxyLoop" });
  }
  return url;
}

export function registerRoute(input: { platform: Platform; baseUrl: string }, root = dataDir()): ProviderRoute {
  if (input.platform !== "codex" && input.platform !== "claude") throw new Error("invalid provider platform");
  const baseUrl = validateBaseUrl(input.baseUrl).href;
  const dir = join(root, "routes");
  mkdirSync(dir, { recursive: true });
  // wx prevents simultaneous plugin processes from replacing the shared signing key.
  const keyFile = join(dir, "key");
  try { writeFileSync(keyFile, randomBytes(32).toString("hex"), { flag: "wx", mode: 0o600 }); }
  catch (error) { if ((error as NodeJS.ErrnoException).code !== "EEXIST") throw error; }
  const key = readFileSync(keyFile, "utf8");
  if (!/^[a-f0-9]{64}$/.test(key)) throw new Error("invalid provider route key");
  const id = createHmac("sha256", key).update(`${input.platform}\n${baseUrl}`).digest("hex").slice(0, 32);
  const route = { id, platform: input.platform, baseUrl };
  try { writeFileSync(join(dir, `${id}.json`), JSON.stringify(route), { flag: "wx", mode: 0o600 }); }
  catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "EEXIST") throw error;
    const existing = readRoute(id, root);
    if (!existing || existing.platform !== route.platform || existing.baseUrl !== baseUrl) throw new Error("invalid provider route record");
  }
  return route;
}

export function readRoute(id: string, root = dataDir()): ProviderRoute | null {
  if (!ID.test(id)) return null;
  try {
    const value = JSON.parse(readFileSync(join(root, "routes", `${id}.json`), "utf8"));
    if (value.id !== id || !["codex", "claude"].includes(value.platform)) return null;
    return { id, platform: value.platform, baseUrl: validateBaseUrl(value.baseUrl).href };
  } catch { return null; }
}

export const routeBaseUrl = (port: number, id: string): string => {
  if (!ID.test(id)) throw new Error("invalid provider route id");
  return `http://localhost:${routingPort(port)}/__cam/routes/${id}`;
};
