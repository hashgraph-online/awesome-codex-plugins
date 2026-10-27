// ShortCodeCore（Tutti/ShortCodeCore.swift）的 JS 版：6 位配方码 TT·7K2Q9X ⇄ 25 位载荷。
// 和 Swift 共用测试向量 site/tests/shortcode-vectors.json（由 scripts/shortcode_vectors_gen.swift 生成）。
(function (root) {
  const ALPHA = '0123456789ABCDEFGHJKMNPQRSTVWXYZ';
  const MASK = (1n << 25n) - 1n, M1 = 0x1A2B3C5n, M2 = 0x0B5AD4Fn, W = [1, 3, 5, 7, 9];
  const SEP = new Set(['·', '•', '・', '.', '-', ':', ' ', '_']);
  const PARAM_BITS = 17;
  const TEMPLATES = 109; // = Tutti/ShortCode.swift Library.codeIDs.count，App 追加模板后同步

  const inv = a => { let x = a; for (let i = 0; i < 6; i++) x = (x * (2n - a * x)) & MASK; return x & MASK; };
  const IM1 = inv(M1), IM2 = inv(M2);
  function mix(v) { let x = v & MASK; x = (x * M1) & MASK; x ^= x >> 13n; x = (x * M2) & MASK; x ^= x >> 11n; return x; }
  function unmix(v) { let x = v & MASK; x = x ^ (x >> 11n) ^ (x >> 22n); x = (x * IM2) & MASK; x = x ^ (x >> 13n); x = (x * IM1) & MASK; return x; }
  function check(syms) { let s = 7; syms.forEach((v, i) => s += W[i] * v); return (32 - s % 32) % 32; }
  function val(ch) { if (ch === 'O') return 0; if (ch === 'I' || ch === 'L') return 1; const i = ALPHA.indexOf(ch); return i < 0 ? null : i; }

  function encode(payload) {
    const x = mix(BigInt(payload));
    const syms = [0, 1, 2, 3, 4].map(i => Number((x >> BigInt(5 * (4 - i))) & 31n));
    syms.push(check(syms));
    return 'TT·' + syms.map(v => ALPHA[v]).join('');
  }
  // 只取 6 位本体（去掉 TT 和分隔符），不校验
  function body(text) {
    let s = String(text).trim().toUpperCase();
    if (s.startsWith('TT')) { s = s.slice(2); if (SEP.has(s[0])) s = s.slice(1); }
    return s;
  }
  // 校验位不对返回 null
  function decode(text) {
    const s = body(text);
    if (s.length !== 6) return null;
    const syms = [...s].map(val);
    if (syms.some(v => v === null)) return null;
    if (check(syms.slice(0, 5)) !== syms[5]) return null;
    let x = 0n; for (const v of syms.slice(0, 5)) x = (x << 5n) | BigInt(v);
    return Number(unmix(x));
  }
  // 抄错一位时，列出改一个字符就能对上的候选（给"码好像抄错了一位"用）
  function nearby(text) {
    const s = body(text);
    if (s.length !== 6) return [];
    const out = [];
    for (let i = 0; i < 6; i++) for (const ch of ALPHA) {
      if (ch === s[i]) continue;
      const t = s.slice(0, i) + ch + s.slice(i + 1);
      const p = decode(t);
      if (p !== null && (p >>> PARAM_BITS) < TEMPLATES) out.push('TT·' + t);
    }
    return out;
  }
  const split = p => ({ index: p >>> PARAM_BITS, params: p & ((1 << PARAM_BITS) - 1) });
  const payload = (index, params = 0) => (index << PARAM_BITS) | params;

  const api = { encode, decode, nearby, split, payload, body, TEMPLATES };
  if (typeof module !== 'undefined') module.exports = api; else root.ShortCode = api;
})(this);
