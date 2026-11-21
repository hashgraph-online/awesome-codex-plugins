#!/usr/bin/env python3
"""chord.py - a small, dependency-free client for the public Chord API (https://api.getchord.xyz).

Part of the Chord agent skill. Python 3.8+ standard library only. It never signs, never holds a key
to a wallet, and never broadcasts: the most it does is ask the API for an UNSIGNED transaction, and
only when the caller passes --user-confirmed.

Commands
  chains                                   the eight chains (+ Solana, data only), their ids, gas tokens and data families
  get PATH                                 GET any public /v1 path, print the JSON
  token CHAIN QUERY                        resolve a symbol, name or 0x address to token candidates
  price CHAIN TOKEN                        price and 24h stats from Chord's index (+ CoinGecko on 43114/8453/56/42161/1)
  board CHAIN [--sort volume] [--limit 10] most traded / moving tokens in the last 24h, compact rows
                                           token / price / board also take CHAIN = solana (read-only: base58 mints,
                                           case-sensitive; Chord does not quote or build Solana swaps)
  stock SYMBOL                             one Robinhood Chain stock token: price, reference (NAV), gap, off-hours share
  meta-quote CHAIN TOKEN_IN TOKEN_OUT AMOUNT [--wallet 0x..]
                                           QUOTE HERE FIRST: Chord's router, or a third-party aggregator only when
                                           Chord fails; the answer names the provider that quoted it
  meta-swap QUOTE_FILE WALLET --user-confirmed
                                           build the unsigned transaction for a saved meta quote (simulated as WALLET)
  quote CHAIN TOKEN_IN TOKEN_OUT AMOUNT    Chord's own router only, with the full route; AMOUNT in human units ("50", "0.25")
  swap-tx QUOTE_FILE WALLET --user-confirmed
                                           build the unsigned transaction for a saved quote
  simulate QUOTE_FILE WALLET               eth_call the built transaction from WALLET before signing

No configuration and no key: every command uses the public API at https://api.getchord.xyz (60 requests a minute).

Exit codes: 0 ok, 1 API or network error, 2 bad input or refused, 3 ambiguous token or stale quote.
"""
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.getchord.xyz"
UA = "chord-skill/0.1 (+https://getchord.xyz/docs)"
ZERO = "0x0000000000000000000000000000000000000000"
# The Chord router proxy sits at the same address on every chain Chord routes on.
ROUTER = "0x1b1fee89a381e595fe6536b99ba91f3e16e9601a"
ARC_USDC = "0x3600000000000000000000000000000000000000"
ADDR_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
# Solana (read-only data, /v1/chains/solana/*): base58 addresses are CASE-SENSITIVE. Never lower-case one.
SOL_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
SOL_KEYS = ("solana", "sol")
SOL_MAJORS = {"SOL": "So11111111111111111111111111111111111111112", "WSOL": "So11111111111111111111111111111111111111112",
              "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"}
SOL_NOTE = ("Chord's Solana tape reads the swap events of 11 venues (PumpSwap, pump.fun, Meteora, Raydium, Orca), not prop AMMs "
            "(SolFi, HumidiFi) or order books: majors such as SOL/USDC are understated; pump / Meteora / Raydium tokens are accurate. "
            "Symbols are creator-chosen and shared by many mints: identify tokens by mint. Timestamps (updatedAt too) are Unix seconds.")
QUOTE_MAX_AGE_S = 60

CHAINS = {
    143: {"key": "monad", "name": "Monad", "gas": "MON", "native": "MON", "family": "/v1/tokens/market?chain=143"},
    4663: {"key": "robinhood", "name": "Robinhood Chain", "gas": "ETH", "native": "ETH", "family": "/v1/rh/*"},
    5042: {"key": "arc", "name": "Arc", "gas": "USDC", "native": None, "family": "/v1/arc/*"},
    43114: {"key": "avalanche", "name": "Avalanche", "gas": "AVAX", "native": "AVAX", "family": "/v1/chains/avalanche/*"},
    8453: {"key": "base", "name": "Base", "gas": "ETH", "native": "ETH", "family": "/v1/chains/base/*"},
    56: {"key": "bnb", "name": "BNB Chain", "gas": "BNB", "native": "BNB", "family": "/v1/chains/bnb/*"},
    42161: {"key": "arbitrum", "name": "Arbitrum One", "gas": "ETH", "native": "ETH", "family": "/v1/chains/arbitrum/*"},
    1: {"key": "ethereum", "name": "Ethereum", "gas": "ETH", "native": "ETH", "family": "/v1/chains/ethereum/*"},
}
ALIASES = {
    "monad": 143, "mon": 143, "143": 143,
    "robinhood": 4663, "robinhood-chain": 4663, "rh": 4663, "4663": 4663,
    "arc": 5042, "5042": 5042,
    "avalanche": 43114, "avax": 43114, "43114": 43114,
    "base": 8453, "8453": 8453,
    "bnb": 56, "bsc": 56, "bnb-chain": 56, "bnbchain": 56, "56": 56,
    "arbitrum": 42161, "arbitrum-one": 42161, "arb": 42161, "arb1": 42161, "42161": 42161,
    # "eth" alone is the coin (on Base, Arbitrum, Robinhood Chain too), never the chain.
    "ethereum": 1, "ethereum-mainnet": 1, "eth-mainnet": 1, "mainnet": 1, "1": 1,
}


def die(msg, code=2):
    print(json.dumps({"error": msg}), file=sys.stderr)
    sys.exit(code)


def is_solana(raw):
    return str(raw).strip().lower() in SOL_KEYS


def chain_id(raw):
    if is_solana(raw):
        die("Solana is read-only in Chord: use 'token solana QUERY', 'price solana MINT', 'board solana' or 'get /v1/chains/solana/...'. Chord does not quote, route or build Solana swaps.")
    cid = ALIASES.get(str(raw).strip().lower().replace(" ", "-"))
    if cid is None:
        die(f"unsupported chain '{raw}'. Chord covers: " + ", ".join(f"{v['name']} ({k})" for k, v in CHAINS.items()) + ", plus Solana data (read-only). It does not cover Optimism, Polygon or other chains.")
    return cid


