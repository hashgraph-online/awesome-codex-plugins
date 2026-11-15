"""TON wallet flows started from a widget (Bot API 10.4).

What Telegram gives the bot (widget_query.type):
* {"type": "data", "wallet_card": TonWalletCard?} - a request sent with
  {wallet: true}: the user's profile wallet card (address, balance, stickers).
* {"type": "sign_data", "wallet": WidgetQueryWallet, "sign_data": "<json>"} -
  TON Connect signData result, signed for the domain "bot<bot_id>".
* {"type": "sent_transaction", "wallet": WidgetQueryWallet, "msg_hash": "..."} -
  the wallet *says* it sent a message.

Boundary (no invented guarantees):
* `from` is authenticated by Telegram - who tapped is reliable.
* `sent_transaction` is a notification, NOT proof of payment. The order becomes
  "awaiting confirmation"; only an on-chain check (sender, recipient, amount,
  comment/payload, success) moves it to "paid". That check is the bot's job,
  through its own TON indexer/node - outside Telegram.
* `sign_data` must be verified by the bot: ed25519 signature with the wallet's
  public_key, domain bot<bot_id>, fresh timestamp, and the public key tied to
  the address on chain (state_init). The standard library has no ed25519, so
  the verifier is injected.
* The wallet that pays is the device's wallet; it can differ from the profile
  wallet card. Never put `from` in the transaction.
* After a TIMEOUT the payment may have gone out: never ask to pay again
  blindly - show the order's server state.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol


class OrderState(str, Enum):
    NEW = "new"
    INVOICED = "invoiced"                 # a transaction request was handed out
    AWAITING_CONFIRMATION = "awaiting"    # wallet reported sent_transaction
    PAID = "paid"                         # verified on chain
    MISMATCH = "mismatch"                 # chain says something else
    EXPIRED = "expired"


@dataclass
class Order:
    order_id: str
    user_id: int
    amount_nano: int
    merchant_address: str
    state: OrderState = OrderState.NEW
    valid_until: int = 0
    msg_hashes: list[str] = field(default_factory=list)


class ChainVerifier(Protocol):
    def check(self, *, msg_hash: str, sender: str, recipient: str,
              amount_nano: int, order_id: str) -> str:
        """Return 'confirmed', 'pending', or 'mismatch'."""


class SignatureVerifier(Protocol):
    def verify(self, *, sign_data_json: str, public_key_hex: str, state_init_b64: str,
               expected_address: str, expected_domain: str, expected_payload: dict[str, Any],
               max_age_s: int) -> bool:
        """True only if ALL hold: the ed25519 signature is valid for public_key; the
        public key belongs to expected_address (derive the address from state_init and
        compare); the signed domain is expected_domain; the signed payload equals the
        server-issued challenge; the timestamp is within max_age_s."""


@dataclass
class SignChallenge:
    """Server-issued, single-use challenge for wallet.signData (prevents replaying a
    signature made for another account, wallet or moment)."""
    user_id: int
    nonce: str
    issued_at: int
    used: bool = False

    def payload(self) -> dict[str, Any]:
        return {"type": "text", "text": f"Link wallet to account {self.user_id} · {self.nonce}"}


def transaction_request(order: Order, *, now: int, ttl: int = 300) -> dict[str, Any] | None:
    """TON Connect sendTransaction request the bot returns in answerWidgetQuery.

    Attach the order reference as a text-comment `payload` (base64 BOC) built
    with your TON library, e.g. @ton/core:
        beginCell().storeUint(0, 32).storeStringTail(order_id).endCell().toBoc()
    It is omitted here on purpose - this repo does not ship a BOC encoder.
    Returns None when the order is already awaiting confirmation, paid or disputed:
    answer with the order's state instead of a new transaction.
    """
    if order.state in (OrderState.AWAITING_CONFIRMATION, OrderState.PAID, OrderState.MISMATCH):
        return None                     # never re-invoice a paid / possibly paid order
    if not (order.state == OrderState.INVOICED and order.valid_until > now):
        order.valid_until = now + ttl   # a replayed "pay:" within validity gets the SAME request
        order.state = OrderState.INVOICED
    return {"valid_until": order.valid_until,
            "messages": [{"address": order.merchant_address, "amount": str(order.amount_nano)}]}


def wallet_card_summary(card: dict[str, Any] | None) -> str:
    """Human summary of a TonWalletCard (balance is in the smallest units)."""
    if not card:
        return "No wallet card on the profile."
    tons = int(card["amount"]) / 1_000_000_000
    stickers = len(card.get("stickers", []))
    return f"Wallet {short_address(card['address'])}: {tons:.2f} TON, {stickers} NFT sticker(s)"


def short_address(addr: str) -> str:
    return addr if len(addr) <= 12 else f"{addr[:4]}…{addr[-4:]}"


def on_sent_transaction(order: Order, query: dict[str, Any], verifier: ChainVerifier,
                        seen_hashes: dict[str, str] | None = None) -> dict[str, Any]:
    """Handle {"type": "sent_transaction"}; returns the answer for the widget.
    `seen_hashes` (msg_hash -> order_id, persistent) stops one transfer from being
    claimed for two orders; the chain check must also match the order's comment."""
    if query["from"]["id"] != order.user_id:
        return {"ok": False, "err": "not_your_order"}
    t = query["type"]
    if order.state in (OrderState.PAID, OrderState.MISMATCH):
        return {"ok": True, "state": order.state.value}       # repeated notification
    if order.state == OrderState.NEW:
        return {"ok": False, "err": "no_invoice"}
    seen = seen_hashes if seen_hashes is not None else {}
    if seen.setdefault(t["msg_hash"], order.order_id) != order.order_id:
        return {"ok": False, "err": "transfer_already_used"}
    order.msg_hashes.append(t["msg_hash"])
    order.state = OrderState.AWAITING_CONFIRMATION
    verdict = verifier.check(msg_hash=t["msg_hash"], sender=t["wallet"]["address"],
                             recipient=order.merchant_address,
                             amount_nano=order.amount_nano, order_id=order.order_id)
    if verdict == "confirmed":
        order.state = OrderState.PAID
    elif verdict == "mismatch":
        order.state = OrderState.MISMATCH
    return {"ok": True, "state": order.state.value}


