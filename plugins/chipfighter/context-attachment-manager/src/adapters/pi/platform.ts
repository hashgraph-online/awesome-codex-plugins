// Purpose: v0.11 — pi (earendil-works/pi): the core alone, no panel. Each provider in ~/.pi/agent/models.json takes
// its own `baseUrl`, so the route is for one provider: the one named, else the one pi uses now (PI_PROVIDER, which pi
// sets for shell commands with PI_SESSION_ID); without a baseUrl of its own a provider uses pi's built-in address (the
// defaults below, from pi's provider code). The request format follows the provider. Our pi extension (extension.ts),
// listed under "extensions" in ~/.pi/agent/settings.json, names each request's session in `x-cam-session` and registers
// the plugin's MCP service. Not tested live.
// Input: the environment, the settings files. Output: the platform's entry (core/platform.ts).

import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { jsonAt } from "../../core/config-edit.ts";
import type { CorePlatform } from "../../core/platform.ts";

const DEFAULTS: Record<string, string> = {
  anthropic: "https://api.anthropic.com",
  openai: "https://api.openai.com/v1",
  google: "https://generativelanguage.googleapis.com/v1beta",
  deepseek: "https://api.deepseek.com",
};
const extension = () => fileURLToPath(new URL("./extension.ts", import.meta.url));

export const pi: CorePlatform = {
  name: "pi",
  title: "pi",
  upstream: null,
  detect: (env) => !!(env.PI_SESSION_ID || env.PI_PROVIDER),
  setup: ({ home, env, provider }) => {
    const dir = join(home, ".pi", "agent");
    const name = provider ?? env.PI_PROVIDER?.trim() ?? null;
    if (!name) throw new Error("pi: name the provider whose requests should go through the engine, e.g. --provider anthropic");
    const models = join(dir, "models.json");
    const set = jsonAt(models, ["providers", name, "baseUrl"]);
    return {
      current: typeof set === "string" ? set : null,
      fallback: DEFAULTS[name] ?? null,
      edits: ({ url }) => [
        { file: models, json: ["providers", name, "baseUrl"], value: url },
        { file: join(dir, "settings.json"), add: ["extensions"], value: extension() },
      ],
    };
  },
  connect: ({ url }) => [
    `In ~/.pi/agent/models.json, set your provider's "baseUrl": "${url}"`,
    `In ~/.pi/agent/settings.json, add to "extensions": ${JSON.stringify(extension())}`,
    "Restart pi.",
  ],
};
