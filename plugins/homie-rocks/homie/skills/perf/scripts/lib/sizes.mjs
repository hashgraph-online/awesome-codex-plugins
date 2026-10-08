/**
 * The perf skill's hints about what a player downloads, from `homie-studio perf sizes`.
 */

/**
 * What the built files say, from `perf sizes`. Whether a script is minified is read from its code (`code`, studio
 * 0.19.1: whitespace, comments and names outside its strings), never from how well it gzips: minified JavaScript gzips
 * to a quarter or a third of its bytes, more than indented source, and a bundle with three.js in it also carries its
 * shaders as GLSL source in strings. A studio before 0.19.1 has no `code`; then nothing is said about minifying.
 */
export function sizeHints(sizes) {
  const h = [];
  const kb = (b) => `${Math.round(b / 1024)} KB`;
  const big = sizes.biggest.filter((f) => f.kind === 'js' && f.bytes > 200 * 1024);
  const unmin = big.filter((f) => f.code && !f.code.minified);
  const known = big.filter((f) => f.code);
  if (sizes.js.gzip > 300 * 1024) {
    const how = unmin.length ? 'Ship the unminified scripts below minified, drop' : known.length && known.length === big.length ? 'Its scripts are minified already, so what is left is how much code it is: drop' : 'Drop';
    h.push(`a player downloads ${kb(sizes.js.gzip)} of JavaScript (gzipped) before playing: a phone on 4G feels that. ${how} what is never imported, load big things after the first frame.`);
  }
  for (const f of unmin) {
    // Whitespace is counted in the code only (strings and comments apart); comments in the whole file.
    const loose = Math.round(f.code.whitespacePct * Math.max(0, 1 - (f.code.stringPct + f.code.commentPct) / 100) + f.code.commentPct);
    h.push(`${f.path} (${kb(f.bytes)}) is not minified: ${f.code.whitespacePct}% of its code is whitespace and ${f.code.commentPct}% of the file comments${f.code.nameLength ? ` (names ${f.code.nameLength} characters on average)` : ''}. A minified copy of the same version is the same code (keep its licence comment): whitespace and comments alone are about ${loose}% of its bytes, before any name is shortened.`);
  }
  // A minified script needs no hint unless it is mostly strings: then say why it is big and still minified.
  for (const f of known.filter((x) => x.code.minified && (x.code.shaderPct >= 5 || x.code.stringPct >= 25))) {
    const strings = f.code.shaderPct >= 5
      ? `${f.code.shaderPct}% of its bytes are GLSL shader source in strings${f.code.stringPct - f.code.shaderPct >= 5 ? ` (${f.code.stringPct}% strings in all)` : ''}: normal for three.js, whose shaders ship as text that no minifier touches.`
      : `${f.code.stringPct}% of its bytes are strings (text and data), which no minifier touches.`;
    h.push(`${f.path} (${kb(f.bytes)}, ${kb(f.gzip)} gzipped) is minified already (${f.code.whitespacePct}% whitespace in its code${f.code.mangled ? ', names shortened' : ', names kept'}): minifying it again gains nothing. ${strings}`);
  }
  return h;
}
