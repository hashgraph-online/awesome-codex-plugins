#!/usr/bin/env node
"use strict";

const { makeKit } = require("./lib/kit");
const version = require("./lib/version");

const USAGE = `Usage: easybrandkit <url> [options]

Reads a website the way a browser draws it and saves its brand in one
folder: the logo files, colors, fonts, the first screen, and the app store
icon and screenshots when the site links to its apps. brand.json is for
tools, BRAND.md for people and coding agents, _brand.yml for Quarto and
Shiny.

Options:
  --out <dir>      where to save (default: ./easybrandkit-<host>)
  --no-stores      skip app store listings and social profiles
  --json           print brand.json instead of a summary
  --timeout <s>    give up after this many seconds (default: 120)
  -h, --help       show this help
  -v, --version    show the version

Needs Node 22 or newer and Chrome, Chromium, Edge or Brave. Set CHROME_PATH
to pick the browser.`;

function parse(argv) {
  const options = { stores: true, json: false, timeout: 120 };
  const rest = [];
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "-h" || arg === "--help") options.help = true;
    else if (arg === "-v" || arg === "--version") options.version = true;
    else if (arg === "--no-stores") options.stores = false;
    else if (arg === "--json") options.json = true;
    else if (arg === "--out" || arg === "--timeout") {
      const value = argv[++i];
      if (!value || value.startsWith("-")) throw new Error(`${arg} needs a value`);
      if (arg === "--out") options.out = value;
      else options.timeout = Number(value);
    } else if (arg.startsWith("--out=")) options.out = arg.slice(6);
    else if (arg.startsWith("--timeout=")) options.timeout = Number(arg.slice(10));
    else if (arg.startsWith("-")) throw new Error(`Unknown option: ${arg}`);
    else rest.push(arg);
  }
  if (!(options.timeout >= 30 && options.timeout <= 600)) throw new Error("--timeout takes 30 to 600 seconds");
  if (!options.help && !options.version && rest.length !== 1) throw new Error("Give one website address, for example: easybrandkit acme.com");
  return { ...options, url: rest[0] };
}

function summary({ dir, kit }) {
  const list = (items) => items.join(", ") || "none found";
  const lines = [`Saved the ${kit.name} brand kit to ${dir}`, ""];
  const logoLine = (logo) => `${logo.file}${logo.svg ? ` and ${logo.svg}` : ""} (${logo.where}, on ${logo.onPicture ? `a picture, mostly ${logo.background}` : logo.background})`;
  lines.push(`  Logos   ${list(kit.logos.map(logoLine))}`);
  lines.push(`  Colors  ${list(kit.colors.map((color) => `${color.hex} ${color.role}`))}`);
  const fonts = [kit.fonts.heading && `${kit.fonts.heading} (headings)`, kit.fonts.body && `${kit.fonts.body} (body)`].filter(Boolean);
  lines.push(`  Fonts   ${list(fonts)}`);
  lines.push(`  Screen  ${list(kit.screenshots.map((shot) => `${shot.file} (${shot.width}x${shot.height})`))}`);
  if (kit.card) lines.push(`  Card    ${kit.card.file}`);
  const sources = kit.stores.filter((source) => source.ok);
  if (sources.length) lines.push(`  Stores  ${list(sources.map((source) => `${source.type}: ${source.assets.length} file${source.assets.length === 1 ? "" : "s"}`))}`);
  for (const note of kit.notes) lines.push(`  Note    ${note}`);
  lines.push("", `Read ${dir}/BRAND.md for the details. ${dir}/_brand.yml is the kit for Quarto and Shiny.`);
  return lines.join("\n");
}

async function main() {
  let options;
  try {
    options = parse(process.argv.slice(2));
  } catch (err) {
    process.stderr.write(`easybrandkit: ${err.message}\n\n${USAGE}\n`);
    process.exit(2);
  }
  if (options.help) return void process.stdout.write(`${USAGE}\n`);
  if (options.version) return void process.stdout.write(`${version}\n`);
  try {
    const result = await makeKit(options.url, {
      dir: options.out,
      stores: options.stores,
      timeLimit: options.timeout * 1000,
      log: options.json ? () => {} : (line) => process.stderr.write(`${line}...\n`),
    });
    process.stdout.write(options.json ? JSON.stringify(result.kit, null, 2) + "\n" : summary(result) + "\n");
  } catch (err) {
    if (options.json) process.stdout.write(JSON.stringify({ ok: false, error: err.message }) + "\n");
    process.stderr.write(`easybrandkit: ${err.message}\n`);
    process.exit(1);
  }
}

main();
