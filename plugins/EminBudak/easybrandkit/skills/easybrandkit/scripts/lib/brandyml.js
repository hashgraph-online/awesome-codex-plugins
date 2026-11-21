"use strict";

// The kit as _brand.yml, in the brand.yml format Quarto and Shiny read
// (https://posit-dev.github.io/brand-yml/): the brand's name and site, its
// logo, its colors by the role the page gives them and its fonts. Only what
// the page showed goes in. A value it did not show is left out, so Quarto
// and Shiny keep their own default for it instead of a guess. The YAML is
// written by hand, so the package keeps no dependencies.

const fs = require("fs");
const path = require("path");

const HEX = /^#[0-9a-f]{6}$/i;

// The families Google Fonts serves, by lower-case name, from a list that
// tools/google-fonts.js refreshes. Quarto and Shiny load a font with
// `source: google` from Google, so a family not on the list would load
// nothing.
let googleFonts = null;
function googleFamily(name) {
  if (!googleFonts) {
    const lines = fs.readFileSync(path.join(__dirname, "google-fonts.txt"), "utf8").split("\n").map((line) => line.trim());
    googleFonts = new Map(lines.filter((line) => line && !line.startsWith("#")).map((family) => [family.toLowerCase(), family]));
  }
  const key = String(name || "").trim().toLowerCase();
  if (!key) return "";
  // A site that serves a Google font itself often names it after its
  // variable build: "Inter Variable", "InterVariable" and "Inter var" are
  // all Inter.
  return googleFonts.get(key) || googleFonts.get(key.replace(/[\s._-]*(variable|var|vf)$/, "")) || "";
}

// A generic CSS family or the system's own interface font names no font
// to load: Bootstrap, under Quarto and Shiny, sets text in the system's
// font by default, and "-apple-system" written as a family would show
// only on Apple devices.
const GENERIC_FAMILY = /^(system-ui|-apple-system|blinkmacsystemfont|ui-(sans-serif|serif|monospace|rounded)|sans-serif|serif|monospace|cursive|fantasy|math|emoji|fangsong)$/i;
// Shiny writes a family into its Sass as it is, where a dot, a colon, a
// plus or an apostrophe breaks the theme or changes the name. Font names
// keep to letters, digits, spaces, hyphens and underscores, as every
// family on Google Fonts does, so a name with anything else is left out.
const FAMILY_NAME = /^[\p{L}\p{N}_-][\p{L}\p{N} _-]*$/u;

