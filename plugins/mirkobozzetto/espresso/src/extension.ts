import { POLICY, rewriteCommand } from './core.cjs';
import ponytail from "../pi-extension/index.js";

type Model = {provider: string; id: string};
type Context = {
  hasUI?: boolean;
  isIdle?(): boolean;
  model?: Model;
  models?: {current(): Model | undefined; list(): Model[]};
  modelRegistry?: {getAvailable(): Model[]};
  ui: {
    notify(text: string, level: "info" | "warning" | "error"): void;
    select?(title: string, options: string[]): Promise<string | undefined>;
  };
};
type Host = {
  sendUserMessage(message: string, options?: {deliverAs: "followUp"}): void;
  exec(command: string, args: string[], options: {timeout: number}): Promise<{stdout: string; stderr: string; code: number}>;
  registerCommand(name: string, command: {
    description: string;
    getArgumentCompletions?(prefix: string): {value: string; label: string}[];
    handler(args: string, ctx: Context): Promise<void>;
  }): void;
  on(event: 'before_agent_start', handler: (event: {systemPrompt: string | string[]; systemPromptOptions?: {sections?: Record<string, string>}}, ctx: Context) => Promise<{systemPrompt: string | string[]} | undefined>): void;
  on(event: 'tool_call', handler: (event: {toolName: string; input: Record<string, unknown>}, ctx: Context) => Promise<{input: Record<string, unknown>} | undefined>): void;
};