def api(path, body=None, retries=1):
    """GET (or POST when body is given) a /v1 path. One retry on 429 / 5xx / network error, then fail."""
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Accept": "application/json", "User-Agent": UA}
    if data is not None:
        headers["Content-Type"] = "application/json"
    last = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data is not None else "GET")
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode() or "null")
        except urllib.error.HTTPError as e:
            text = e.read().decode(errors="replace")
            try:
                payload = json.loads(text)
            except ValueError:
                payload = {"error": f"HTTP_{e.code}", "message": text[:300]}
            if e.code == 429 or e.code >= 500:
                last = {"status": e.code, **(payload if isinstance(payload, dict) else {"body": payload})}
                if attempt < retries:
                    wait = min(int(e.headers.get("Retry-After") or 5), 15)
                    time.sleep(wait)
                    continue
            else:
                return {"__http_error__": e.code, **(payload if isinstance(payload, dict) else {"body": payload})}
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = {"error": "NETWORK", "message": str(e)[:300]}
            if attempt < retries:
                time.sleep(3)
                continue
    print(json.dumps({"error": "API_UNAVAILABLE", "detail": last, "path": path}), file=sys.stderr)
    sys.exit(1)


def token_list(cid):
    d = api(f"/v1/tokens?chain={cid}")
    if isinstance(d, dict) and "__http_error__" in d:
        die(f"token list for chain {cid} failed: {d}", 1)
    return d if isinstance(d, list) else d.get("tokens", [])


def slim(t, source):
    return {
        "symbol": t.get("symbol"), "name": t.get("name"), "address": t.get("address"), "decimals": t.get("decimals"),
        "tags": t.get("tags") or [], "listed": t.get("listed", t.get("verified")), "flags": t.get("flags") or None,
        "volume24hUsd": round(t["volume24h"]) if isinstance(t.get("volume24h"), (int, float)) else None, "source": source,
    }


def detail_decimals(cid, addr):
    """Decimals for an address that is not on the curated list, from the chain's own token endpoint."""
    a = addr.lower()
    if cid == 5042:
        d = api(f"/v1/arc/token/{a}?hours=1")
    elif cid == 4663:
        d = api(f"/v1/rh/token/{a}?hours=1")
    elif cid in (43114, 8453, 56, 42161, 1):
        d = api(f"/v1/chains/{cid}/token/{a}?hours=1")
    else:
        return None
    tok = d.get("token") if isinstance(d, dict) else None
    if isinstance(tok, dict) and isinstance(tok.get("decimals"), int):
        return {"symbol": tok.get("symbol"), "name": tok.get("name"), "address": tok.get("address") or a, "decimals": tok["decimals"], "tags": tok.get("tags") or [], "listed": tok.get("listed", False), "flags": tok.get("flags") or None, "volume24hUsd": None, "source": "token-endpoint (not on the curated list)"}
    return None


def candidates(cid, query):
    q = query.strip()
    meta = CHAINS[cid]
    if cid == 5042 and q.lower() == ZERO:
        q = ARC_USDC  # on Arc the zero address is an alias for the 6-decimal USDC predeploy
    if meta["native"] and q.upper() == meta["native"]:
        return [{"symbol": meta["native"], "name": f"{meta['native']} (native gas token)", "address": ZERO, "decimals": 18, "tags": ["native"], "listed": True, "flags": None, "volume24hUsd": None, "source": "native"}]
    lst = token_list(cid)
    if ADDR_RE.match(q):
        hit = [slim(t, "curated list") for t in lst if t["address"].lower() == q.lower()]
        if hit:
            return hit
        d = detail_decimals(cid, q)
        return [d] if d else [{"symbol": None, "name": None, "address": q, "decimals": None, "tags": [], "listed": False, "flags": None, "volume24hUsd": None, "source": "unknown to Chord on this chain"}]
    exact = [slim(t, "curated list") for t in lst if (t.get("symbol") or "").lower() == q.lower()]
    if cid == 5042:
        # The Arc search covers every token traded in 24 h (listed or not) and carries impostor / wash flags.
        s = api("/v1/arc/tokens/search?" + urllib.parse.urlencode({"q": q, "limit": 20}))
        seen = {c["address"].lower() for c in exact}
        for t in (s.get("tokens") or []) if isinstance(s, dict) else []:
            if (t.get("symbol") or "").lower() == q.lower() and t["address"].lower() not in seen:
                exact.append(slim(t, "arc search (24h tape)"))
    if exact:
        return exact
    ql = q.lower()
    loose = [slim(t, "curated list (partial match)") for t in lst if ql in (t.get("symbol") or "").lower() or ql in (t.get("name") or "").lower()]
    return loose[:15]


def rank_candidates(c):
    """Curated list first, then by 24h volume (unknown volume last)."""
    return sorted(c, key=lambda x: (x["source"] not in ("native", "curated list"), -(x.get("volume24hUsd") or 0)))


def resolve_one(cid, query, role):
    """One token or a clean refusal. Curated-list identity wins; several curated tokens with one symbol = ask."""
    c = candidates(cid, query)
    exact = [x for x in c if "partial" not in x["source"] and x.get("decimals") is not None]
    if ADDR_RE.match(query.strip()):
        if not exact:
            die(f"{role}: {query} is not a token Chord can price on {CHAINS[cid]['name']} ({cid}); cannot read its decimals. Do not guess decimals.", 2)
        return exact[0]
    curated = [x for x in exact if x["source"] in ("native", "curated list")]
    if len(curated) == 1:
        pick = dict(curated[0])
        others = len(exact) - 1
        if others:
            pick["sameSymbolOthers"] = others
        return pick
    if not curated and len(exact) == 1:
        return exact[0]
    if not exact:
        print(json.dumps({"error": "NO_MATCH", "role": role, "chain": cid, "query": query, "nearMatches": c[:10]}, indent=1), file=sys.stderr)
        sys.exit(3)
    ranked = rank_candidates(exact)
    print(json.dumps({"error": "AMBIGUOUS", "role": role, "chain": cid, "query": query, "message": "Several tokens share this symbol. Show the user the candidates (with full addresses) and ask which one; then pass the 0x address.", "candidates": ranked[:10], "moreCandidates": max(0, len(ranked) - 10)}, indent=1), file=sys.stderr)
    sys.exit(3)


def to_raw(amount, decimals):
    s = amount.strip()
    if not re.match(r"^\d+(\.\d+)?$", s):
        die(f"amount '{amount}' must be plain digits with an optional '.' decimal point (no commas, no units, no scientific notation)")
    whole, _, frac = s.partition(".")
    if len(frac) > decimals:
        die(f"amount '{amount}' has {len(frac)} decimal places; this token has {decimals}. Ask the user, do not round silently.")
    raw = int(whole) * 10 ** decimals + int((frac + "0" * decimals)[:decimals] or "0")
    if raw <= 0:
        die("amount must be greater than zero")
    return str(raw)


