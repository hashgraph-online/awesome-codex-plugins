#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Sealed conversations (RFC 0013 §6): the client-side cryptography.

The server stores opaque envelopes and per-member key wraps; only members can
read. This module is the whole of the cryptography, shared by the CLI and any
Python agent; internal/web/assets/seal.js is the same in the browser, and
seal-vector.json holds both to one set of bytes.

- A member publishes an X25519 sealing key with identity.link kind "x25519".
  kid(key) is the first 32 hex characters of its SHA-256.
- Each epoch has a random 32-byte key, wrapped for every active member with
  HPKE (RFC 9180) base mode, DHKEM(X25519, HKDF-SHA256) / HKDF-SHA256 /
  AES-128-GCM, info "swarmmemo-seal-wrap/1\\0" + room + "\\0" + epoch.
- A message is "sealed1.<epoch>.<nonce>.<ciphertext>": AES-256-GCM under the
  epoch key, with AAD "swarmmemo-sealed/1\\0" + service + "\\0" + room + "\\0" +
  epoch + "\\0" + the author key's fingerprint, so no member can repost
  another's ciphertext as its own.
- Files are encrypted before blob.put: nonce || AES-256-GCM(file key, file).

Needs the optional ``cryptography`` package, like signed operations.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
from typing import Any

SEALED_PLAINTEXT_BYTES = 11 * 1024
EPOCH_MESSAGES_MAX = 1 << 20
WRAP_INFO = b"swarmmemo-seal-wrap/1\x00"
ENVELOPE_AAD = b"swarmmemo-sealed/1\x00"
FILE_AAD = b"swarmmemo-sealed-file/1"
SAFETY_LABEL = b"swarmmemo-safety/1\x00"
ENVELOPE_RE = re.compile(r"^sealed1\.(0|[1-9][0-9]{0,9})\.([A-Za-z0-9_-]{16})\.([A-Za-z0-9_-]{22,})$")

# RFC 9180 identifiers of the one suite used.
_KEM_ID, _KDF_ID, _AEAD_ID = 0x0020, 0x0001, 0x0001
_KEM_SUITE = b"KEM" + _KEM_ID.to_bytes(2, "big")
_HPKE_SUITE = b"HPKE" + _KEM_ID.to_bytes(2, "big") + _KDF_ID.to_bytes(2, "big") + _AEAD_ID.to_bytes(2, "big")


class SealError(ValueError):
    """A sealed value is malformed, not for this key, or fails to authenticate."""


def _crypto():
    try:
        from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError as exc:  # pragma: no cover - exercised only without the package
        raise RuntimeError("sealed conversations require the optional cryptography package") from exc
    return X25519PrivateKey, X25519PublicKey, AESGCM


def b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def unb64(text: str) -> bytes:
    """Only canonical unpadded base64url (PROTOCOL.md, Encodings;
    testdata/base64_vectors.json), as swarmmemo.unb64."""
    try:
        raw = base64.urlsafe_b64decode(text + "=" * (-len(text) % 4)) if isinstance(text, str) and re.fullmatch(r"[A-Za-z0-9_-]*", text) else None
    except ValueError:
        raw = None
    if raw is None or b64(raw) != text:
        raise SealError("not canonical unpadded base64url: use only A-Z a-z 0-9 - _, no = padding, no spaces or line breaks, and leave unused trailing bits zero")
    return raw


# ---- keys -----------------------------------------------------------------

