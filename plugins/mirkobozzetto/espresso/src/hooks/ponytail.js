#!/usr/bin/env node
"use strict";
const fs = require("node:fs");
const {getDefaultMode, writeDefaultMode, isDeactivationCommand, getQuietStartup} = require("../../hooks/ponytail-config.js");
const {getPonytailInstructions} = require("../../hooks/ponytail-instructions.js");
const {setMode, clearMode, readMode, isCodex} = require("../../hooks/ponytail-runtime.js");
const {POLICY} = require("../core.cjs");

try {
  const event = process.argv[2];
  let mode;
  let context;
  if (event === "SessionStart") {
    mode = getDefaultMode();
    if (mode === "off") clearMode(); else setMode(mode);
    context = mode === "off" ? "Ponytail is off." : getPonytailInstructions(mode);
  } else if (event === "SubagentStart") {
    mode = readMode();
    const input = fs.readFileSync(0, "utf8").trim();
    // The read-only scout writes no code: Ponytail would only cost context.
    if ((input ? JSON.parse(input) : {}).agent_type === "espresso:scout") context = "";
    else if (!mode || mode === "off") process.exit(0);
    else context = getPonytailInstructions(mode);
  } else if (event === "UserPromptSubmit") {
    const data = JSON.parse(fs.readFileSync(0, "utf8"));
    const prompt = String(data.prompt || "").trim().toLowerCase().replace(/^[/@$](?:espresso:|ponytail:)?ponytail(?=\s|$)/, "/ponytail");
    const match = prompt.match(/^\/ponytail(?:\s+(.*))?$/);
    if (!match && !isDeactivationCommand(prompt)) process.exit(0);
    const args = match ? (match[1] || "status").split(/\s+/) : ["off"];
    mode = readMode() || "off";
    if (args[0] === "status") {
      context = `Ponytail: current ${mode}; default ${getDefaultMode()}. Modes: full (standard), lite (gentle), ultra (aggressive), off. Use /ponytail <mode> or /ponytail default <mode>.`;
    } else if (args[0] === "default" && args.length === 2 && ["full", "lite", "ultra", "off"].includes(args[1])) {
      writeDefaultMode(args[1]);
      context = `Saved Ponytail default ${args[1]}; effective default ${getDefaultMode()}. Current session remains ${mode}.`;
    } else if (args.length === 1 && ["full", "lite", "ultra", "off"].includes(args[0])) {
      mode = args[0];
      if (mode === "off") clearMode(); else setMode(mode);
      context = mode === "off" ? "Ponytail is off. Stop applying its instructions." : getPonytailInstructions(mode);
    } else {
      throw new Error("Use /ponytail full|lite|ultra|off|status or /ponytail default <mode>.");
    }
  } else {
    throw new Error("Expected SessionStart, SubagentStart or UserPromptSubmit.");
  }
  const output = {hookSpecificOutput: {
    hookEventName: event, additionalContext: [context, POLICY].filter(Boolean).join("\n\n"),
  }};
  // additionalContext is invisible in the UI; this one line tells the user what
  // runs. Codex renders systemMessage as a warning, so it stays silent there.
  const announce = event === "SessionStart" ? !getQuietStartup() : event === "UserPromptSubmit";
  if (announce && !isCodex) output.systemMessage = `Espresso · Ponytail ${mode}`;
  process.stdout.write(JSON.stringify(output));
} catch (error) {
  process.stderr.write(`Ponytail: ${error.message}\n`);
  process.exitCode = 1;
}
