#!/usr/bin/env python3
"""Candlestick chart of any token Chord indexes, as a standalone SVG. Python 3.8+, standard library only.

  python3 chart.py --chain base --token AERO --tf 1h --limit 48
  python3 chart.py --chain solana --token BONK --tf 15m --limit 96 --out bonk.svg
  python3 chart.py --chain robinhood --token 0xd0601ce157db5bdc3162bbac2a2c8af5320d9eec --tf 1d --limit 60

--token takes a symbol / name (resolved through Chord's search; the best verified, most liquid hit wins and is
printed so you can check it) or an address (0x... on EVM chains, the base58 mint on Solana, case-sensitive).
Prints a JSON summary (the resolved token, change, high, low, volume, trades, the SVG path) on stdout.
Data: Chord (https://getchord.xyz), no API key, about 60 requests a minute.
"""
import argparse
import datetime as dt
import json
import re
import sys
import urllib.parse
import urllib.request

API = "https://api.getchord.xyz/v1"
CHAINS = {"ethereum": 1, "monad": 143, "robinhood": 4663, "arc": 5042, "avalanche": 43114, "base": 8453, "bnb": 56, "arbitrum": 42161}
TFS = ("1m", "5m", "15m", "1h", "4h", "1d", "1w")
EVM_ADDR = re.compile(r"^0x[0-9a-fA-F]{40}$")
SOL_ADDR = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


