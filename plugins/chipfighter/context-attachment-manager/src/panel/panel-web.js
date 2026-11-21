// Purpose: v0.4 — runs the panel (panel.html) as a page of its own for a Claude Code session: the engine serves the
// page at /__cam/panel?session=<id> with this script before the panel's own (proxy.ts), and the Claude plugin's mod
// links to it; it opens in a browser, Claude Desktop's own pane or another. It stands in for the MCP Apps host
// (window.camHost): it answers ui/initialize with the plugin's language, the browser's theme and the window's height,
// and turns the panel's tool calls into the engine's local panel API (/__cam/claude/…). The panel itself is the same
// file Codex shows.
// Input: the panel's JSON-RPC messages; the session id in the page's address. Output: replies as message events.
(() => {
  const session = new URLSearchParams(location.search).get("session") ?? "";
  const api = async (path, init = {}) => {
    const response = await fetch(path, { ...init, headers: { "x-cam-panel": "1", ...(init.headers ?? {}) } });
    const body = await response.json().catch(() => null);
    if (!response.ok) throw new Error(body?.error ?? `HTTP ${response.status}`);
    return body;
  };
  const query = (params) => new URLSearchParams({ session, ...params }).toString();
  const darkQuery = window.matchMedia?.("(prefers-color-scheme: dark)");
  // The panel's language is the plugin's (the engine's, as for the placeholders), as Codex gives it Codex's own; the
  // browser's only until the engine answers.
  let lang = null;
  let told = null;
  const context = () => {
    told = lang ?? navigator.language;
    return { locale: told, theme: darkQuery?.matches ? "dark" : "light", containerDimensions: { height: window.innerHeight } };
  };
  async function panel() {
    const state = await api(`/__cam/claude/panel?${query({})}`);
    if (typeof state?.lang === "string") {
      lang = state.lang;
      if (told !== null && told !== lang) {
        told = lang;
        changed({ locale: lang });
      }
    }
    return state;
  }
  async function initialize(params) {
    await panel().catch(() => null);
    return { protocolVersion: params?.protocolVersion, hostContext: context() };
  }
  async function tool(name, args = {}) {
    if (name === "cam_panel") return { content: [], structuredContent: await panel() };
    if (name === "cam_set_selection") {
      return { content: [], structuredContent: await api(`/__cam/claude/select?${query({})}`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(args) }) };
    }
    if (name === "cam_image") {
      const image = await api(`/__cam/claude/image?${query({ id: String(args.id ?? ""), max: String(args.maxSide ?? 160) })}`);
      return { content: [], structuredContent: { id: image.id, available: image.dataUrl !== null }, _meta: { dataUrl: image.dataUrl } };
    }
    // Codex's setup and new-task binding have no part under Claude Code.
    return { isError: true, content: [{ type: "text", text: `${name} is not available here` }] };
  }
  const deliver = (data) => window.dispatchEvent(new MessageEvent("message", { data }));
  window.camHost = {
    post(message) {
      // Notifications (the frame's height, initialized) need no answer here: the page has the whole window.
      if (message.id === undefined) return;
      const answer = message.method === "ui/initialize" ? initialize(message.params)
        : message.method === "tools/call" ? tool(message.params?.name, message.params?.arguments)
        : Promise.resolve({});
      answer.then(
        (result) => deliver({ jsonrpc: "2.0", id: message.id, result }),
        (error) => deliver({ jsonrpc: "2.0", id: message.id, error: { message: String(error?.message ?? error) } }),
      );
    },
  };
  const changed = (params) => deliver({ jsonrpc: "2.0", method: "ui/notifications/host-context-changed", params });
  window.addEventListener("resize", () => changed({ containerDimensions: { height: window.innerHeight } }));
  darkQuery?.addEventListener?.("change", () => changed({ theme: darkQuery.matches ? "dark" : "light" }));
})();