export default function espresso(pi: Host, options: {auto?: boolean} = {}) {
  const registerPonytailCommand = (name: string, command: Parameters<Host["registerCommand"]>[1]) => {
    pi.registerCommand(name, {...command,
      getArgumentCompletions: name === "ponytail"
        ? prefix => ["full", "lite", "ultra", "off", "status", "default full", "default lite", "default ultra", "default off"]
          .filter(value => value.startsWith(prefix)).map(value => ({value, label: value}))
        : command.getArgumentCompletions,
      handler: async (args, ctx) => {
        if (name.startsWith("ponytail-")) {
          const integration = name === "ponytail-help"
            ? " Espresso integration: Ponytail is already bundled and enabled by default. In OMP/Pi, /ponytail opens a mode selector rather than directly activating it. Mention /ponytail off (session), /ponytail default off (future sessions), and /ponytail default full."
            : "";
          pi.sendUserMessage("/skill:" + name + (args.trim() ? " " + args.trim() : "") + integration,
            ctx.isIdle?.() === false ? {deliverAs: "followUp"} : undefined);
          return;
        }
        if (name === "ponytail" && !args.trim()) {
          if (ctx.hasUI !== false && ctx.ui.select) {
            const choice = await ctx.ui.select("Ponytail", [
              "full - Standard library and native features first (default)",
              "lite - Build the request, suggest simpler alternatives",
              "ultra - Aggressive simplification",
              "off - Disable for this session",
              "status - Show current and default modes",
            ]);
            if (!choice) return;
            args = choice.split(" ")[0];
          } else args = "status";
        }
        await command.handler(args, ctx.hasUI === false
          ? {...ctx, ui: {...ctx.ui, notify: (text: string) => console.log(text)}}
          : ctx);
      },
    });
  };
  // OMP exposes prototype methods; spreading its API drops event registration.
  ponytail(new Proxy(pi, {get(target, key) {
    if (key === "registerCommand") return registerPonytailCommand;
    const value = Reflect.get(target, key, target);
    return typeof value === "function" ? value.bind(target) : value;
  }}));
  let enabled = true;
  let rtk = false;
  let auto = options.auto ?? false;
  let workerEffort = 'inherit';
  pi.registerCommand('espresso', {
    description: 'Concise output and delegation: on, off, auto, manual, status, rtk-on, rtk-off, effort, worker',
    getArgumentCompletions: prefix => ['on', 'off', 'auto', 'manual', 'status', 'rtk-on', 'rtk-off', 'effort inherit', 'effort low', 'effort medium', 'effort high', 'worker ']
      .filter(value => value.startsWith(prefix)).map(value => ({value, label: value})),
    handler: async (args, ctx) => {
      const notify = (text: string) => ctx.hasUI === false ? console.log(text) : ctx.ui.notify(text, 'info');
      const request = args.trim();
      if (request === 'effort' || request.startsWith('effort ')) {
        const level = request.slice(6).trim();
        if (level && !['inherit', 'low', 'medium', 'high'].includes(level)) throw new Error('Use /espresso effort inherit|low|medium|high.');
        if (level) workerEffort = level;
        notify('Text worker effort: ' + workerEffort + (workerEffort === 'inherit' ? ' (follows the session thinking level)' : '') + '. Session-only; named agents use OMP agentModelOverrides.');
        return;
      }
      const mode = request.startsWith('worker ') ? 'worker' : request || 'status';
      if (mode === 'auto') {
        if (!ctx.models) throw new Error('Automatic native delegation is supported only in OMP.');
        auto = true;
        enabled = true;
      } else if (mode === 'manual') auto = false;
      else if (mode === 'on') enabled = true;
      else if (mode === 'off') { enabled = false; auto = false; }
      else if (mode === 'rtk-on') rtk = true;
      else if (mode === 'rtk-off') rtk = false;
      else if (!['status', 'worker'].includes(mode)) throw new Error('Use on, off, auto, manual, status, rtk-on, rtk-off or worker <assignment>.');
      const model = ctx.models?.current() ?? ctx.model;
      const current = model ? `${model.provider}/${model.id}` : '';
      // The worker keeps the session model: only its thinking effort changes.
      const target = current;
      if (mode === 'worker') {
        if (!enabled || !target) throw new Error('No enabled session model for the worker.');
        const assignment = request.slice(7).trim();
        const resolved = workerEffort === 'inherit' ? (ctx.thinkingLevel ?? 'low') : workerEffort;
        if (!assignment) {
          notify('Usage: /espresso worker <assignment>\nExample: /espresso worker summarize this stack trace in one line\nWould run ' + target + ' at ' + resolved + ' effort on the supplied text only.');
          return;
        }
        const omp = Boolean(ctx.models);
        const slash = target.indexOf('/');
        const selectors = omp ? ['--model', target] : ['--provider', target.slice(0, slash), '--model', target.slice(slash + 1)];
        // 'inherit' follows the session thinking level. ctx.thinkingLevel is a pi
        // field; OMP leaves it undefined, so that host keeps the old 'low' floor.
        const effort = resolved;
        notify('Text worker | ' + target + ' | ' + effort + ' | bounded supplied-text assignment');
        const result = await pi.exec(omp ? 'omp' : 'pi', [
          '--no-session', '--no-extensions', '--no-skills', '--no-tools',
          ...selectors, '--thinking', effort,
          '--system-prompt', `${POLICY} Work only on the supplied text. No tools or further delegation.`,
          '-p', assignment,
        ], {timeout: 120000});
        if (result.code !== 0) throw new Error(`Worker ${target} failed: ${result.stderr}`);
        notify(`${target}\n${result.stdout}`);
        return;
      }
      notify(JSON.stringify({enabled, rtk, auto: enabled && auto && Boolean(ctx.models), current, worker: target, workerEffort,
        workerEffortResolved: workerEffort === 'inherit' ? (ctx.thinkingLevel ?? 'low') : workerEffort,
        routing: auto && ctx.models ? 'Automatic research delegation policy; stricter instructions still apply; concurrency is advisory' : 'Named agents or /espresso worker <text assignment>; existing overrides preserved'}));
    },
  });
  pi.on('before_agent_start', async (event, ctx) => {
    const sections = event.systemPromptOptions?.sections;
    if (!enabled) {
      if (sections) delete sections.espresso;
      return;
    }
    const routing = auto && ctx.models
      ? ` Espresso automatic research delegation is enabled by the user. This is standing authorization for substantial independent read-only research, not code edits. After inspecting the task yourself, delegate only when at least two genuinely independent research slices justify the startup and context overhead. Use at most two workers concurrently on the session model, one bounded assignment per worker, with explicit read-only scope and an evidence-based deliverable. Announce scope and selected agent briefly, then proceed without asking again unless a higher-priority instruction or active skill requires it. Do not delegate small questions, simple lookups or small corrections. Do not force delegation or invent work to fill slots. No nested delegation. Preserve explicit agent/model choices. Keep architecture, edits, integration and consequential review on the parent. Verify returned evidence proportionately; never claim token or quota savings. These are behavioral instructions, not a sandbox or enforced concurrency limit.`
      : '';
    const effortPolicy = ' For every authorized delegation, announce agent, resolved model, thinking effort and a short reason before launching. For named agents, read the effective agent configuration rather than inferring effort from the parent. Use low for simple bounded lookup/extraction; retain medium for cross-component analysis and medium/high for consequential review. If the selected research profile is low but the task needs deeper analysis, select an appropriately configured analysis/review agent instead. Never claim an unverified effective model or effort.';
    const text = `${POLICY}${routing}${effortPolicy}`;
    // Same order as Ponytail: a named section keeps Pi's cached prefix, and OMP
    // hands an array that string concatenation would flatten with commas.
    if (sections && typeof sections === 'object') {
      sections.espresso = text;
      return;
    }
    if (Array.isArray(event.systemPrompt)) return {systemPrompt: [...event.systemPrompt, text]};
    return {systemPrompt: `${event.systemPrompt}\n\n${text}`};
  });
  pi.on('tool_call', async (event, ctx) => {
    if (!enabled || !rtk || event.toolName !== 'bash') return;
    const command = rewriteCommand(event.input.command);
    if (!command) return;
    if (ctx.models) return {input: {...event.input, command}};
    event.input.command = command;
  });
}
