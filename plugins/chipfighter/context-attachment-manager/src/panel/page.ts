// Purpose: the panel page itself (v0.11: the panel layer reads its own files, docs/v0.11/plan.md). Codex shows
// panel.html as an MCP app; Claude Desktop opens it as a page the engine serves, with panel-web.js before its own script
// standing in for the MCP app host (v0.4).
// Output: the page's HTML.

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

export const panelHtml = (): string => readFileSync(join(here, "panel.html"), "utf8");

export function webPanelPage(): string {
  const page = panelHtml();
  const bridge = readFileSync(join(here, "panel-web.js"), "utf8");
  const at = page.indexOf("<script>");
  if (at < 0) throw new Error("panel.html has no script");
  return `${page.slice(0, at)}<script>\n${bridge}\n</script>\n${page.slice(at)}`;
}
