"""Verify Telegram Mini App initData on a server. Python standard library only.

Two ways, both from https://core.telegram.org/bots/webapps (checked 2026-11-23):

* verify_hmac(init_data, bot_token)       - your server owns the bot token
* verify_ed25519(init_data, bot_id, key)  - a third party with only the bot id (Bot API 8.0)

Both return the parsed fields (with `user`, `receiver`, `chat` decoded from JSON) or raise
InitDataError. Both check `auth_date` (Telegram sets no lifetime; pass max_age for your policy:
references/mini-apps/security.md section 4) and reject duplicate keys.

The Python standard library has no Ed25519, so a small verifier written from RFC 8032 (section 5.1)
is included. It only verifies (no secret keys, so constant time is not a concern for it); it is slow
(about 10 ms) but correct, and tested against the RFC 8032 vectors. Prefer a vetted library
(`cryptography`, PyNaCl) where dependencies are allowed.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import time
import urllib.parse

TELEGRAM_ED25519_PROD = "e7bf03a2fa4602af4580703d88dda5bb59f32ed8b02a56c187fe7d34caed242d"
TELEGRAM_ED25519_TEST = "40055058a4ee38156a06562e52eece92a771bcd8346a8c4615cb7376eddf72ec"
JSON_FIELDS = ("user", "receiver", "chat")
CLOCK_SKEW = 60
KEY = re.compile(r"[a-z_]{1,64}")
SIGNATURE = re.compile(r"[A-Za-z0-9_-]{86}(?:==)?")  # 64 bytes in base64url, padding optional


class InitDataError(ValueError):
    """initData is malformed, forged, expired or from the future. The message is safe to log."""


# ------------------------------------------------------------------ parsing

def parse(init_data: str) -> dict[str, str]:
    """Strict query-string parse: no duplicate keys, no empty input."""
    if not isinstance(init_data, str) or not init_data or len(init_data) > 16384:
        raise InitDataError("empty or oversized initData")
    if init_data.startswith("?") or any("=" not in part for part in init_data.split("&")):
        raise InitDataError("initData is not a query string")  # same grammar as the TypeScript twin
    try:
        pairs = urllib.parse.parse_qsl(init_data, keep_blank_values=True, strict_parsing=True)
    except ValueError as exc:
        raise InitDataError("initData is not a query string") from exc
    fields: dict[str, str] = {}
    for key, value in pairs:
        if key in fields:
            raise InitDataError(f"duplicate field {key!r}")
        # The check string joins key=value pairs with newlines: a newline inside a value (%0A) could fold the
        # next field into this one without changing the signed text. Telegram never sends one (JSON escapes it).
        if not KEY.fullmatch(key) or "\n" in value or "\r" in value:
            raise InitDataError("malformed field name or value")
        fields[key] = value
    return fields


def check_string(fields: dict[str, str], exclude: tuple[str, ...]) -> str:
    return "\n".join(f"{k}={v}" for k, v in sorted(fields.items()) if k not in exclude)


def _decode(fields: dict[str, str]) -> dict:
    out: dict = dict(fields)
    for key in JSON_FIELDS:
        if key in out:
            try:
                out[key] = json.loads(out[key])
            except ValueError as exc:
                raise InitDataError(f"{key} is not JSON") from exc
    return out


def _check_age(fields: dict[str, str], max_age: int | None, now: float | None) -> None:
    raw = fields.get("auth_date", "")
    if not re.fullmatch(r"[0-9]{1,12}", raw):
        raise InitDataError("auth_date missing or not a number")
    now = time.time() if now is None else now
    age = now - int(raw)
    if age < -CLOCK_SKEW:
        raise InitDataError("auth_date is in the future")
    if max_age is not None and age > max_age:
        raise InitDataError("initData expired")


# ------------------------------------------------------------------ bot token (HMAC-SHA256)

def secret_key(bot_token: str) -> bytes:
    """HMAC_SHA256(key="WebAppData", msg=bot_token). Keep this in memory instead of the token if you can."""
    return hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()


def verify_hmac(init_data: str, bot_token: str | None = None, *, key: bytes | None = None,
                max_age: int | None = 86400, now: float | None = None) -> dict:
    """Every field except `hash` (so `signature` stays in), sorted, key=value joined by newlines."""
    fields = parse(init_data)
    received = fields.get("hash", "")
    if len(received) != 64 or any(c not in "0123456789abcdef" for c in received):
        raise InitDataError("hash missing or malformed")
    if key is None:
        if not bot_token:
            raise InitDataError("no bot token or secret key configured")
        key = secret_key(bot_token)
    expected = hmac.new(key, check_string(fields, ("hash",)).encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received):
        raise InitDataError("hash mismatch")
    _check_age(fields, max_age, now)
    return _decode(fields)


# ------------------------------------------------------------------ third party (Ed25519)

def verify_ed25519(init_data: str, bot_id: int, public_key_hex: str = TELEGRAM_ED25519_PROD, *,
                   max_age: int | None = 86400, now: float | None = None) -> dict:
    """`"<bot_id>:WebAppData\\n"` + every field except `hash` and `signature`, sorted, newline-joined.
    `signature` is base64url without padding. Choose the public key from configuration, never the request."""
    fields = parse(init_data)
    sig_b64 = fields.get("signature", "")
    if not sig_b64:
        raise InitDataError("signature missing")
    if not SIGNATURE.fullmatch(sig_b64):
        raise InitDataError("signature or public key malformed")
    try:
        signature = base64.b64decode(sig_b64 + "=" * (-len(sig_b64) % 4), altchars=b"-_", validate=True)
        public_key = bytes.fromhex(public_key_hex)
    except (ValueError, TypeError) as exc:
        raise InitDataError("signature or public key malformed") from exc
    message = f"{int(bot_id)}:WebAppData\n" + check_string(fields, ("hash", "signature"))
    if not ed25519_verify(public_key, message.encode(), signature):
        raise InitDataError("signature mismatch")
    _check_age(fields, max_age, now)
    return _decode(fields)


# ------------------------------------------------------------------ Ed25519 verify (RFC 8032, 5.1)

_P = 2 ** 255 - 19
_L = 2 ** 252 + 27742317777372353535851937790883648493
_D = -121665 * pow(121666, _P - 2, _P) % _P
_SQRT_M1 = pow(2, (_P - 1) // 4, _P)


def _add(a, b):
    """Extended coordinates (X, Y, Z, T), x = X/Z, y = Y/Z, xy = T/Z."""
    x1, y1, z1, t1 = a
    x2, y2, z2, t2 = b
    aa = (y1 - x1) * (y2 - x2) % _P
    bb = (y1 + x1) * (y2 + x2) % _P
    cc = 2 * t1 * t2 * _D % _P
    dd = 2 * z1 * z2 % _P
    e, f, g, h = bb - aa, dd - cc, dd + cc, bb + aa
    return (e * f % _P, g * h % _P, f * g % _P, e * h % _P)


def _mul(s: int, point):
    result = (0, 1, 1, 0)
    while s:
        if s & 1:
            result = _add(result, point)
        point = _add(point, point)
        s >>= 1
    return result


def _equal(a, b) -> bool:
    return (a[0] * b[2] - b[0] * a[2]) % _P == 0 and (a[1] * b[2] - b[1] * a[2]) % _P == 0


def _recover_x(y: int, sign: int) -> int | None:
    if y >= _P:
        return None
    x2 = (y * y - 1) * pow(_D * y * y + 1, _P - 2, _P) % _P
    if x2 == 0:
        return None if sign else 0
    x = pow(x2, (_P + 3) // 8, _P)
    if (x * x - x2) % _P != 0:
        x = x * _SQRT_M1 % _P
    if (x * x - x2) % _P != 0:
        return None
    if (x & 1) != sign:
        x = _P - x
    return x


def _decompress(data: bytes):
    if len(data) != 32:
        return None
    y = int.from_bytes(data, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    x = _recover_x(y, sign)
    return None if x is None else (x, y, 1, x * y % _P)


_GY = 4 * pow(5, _P - 2, _P) % _P
_G = (_recover_x(_GY, 0), _GY, 1, _recover_x(_GY, 0) * _GY % _P)


def ed25519_verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
    if len(public_key) != 32 or len(signature) != 64:
        return False
    a = _decompress(public_key)
    r = _decompress(signature[:32])
    s = int.from_bytes(signature[32:], "little")
    if a is None or r is None or s >= _L:
        return False
    if _equal(_mul(8, a), (0, 1, 1, 0)):  # identity or small-order key: never a real Telegram key
        return False
    k = int.from_bytes(hashlib.sha512(signature[:32] + public_key + message).digest(), "little") % _L
    return _equal(_mul(s, _G), _add(r, _mul(k, a)))


def ed25519_public_key(seed: bytes) -> bytes:
    """Test helper: public key of a 32-byte seed (for self-signed test vectors only)."""
    h = hashlib.sha512(seed).digest()
    a = int.from_bytes(h[:32], "little") & ((1 << 254) - 8) | (1 << 254)
    return _compress(_mul(a, _G))


def ed25519_sign(seed: bytes, message: bytes) -> bytes:
    """Test helper only: not constant time. Never sign with a real secret key in this code."""
    h = hashlib.sha512(seed).digest()
    a = int.from_bytes(h[:32], "little") & ((1 << 254) - 8) | (1 << 254)
    public = _compress(_mul(a, _G))
    r = int.from_bytes(hashlib.sha512(h[32:] + message).digest(), "little") % _L
    big_r = _compress(_mul(r, _G))
    k = int.from_bytes(hashlib.sha512(big_r + public + message).digest(), "little") % _L
    return big_r + ((r + k * a) % _L).to_bytes(32, "little")


def _compress(point) -> bytes:
    x, y, z, _ = point
    zi = pow(z, _P - 2, _P)
    x, y = x * zi % _P, y * zi % _P
    return (y | ((x & 1) << 255)).to_bytes(32, "little")