def to_human(raw, decimals):
    v = int(raw)
    neg = v < 0
    v = abs(v)
    whole, frac = divmod(v, 10 ** decimals)
    f = str(frac).rjust(decimals, "0").rstrip("0") if decimals else ""
    return ("-" if neg else "") + (f"{whole}.{f}" if f else str(whole))


def num(x, nd=None):
    if not isinstance(x, (int, float)):
        return x
    return round(x, nd) if nd is not None else x


def cmd_price(args):
    if len(args) != 2:
        die("usage: chord.py price CHAIN TOKEN")
    if is_solana(args[0]):
        return sol_price(args[1])
    cid = chain_id(args[0])
    tok = resolve_one(cid, args[1], "token")
    a = tok["address"].lower()
    out = {"chain": {"id": cid, "name": CHAINS[cid]["name"]}, "token": {k: tok.get(k) for k in ("symbol", "name", "address", "decimals", "tags")}, "source": "Chord index (last on-chain trade on the main venue)"}
    if cid in (143, 4663):
        m = api(f"/v1/tokens/market?chain={cid}")
        row = (m.get("market") or {}).get(a) if isinstance(m, dict) else None
        if not row and a == ZERO:
            wrapped = next((x for x in token_list(cid) if (x.get("symbol") or "").upper() == "W" + CHAINS[cid]["native"]), None)
            if wrapped:
                row = (m.get("market") or {}).get(wrapped["address"].lower())
                out["note"] = f"native {CHAINS[cid]['native']} priced through {wrapped['symbol']} {wrapped['address']}"
        if not row:
            die(f"Chord has no 24h market row for {tok['symbol']} {tok['address']} on {CHAINS[cid]['name']} ({cid})", 1)
        out.update({"priceUsd": row.get("priceUsd"), "change24hPct": row.get("change24h"), "volume24hUsd": row.get("volume24h"), "trades24h": row.get("txns24h"), "liquidityUsd": row.get("liquidityUsd"), "updatedAt": m.get("updatedAt")})
    elif cid == 5042:
        d = api(f"/v1/arc/token/{a}?hours=24")
        t2 = d.get("token") if isinstance(d, dict) else None
        if not isinstance(t2, dict) or t2.get("priceUsd") is None:
            die(f"Chord has no 24h trades for {a} on Arc (5042)", 1)
        out.update({k: t2.get(k) for k in ("priceUsd", "change24hPct", "volume24h", "trades24h", "traders", "marketCapUsd", "listed", "flags", "routable")})
        out["updatedAt"] = d.get("updatedAt")
    else:
        d = api(f"/v1/chains/{cid}/token/{a}?hours=24")
        if isinstance(d, dict) and "__http_error__" in d:
            die(f"{d.get('error')}: {d.get('message')}", 1)
        s = d.get("stats24h") or {}
        out.update({"priceUsd": s.get("priceUsd"), "change24hPct": s.get("change24hPct"), "volume24hUsd": s.get("volUsd"), "trades24h": s.get("trades"), "dominantDex": s.get("dominantDex"), "lastTradeTs": s.get("lastTs"), "coverage": d.get("coverage"), "updatedAt": d.get("updatedAt")})
        r = api(f"/v1/chains/{cid}/token/{a}/ref-price")
        out["coingecko"] = ({"priceUsd": r.get("priceUsd"), "change24hPct": r.get("change24hPct")} if isinstance(r, dict) and "__http_error__" not in r
                            else {"error": r.get("error"), "message": r.get("message")} if isinstance(r, dict) else None)
    print(json.dumps({k: v for k, v in out.items() if v is not None}, indent=1))


def cmd_board(args):
    opts, rest = parse_opts(args, {"--sort": True, "--limit": True})
    if len(rest) != 1:
        die("usage: chord.py board CHAIN [--sort volume|trades|change|traders|mcap|new] [--limit 10]")
    sort = opts.get("--sort", "volume")
    limit = int(opts.get("--limit", 10))
    if not 1 <= limit <= 100:
        die("--limit must be between 1 and 100")
    if is_solana(rest[0]):
        return sol_board(sort, limit)
    cid = chain_id(rest[0])
    allowed = {5042: ("volume", "trades", "traders", "change", "mcap"), 4663: ("volume", "trades", "traders", "change"), 143: ("volume", "change")}.get(cid, ("volume", "trades", "change"))
    if sort not in allowed:
        die(f"--sort on {CHAINS[cid]['name']} takes one of {', '.join(allowed)}")
    rows, meta = [], {}
    if cid == 5042:
        d = api(f"/v1/arc/tokens?sort={sort}&limit={limit}")
        meta = {"total": d.get("total"), "updatedAt": d.get("updatedAt")}
        for t in d.get("tokens") or []:
            rows.append({"symbol": t.get("symbol"), "name": t.get("name"), "address": t.get("address"), "volume24hUsd": num(t.get("volume24h"), 0), "trades24h": t.get("trades24h"), "traders": t.get("traders"), "priceUsd": t.get("priceUsd"), "change24hPct": num(t.get("change24hPct"), 2), "marketCapUsd": num(t.get("marketCapUsd"), 0), "listed": t.get("listed"), "flags": t.get("flags") or None})
    elif cid == 4663:
        d = api(f"/v1/rh/tokens?sort={sort}&limit={limit}")
        meta = {"total": d.get("total"), "updatedAt": d.get("updatedAt")}
        for t in d.get("tokens") or []:
            rows.append({"symbol": t.get("symbol"), "name": t.get("name"), "address": t.get("address"), "tags": t.get("tags"), "volume24hUsd": num(t.get("volume24h"), 0), "trades24h": t.get("trades24h"), "traders": t.get("traders"), "priceUsd": t.get("priceUsd"), "change24hPct": num(t.get("change24hPct"), 2)})
    elif cid == 143:
        m = api("/v1/tokens/market?chain=143")
        names = {x["address"].lower(): x for x in token_list(143)}
        key = "volume24h" if sort == "volume" else "change24h"
        items = sorted(((a, r) for a, r in (m.get("market") or {}).items() if isinstance(r.get(key), (int, float))), key=lambda ar: -ar[1][key])[:limit]
        meta = {"total": len(m.get("market") or {}), "updatedAt": m.get("updatedAt"), "note": "sorted locally from /v1/tokens/market?chain=143"}
        for a, r in items:
            n = names.get(a, {})
            rows.append({"symbol": n.get("symbol"), "name": n.get("name"), "address": n.get("address", a), "volume24hUsd": r.get("volume24h"), "priceUsd": r.get("priceUsd"), "change24hPct": num(r.get("change24h"), 2)})
    else:
        d = api(f"/v1/chains/{cid}/tokens?sort={sort}&limit={limit}")
        if isinstance(d, dict) and "__http_error__" in d:
            die(f"{d.get('error')}: {d.get('message')}", 1)
        meta = {"total": d.get("total"), "coverage": d.get("coverage"), "ingestFloor": d.get("ingestFloor"), "updatedAt": d.get("updatedAt")}
        for t in d.get("tokens") or []:
            rows.append({"symbol": t.get("symbol"), "name": t.get("name"), "address": t.get("address"), "volume24hUsd": num(t.get("volume24h"), 0), "trades24h": t.get("trades24h"), "priceUsd": t.get("priceUsd"), "change24hPct": num(t.get("change24hPct"), 2), "dominantDex": t.get("dominantDex")})
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    print(json.dumps({"chain": {"id": cid, "name": CHAINS[cid]["name"]}, "sort": sort, "window": "24h", "source": "Chord index", **meta, "rows": rows}, indent=1))