def get(path, **params):
    q = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    req = urllib.request.Request(f"{API}{path}{'?' + q if q else ''}", headers={"user-agent": "chord-charts-skill/1.0", "accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def resolve(chain, query):
    """(address, symbol) for an address or a symbol / name."""
    if chain == "solana":
        if SOL_ADDR.match(query):
            return query, None
        rows = get("/chains/solana/search", q=query).get("tokens", [])
        if not rows:
            sys.exit(f"no Solana token matches {query!r}")
        best = max(rows, key=lambda t: (t.get("symbol", "").lower() == query.lower(), t.get("liquidityUsd") or 0))
        return best["token"], best.get("symbol")
    if EVM_ADDR.match(query):
        return query.lower(), None
    cid = CHAINS[chain]
    if cid == 143:  # Monad: search answers only off-list tokens; the main list is /tokens
        rows = get("/tokens").get("tokens", []) + get("/tokens/search", q=query).get("tokens", [])
    else:
        rows = get("/tokens/search", chain=cid, q=query).get("tokens", [])
    q = query.lower()
    hits = [t for t in rows if t.get("symbol", "").lower() == q] or [t for t in rows if q in (t.get("symbol", "") + " " + t.get("name", "")).lower()]
    if not hits:
        sys.exit(f"no token on {chain} matches {query!r}")
    best = max(hits, key=lambda t: (bool(t.get("verified")), t.get("liquidityUsd") or 0))
    return best["address"].lower(), best.get("symbol")


def candles(chain, token, tf, limit):
    if chain == "solana":
        d = get(f"/chains/solana/token/{token}/candles", tf=tf, limit=limit)
        rows = [{"t": c["t"], "o": c["o"], "h": c["h"], "l": c["l"], "c": c["c"], "v": c.get("volumeUsd", 0), "n": c.get("trades", 0)} for c in d.get("candles", [])]
        return rows, False
    d = get("/candles", chain=CHAINS[chain], token=token, tf=tf, limit=limit, fill=1)
    return d.get("candles", []), bool(d.get("forming"))


def fmt_price(p):
    if p == 0:
        return "0"
    if p >= 1000:
        return f"{p:,.0f}"
    if p >= 1:
        return f"{p:,.2f}"
    digits = max(2, -int(f"{p:e}".split("e")[1]) + 2)
    return f"{p:.{min(digits, 12)}f}"


def fmt_usd(v):
    for unit, size in (("B", 1e9), ("M", 1e6), ("k", 1e3)):
        if v >= size:
            return f"${v / size:.2f}{unit}"
    return f"${v:,.0f}"


def svg(rows, title, subtitle, tf):
    W, H, R, T = 1000, 560, 20, 64
    price_h, gap, vol_h = 330, 20, 90
    hi = max(r["h"] for r in rows)
    lo = min(r["l"] for r in rows)
    pad = (hi - lo) * 0.06 or hi * 0.01 or 1
    hi, lo = hi + pad, max(lo - pad, 0)
    L = max(70, 14 + 7 * max(len(fmt_price(lo + (hi - lo) * i / 5)) for i in range(6)))  # room for the longest price label
    vmax = max(r["v"] for r in rows) or 1
    n = len(rows)
    step = (W - L - R) / n
    body = max(1.0, step * 0.62)
    y = lambda p: T + (hi - p) / (hi - lo) * price_h
    vy0 = T + price_h + gap + vol_h
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="ui-monospace,Menlo,Consolas,monospace">',
           f'<rect width="{W}" height="{H}" fill="#0b0f0e"/>',
           f'<text x="{L}" y="30" fill="#e8ecea" font-size="20" font-family="system-ui,sans-serif" font-weight="700">{title}</text>',
           f'<text x="{L}" y="50" fill="#8a9590" font-size="12">{subtitle}</text>']
    for i in range(6):
        p = lo + (hi - lo) * i / 5
        out.append(f'<line x1="{L}" x2="{W - R}" y1="{y(p):.1f}" y2="{y(p):.1f}" stroke="#1c2522"/>')
        out.append(f'<text x="{L - 8}" y="{y(p) + 4:.1f}" fill="#8a9590" font-size="11" text-anchor="end">{fmt_price(p)}</text>')
    for i, r in enumerate(rows):
        x = L + step * i + step / 2
        up = r["c"] >= r["o"]
        col = "#16c784" if up else "#ea3943"
        out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y(r["h"]):.1f}" y2="{y(r["l"]):.1f}" stroke="{col}"/>')
        top, bot = y(max(r["o"], r["c"])), y(min(r["o"], r["c"]))
        out.append(f'<rect x="{x - body / 2:.1f}" y="{top:.1f}" width="{body:.1f}" height="{max(bot - top, 1):.1f}" fill="{col}"/>')
        vh = r["v"] / vmax * vol_h
        out.append(f'<rect x="{x - body / 2:.1f}" y="{vy0 - vh:.1f}" width="{body:.1f}" height="{vh:.1f}" fill="{col}" opacity="0.45"/>')
    fmt = "%H:%M" if tf in ("1m", "5m", "15m", "1h") else "%b %d"
    for i in range(0, n, max(1, n // 6)):
        x = L + step * i + step / 2
        label = dt.datetime.fromtimestamp(rows[i]["t"], dt.timezone.utc).strftime(fmt)
        out.append(f'<text x="{x:.1f}" y="{vy0 + 18:.1f}" fill="#8a9590" font-size="11" text-anchor="middle">{label}</text>')
    out.append(f'<text x="{L}" y="{T + price_h + gap - 4}" fill="#5c6863" font-size="10">volume (USD)</text>')
    out.append(f'<text x="{W - R}" y="{H - 10}" fill="#5c6863" font-size="10" text-anchor="end">times UTC · data: Chord (getchord.xyz)</text>')
    out.append("</svg>")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="Candlestick chart from Chord candles (SVG).")
    ap.add_argument("--chain", required=True, choices=sorted(CHAINS) + ["solana"])
    ap.add_argument("--token", required=True, help="symbol, name or address")
    ap.add_argument("--tf", default="1h", choices=TFS)
    ap.add_argument("--limit", type=int, default=48)
    ap.add_argument("--out", help="SVG path (default chart-<symbol>-<chain>-<tf>.svg)")
    a = ap.parse_args()
    if a.chain == "solana" and a.tf == "1w":
        sys.exit("Solana candles go up to 1d")
    addr, sym = resolve(a.chain, a.token)
    rows, forming = candles(a.chain, addr, a.tf, max(2, min(a.limit, 1000)))
    if len(rows) < 2:
        sys.exit(f"not enough candles for {addr} on {a.chain} ({len(rows)})")
    sym = sym or a.token[:10]
    first, last = rows[0]["o"], rows[-1]["c"]
    chg = (last / first - 1) * 100 if first else 0.0
    vol = sum(r["v"] for r in rows)
    trades = sum(r.get("n") or 0 for r in rows)
    span = f'{dt.datetime.fromtimestamp(rows[0]["t"], dt.timezone.utc):%Y-%m-%d %H:%M} to {dt.datetime.fromtimestamp(rows[-1]["t"], dt.timezone.utc):%Y-%m-%d %H:%M} UTC'
    title = f"{sym} · {a.chain} · {a.tf}   ${fmt_price(last)}  {chg:+.2f}%"
    subtitle = f"{len(rows)} candles, {span} · high ${fmt_price(max(r['h'] for r in rows))} · low ${fmt_price(min(r['l'] for r in rows))} · volume {fmt_usd(vol)}" + (" · last candle still open" if forming else "")
    out = a.out or re.sub(r"[^A-Za-z0-9._-]", "_", f"chart-{sym}-{a.chain}-{a.tf}.svg")
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg(rows, title, subtitle, a.tf))
    print(json.dumps({"chain": a.chain, "token": addr, "symbol": sym, "tf": a.tf, "candles": len(rows), "from": rows[0]["t"], "to": rows[-1]["t"],
                      "open": first, "close": last, "changePct": round(chg, 3), "high": max(r["h"] for r in rows), "low": min(r["l"] for r in rows),
                      "volumeUsd": round(vol, 2), "trades": trades, "lastCandleOpen": forming, "svg": out}, indent=1))


if __name__ == "__main__":
    main()