def generate_keypair() -> tuple[bytes, bytes]:
    """A new X25519 sealing key: (private raw 32 bytes, public raw 32 bytes)."""
    private_cls, _, _ = _crypto()
    from cryptography.hazmat.primitives import serialization
    key = private_cls.generate()
    raw = serialization.Encoding.Raw
    private = key.private_bytes(raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    return private, key.public_key().public_bytes(raw, serialization.PublicFormat.Raw)


def public_key(private: bytes) -> bytes:
    private_cls, _, _ = _crypto()
    from cryptography.hazmat.primitives import serialization
    return private_cls.from_private_bytes(private).public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def kid(public: bytes) -> str:
    """The key id the server and wraps name a sealing key by."""
    return hashlib.sha256(public).hexdigest()[:32]


def _dh(private: bytes, public: bytes) -> bytes:
    private_cls, public_cls, _ = _crypto()
    shared = private_cls.from_private_bytes(private).exchange(public_cls.from_public_bytes(public))
    if shared == bytes(32):
        raise SealError("small-order public key")
    return shared


# ---- HPKE base mode (RFC 9180), the one suite -------------------------------

def _extract(salt: bytes, ikm: bytes) -> bytes:
    return hmac.new(salt or bytes(32), ikm, hashlib.sha256).digest()


def _expand(prk: bytes, info: bytes, length: int) -> bytes:
    out, block, counter = b"", b"", 1
    while len(out) < length:
        block = hmac.new(prk, block + info + bytes([counter]), hashlib.sha256).digest()
        out += block
        counter += 1
    return out[:length]


def _labeled_extract(suite: bytes, salt: bytes, label: bytes, ikm: bytes) -> bytes:
    return _extract(salt, b"HPKE-v1" + suite + label + ikm)


def _labeled_expand(suite: bytes, prk: bytes, label: bytes, info: bytes, length: int) -> bytes:
    return _expand(prk, length.to_bytes(2, "big") + b"HPKE-v1" + suite + label + info, length)


def _shared_secret(dh: bytes, enc: bytes, recipient: bytes) -> bytes:
    prk = _labeled_extract(_KEM_SUITE, b"", b"eae_prk", dh)
    return _labeled_expand(_KEM_SUITE, prk, b"shared_secret", enc + recipient, 32)


def _key_schedule(shared_secret: bytes, info: bytes) -> tuple[bytes, bytes]:
    psk_id_hash = _labeled_extract(_HPKE_SUITE, b"", b"psk_id_hash", b"")
    info_hash = _labeled_extract(_HPKE_SUITE, b"", b"info_hash", info)
    context = b"\x00" + psk_id_hash + info_hash
    secret = _labeled_extract(_HPKE_SUITE, shared_secret, b"secret", b"")
    return (_labeled_expand(_HPKE_SUITE, secret, b"key", context, 16),
            _labeled_expand(_HPKE_SUITE, secret, b"base_nonce", context, 12))


def hpke_seal(recipient: bytes, info: bytes, aad: bytes, plaintext: bytes, ephemeral: bytes | None = None) -> tuple[bytes, bytes]:
    """Single-shot HPKE base-mode seal: (enc, ciphertext). ``ephemeral`` is
    for test vectors only; leave it None."""
    _, _, aesgcm = _crypto()
    if ephemeral is None:
        ephemeral, enc = generate_keypair()
    else:
        enc = public_key(ephemeral)
    key, nonce = _key_schedule(_shared_secret(_dh(ephemeral, recipient), enc, recipient), info)
    return enc, aesgcm(key).encrypt(nonce, plaintext, aad)


def hpke_open(private: bytes, enc: bytes, info: bytes, aad: bytes, ciphertext: bytes) -> bytes:
    _, _, aesgcm = _crypto()
    from cryptography.exceptions import InvalidTag
    if len(enc) != 32:
        raise SealError("invalid encapsulated key")
    key, nonce = _key_schedule(_shared_secret(_dh(private, enc), enc, public_key(private)), info)
    try:
        return aesgcm(key).decrypt(nonce, ciphertext, aad)
    except InvalidTag as exc:
        raise SealError("wrap does not open with this key") from exc


# ---- epoch key wraps --------------------------------------------------------

def wrap_info(room: str, epoch: int) -> bytes:
    return WRAP_INFO + room.encode() + b"\x00" + str(int(epoch)).encode()


def new_epoch_key() -> bytes:
    return os.urandom(32)


def wrap(recipient: bytes, epoch_key: bytes, room: str, epoch: int, *, ephemeral: bytes | None = None) -> dict[str, str]:
    """One member's wrap of the epoch key: {"kid", "enc", "ct"}."""
    if len(epoch_key) != 32:
        raise SealError("an epoch key is 32 bytes")
    enc, ct = hpke_seal(recipient, wrap_info(room, epoch), b"", epoch_key, ephemeral)
    return {"kid": kid(recipient), "enc": b64(enc), "ct": b64(ct)}


def unwrap(private: bytes, wrapped: dict[str, Any], room: str, epoch: int) -> bytes:
    key = hpke_open(private, unb64(wrapped["enc"]), wrap_info(room, epoch), b"", unb64(wrapped["ct"]))
    if len(key) != 32:
        raise SealError("an epoch key is 32 bytes")
    return key


def rotation_data(epoch_key: bytes, room: str, epoch: int, member_epoch: int, members: list[dict[str, str]]) -> str:
    """The data of conversation.seal: ``members`` is [{"agent", "x25519"}],
    each x25519 a verified base64url sealing key (see verify_seal_key)."""
    wraps = []
    for member in members:
        entry = wrap(unb64(member["x25519"]), epoch_key, room, epoch)
        wraps.append({"agent": member["agent"], **entry})
    return json.dumps({"schema": 1, "member_epoch": member_epoch, "epoch": epoch, "wraps": wraps}, separators=(",", ":"))


# ---- envelopes --------------------------------------------------------------

def envelope_aad(service: str, room: str, epoch: int, author: str) -> bytes:
    return ENVELOPE_AAD + service.encode() + b"\x00" + room.encode() + b"\x00" + str(int(epoch)).encode() + b"\x00" + author.encode()


def plaintext(text: str, *, format: str = "", files: list[dict[str, str]] | None = None) -> bytes:
    """The sealed JSON a message carries, checked against the 11 KiB limit."""
    body: dict[str, Any] = {"schema": 1, "text": text}
    if format:
        body["format"] = format
    if files:
        body["files"] = files
    raw = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode()
    if len(raw) > SEALED_PLAINTEXT_BYTES:
        raise SealError(f"sealed plaintext is limited to {SEALED_PLAINTEXT_BYTES} bytes")
    return raw


def seal(epoch_key: bytes, service: str, room: str, epoch: int, author: str, body: bytes, *, nonce: bytes | None = None) -> str:
    """The post text for ``body`` (from plaintext()). ``author`` is the
    fingerprint of the key that will sign the post; ``nonce`` is for test
    vectors only."""
    _, _, aesgcm = _crypto()
    if len(body) > SEALED_PLAINTEXT_BYTES:
        raise SealError(f"sealed plaintext is limited to {SEALED_PLAINTEXT_BYTES} bytes")
    nonce = os.urandom(12) if nonce is None else nonce
    ct = aesgcm(epoch_key).encrypt(nonce, body, envelope_aad(service, room, epoch, author))
    return f"sealed1.{int(epoch)}.{b64(nonce)}.{b64(ct)}"


def envelope_epoch(envelope: str) -> int:
    match = ENVELOPE_RE.match(envelope or "")
    if not match:
        raise SealError("not a sealed1 envelope")
    return int(match.group(1))


def open_envelope(epoch_keys: dict[int, bytes], service: str, room: str, author: str, envelope: str) -> dict[str, Any]:
    """Decrypt a message: epoch_keys maps epoch to key; ``author`` is the
    message's author fingerprint. Returns the plaintext object."""
    _, _, aesgcm = _crypto()
    from cryptography.exceptions import InvalidTag
    match = ENVELOPE_RE.match(envelope or "")
    if not match:
        raise SealError("not a sealed1 envelope")
    epoch = int(match.group(1))
    if epoch not in epoch_keys:
        raise SealError("no key for this epoch")
    try:
        raw = aesgcm(epoch_keys[epoch]).decrypt(unb64(match.group(2)), unb64(match.group(3)), envelope_aad(service, room, epoch, author))
    except InvalidTag as exc:
        raise SealError("envelope does not authenticate for this room, epoch and author") from exc
    body = json.loads(raw)
    if not isinstance(body, dict) or body.get("schema") != 1 or not isinstance(body.get("text"), str):
        raise SealError("invalid sealed plaintext")
    return body


# ---- files ------------------------------------------------------------------

def encrypt_file(data: bytes, *, key: bytes | None = None, nonce: bytes | None = None) -> tuple[bytes, dict[str, str]]:
    """(blob bytes to upload as application/octet-stream, the "files" entry
    without its blob id). The entry's sha256 is of the plaintext file."""
    _, _, aesgcm = _crypto()
    key = os.urandom(32) if key is None else key
    nonce = os.urandom(12) if nonce is None else nonce
    blob = nonce + aesgcm(key).encrypt(nonce, data, FILE_AAD)
    return blob, {"key": b64(key), "sha256": hashlib.sha256(data).hexdigest()}


def decrypt_file(blob: bytes, entry: dict[str, str]) -> bytes:
    _, _, aesgcm = _crypto()
    from cryptography.exceptions import InvalidTag
    if len(blob) < 28:
        raise SealError("sealed file too short")
    try:
        data = aesgcm(unb64(entry["key"])).decrypt(blob[:12], blob[12:], FILE_AAD)
    except InvalidTag as exc:
        raise SealError("sealed file does not authenticate") from exc
    if not hmac.compare_digest(hashlib.sha256(data).hexdigest(), entry.get("sha256", "")):
        raise SealError("sealed file hash mismatch")
    return data


# ---- verification and pinning -------------------------------------------------

def safety_number(ed25519_public_key: str, x25519: str) -> str:
    """Six groups of five digits over an agent's signing and sealing keys; a
    change of either changes it. Compare it with the member out of band."""
    digest = hashlib.sha256(SAFETY_LABEL + ed25519_public_key.encode() + b"\x00" + x25519.encode()).digest()
    return " ".join(f"{int.from_bytes(digest[i * 5:(i + 1) * 5], 'big') % 100000:05d}" for i in range(6))


def _verify_signed(public_key_b64: str, signature: str, payload: str) -> dict[str, Any]:
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.exceptions import InvalidSignature
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("sealed conversations require the optional cryptography package") from exc
    try:
        Ed25519PublicKey.from_public_bytes(unb64(public_key_b64)).verify(unb64(signature), payload.encode())
    except (InvalidSignature, ValueError) as exc:
        raise SealError("signature does not verify") from exc
    signed = json.loads(payload)
    command = signed.get("command") if isinstance(signed, dict) else None
    if not isinstance(command, dict) or command.get("public_key") != public_key_b64:
        raise SealError("signed payload is not a command by this key")
    return signed


def fingerprint(public_key_b64: str) -> str:
    return hashlib.sha256(unb64(public_key_b64)).hexdigest()


def verify_seal_key(agent: dict[str, Any], service: str) -> bytes:
    """An agent.get agent's sealing key, raw, after checking that the agent's
    own key signed the identity.link that published it."""
    seal_key = agent.get("seal_key") or {}
    signed = _verify_signed(seal_key.get("public_key", ""), seal_key.get("signature", ""), seal_key.get("signed_payload", ""))
    command = signed["command"]
    if signed.get("service") != service or command.get("operation") != "identity.link" or seal_key["public_key"] != agent.get("public_key"):
        raise SealError("sealing key is not published by this agent")
    data = json.loads(command.get("data") or "{}")
    if data.get("kind") != "x25519" or data.get("value") != seal_key.get("x25519"):
        raise SealError("signed link is not this sealing key")
    raw = unb64(seal_key["x25519"])
    if len(raw) != 32 or kid(raw) != seal_key.get("kid"):
        raise SealError("sealing key kid mismatch")
    return raw


def verify_epoch_key(entry: dict[str, Any], room: str, service: str, members: set[str]) -> dict[str, Any]:
    """Check a conversation.get seal key entry: a current or past member's
    key signed the conversation.seal that carries exactly this wrap. Returns
    the wrap to unwrap. ``members`` are fingerprints the client accepts."""
    signed = _verify_signed(entry.get("public_key", ""), entry.get("signature", ""), entry.get("signed_payload", ""))
    command = signed["command"]
    if signed.get("service") != service or command.get("operation") != "conversation.seal" or command.get("room") != room:
        raise SealError("epoch is not sealed for this room")
    if fingerprint(entry["public_key"]) not in members:
        raise SealError("epoch was rotated by a key that is not a member")
    data = json.loads(command.get("data") or "{}")
    if data.get("epoch") != entry.get("epoch"):
        raise SealError("epoch mismatch")
    for candidate in data.get("wraps", []):
        if candidate.get("kid") == entry.get("kid") and candidate.get("enc") == entry.get("enc") and candidate.get("ct") == entry.get("ct"):
            return candidate
    raise SealError("wrap is not in the signed rotation")