# -- Solana (read-only) ---------------------------------------------------------------------------
def sol_api(path):
    d = api("/v1/chains/solana" + path)
    if isinstance(d, dict) and "__http_error__" in d:
        die(f"{d.get('error')}: {d.get('message')}", 1)
    return d


def sol_candidates(query):
    q = query.strip()
    major = q.upper().lstrip("$")
    if not SOL_RE.match(q) and major in SOL_MAJORS:
        return [{"mint": SOL_MAJORS[major], "symbol": "SOL" if major == "WSOL" else major, "source": "canonical mint"}]
    d = sol_api("/search?" + urllib.parse.urlencode({"q": q}))
    return [{"mint": t.get("token"), "symbol": t.get("symbol"), "name": t.get("name"), "priceUsd": t.get("priceUsd"), "liquidityUsd": num(t.get("liquidityUsd"), 0),
             "volumeUsd": num(t.get("volumeUsd"), 0), "source": "solana tape search"} for t in d.get("tokens") or []]


def sol_token(query):
    c = sol_candidates(query)
    out = {"chain": {"id": "solana", "name": "Solana"}, "query": query, "candidates": c[:10], "note": SOL_NOTE}
    if len(c) > 10:
        out["moreCandidates"] = len(c) - 10
    if len(c) > 1:
        out["warning"] = (f"{len(c)} mints match. Symbols on Solana are creator-chosen: show the candidates with their full mints and ask, or use the mint "
                          "the user named. volumeUsd here is the main pool's volume since the tape first saw it, a ranking hint only.")
    print(json.dumps(out, indent=1, ensure_ascii=False))


def sol_price(query):
    q = query.strip()
    if SOL_RE.match(q):
        mint = q
    else:
        c = sol_candidates(q)
        if not c:
            die(f"no Solana token on Chord's tape has the symbol or name '{q}' (exact match). Ask the user for the mint.", 3)
        if len(c) > 1:
            print(json.dumps({"error": "AMBIGUOUS", "chain": "solana", "query": q, "message": "Several Solana mints use this symbol or name. Show the candidates (full mints) and ask which one; then pass the mint.",
                              "candidates": c[:10]}, indent=1, ensure_ascii=False), file=sys.stderr)
            sys.exit(3)
        mint = c[0]["mint"]
    d = sol_api(f"/token/{urllib.parse.quote(mint, safe='')}?hours=24")
    st = sol_api("/status")
    main_pool = next((p for p in d.get("pools") or [] if p.get("priceUsd") is not None), None)
    out = {"chain": {"id": "solana", "name": "Solana"}, "token": {"mint": d.get("token"), "symbol": d.get("symbol"), "name": d.get("name"), "decimals": d.get("decimals")},
           "source": "Chord Solana tape (last swap on the main pool)", "priceUsd": d.get("priceUsd"), "change1hPct": num(d.get("change1hPct"), 2), "change24hPct": num(d.get("change24hPct"), 2),
           "volume24hUsd": num(d.get("volume24hUsd"), 0), "trades24h": d.get("trades24h"), "liquidityUsd": num(d.get("liquidityUsd"), 0), "marketCapUsd": num(d.get("marketCapUsd"), 0),
           "mainPool": {"pool": main_pool.get("pool"), "dex": main_pool.get("dex"), "quote": main_pool.get("quote")} if main_pool else None,
           "venues24h": [{"dex": v.get("dex"), "volumeUsd": num(v.get("volumeUsd"), 0)} for v in d.get("venues") or []],
           "updatedAt": d.get("updatedAt"), "tape": {"ok": st.get("ok"), "blockAgeS": st.get("blockAgeS")}, "note": SOL_NOTE}
    if st.get("ok") is False:
        out["warning"] = f"The Solana tape is behind right now (newest block written {st.get('blockAgeS')} s ago): say the numbers may be stale."
    print(json.dumps({k: v for k, v in out.items() if v is not None}, indent=1, ensure_ascii=False))


def sol_board(sort, limit):
    if sort not in ("volume", "trades", "change", "new"):
        die("--sort on Solana takes one of volume, trades, change, new")
    d = sol_api(f"/tokens?sort={sort}&limit={limit}")
    rows = []
    for i, t in enumerate(d.get("tokens") or [], 1):
        rows.append({"rank": i, "symbol": t.get("symbol"), "name": t.get("name"), "mint": t.get("token"), "volume24hUsd": num(t.get("volume24hUsd"), 0), "trades24h": t.get("trades24h"),
                     "priceUsd": t.get("priceUsd"), "change24hPct": num(t.get("change24hPct"), 2), "liquidityUsd": num(t.get("liquidityUsd"), 0), "marketCapUsd": num(t.get("marketCapUsd"), 0), "dex": t.get("dex")})
    note = SOL_NOTE + (" There are no wash flags on Solana: a volume hundreds of times the liquidity, or millions of dollars over a few hundred trades, "
                       "usually means a thin or wash-traded pool. Say so when you show such a row.")
    print(json.dumps({"chain": {"id": "solana", "name": "Solana"}, "sort": sort, "window": "24h", "source": "Chord Solana tape", "updatedAt": d.get("updatedAt"), "rows": rows, "note": note},
                     indent=1, ensure_ascii=False))


