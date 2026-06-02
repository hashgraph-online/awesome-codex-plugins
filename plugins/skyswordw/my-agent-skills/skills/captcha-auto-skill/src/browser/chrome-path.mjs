import { existsSync } from "node:fs";

export function detectChromePath({
  platform = process.platform,
  exists = existsSync
} = {}) {
  const candidates =
    platform === "darwin"
      ? ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
      : platform === "linux"
        ? ["/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"]
        : ["C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"];

  for (const candidate of candidates) {
    if (exists(candidate)) {
      return candidate;
    }
  }

  return candidates[0];
}