def on_sign_data(query: dict[str, Any], verifier: SignatureVerifier, *, bot_id: int,
                 challenge: "SignChallenge | None", now: int, max_age_s: int = 300) -> dict[str, Any]:
    """Verify a signData result against a server-issued challenge. The address that
    gets linked is the one the verifier proved owns the key - never just the claim."""
    t = query["type"]
    wallet = t["wallet"]
    if challenge is None or challenge.used or challenge.user_id != query["from"]["id"]:
        return {"ok": False, "err": "no_challenge"}
    if now - challenge.issued_at > max_age_s:
        return {"ok": False, "err": "challenge_expired"}
    if not wallet.get("public_key") or not wallet.get("state_init"):
        return {"ok": False, "err": "unknown_public_key"}      # can't verify: say so
    good = verifier.verify(sign_data_json=t["sign_data"], public_key_hex=wallet["public_key"],
                           state_init_b64=wallet["state_init"], expected_address=wallet["address"],
                           expected_domain=f"bot{bot_id}", expected_payload=challenge.payload(),
                           max_age_s=max_age_s)
    if not good:
        return {"ok": False, "err": "bad_signature"}
    challenge.used = True                                      # single use
    return {"ok": True, "address": short_address(wallet["address"])}


def describe_transfer(service: dict[str, Any]) -> str:
    """Message.ton_wallet_transfer service message -> a line for the user."""
    amount = int(service["amount"]) / 1_000_000_000
    direction = "Sent" if amount < 0 else "Received"
    comment = service.get("comment")
    status = "pending" if not service.get("transaction_id") else "recorded"
    tail = f" — “{comment}”" if comment else (" — encrypted comment" if "comment" not in service else "")
    return f"{direction} {abs(amount):.2f} TON {'to' if amount < 0 else 'from'} {short_address(service['peer_address'])} ({status}){tail}"