def cmd_stock(args):
    if len(args) != 1:
        die("usage: chord.py stock SYMBOL_OR_ADDRESS")
    q = args[0].strip().lower()
    d = api("/v1/rh/stocks")
    rows = d.get("stocks") or [] if isinstance(d, dict) else []
    hit = [s for s in rows if s.get("symbol", "").lower() == q or s.get("address", "").lower() == q]
    if not hit:
        die(f"'{args[0]}' is not one of the {len(rows)} stock tokens on Robinhood Chain (4663). A memecoin may use the ticker: check with 'chord.py token robinhood {args[0]}'.", 3)
    s = hit[0]
    out = {"chain": {"id": 4663, "name": "Robinhood Chain"}, "symbol": s.get("symbol"), "name": s.get("name"), "address": s.get("address"), "tags": s.get("tags"),
           "priceUsd": s.get("priceUsd"), "change24hPct": num(s.get("change24hPct"), 2), "volume24hUsd": num(s.get("volume24h"), 0), "trades24h": s.get("trades24h"), "traders": s.get("traders"), "liquidityUsd": s.get("liquidityUsd"),
           "referencePriceUsd": s.get("navUsd"), "referenceSource": s.get("navSource"), "gapToReferencePct": num(s.get("basisPct"), 4),
           "offHours7dSharePct": num((s.get("offHours7d") or {}).get("sharePct"), 1), "lastTradeTs": s.get("lastTradeTs"), "updatedAt": d.get("updatedAt"),
           "notes": ["priceUsd is the last on-chain trade of the token, from Chord's index.",
                     "referenceSource xyz-perp = the trade.xyz perpetual's mark on Hyperliquid (tracks the share 24/7, may carry a funding premium off-hours); catalogue = the issuer's rate at the last catalogue refresh; null = Chord has no reference for this stock.",
                     "gapToReferencePct = (priceUsd / referencePriceUsd - 1) x 100; positive = token above the reference.",
                     "The token tracks the share; it is not the share."]}
    print(json.dumps(out, indent=1))


def cmd_chains(_args):
    rows = [{"chainId": k, "key": v["key"], "name": v["name"], "gasToken": v["gas"], "dataEndpoints": v["family"], "quoteAndSwap": True} for k, v in CHAINS.items()]
    rows.append({"chainId": None, "key": "solana", "name": "Solana", "gasToken": "SOL", "dataEndpoints": "/v1/chains/solana/*", "quoteAndSwap": False})
    print(json.dumps({"chains": rows, "router": ROUTER, "note": "The eight EVM chains answer /v1/quote, POST /v1/swap and /v1/candles with ?chain=<id>. Solana is data only, under /v1/chains/solana/* (no chain id; base58 addresses, case-sensitive)."}, indent=1))


def cmd_get(args):
    if not args or not args[0].startswith("/v1/"):
        die("usage: chord.py get /v1/<path>?<query>")
    path = args[0]
    if re.search(r"/v1/(admin|internal)", path):
        die("admin paths are not part of the public API")
    d = api(path)
    print(json.dumps(d, indent=1))
    if isinstance(d, dict) and "__http_error__" in d:
        sys.exit(1)


def cmd_token(args):
    if len(args) < 2:
        die("usage: chord.py token CHAIN QUERY")
    if is_solana(args[0]):
        return sol_token(" ".join(args[1:]))
    cid = chain_id(args[0])
    c = rank_candidates(candidates(cid, " ".join(args[1:])))
    out = {"chain": {"id": cid, "name": CHAINS[cid]["name"]}, "query": " ".join(args[1:]), "candidates": c[:10]}
    if len(c) > 10:
        out["moreCandidates"] = len(c) - 10
    exact = [x for x in c if "partial" not in x["source"]]
    curated = [x for x in exact if x["source"] in ("native", "curated list")]
    if len(exact) > 1 and len(curated) == 1:
        out["warning"] = f"{len(exact) - 1} other token(s) use this symbol on this chain. The curated-list entry ({curated[0]['address']}) is the one Chord treats as canonical; the rest are copies or unrelated tokens. Always show the address you use."
    elif len(exact) > 1:
        out["warning"] = "Several curated tokens share this symbol on this chain. Never pick silently: show the candidates with their full addresses and ask, or use the one the user named by address."
    if cid == 4663 and any("stock" in (x.get("tags") or []) for x in c) and any("stock" not in (x.get("tags") or []) for x in exact):
        out["stockNote"] = "Only the row tagged 'stock' (name ends with 'Robinhood Token') is the tokenized share. Rows tagged 'meme' are unrelated coins using the same ticker."
    if any(x.get("flags") for x in c):
        out["flagsNote"] = "flags.impostor = an unlisted token wearing a listed symbol; flags.wash = volume carried by one or two wallets."
    print(json.dumps(out, indent=1))


def parse_opts(args, names):
    opts, rest, i = {}, [], 0
    while i < len(args):
        a = args[i]
        if a in names:
            if names[a]:
                if i + 1 >= len(args):
                    die(f"{a} needs a value")
                opts[a] = args[i + 1]
                i += 2
                continue
            opts[a] = True
        else:
            rest.append(a)
        i += 1
    return opts, rest


