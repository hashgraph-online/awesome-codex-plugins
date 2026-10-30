# Rendering statechart diagrams

Render every `.mmd` you show the user with Pele, an npm Mermaid renderer, pinned to version 1.9.0. Save the SVG next to the `.mmd` with the same base name (`chart.mmd` becomes `chart.svg`).

## Install once, outside the repo

```sh
mkdir -p ~/.endostack/render && cd ~/.endostack/render
npm init -y >/dev/null
npm install --save-exact pele@1.9.0
```

Installing outside the repo keeps the dependency out of the project's lockfile.

## Render call

The defaults are too small for a 500-state diagram, so raise the input size to 1,000,000 characters, the output size to 8,000,000 characters, and the edge count to 10,000. The export and option names below follow Pele 1.9.0's README; if your installed copy differs, check its README and keep the same three limits.

```js
// ~/.endostack/render/render.mjs
import { readFileSync, writeFileSync } from "node:fs";
import { render, PeleError } from "pele";
import { STYLE } from "./style.mjs";

const [, , input] = process.argv;
const source = readFileSync(input, "utf8");

try {
	const svg = await render(source, {
		maxInputSize: 1_000_000,
		maxOutputSize: 8_000_000,
		maxEdges: 10_000,
	});
	writeFileSync(input.replace(/\.mmd$/, ".svg"), svg.replace(/(<svg[^>]*>)/, `$1${STYLE}`));
} catch (err) {
	if (err instanceof PeleError) {
		console.error(err.message);
		process.exit(1);
	}
	throw err;
}
```

Run it with `node ~/.endostack/render/render.mjs <out>/chart.mmd`. If it exits with a Pele error, give the user the error message and the Mermaid source so they can render it elsewhere.

## Theming

Pele ignores Mermaid's `theme` and `themeVariables`. It reads CSS custom properties prefixed `--pele-` on its root element:

| Property | Controls |
| --- | --- |
| `--pele-bg` | background |
| `--pele-fg` | main text |
| `--pele-muted` | secondary text, edge labels |
| `--pele-line` | arrows and borders of plain states |
| `--pele-surface` | default state fill |
| `--pele-surface-alt` | composite state fill |
| `--pele-border` | composite borders |

The statechart tool assigns these classes to states: the seven phase colors (`blue`, `orange`, `purple`, `yellow`, `teal`, `tan`, `pink`), and the marks `breaks`, `mayBreak`, `bugPath`, and `repeats`.

Only `breaks` and `mayBreak` have `classDef` lines in the `.mmd`, so a plain Mermaid viewer still shows violations. Pele turns `classDef` colors into inline `style` attributes, which beat ordinary stylesheet rules. Your CSS for the mark classes therefore needs `!important`, or dark mode keeps the light-mode mark colors.

What each mark changes:

- `breaks` (every merged state violates): fill and text color.
- `mayBreak` (some merged states violate): fill and text color.
- `bugPath` (on a shortest violation path): outline only.
- `repeats` (in a temporal counterexample's cycle): outline only, dashed.

Write the mark rules after the phase-color rules so a marked state shows its mark over its phase color.

## Style block

Insert one `<style>` block at the top of each SVG with light-mode values and a `prefers-color-scheme: dark` override, so the image follows the viewer's theme. This palette is a starting point; keep the meaning of each class if you change the colors.

```js
// ~/.endostack/render/style.mjs
export const STYLE = `<style>
:root, svg {
	--pele-bg: #ffffff;
	--pele-fg: #1d232b;
	--pele-muted: #5b6672;
	--pele-line: #8a96a3;
	--pele-surface: #f4f6f8;
	--pele-surface-alt: #eaeef2;
	--pele-border: #c5cdd5;
}
.blue rect, .blue path { fill: #dbe9fb; }
.orange rect, .orange path { fill: #fde6cf; }
.purple rect, .purple path { fill: #e9e0f8; }
.yellow rect, .yellow path { fill: #fbf3c8; }
.teal rect, .teal path { fill: #d3f0ec; }
.tan rect, .tan path { fill: #efe5d6; }
.pink rect, .pink path { fill: #fadde8; }

.breaks rect, .breaks path { fill: #d93a3a !important; stroke: #a32020 !important; }
.breaks text, .breaks span { fill: #ffffff !important; color: #ffffff !important; }
.mayBreak rect, .mayBreak path { fill: #f0a03c !important; stroke: #b86d10 !important; }
.mayBreak text, .mayBreak span { fill: #1d232b !important; color: #1d232b !important; }
.bugPath rect, .bugPath path { stroke: #2f6fd6 !important; stroke-width: 3px !important; }
.repeats rect, .repeats path { stroke: #8a4fd1 !important; stroke-width: 3px !important; stroke-dasharray: 6 4 !important; }

@media (prefers-color-scheme: dark) {
	:root, svg {
		--pele-bg: #12161b;
		--pele-fg: #e6eaef;
		--pele-muted: #9aa5b1;
		--pele-line: #6c7884;
		--pele-surface: #1d232b;
		--pele-surface-alt: #242b34;
		--pele-border: #3a4450;
	}
	.blue rect, .blue path { fill: #1f3552; }
	.orange rect, .orange path { fill: #4a3218; }
	.purple rect, .purple path { fill: #352a4d; }
	.yellow rect, .yellow path { fill: #47401a; }
	.teal rect, .teal path { fill: #183f3a; }
	.tan rect, .tan path { fill: #3e3427; }
	.pink rect, .pink path { fill: #4a2535; }

	.breaks rect, .breaks path { fill: #b42828 !important; stroke: #ff7a7a !important; }
	.breaks text, .breaks span { fill: #ffffff !important; color: #ffffff !important; }
	.mayBreak rect, .mayBreak path { fill: #a8661a !important; stroke: #f5b660 !important; }
	.mayBreak text, .mayBreak span { fill: #ffffff !important; color: #ffffff !important; }
	.bugPath rect, .bugPath path { stroke: #6aa3ff !important; }
	.repeats rect, .repeats path { stroke: #b48af0 !important; }
}
</style>`;
```

Check one rendered SVG in a browser with the system in light mode and again in dark mode before handing it over. A violation mark that keeps its light colors in dark mode means an `!important` is missing.