// WCAG's relative luminance and contrast ratio.
function luminance(hex) {
  const [r, g, b] = [1, 3, 5].map((k) => {
    const v = parseInt(hex.slice(k, k + 2), 16) / 255;
    return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a, b) {
  const [x, y] = [luminance(a), luminance(b)];
  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
}

// A ground white text reads better on than black text does.
const isDark = (hex) => HEX.test(hex) && luminance(hex) < 0.179;

// A YAML scalar: plain when nothing in it reads as other YAML (a number,
// true, null, a comment, a key), else double-quoted, which takes JSON's
// escapes.
function scalar(value) {
  const text = String(value);
  if (/^[A-Za-z][\w ./-]*$/.test(text) && !text.endsWith(" ") && !/^(true|false|yes|no|on|off|y|n|null)$/i.test(text)) return text;
  return JSON.stringify(text).replace(/[\u2028\u2029]/g, (c) => `\\u${c.charCodeAt(0).toString(16)}`);
}

// Page text in a comment stays on its line.
const oneLine = (text) => String(text).replace(/[\u0000-\u001f\u007f\u2028\u2029]+/g, " ");

// The page's colors under the role it gives them, numbered from the second
// of a role on: button, button-2, surface, surface-2 and so on.
function palette(colors) {
  const count = {};
  return colors
    .filter((color) => color && HEX.test(color.hex) && /^[a-z]+$/.test(color.role))
    .map((color) => {
      count[color.role] = (count[color.role] || 0) + 1;
      return [count[color.role] === 1 ? color.role : `${color.role}-${count[color.role]}`, color.hex.toLowerCase()];
    });
}

// The theme colors: the button color as primary, the page's own ground as
// background and its heading color as the text color. Text has to read on
// its ground at 7:1 (WCAG's AAA): a heading color in the brand's hue, or
// one from a dark band of a white page, is not a color for running text.
// A dark ground whose text color is unknown would get Bootstrap's dark
// text, so it is left out too. Links keep a color of their own when the
// page gives them one that reads on the ground.
function themeColors(colors, background) {
  const role = (name) => (colors.find((color) => color && color.role === name && HEX.test(color.hex)) || { hex: "" }).hex.toLowerCase();
  const ground = HEX.test(background) ? background.toLowerCase() : "";
  const heading = role("heading");
  const foreground = heading && contrast(heading, ground || "#ffffff") >= 7 ? heading : "";
  const kept = ground && (foreground || contrast(ground, "#212529") >= 7) ? ground : "";
  const link = role("link");
  return {
    foreground,
    background: kept,
    primary: role("button"),
    link: link && contrast(link, kept || "#ffffff") >= 4.5 ? link : "",
  };
}

const imageName = (logo) => path.basename(logo.file || logo.svg).replace(/\.[a-z]+$/i, "");

// The logo for a header, brand.yml's medium size, which Quarto also falls
// back to for the other sizes, or "" for none. The brand's own marks sit in
// the header and the footer; one in the page body can be a product's or a
// partner's. First choice is a mark cut on a ground like the page's, light
// or dark: its vector was drawn for that ground and shows on the page. Next
// is one on a solid ground of another color, as the cut, which keeps that
// ground around it: a white vector drawn for a dark header would vanish on
// a white page. A mark shown only over a photo is left out, since its
// vector was drawn for the photo and its cut carries part of it.
function headerLogo(logos, background) {
  const own = logos.filter((logo) => logo.where === "header" || logo.where === "footer");
  const marks = own.length ? own : logos;
  const dark = isDark(background || "#ffffff");
  const fits = marks.find((logo) => (logo.svg || !logo.onPicture) && isDark(logo.background) === dark);
  if (fits) return imageName(fits);
  const solid = marks.find((logo) => !logo.onPicture && logo.file);
  if (solid) return solid.svg ? path.basename(solid.file) : imageName(solid);
  return "";
}

function brandYml(kit, { background = "", site = kit.url } = {}) {
  const lines = [
    "# The brand kit for Quarto and Shiny, in the brand.yml format: https://posit-dev.github.io/brand-yml/",
    `# ${kit.generator} read it from ${kit.url} on ${String(kit.capturedAt).slice(0, 10)}.`,
    "",
    "meta:",
    `  name: ${scalar(kit.name)}`,
  ];
  if (site) lines.push(`  link: ${scalar(site)}`);

  // Each logo as its vector when the page draws one, else as the cut.
  const logos = [].concat(kit.logos || []).filter((logo) => logo && typeof (logo.svg || logo.file) === "string");
  if (logos.length) {
    lines.push("", "logo:", "  images:");
    for (const logo of logos) {
      const file = scalar(path.basename(logo.svg || logo.file));
      if (logo.alt) lines.push(`    ${scalar(imageName(logo))}:`, `      path: ${file}`, `      alt: ${scalar(logo.alt)}`);
      else lines.push(`    ${scalar(imageName(logo))}: ${file}`);
    }
    const medium = headerLogo(logos, background);
    if (medium) lines.push(`  medium: ${scalar(medium)}`);
  }

  const colors = [].concat(kit.colors || []);
  const swatches = palette(colors);
  const theme = themeColors(colors, background);
  const themed = ["foreground", "background", "primary"].filter((key) => theme[key]);
  if (swatches.length || themed.length) {
    lines.push("", "color:");
    if (swatches.length) {
      lines.push("  # The page's colors, named for where it uses them.", "  palette:");
      for (const [key, hex] of swatches) lines.push(`    ${key}: ${scalar(hex)}`);
    }
    for (const key of themed) lines.push(`  ${key}: ${scalar(theme[key])}`);
  }

  const fonts = [];
  const families = {};
  for (const [role, given] of [["base", (kit.fonts || {}).body], ["headings", (kit.fonts || {}).heading]]) {
    const named = String(given || "").trim();
    if (!named || GENERIC_FAMILY.test(named)) continue;
    const google = googleFamily(named);
    if (!google && !FAMILY_NAME.test(named)) continue;
    const family = google || named;
    if (!fonts.some((font) => font.family === family)) fonts.push({ family, named, source: google ? "google" : "system" });
    families[role] = family;
  }
  if (fonts.length || theme.link) {
    lines.push("", "typography:");
    if (fonts.length) lines.push("  fonts:");
    for (const font of fonts) {
      if (font.source === "system") lines.push(`    # ${oneLine(font.named)} is not on Google Fonts, so it shows only where it is installed.`);
      else if (font.named !== font.family) lines.push(`    # The page calls it ${oneLine(font.named)}.`);
      lines.push(`    - family: ${scalar(font.family)}`, `      source: ${font.source}`);
    }
    for (const role of ["base", "headings"]) if (families[role]) lines.push(`  ${role}: ${scalar(families[role])}`);
    if (theme.link) lines.push("  link:", `    color: ${scalar(theme.link)}`);
  }
  return lines.join("\n") + "\n";
}

module.exports = { brandYml, googleFamily };