def cmd_quote(args):
    opts, rest = parse_opts(args, {"--slippage-bps": True, "--save": True})
    if len(rest) != 4:
        die("usage: chord.py quote CHAIN TOKEN_IN TOKEN_OUT AMOUNT [--slippage-bps 50] [--save FILE]")
    cid = chain_id(rest[0])
    slip = int(opts.get("--slippage-bps", 50))
    if not 1 <= slip <= 5000:
        die("--slippage-bps must be between 1 and 5000")
    tin = resolve_one(cid, rest[1], "tokenIn")
    tout = resolve_one(cid, rest[2], "tokenOut")
    if tin["address"].lower() == tout["address"].lower():
        die("tokenIn and tokenOut are the same token")
    raw = to_raw(rest[3], tin["decimals"])
    qs = urllib.parse.urlencode({"chain": cid, "inputMint": tin["address"], "outputMint": tout["address"], "amount": raw, "slippageBps": slip})
    q = api(f"/v1/quote?{qs}")
    if isinstance(q, dict) and "__http_error__" in q:
        print(json.dumps({"error": q.get("error"), "message": q.get("message"), "status": q["__http_error__"], "chain": cid}, indent=1), file=sys.stderr)
        sys.exit(1)
    plan = q.get("routePlan") or []
    meta = CHAINS[cid]
    summary = {
        "chain": {"id": cid, "name": meta["name"], "gasToken": meta["gas"]},
        "sell": {"symbol": tin["symbol"], "address": tin["address"], "decimals": tin["decimals"], "amount": to_human(raw, tin["decimals"]), "amountRaw": raw},
        "buy": {"symbol": tout["symbol"], "address": tout["address"], "decimals": tout["decimals"]},
        "noRoute": len(plan) == 0,
    }
    warnings = []
    if not plan:
        summary["noRouteReason"] = q.get("noRouteReason")
        warnings.append("No route: Chord found no pool that can fill this. Do not build a transaction.")
    else:
        gross = int(q["outputAmount"])
        fee = int(q.get("feeAmount") or 0)
        summary.update({
            "expectedOutGross": to_human(gross, tout["decimals"]),
            "fee": {"bps": q.get("feeBps"), "amount": to_human(fee, tout["decimals"]), "token": tout["symbol"]},
            "expectedOutAfterFee": to_human(gross - fee, tout["decimals"]),
            "minimumReceived": to_human(q["otherAmountThreshold"], tout["decimals"]),
            "slippageBps": q.get("slippageBps", slip),
            "priceImpactPct": q.get("priceImpactPct"),
            "valueLossPct": q.get("valueLossPct"),
            "route": [{"dex": s["swapInfo"].get("dex"), "percent": s.get("percent"), "pool": s["swapInfo"].get("pool")} for s in plan],
            "router": ROUTER,
            "approvalNeeded": tin["address"] != ZERO,  # Arc USDC resolves to the predeploy, which needs one
            "blockNumber": q.get("blockNumber"),
        })
        try:
            if float(q.get("priceImpactPct") or 0) >= 2:
                warnings.append(f"Price impact {q.get('priceImpactPct')}% is high: suggest a smaller size.")
        except ValueError:
            pass
        vl = q.get("valueLossPct")
        if isinstance(vl, (int, float)) and vl >= 2:
            warnings.append(f"The output is worth {vl}% less than the input at Chord's own prices.")
        if q.get("preliminary"):
            warnings.append("Preliminary (fast) quote; re-quote without fast before building.")
    for t in (tin, tout):
        if t.get("sameSymbolOthers"):
            warnings.append(f"{t['sameSymbolOthers']} other token(s) on {meta['name']} also use the symbol {t['symbol']}; this quote uses the curated one at {t['address']}. Show that address.")
        if t.get("flags"):
            warnings.append(f"{t['symbol']} {t['address']} carries flags {t['flags']}.")
        if t["source"].startswith("token-endpoint"):
            warnings.append(f"{t['symbol'] or t['address']} is not on Chord's curated list for {meta['name']}: verify the contract before trading.")
    summary["warnings"] = warnings
    summary["quotedAt"] = int(time.time())
    path = opts.get("--save") or os.path.join(tempfile.gettempdir(), f"chord-quote-{cid}-{int(time.time())}.json")
    with open(path, "w") as f:
        json.dump({"chain": cid, "savedAt": summary["quotedAt"], "slippageBps": slip, "summary": summary, "quote": q}, f)
    summary["quoteFile"] = path
    print(json.dumps(summary, indent=1))


def load_quote(path):
    try:
        with open(path) as f:
            saved = json.load(f)
    except (OSError, ValueError) as e:
        die(f"cannot read quote file {path}: {e}")
    if "quote" not in saved or "chain" not in saved:
        die("not a quote file written by chord.py quote")
    return saved


def cmd_swap_tx(args):
    opts, rest = parse_opts(args, {"--user-confirmed": False})
    if len(rest) != 2:
        die("usage: chord.py swap-tx QUOTE_FILE WALLET --user-confirmed")
    if not opts.get("--user-confirmed"):
        die("refused: show the user the quote summary and wait for their explicit yes in a new message, then re-run with --user-confirmed. Never pass this flag on the user's behalf.")
    saved = load_quote(rest[0])
    wallet = rest[1]
    if not ADDR_RE.match(wallet):
        die(f"wallet '{wallet}' is not a 0x address with 40 hex characters")
    age = int(time.time()) - int(saved.get("savedAt") or 0)
    if age > QUOTE_MAX_AGE_S:
        print(json.dumps({"error": "STALE_QUOTE", "ageSeconds": age, "message": "Re-quote, show the new numbers, and confirm again if the minimum received moved."}), file=sys.stderr)
        sys.exit(3)
    if not (saved["quote"].get("routePlan") or []):
        die("this quote has no route; there is nothing to build")
    cid = saved["chain"]
    d = api("/v1/swap", body={"quoteResponse": saved["quote"], "userPublicKey": wallet, "slippageBps": saved.get("slippageBps", 50), "chain": cid})
    if isinstance(d, dict) and "__http_error__" in d:
        print(json.dumps({"error": d.get("error"), "message": d.get("message"), "status": d["__http_error__"]}, indent=1), file=sys.stderr)
        sys.exit(1)
    tx = d.get("transaction") or {}
    problems = []
    if str(tx.get("to", "")).lower() != ROUTER:
        problems.append(f"transaction.to {tx.get('to')} is not the Chord router {ROUTER}: DO NOT SIGN")
    if int(tx.get("chainId") or cid) != cid:
        problems.append(f"transaction.chainId {tx.get('chainId')} does not match the quoted chain {cid}: DO NOT SIGN")
    s = saved["summary"]
    out = {
        "unsigned": True,
        "chain": s["chain"],
        "from": wallet,
        "transaction": tx,
        "summary": {k: s.get(k) for k in ("sell", "buy", "expectedOutAfterFee", "minimumReceived", "priceImpactPct", "route")},
        "approval": None if s["sell"]["address"] == ZERO else {"token": s["sell"]["address"], "spender": tx.get("to"), "amountRaw": s["sell"]["amountRaw"], "note": "Approve exactly this amount (not unlimited) before the swap, or the swap reverts."},
        "problems": problems,
        "next": "Hand this to the user's own wallet to review and sign. Chord and this script never sign or broadcast.",
    }
    print(json.dumps(out, indent=1))
    if problems:
        sys.exit(2)


def cmd_simulate(args):
    if len(args) != 2:
        die("usage: chord.py simulate QUOTE_FILE WALLET   (builds the tx again and eth_calls it from WALLET)")
    saved = load_quote(args[0])
    wallet = args[1]
    if not ADDR_RE.match(wallet):
        die("wallet must be a 0x address")
    cid = saved["chain"]
    d = api("/v1/swap", body={"quoteResponse": saved["quote"], "userPublicKey": wallet, "slippageBps": saved.get("slippageBps", 50), "chain": cid})
    tx = (d or {}).get("transaction") if isinstance(d, dict) else None
    if not tx:
        die(f"could not build the transaction: {d}", 1)
    r = api("/v1/swap/simulate", body={"chain": cid, "from": wallet, "to": tx["to"], "data": tx["data"], "value": tx.get("value", "0")})
    print(json.dumps({"chain": cid, "from": wallet, "simulation": r}, indent=1))


