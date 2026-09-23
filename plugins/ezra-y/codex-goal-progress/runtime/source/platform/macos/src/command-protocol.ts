export const MACOS_COMMAND_NAMES = [
  "install",
  "doctor",
  "verify",
  "restore",
  "uninstall",
  "upgrade",
  "emergency-disable",
  "repair",
] as const;

export type MacosCommandName = (typeof MACOS_COMMAND_NAMES)[number];

export interface MacosCommandInput {
  readonly command: MacosCommandName;
  readonly json: boolean;
  readonly human: boolean;
  readonly verbose: boolean;
  readonly restartCodex: boolean;
  readonly preserveHistory: boolean;
}

export interface MacosCommandResult {
  readonly schemaVersion: 1;
  readonly command: MacosCommandName | null;
  readonly ok: boolean;
  readonly code: string;
  readonly changed: boolean;
  readonly nextStep: string | null;
  readonly details: Readonly<Record<string, unknown>>;
}

export type MacosCommandHandler = (input: MacosCommandInput) => Promise<MacosCommandResult>;

export type MacosCommandHandlers = {
  [Command in MacosCommandName]: MacosCommandHandler;
};

export type ParseMacosCommandResult =
  | { readonly ok: true; readonly input: MacosCommandInput }
  | { readonly ok: false; readonly result: MacosCommandResult };

function invalidCommand(message: string): ParseMacosCommandResult {
  return {
    ok: false,
    result: {
      schemaVersion: 1,
      command: null,
      ok: false,
      code: "COMMAND_INVALID",
      changed: false,
      nextStep: "Run goal-progress <command> --json.",
      details: { message },
    },
  };
}

function isCommandName(value: string | undefined): value is MacosCommandName {
  return value !== undefined && (MACOS_COMMAND_NAMES as readonly string[]).includes(value);
}

export function parseMacosCommand(argv: readonly string[]): ParseMacosCommandResult {
  const [commandValue, ...flags] = argv;
  if (!isCommandName(commandValue)) {
    return invalidCommand("Unknown or missing command");
  }
  const outputFlags = flags.filter((flag) => flag === "--json" || flag === "--human");
  if (outputFlags.length !== 1) {
    return invalidCommand("Choose exactly one output mode: --json or --human");
  }
  const allowedFlags = new Set(["--json", "--human", "--verbose"]);
  if (
    commandValue === "install" ||
    commandValue === "upgrade" ||
    commandValue === "restore" ||
    commandValue === "repair"
  ) {
    allowedFlags.add("--restart-codex");
  }
  if (commandValue === "uninstall") {
    allowedFlags.add("--keep-history");
    allowedFlags.add("--delete-history");
  }
  const unsupported = flags.find((flag) => !allowedFlags.has(flag));
  if (unsupported) {
    return invalidCommand(`Unsupported flag: ${unsupported}`);
  }
  if (flags.includes("--keep-history") && flags.includes("--delete-history")) {
    return invalidCommand("Choose either --keep-history or --delete-history");
  }
  if (flags.includes("--verbose") && !flags.includes("--human")) {
    return invalidCommand("--verbose is available only with --human");
  }
  return {
    ok: true,
    input: {
      command: commandValue,
      json: flags.includes("--json"),
      human: flags.includes("--human"),
      verbose: flags.includes("--verbose"),
      restartCodex: flags.includes("--restart-codex"),
      preserveHistory: !flags.includes("--delete-history"),
    },
  };
}

function assertCommandResult(
  command: MacosCommandName,
  result: MacosCommandResult,
): MacosCommandResult {
  if (
    result.schemaVersion !== 1 ||
    result.command !== command ||
    typeof result.ok !== "boolean" ||
    !result.code ||
    typeof result.changed !== "boolean" ||
    (result.nextStep !== null && typeof result.nextStep !== "string") ||
    result.details === null ||
    typeof result.details !== "object" ||
    Array.isArray(result.details)
  ) {
    throw new Error("Handler returned an invalid command result");
  }
  return result;
}

export async function executeMacosCommand(
  argv: readonly string[],
  handlers: MacosCommandHandlers,
): Promise<MacosCommandResult> {
  const parsed = parseMacosCommand(argv);
  if (!parsed.ok) {
    return parsed.result;
  }
  try {
    return assertCommandResult(
      parsed.input.command,
      await handlers[parsed.input.command](parsed.input),
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    const stableCode = /^(GOAL_PROGRESS_[A-Z0-9_]+)/u.exec(message)?.[1];
    return {
      schemaVersion: 1,
      command: parsed.input.command,
      ok: false,
      code: stableCode ?? "COMMAND_FAILED",
      changed: false,
      nextStep: "Run doctor --json, fix the reported issue, then retry.",
      details: {
        message,
      },
    };
  }
}

export function serializeMacosCommandResult(result: MacosCommandResult): string {
  return `${JSON.stringify(result)}\n`;
}

export function serializeMacosCommandResultHuman(
  result: MacosCommandResult,
  verbose = false,
): string {
  const lines = [
    `${result.ok ? "OK" : "ERROR"} ${result.code}`,
    result.nextStep ?? "No further action.",
  ];
  if (verbose) {
    lines.push(JSON.stringify(result.details, null, 2));
  }
  return `${lines.join("\n")}\n`;
}
