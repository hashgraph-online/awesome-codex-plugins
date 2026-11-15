/* Widget kit charts: inline SVG strings, no library. Values are plain numbers; the SVG uses
   currentColor and theme variables, so it follows the chat theme. Insert with innerHTML. */
K.scale = function (v, h, pad) {
  var lo = Math.min.apply(null, v), hi = Math.max.apply(null, v), span = hi - lo || 1;
  return function (x) { return (h - pad - (x - lo) / span * (h - 2 * pad)).toFixed(1); };
};
// A sparkline with a soft area under it; the last point is marked.
K.spark = function (v, w, h) {
  if (!v || v.length < 2) return "";
  var y = K.scale(v, h, 3), dx = w / (v.length - 1), p = "";
  for (var i = 0; i < v.length; i++) p += (i ? "L" : "M") + (i * dx).toFixed(1) + " " + y(v[i]);
  return '<svg viewBox="0 0 ' + w + " " + h + '" width="100%" height="' + h + '" preserveAspectRatio="none" aria-hidden="true">' +
    '<path d="' + p + "L" + w + " " + h + "L0 " + h + 'Z" fill="currentColor" fill-opacity=".12"/>' +
    '<path d="' + p + '" fill="none" stroke="currentColor" stroke-width="2" vector-effect="non-scaling-stroke"/>' +
    '<circle cx="' + w + '" cy="' + y(v[v.length - 1]) + '" r="3" fill="currentColor"/></svg>';
};
// Vertical bars from a zero baseline; `hi` marks bars at or above the threshold.
K.bars = function (v, w, h, hi) {
  var max = Math.max.apply(null, v.concat([1])), bw = w / v.length, s = "";
  for (var i = 0; i < v.length; i++) {
    var bh = Math.max(1, v[i] / max * (h - 2));
    s += '<rect x="' + (i * bw + 1).toFixed(1) + '" y="' + (h - bh).toFixed(1) + '" width="' + (bw - 2).toFixed(1) +
      '" height="' + bh.toFixed(1) + '" rx="1.5" fill="' + (hi != null && v[i] >= hi ? "var(--k-bad)" : "currentColor") + '"/>';
  }
  return '<svg viewBox="0 0 ' + w + " " + h + '" width="100%" height="' + h + '" preserveAspectRatio="none" aria-hidden="true">' + s + "</svg>";
};