# The ONLY contracts a meta-aggregator transaction may target or ask an approval for, per provider and chain.
# A pinned copy of packages/api/src/services/meta/config.ts (a test there keeps the two equal): the API checks its own
# list, this is the second, independent check before anything reaches a wallet.
META_ROUTERS = {
    "chord": {c: [ROUTER] for c in (143, 4663, 5042, 43114, 8453, 56, 42161, 1)},
    "kyberswap": {c: ["0x6131b5fae19ea4f9d964eac0408e4408b66337b5"] for c in (143, 4663, 5042, 43114, 8453, 56, 42161, 1)},
    "monorail": {143: ["0xa68a7f0601effdc65c64d9c47ca1b18d96b4352c"]},
    "lifi": {
        143: ["0x026f252016a7c47cdef1f05a3fc9e20c92a49c37"],
        4663: ["0xb477751b76cf82d00a686a1232f5fcd772414af3"],
        5042: ["0xa4072583658fae592a3506a42431cb6316a8d40b"],
        43114: ["0x1231deb6f5749ef6ce6943a275a1d3e7486f4eae"],
        8453: ["0x1231deb6f5749ef6ce6943a275a1d3e7486f4eae"],
        56: ["0x1231deb6f5749ef6ce6943a275a1d3e7486f4eae"],
        42161: ["0x1231deb6f5749ef6ce6943a275a1d3e7486f4eae"],
        1: ["0x1231deb6f5749ef6ce6943a275a1d3e7486f4eae"],
    },
    "relay": {c: ["0xccc88a9d1b4ed6b0eaba998850414b24f1c315be", "0xb92fe925dc43a0ecde6c8b1a2709c170ec4fff4f"] for c in (143, 4663, 5042, 43114, 8453, 56, 42161, 1)},
}
PROVIDER_NAMES = {"chord": "Chord router", "kyberswap": "KyberSwap", "monorail": "Monorail", "lifi": "LI.FI", "relay": "Relay"}


def meta_problems(m, cid):
    """Why a meta answer must not be signed (empty list = nothing found)."""
    problems = []
    prov = m.get("provider")
    allowed = [a.lower() for a in (META_ROUTERS.get(prov) or {}).get(cid, [])]
    tx = m.get("tx") or {}
    if tx:
        if str(tx.get("to", "")).lower() not in allowed:
            problems.append(f"transaction.to {tx.get('to')} is not a known {PROVIDER_NAMES.get(prov, prov)} router on chain {cid}: DO NOT SIGN")
        if int(tx.get("chainId") or 0) != cid:
            problems.append(f"transaction.chainId {tx.get('chainId')} does not match the quoted chain {cid}: DO NOT SIGN")
        sim = m.get("simulation") or {}
        if sim.get("ok") is False:
            problems.append(f"the simulation reverted ({sim.get('revert')}): DO NOT SIGN")
        elif sim.get("ok") is not True and prov != "chord":
            problems.append("a third-party transaction without a passing simulation: DO NOT SIGN")
    ap = m.get("approval")
    if ap and str(ap.get("spender", "")).lower() not in allowed:
        problems.append(f"approval spender {ap.get('spender')} is not a known {PROVIDER_NAMES.get(prov, prov)} router on chain {cid}: DO NOT APPROVE")
    return problems


def meta_summary(m, cid, tin, tout, raw):
    meta = CHAINS[cid]
    prov = m.get("provider")
    s = {
        "chain": {"id": cid, "name": meta["name"], "gasToken": meta["gas"]},
        "sell": {"symbol": tin["symbol"], "address": m.get("tokenIn") or tin["address"], "decimals": tin["decimals"], "amount": to_human(raw, tin["decimals"]), "amountRaw": raw},
        "buy": {"symbol": tout["symbol"], "address": m.get("tokenOut") or tout["address"], "decimals": tout["decimals"]},
        "noRoute": prov is None,
        "provider": prov,
        "providerName": PROVIDER_NAMES.get(prov, prov),
        "fallbackReason": m.get("fallbackReason"),
        "attempts": [{"provider": a.get("provider"), "status": a.get("status"), "ms": a.get("ms")} for a in (m.get("attempts") or [])],
    }
    if prov is not None:
        s.update({
            "expectedOutAfterFee": to_human(m["amountOut"], tout["decimals"]),
            "minimumReceived": to_human(m["minAmountOut"], tout["decimals"]),
            "minimumReceivedRaw": m["minAmountOut"],
            "slippageBps": m.get("slippageBps"),
            "priceImpactPct": m.get("priceImpactPct"),
            "valueLossPct": m.get("valueLossPct"),
            "fee": {"bps": m.get("feeBps"), "recipient": m.get("feeRecipient")},
            "route": m.get("route", {}).get("venues"),
            "router": (m.get("tx") or {}).get("to") or (m.get("approval") or {}).get("spender"),
            "approval": m.get("approval"),
            "simulation": m.get("simulation"),
            "safety": m.get("safety"),
            "expiresAt": m.get("expiresAt"),
        })
    return s


def cmd_meta_quote(args):
    opts, rest = parse_opts(args, {"--slippage-bps": True, "--save": True, "--wallet": True})
    if len(rest) != 4:
        die("usage: chord.py meta-quote CHAIN TOKEN_IN TOKEN_OUT AMOUNT [--slippage-bps 50] [--wallet 0x..] [--save FILE]")
    cid = chain_id(rest[0])
    slip = int(opts.get("--slippage-bps", 50))
    if not 1 <= slip <= 5000:
        die("--slippage-bps must be between 1 and 5000")
    wallet = opts.get("--wallet")
    if wallet and not ADDR_RE.match(wallet):
        die(f"wallet '{wallet}' is not a 0x address with 40 hex characters")
    tin = resolve_one(cid, rest[1], "tokenIn")
    tout = resolve_one(cid, rest[2], "tokenOut")
    if tin["address"].lower() == tout["address"].lower():
        die("tokenIn and tokenOut are the same token")
    raw = to_raw(rest[3], tin["decimals"])
    params = {"chain": cid, "tokenIn": tin["address"], "tokenOut": tout["address"], "amount": raw, "slippageBps": slip}
    q = dict(params, taker=wallet) if wallet else params
    m = api(f"/v1/meta/quote?{urllib.parse.urlencode(q)}")
    if isinstance(m, dict) and "__http_error__" in m:
        print(json.dumps({"error": m.get("error"), "message": m.get("message"), "status": m["__http_error__"], "chain": cid, "attempts": m.get("attempts")}, indent=1), file=sys.stderr)
        sys.exit(1)
    summary = meta_summary(m, cid, tin, tout, raw)
    warnings = list(m.get("warnings") or [])
    prov = m.get("provider")
    if prov is None:
        warnings.append("No route anywhere: neither Chord's router nor any fallback aggregator can fill this. Do not build a transaction.")
    elif prov != "chord":
        warnings.append(f"Chord's own router did not answer ({m.get('fallbackReason')}). This quote is from {PROVIDER_NAMES.get(prov, prov)}, a third-party aggregator: say so, and show its router address as the approval spender.")
    for label in ("priceImpactPct", "valueLossPct"):
        try:
            v = float(m.get(label)) if m.get(label) is not None else None
        except (TypeError, ValueError):
            v = None
        if v is not None and v >= 2:
            warnings.append(f"{label} {v}% is high: suggest a smaller size.")
    sf = m.get("safety") or {}
    if sf.get("worstFlag") in ("medium", "high"):
        warnings.append(f"Security scan ({sf.get('source')}): {sf.get('worstFlag')} risk. " + " ".join(sf.get("risks") or [])[:300])
    for t in (tin, tout):
        if t.get("sameSymbolOthers"):
            warnings.append(f"{t['sameSymbolOthers']} other token(s) on {CHAINS[cid]['name']} also use the symbol {t['symbol']}; this quote uses the curated one at {t['address']}. Show that address.")
        if t.get("flags"):
            warnings.append(f"{t['symbol']} {t['address']} carries flags {t['flags']}.")
        if t["source"].startswith("token-endpoint"):
            warnings.append(f"{t['symbol'] or t['address']} is not on Chord's curated list for {CHAINS[cid]['name']}: verify the contract before trading.")
    problems = meta_problems(m, cid) if prov is not None else []
    summary["warnings"] = warnings
    summary["problems"] = problems
    summary["quotedAt"] = int(time.time())
    path = opts.get("--save") or os.path.join(tempfile.gettempdir(), f"chord-meta-{cid}-{int(time.time())}.json")
    with open(path, "w") as f:
        json.dump({"kind": "meta", "chain": cid, "savedAt": summary["quotedAt"], "slippageBps": slip, "params": params, "tokens": {"in": tin, "out": tout}, "summary": summary}, f)
    summary["quoteFile"] = path
    print(json.dumps(summary, indent=1))
    if problems:
        sys.exit(2)


def cmd_meta_swap(args):
    opts, rest = parse_opts(args, {"--user-confirmed": False})
    if len(rest) != 2:
        die("usage: chord.py meta-swap QUOTE_FILE WALLET --user-confirmed")
    if not opts.get("--user-confirmed"):
        die("refused: show the user the meta-quote summary (provider, minimum received, router) and wait for their explicit yes in a new message, then re-run with --user-confirmed. Never pass this flag on the user's behalf.")
    try:
        with open(rest[0]) as f:
            saved = json.load(f)
    except (OSError, ValueError) as e:
        die(f"cannot read quote file {rest[0]}: {e}")
    if saved.get("kind") != "meta" or "params" not in saved:
        die("not a quote file written by chord.py meta-quote")
    wallet = rest[1]
    if not ADDR_RE.match(wallet):
        die(f"wallet '{wallet}' is not a 0x address with 40 hex characters")
    age = int(time.time()) - int(saved.get("savedAt") or 0)
    if age > QUOTE_MAX_AGE_S:
        print(json.dumps({"error": "STALE_QUOTE", "ageSeconds": age, "message": "Re-quote, show the new numbers, and confirm again if the provider or the minimum received moved."}), file=sys.stderr)
        sys.exit(3)
    old = saved["summary"]
    if old.get("noRoute"):
        die("this quote has no route; there is nothing to build")
    cid = saved["chain"]
    m = api("/v1/meta/swap", body=dict(saved["params"], taker=wallet))
    if isinstance(m, dict) and "__http_error__" in m:
        print(json.dumps({"error": m.get("error"), "message": m.get("message"), "status": m["__http_error__"], "attempts": m.get("attempts")}, indent=1), file=sys.stderr)
        sys.exit(1)
    problems = meta_problems(m, cid)
    if not m.get("tx"):
        problems.append("the answer carries no transaction")
    # The user said yes to ONE provider and ONE minimum. Anything else is a new decision.
    if m.get("provider") != old.get("provider"):
        problems.append(f"the provider changed from {old.get('providerName')} to {PROVIDER_NAMES.get(m.get('provider'), m.get('provider'))} since the confirmed quote: show the new summary and ask again")
    elif int(m.get("minAmountOut") or 0) < int(old.get("minimumReceivedRaw") or 0):
        problems.append("the minimum received is lower than the one the user confirmed: show the new summary and ask again")
    s = meta_summary(m, cid, saved["tokens"]["in"], saved["tokens"]["out"], saved["params"]["amount"])
    out = {
        "unsigned": True,
        "chain": s["chain"],
        "from": wallet,
        "provider": s["provider"],
        "providerName": s["providerName"],
        "fallbackReason": s["fallbackReason"],
        "transaction": m.get("tx"),
        "approval": None if not m.get("approval") else dict(m["approval"], note=("This token (USDT on Ethereum) reverts a new approval while an old one is left: approve 0 to this spender first, then exactly this amount, then swap." if m["approval"].get("resetFirst") else "Approve exactly this amount (not unlimited) to this spender before the swap.")),
        "simulation": m.get("simulation"),
        "summary": {k: s.get(k) for k in ("sell", "buy", "expectedOutAfterFee", "minimumReceived", "priceImpactPct", "valueLossPct", "route")},
        "warnings": m.get("warnings") or [],
        "problems": problems,
        "next": "Hand this to the user's own wallet to review and sign. Chord and this script never sign or broadcast.",
    }
    print(json.dumps(out, indent=1))
    if problems:
        sys.exit(2)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        return
    cmd, args = sys.argv[1], sys.argv[2:]
    handlers = {"chains": cmd_chains, "get": cmd_get, "token": cmd_token, "price": cmd_price, "board": cmd_board, "stock": cmd_stock, "quote": cmd_quote, "swap-tx": cmd_swap_tx, "simulate": cmd_simulate, "meta-quote": cmd_meta_quote, "meta-swap": cmd_meta_swap}
    if cmd not in handlers:
        die(f"unknown command '{cmd}'. Run chord.py --help.")
    handlers[cmd](args)


if __name__ == "__main__":
    main()
