"""Telegram Stars payments: order -> invoice -> pre-checkout -> payment -> delivery
-> refund -> reconciliation (Bot API 10.5).

The pipeline and its screens: references/payments-pipeline.md. This module is the
Stars rail only; the Gram rail (TON wallet in a widget) lives in wallet.py.

What Telegram guarantees, and what this module adds on top:
* `pre_checkout_query` must be answered within 10 s or the payment is cancelled.
  The handler does local checks only, answers first, and does any slow work
  (a fresh invoice after a price change) after the answer.
* Only `successful_payment` proves a payment. Delivery happens there, once per
  `telegram_payment_charge_id` (UNIQUE in the store): a re-delivered update
  never delivers twice; a crash between "paid" and "delivered" is resumed.
* `payload` (1-128 bytes, never shown) is `ord:<order>.<tag>` for a personal
  order or `inv:<offer>.<tag>` for a multi-use invoice (group, channel,
  forward); `tag` = 8 bytes of HMAC-SHA256 in hex. A forged payload, someone
  else's order, a changed price, a stale order are declined at pre-checkout.
  Every payment of a multi-use invoice becomes its own order.
* `refundStarPayment(user_id, charge_id)` refunds the WHOLE payment; there is no
  amount. Refunds here are admin-only, two-step (request -> confirm) and
  journaled; an automatic rule exists but is off by default.
* Subscriptions: access is granted by `expires_at` from
  `subscription_expiration_date`, never by the last update seen;
  `Update.subscription` with state `failed` sends ONE message per period.
* Reconciliation pages `getStarTransactions`; amounts are compared in nanostars
  (`amount * 10**9 + nanostar_amount`). An outgoing transaction that carries a
  known charge id the bot never refunded is treated as a chargeback (heuristic:
  the Bot API documents the balance debit, not the transaction shape).
* `audit_ledger` is the read-only check of the ledger against the same statement:
  a refund Telegram made that the ledger never posted, and one charge id posted as
  income twice. It writes and sends nothing; an admin decides what to post.

Money is integers only: whole Stars plus nanostars, never floats. Standard
library only; storage is the PaymentStore interface with a SQLite implementation.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Any, Callable, Iterator, Protocol

from .errors import OutcomeUnknown, TelegramError

XTR = "XTR"
GRAM_CODES = frozenset({"GRAM", "TON"})       # Gram, ex-Toncoin; "TON grams" in the Bot API
NANO = 1_000_000_000
PAYLOAD_MAX_BYTES = 128
PRE_CHECKOUT_DEADLINE_S = 10
SUBSCRIPTION_PERIOD_S = 2_592_000
SUBSCRIPTION_MAX_STARS = 10_000
TAG_HEX = 16                                   # 8 bytes of HMAC-SHA256
REASON_MAX = 500                               # refund reason shown on the admin card
EVENT_TTL_S = 86_400                           # Telegram keeps undelivered updates at most 24 h
ALLOWED_UPDATES = ("message", "callback_query", "pre_checkout_query", "subscription")
DIGITAL_KINDS = frozenset({"digital", "subscription", "paid_media"})
KINDS = DIGITAL_KINDS | {"physical", "donation"}


# ------------------------------------------------------------------ rail policy

@dataclass(frozen=True)
class RailVerdict:
    ok: bool
    warning: str = ""
    suggest: str = ""


def check_rail(kind: str, rail: str, *, owner_accepts_risk: bool = False) -> RailVerdict:
    """Which rail may sell this kind of product.

    Digital goods and services inside Telegram are Stars-only [Official]; the
    2026-11-17 reminder to developers names bot subscriptions, paid tools, AI
    model access and credits [News]. A digital product on Gram or a card
    provider is refused unless the owner explicitly accepts the risk - and even
    then the warning stays.
    """
    if kind not in KINDS:
        raise ValueError(f"unknown product kind {kind!r}")
    rail = rail.upper()
    if kind in DIGITAL_KINDS and rail != XTR:
        name = "Gram" if rail in GRAM_CODES else rail
        return RailVerdict(
            ok=owner_accepts_risk and kind != "subscription",   # subscriptions are XTR-only in the API
            warning=(f"{kind} products inside Telegram are sold only for Stars (XTR); {name} breaks "
                     "Telegram's rules for digital goods (reminder of 2026-11-17)."),
            suggest=XTR)
    return RailVerdict(ok=True)


# ------------------------------------------------------------------ catalog

@dataclass(frozen=True)
class Product:
    id: str
    kind: str
    title: dict[str, str]           # locale -> 1-32 characters
    description: dict[str, str]     # locale -> 1-255 characters
    price: int                      # whole Stars
    stock: int | None = None        # None = unlimited
    per_user_limit: int | None = None
    active: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.price, int) or isinstance(self.price, bool) or self.price < 1:
            raise ValueError("price is a positive integer number of Stars")
        if not check_rail(self.kind, XTR).ok:
            raise ValueError(f"kind {self.kind!r} cannot be sold for Stars here")
        if self.kind == "subscription" and self.price > SUBSCRIPTION_MAX_STARS:
            raise ValueError(f"a subscription costs at most {SUBSCRIPTION_MAX_STARS} Stars")


# ------------------------------------------------------------------ state machine

class OrderStatus(str, Enum):
    DRAFT = "draft"
    INVOICED = "invoiced"
    PRE_CHECKOUT = "pre_checkout"
    DECLINED = "declined"
    EXPIRED = "expired"
    PAID = "paid"
    DELIVERED = "delivered"
    REFUND_REQUESTED = "refund_requested"
    REFUNDED = "refunded"
    CHARGEBACK = "chargeback"


S = OrderStatus
# successful_payment is the fact: it may land on an order we already expired or declined.
TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    S.DRAFT: frozenset({S.INVOICED}),
    S.INVOICED: frozenset({S.PRE_CHECKOUT, S.DECLINED, S.EXPIRED, S.PAID}),
    S.PRE_CHECKOUT: frozenset({S.PRE_CHECKOUT, S.DECLINED, S.EXPIRED, S.PAID}),
    S.DECLINED: frozenset({S.PAID}),
    S.EXPIRED: frozenset({S.PAID}),
    S.PAID: frozenset({S.DELIVERED, S.REFUND_REQUESTED, S.REFUNDED, S.CHARGEBACK}),
    S.DELIVERED: frozenset({S.REFUND_REQUESTED, S.REFUNDED, S.CHARGEBACK}),
    S.REFUND_REQUESTED: frozenset({S.REFUNDED, S.DELIVERED, S.PAID, S.CHARGEBACK}),
    S.REFUNDED: frozenset(),
    S.CHARGEBACK: frozenset(),
}
OPEN_VALUES = frozenset({S.INVOICED.value, S.PRE_CHECKOUT.value})
AFTER_PAYMENT = frozenset({S.PAID.value, S.DELIVERED.value, S.REFUND_REQUESTED.value, S.REFUNDED.value,
                           S.CHARGEBACK.value})


def sources_of(to: OrderStatus) -> list[str]:
    return [s.value for s, targets in TRANSITIONS.items() if to in targets]


# ------------------------------------------------------------------ records

@dataclass
class Order:
    id: str
    user_id: int | None
    chat_id: int
    product_id: str
    offer_id: str | None
    currency: str
    amount: int
    status: str
    payload: str
    valid_until: int
    created_at: int
    decline_reason: str | None = None
    lang: str = "en"


@dataclass
class Offer:
    id: str
    product_id: str
    chat_id: int
    amount: int
    payload: str
    valid_until: int


@dataclass
class Payment:
    id: int | None
    order_id: str | None
    user_id: int
    currency: str
    amount: int
    nano: int
    charge_id: str
    provider_charge_id: str
    is_recurring: int
    paid_at: int

    @property
    def total_nano(self) -> int:
        return self.amount * NANO + self.nano


@dataclass
class Refund:
    id: int
    payment_id: int
    amount: int
    reason: str
    requested_by: int
    approved_by: int | None
    status: str                 # requested, sending, done, failed, unknown, canceled
    created_at: int


@dataclass
class Subscription:
    id: str                     # first telegram_payment_charge_id
    user_id: int
    product_id: str
    order_id: str
    state: str                  # active, failed, canceled_by_user, canceled_by_bot, refunded
    expires_at: int
    failed_notice_for: int | None = None


# ------------------------------------------------------------------ payload

def sign_payload(secret: bytes, kind: str, ident: str) -> str:
    body = f"{kind}:{ident}"
    payload = f"{body}.{hmac.new(secret, body.encode(), hashlib.sha256).hexdigest()[:TAG_HEX]}"
    if len(payload.encode()) > PAYLOAD_MAX_BYTES:
        raise ValueError("payload is longer than 128 bytes")
    return payload


def parse_payload(secret: bytes, payload: str) -> tuple[str, str] | None:
    """(kind, ident) for a payload this bot signed, else None."""
    body, dot, tag = (payload or "").rpartition(".")
    kind, _, ident = body.partition(":")
    if not dot or kind not in ("ord", "inv") or not ident or len(tag) != TAG_HEX:
        return None
    good = hmac.new(secret, body.encode(), hashlib.sha256).hexdigest()[:TAG_HEX]
    return (kind, ident) if hmac.compare_digest(tag, good) else None


def webhook_secret_ok(headers: dict[str, str], secret: str) -> bool:
    """True only when the request carries setWebhook's secret_token. Feed `handle()` only
    updates from getUpdates or from a webhook that passed this check: otherwise anyone can
    POST a forged refund tap or `refunded_payment`."""
    got = next((v for k, v in headers.items() if k.lower() == "x-telegram-bot-api-secret-token"), "")
    return bool(secret) and hmac.compare_digest(got.encode(), secret.encode())


# ------------------------------------------------------------------ texts (ru / en / uk)

TEXTS: dict[str, dict[str, str]] = {
    "pay": {"en": "Pay ⭐{amount}", "ru": "Оплатить ⭐{amount}", "uk": "Сплатити ⭐{amount}"},
    "terms": {"en": "Terms", "ru": "Условия", "uk": "Умови"},
    "decline.invalid": {
        "en": "This invoice is no longer valid. Open /shop to get a new one.",
        "ru": "Этот счёт больше не действует. Откройте /shop, чтобы получить новый.",
        "uk": "Цей рахунок більше не дійсний. Відкрийте /shop, щоб отримати новий."},
    "decline.not_yours": {
        "en": "This invoice was issued to another person. Open /shop to get your own.",
        "ru": "Этот счёт выставлен другому человеку. Откройте /shop, чтобы получить свой.",
        "uk": "Цей рахунок виставлено іншій людині. Відкрийте /shop, щоб отримати свій."},
    "decline.expired": {
        "en": "The invoice has expired. Open /shop for a fresh one — no Stars were charged.",
        "ru": "Срок счёта истёк. Откройте /shop за новым — звёзды не списаны.",
        "uk": "Термін рахунку минув. Відкрийте /shop по новий — зірки не списано."},
    "decline.price_changed": {
        "en": "The price has changed to ⭐{price}. A new invoice is below — no Stars were charged.",
        "ru": "Цена изменилась: теперь ⭐{price}. Новый счёт ниже — звёзды не списаны.",
        "uk": "Ціна змінилася: тепер ⭐{price}. Новий рахунок нижче — зірки не списано."},
    "decline.sold_out": {
        "en": "This item has just sold out. No Stars were charged.",
        "ru": "Этот товар только что закончился. Звёзды не списаны.",
        "uk": "Цей товар щойно закінчився. Зірки не списано."},
    "decline.limit": {
        "en": "You have reached the purchase limit for this item.",
        "ru": "Вы достигли лимита покупок этого товара.",
        "uk": "Ви досягли ліміту покупок цього товару."},
    "decline.unavailable": {
        "en": "This item is no longer on sale. Open /shop to see what is available.",
        "ru": "Этот товар больше не продаётся. Откройте /shop, чтобы посмотреть, что есть.",
        "uk": "Цей товар більше не продається. Відкрийте /shop, щоб подивитися, що є."},
    "decline.already_paid": {
        "en": "This order is already paid. See /purchases.",
        "ru": "Этот заказ уже оплачен. Смотрите /purchases.",
        "uk": "Це замовлення вже сплачено. Дивіться /purchases."},
    "decline.error": {
        "en": "We could not check the order. Try again in a minute — no Stars were charged.",
        "ru": "Не удалось проверить заказ. Попробуйте через минуту — звёзды не списаны.",
        "uk": "Не вдалося перевірити замовлення. Спробуйте за хвилину — зірки не списано."},
    "receipt": {
        "en": "Paid ⭐{amount}. «{title}» is unlocked.\nOrder {order} · /paysupport if something is wrong.",
        "ru": "Оплачено ⭐{amount}. «{title}» уже доступен.\nЗаказ {order} · /paysupport, если что-то не так.",
        "uk": "Сплачено ⭐{amount}. «{title}» вже доступний.\nЗамовлення {order} · /paysupport, якщо щось не так."},
    "renewed": {
        "en": "«{title}» renewed until {date}. ⭐{amount} charged.",
        "ru": "«{title}» продлён до {date}. Списано ⭐{amount}.",
        "uk": "«{title}» подовжено до {date}. Списано ⭐{amount}."},
    "refund.done": {
        "en": "⭐{amount} returned for «{title}» (order {order}). Access is switched off.",
        "ru": "⭐{amount} возвращены за «{title}» (заказ {order}). Доступ отключён.",
        "uk": "⭐{amount} повернуто за «{title}» (замовлення {order}). Доступ вимкнено."},
    "sub.failed": {
        "en": "The payment for «{title}» did not go through. Access stays on until {date}, then stops.",
        "ru": "Оплата «{title}» не прошла. Доступ сохранится до {date}, потом отключится.",
        "uk": "Оплата «{title}» не пройшла. Доступ збережеться до {date}, потім вимкнеться."},
    "sub.renew": {"en": "Renew ⭐{amount}", "ru": "Продлить ⭐{amount}", "uk": "Подовжити ⭐{amount}"},
    "refund.ask": {
        "en": "Refund ⭐{amount} to user {user} for «{title}» (order {order})?\nReason: {reason}\n"
              "Stars refunds are whole-payment only and cannot be undone.",
        "ru": "Вернуть ⭐{amount} пользователю {user} за «{title}» (заказ {order})?\nПричина: {reason}\n"
              "Звёзды возвращаются только целиком, отменить нельзя.",
        "uk": "Повернути ⭐{amount} користувачу {user} за «{title}» (замовлення {order})?\nПричина: {reason}\n"
              "Зірки повертаються лише повністю, скасувати не можна."},
    "refund.confirm": {"en": "Refund ⭐{amount}", "ru": "Вернуть ⭐{amount}", "uk": "Повернути ⭐{amount}"},
    "refund.cancel": {"en": "Keep the payment", "ru": "Не возвращать", "uk": "Не повертати"},
    "refund.sent": {"en": "Refunded ⭐{amount} (order {order}).", "ru": "Возврат ⭐{amount} выполнен (заказ {order}).",
                    "uk": "Повернення ⭐{amount} виконано (замовлення {order})."},
    "refund.kept": {"en": "Refund cancelled. Order {order} stays paid.", "ru": "Возврат отменён. Заказ {order} остаётся оплаченным.",
                    "uk": "Повернення скасовано. Замовлення {order} лишається сплаченим."},
    "refund.failed": {
        "en": "Telegram refused the refund (code {code}). Order {order} stays paid.",
        "ru": "Telegram отклонил возврат (код {code}). Заказ {order} остаётся оплаченным.",
        "uk": "Telegram відхилив повернення (код {code}). Замовлення {order} лишається сплаченим."},
    "refund.unknown": {
        "en": "Telegram did not answer. Do not repeat: the daily reconciliation will settle order {order}.",
        "ru": "Telegram не ответил. Не повторяйте: ежедневная сверка покажет итог по заказу {order}.",
        "uk": "Telegram не відповів. Не повторюйте: щоденна звірка покаже підсумок замовлення {order}."},
    "refund.handled": {"en": "Already handled.", "ru": "Уже обработано.", "uk": "Вже оброблено."},
    "admins_only": {"en": "Admins only.", "ru": "Только для администраторов.", "uk": "Лише для адміністраторів."},
}


def lang_of(user: dict[str, Any] | None) -> str:
    code = ((user or {}).get("language_code") or "en")[:2]
    return code if code in ("ru", "uk") else "en"


def t(key: str, lang: str, **values: Any) -> str:
    return TEXTS[key].get(lang, TEXTS[key]["en"]).format(**values)


def fmt_date(ts: int) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(ts))


# ------------------------------------------------------------------ storage

class PaymentStore(Protocol):
    """Persistence the runtime needs. Implement it on Postgres with the DDL in
    references/payments-pipeline.md; keep the UNIQUE constraints - they are the
    idempotency, not an optimisation."""

    def transaction(self) -> Any: ...
    def has_event(self, key: str) -> bool: ...
    def add_event(self, key: str, kind: str, at: int) -> None: ...
    def add_order(self, order: Order) -> None: ...
    def get_order(self, order_id: str) -> Order | None: ...
    def move_order(self, order_id: str, to: OrderStatus, at: int, *, reason: str | None = None,
                   valid_until: int | None = None) -> bool: ...
    def open_child_order(self, offer_id: str, user_id: int) -> Order | None: ...
    def taken_count(self, product_id: str, now: int, exclude: str | None) -> int: ...
    def user_bought_count(self, user_id: int, product_id: str, now: int, exclude: str | None) -> int: ...
    def add_offer(self, offer: Offer) -> None: ...
    def get_offer(self, offer_id: str) -> Offer | None: ...
    def add_payment(self, payment: Payment) -> bool: ...
    def get_payment(self, charge_id: str) -> Payment | None: ...
    def get_payment_by_id(self, payment_id: int) -> Payment | None: ...
    def payments_between(self, since: int, until: int) -> list[Payment]: ...
    def grant(self, user_id: int, product_id: str, payment_id: int, at: int, expires_at: int | None) -> bool: ...
    def has_entitlement(self, payment_id: int) -> bool: ...
    def revoke(self, payment_id: int, at: int) -> None: ...
    def has_access(self, user_id: int, product_id: str, now: int) -> bool: ...
    def add_refund(self, payment_id: int, amount: int, reason: str, requested_by: int, at: int) -> Refund | None: ...
    def get_refund(self, refund_id: int) -> Refund | None: ...
    def active_refund(self, payment_id: int) -> Refund | None: ...
    def move_refund(self, refund_id: int, frm: tuple[str, ...], to: str, at: int, approved_by: int | None = None) -> bool: ...
    def add_subscription(self, sub: Subscription) -> bool: ...
    def subscription_for_order(self, order_id: str) -> Subscription | None: ...
    def update_subscription(self, sub_id: str, **changes: Any) -> None: ...
    def post(self, at: int, debit: str, credit: str, amount_nano: int, ref: str) -> None: ...
    def balance(self, account: str) -> int: ...
    def ledger_rows(self, account: str) -> list[tuple[str, int, int]]: ...
    def save_run(self, report: "ReconReport", at: int) -> None: ...


SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
  id TEXT PRIMARY KEY, user_id INTEGER, chat_id INTEGER NOT NULL, product_id TEXT NOT NULL,
  offer_id TEXT, currency TEXT NOT NULL, amount INTEGER NOT NULL CHECK (amount > 0),
  status TEXT NOT NULL, payload TEXT NOT NULL, valid_until INTEGER NOT NULL,
  created_at INTEGER NOT NULL, decline_reason TEXT, lang TEXT NOT NULL DEFAULT 'en',
  updated_at INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS orders_offer ON orders (offer_id, user_id, status);
CREATE TABLE IF NOT EXISTS offers (
  id TEXT PRIMARY KEY, product_id TEXT NOT NULL, chat_id INTEGER NOT NULL,
  amount INTEGER NOT NULL CHECK (amount > 0), payload TEXT NOT NULL, valid_until INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS payments (
  id INTEGER PRIMARY KEY, order_id TEXT, user_id INTEGER NOT NULL, currency TEXT NOT NULL,
  amount INTEGER NOT NULL, nano INTEGER NOT NULL DEFAULT 0, charge_id TEXT NOT NULL UNIQUE,
  provider_charge_id TEXT NOT NULL, is_recurring INTEGER NOT NULL, paid_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS refunds (
  id INTEGER PRIMARY KEY, payment_id INTEGER NOT NULL REFERENCES payments (id),
  amount INTEGER NOT NULL, reason TEXT NOT NULL, requested_by INTEGER NOT NULL,
  approved_by INTEGER, status TEXT NOT NULL, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS refunds_one_active ON refunds (payment_id)
  WHERE status IN ('requested', 'sending', 'unknown', 'done');
CREATE TABLE IF NOT EXISTS subscriptions (
  id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, product_id TEXT NOT NULL, order_id TEXT NOT NULL UNIQUE,
  state TEXT NOT NULL, expires_at INTEGER NOT NULL, failed_notice_for INTEGER);
CREATE TABLE IF NOT EXISTS entitlements (
  id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, product_id TEXT NOT NULL,
  payment_id INTEGER NOT NULL UNIQUE, granted_at INTEGER NOT NULL, expires_at INTEGER, revoked_at INTEGER);
CREATE TABLE IF NOT EXISTS ledger (
  id INTEGER PRIMARY KEY, at INTEGER NOT NULL, account TEXT NOT NULL,
  debit INTEGER NOT NULL DEFAULT 0, credit INTEGER NOT NULL DEFAULT 0, ref TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events (key TEXT PRIMARY KEY, kind TEXT NOT NULL, received_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS reconciliation_runs (
  id INTEGER PRIMARY KEY, at INTEGER NOT NULL, rail TEXT NOT NULL, period_from INTEGER NOT NULL,
  period_to INTEGER NOT NULL, matched INTEGER NOT NULL, missing_here INTEGER NOT NULL,
  missing_there INTEGER NOT NULL, chargebacks INTEGER NOT NULL, diff_nano INTEGER NOT NULL, details TEXT NOT NULL);
"""


def _row(cls, row):
    if row is None:
        return None
    names = {f.name for f in fields(cls)}
    return cls(**{k: row[k] for k in row.keys() if k in names})


class SqliteStore:
    """PaymentStore on sqlite3 (stdlib). One connection, explicit transactions."""

    def __init__(self, path: str = ":memory:") -> None:
        self.db = sqlite3.connect(path, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self._depth = 0

    def close(self) -> None:
        self.db.close()

    __del__ = close

    @contextmanager
    def transaction(self) -> Iterator[None]:
        if self._depth:                      # nested: join the outer transaction
            self._depth += 1
            try:
                yield
            finally:
                self._depth -= 1
            return
        self.db.execute("BEGIN IMMEDIATE")
        self._depth = 1
        try:
            yield
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        else:
            self.db.execute("COMMIT")
        finally:
            self._depth = 0

    def _one(self, sql: str, *args: Any) -> sqlite3.Row | None:
        return self.db.execute(sql, args).fetchone()

    def has_event(self, key):
        return self._one("SELECT 1 FROM events WHERE key = ?", key) is not None

    def add_event(self, key, kind, at):
        # update_id restarts at random after a week of silence: keep only the 24 h Telegram may redeliver
        self.db.execute("DELETE FROM events WHERE received_at < ?", (at - EVENT_TTL_S,))
        self.db.execute("INSERT OR IGNORE INTO events (key, kind, received_at) VALUES (?, ?, ?)", (key, kind, at))

    def add_order(self, o):
        self.db.execute(
            "INSERT INTO orders (id, user_id, chat_id, product_id, offer_id, currency, amount, status, payload,"
            " valid_until, created_at, decline_reason, lang, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (o.id, o.user_id, o.chat_id, o.product_id, o.offer_id, o.currency, o.amount, o.status, o.payload,
             o.valid_until, o.created_at, o.decline_reason, o.lang, o.created_at))

    def get_order(self, order_id):
        return _row(Order, self._one("SELECT * FROM orders WHERE id = ?", order_id))

    def move_order(self, order_id, to, at, *, reason=None, valid_until=None):
        frm = sources_of(to)
        cur = self.db.execute(
            f"UPDATE orders SET status = ?, updated_at = ?, decline_reason = COALESCE(?, decline_reason),"
            f" valid_until = COALESCE(?, valid_until) WHERE id = ? AND status IN ({','.join('?' * len(frm))})",
            (to.value, at, reason, valid_until, order_id, *frm))
        return cur.rowcount == 1

    def open_child_order(self, offer_id, user_id):
        return _row(Order, self._one(
            "SELECT * FROM orders WHERE offer_id = ? AND user_id = ? AND status IN ('invoiced', 'pre_checkout')"
            " ORDER BY created_at, id LIMIT 1", offer_id, user_id))

    def taken_count(self, product_id, now, exclude):
        row = self._one(
            "SELECT COUNT(*) FROM orders WHERE product_id = ? AND id IS NOT ? AND (status IN"
            " ('paid', 'delivered', 'refund_requested') OR (status = 'pre_checkout' AND valid_until > ?))",
            product_id, exclude, now)
        return row[0]

    def user_bought_count(self, user_id, product_id, now, exclude):
        return self._one(
            "SELECT COUNT(*) FROM orders WHERE user_id = ? AND product_id = ? AND id IS NOT ? AND (status IN"
            " ('paid', 'delivered', 'refund_requested') OR (status = 'pre_checkout' AND valid_until > ?))",
            user_id, product_id, exclude, now)[0]

    def add_offer(self, o):
        self.db.execute("INSERT INTO offers (id, product_id, chat_id, amount, payload, valid_until) VALUES (?,?,?,?,?,?)",
                        (o.id, o.product_id, o.chat_id, o.amount, o.payload, o.valid_until))

    def get_offer(self, offer_id):
        return _row(Offer, self._one("SELECT * FROM offers WHERE id = ?", offer_id))

    def add_payment(self, p):
        cur = self.db.execute(
            "INSERT OR IGNORE INTO payments (order_id, user_id, currency, amount, nano, charge_id,"
            " provider_charge_id, is_recurring, paid_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (p.order_id, p.user_id, p.currency, p.amount, p.nano, p.charge_id, p.provider_charge_id,
             p.is_recurring, p.paid_at))
        if cur.rowcount == 1:
            p.id = cur.lastrowid
        return cur.rowcount == 1

    def get_payment(self, charge_id):
        return _row(Payment, self._one("SELECT * FROM payments WHERE charge_id = ?", charge_id))

    def get_payment_by_id(self, payment_id):
        return _row(Payment, self._one("SELECT * FROM payments WHERE id = ?", payment_id))

    def payments_between(self, since, until):
        rows = self.db.execute("SELECT * FROM payments WHERE paid_at >= ? AND paid_at < ? ORDER BY id", (since, until))
        return [_row(Payment, r) for r in rows]

    def grant(self, user_id, product_id, payment_id, at, expires_at):
        cur = self.db.execute("INSERT OR IGNORE INTO entitlements (user_id, product_id, payment_id, granted_at,"
                              " expires_at) VALUES (?,?,?,?,?)", (user_id, product_id, payment_id, at, expires_at))
        return cur.rowcount == 1

    def has_entitlement(self, payment_id):
        return self._one("SELECT 1 FROM entitlements WHERE payment_id = ?", payment_id) is not None

    def revoke(self, payment_id, at):
        self.db.execute("UPDATE entitlements SET revoked_at = ? WHERE payment_id = ? AND revoked_at IS NULL", (at, payment_id))

    def has_access(self, user_id, product_id, now):
        return self._one("SELECT 1 FROM entitlements WHERE user_id = ? AND product_id = ? AND revoked_at IS NULL"
                         " AND (expires_at IS NULL OR expires_at > ?)", user_id, product_id, now) is not None

    def add_refund(self, payment_id, amount, reason, requested_by, at):
        try:
            cur = self.db.execute(
                "INSERT INTO refunds (payment_id, amount, reason, requested_by, status, created_at, updated_at)"
                " VALUES (?,?,?,?, 'requested', ?, ?)", (payment_id, amount, reason, requested_by, at, at))
        except sqlite3.IntegrityError:       # an active or finished refund already exists
            return None
        return self.get_refund(cur.lastrowid)

    def get_refund(self, refund_id):
        return _row(Refund, self._one("SELECT * FROM refunds WHERE id = ?", refund_id))

    def active_refund(self, payment_id):
        return _row(Refund, self._one("SELECT * FROM refunds WHERE payment_id = ? AND status IN"
                                      " ('requested', 'sending', 'unknown', 'done')", payment_id))

    def move_refund(self, refund_id, frm, to, at, approved_by=None):
        cur = self.db.execute(
            f"UPDATE refunds SET status = ?, updated_at = ?, approved_by = COALESCE(?, approved_by)"
            f" WHERE id = ? AND status IN ({','.join('?' * len(frm))})", (to, at, approved_by, refund_id, *frm))
        return cur.rowcount == 1

    def add_subscription(self, s):
        cur = self.db.execute("INSERT OR IGNORE INTO subscriptions (id, user_id, product_id, order_id, state,"
                              " expires_at, failed_notice_for) VALUES (?,?,?,?,?,?,?)",
                              (s.id, s.user_id, s.product_id, s.order_id, s.state, s.expires_at, s.failed_notice_for))
        return cur.rowcount == 1

    def subscription_for_order(self, order_id):
        return _row(Subscription, self._one("SELECT * FROM subscriptions WHERE order_id = ?", order_id))

    def update_subscription(self, sub_id, **changes):
        allowed = {"state", "expires_at", "failed_notice_for"}
        if not changes or set(changes) - allowed:
            raise ValueError(f"can update only {sorted(allowed)}")
        sets = ", ".join(f"{k} = ?" for k in changes)
        self.db.execute(f"UPDATE subscriptions SET {sets} WHERE id = ?", (*changes.values(), sub_id))

    def post(self, at, debit, credit, amount_nano, ref):
        self.db.executemany("INSERT INTO ledger (at, account, debit, credit, ref) VALUES (?,?,?,?,?)",
                            [(at, debit, amount_nano, 0, ref), (at, credit, 0, amount_nano, ref)])

    def balance(self, account):
        return self._one("SELECT COALESCE(SUM(debit - credit), 0) FROM ledger WHERE account = ?", account)[0]

    def ledger_rows(self, account):
        """(ref, debit, credit) of every posting on `account`, oldest first."""
        return [tuple(r) for r in self.db.execute(
            "SELECT ref, debit, credit FROM ledger WHERE account = ? ORDER BY id", (account,))]

    def save_run(self, r, at):
        self.db.execute(
            "INSERT INTO reconciliation_runs (at, rail, period_from, period_to, matched, missing_here,"
            " missing_there, chargebacks, diff_nano, details) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (at, XTR, r.since, r.until, r.matched, len(r.missing_here), len(r.missing_there),
             len(r.chargebacks), r.diff_nano, json.dumps(r.details(), ensure_ascii=False)))


# ------------------------------------------------------------------ reconciliation report

@dataclass
class ReconReport:
    since: int
    until: int
    matched: int = 0
    refunds_matched: int = 0
    refunds_settled: int = 0                  # unknown refund outcomes the statement resolved
    missing_here: list[str] = field(default_factory=list)     # in Telegram, not in our payments
    missing_there: list[str] = field(default_factory=list)    # in our payments, not in Telegram
    amount_mismatch: list[str] = field(default_factory=list)
    chargebacks: list[str] = field(default_factory=list)
    other: list[str] = field(default_factory=list)            # withdrawals, ads, paid broadcasts, paid media
    diff_nano: int = 0                        # Telegram incoming minus ours, in nanostars
    next_offset: int = 0

    @property
    def clean(self) -> bool:
        return not (self.missing_here or self.missing_there or self.amount_mismatch or self.chargebacks or self.diff_nano)

    def details(self) -> dict[str, Any]:
        return {"missing_here": self.missing_here, "missing_there": self.missing_there,
                "amount_mismatch": self.amount_mismatch, "chargebacks": self.chargebacks,
                "other": self.other, "refunds_matched": self.refunds_matched,
                "refunds_settled": self.refunds_settled, "next_offset": self.next_offset}


@dataclass
class LedgerAudit:
    """What `audit_ledger` found. Nothing was written or sent to produce it."""
    missing_refunds: list[str] = field(default_factory=list)   # refunded in Telegram, no refund/chargeback posted
    double_credits: list[str] = field(default_factory=list)    # one charge id posted as income more than once
    pages: int = 0
    next_offset: int = 0

    @property
    def clean(self) -> bool:
        return not (self.missing_refunds or self.double_credits)


# ------------------------------------------------------------------ runtime

@dataclass(frozen=True)
class RefundPolicy:
    """Refunds are manual and admin-confirmed by default. `auto_within_s` (off)
    refunds a payer's own request at once when the payment is that recent and
    `is_used(payment)` says the purchase was not used; without `is_used` it never fires."""
    auto_within_s: int | None = None
    is_used: Callable[["Payment"], bool] | None = None
    revoke_on_chargeback: bool = True


Deliver = Callable[[Order, Product, Payment], None]


# Ledger ref prefixes of the postings that reverse a charge (finalize_refund, _chargeback); any other
# credit on bot:stars, a fee for example, never counts as a refund even when it names the same charge.
REVERSAL_REFS = ("refund", "chargeback")


class StarsPayments:
    """Stars rail of the pipeline. Feed it updates with `handle(update)`; pass
    `ALLOWED_UPDATES` (or a superset) to getUpdates / setWebhook."""

    def __init__(self, transport: Any, store: PaymentStore, catalog: dict[str, Product], *,
                 secret: bytes, admins: set[int], admin_chat_id: int | None = None,
                 now: Callable[[], float] = time.time, order_ttl_s: int = 3600,
                 refund_policy: RefundPolicy = RefundPolicy(), on_deliver: Deliver | None = None) -> None:
        if len(secret) < 16:
            raise ValueError("payload secret must be at least 16 bytes")
        self.tx, self.store, self.catalog = transport, store, catalog
        self._secret, self.admins, self.admin_chat_id = secret, set(admins), admin_chat_id
        self._now, self.ttl, self.policy, self.on_deliver = now, order_ttl_s, refund_policy, on_deliver

    def now(self) -> int:
        return int(self._now())

    def title(self, product_id: str, lang: str) -> str:
        product = self.catalog[product_id]
        return product.title.get(lang, product.title["en"])

    # ---------------------------------------------------------------- selling

    def _new_order(self, user_id: int | None, chat_id: int, product: Product, lang: str, *,
                   offer_id: str | None = None, status: OrderStatus = S.DRAFT) -> Order:
        oid = secrets.token_hex(6)
        now = self.now()
        order = Order(id=oid, user_id=user_id, chat_id=chat_id, product_id=product.id, offer_id=offer_id,
                      currency=XTR, amount=product.price, status=status.value,
                      payload=sign_payload(self._secret, "ord", oid), valid_until=now + self.ttl,
                      created_at=now, lang=lang)
        self.store.add_order(order)
        return order

    def _product(self, product_id: str) -> Product:
        product = self.catalog.get(product_id)
        if product is None or not product.active:
            raise LookupError(f"product {product_id!r} is not on sale")
        return product

    def _invoice_params(self, chat_id: int, product: Product, payload: str, lang: str) -> dict[str, Any]:
        title = self.title(product.id, lang)
        return {"chat_id": chat_id, "title": title,
                "description": product.description.get(lang, product.description["en"]),
                "payload": payload, "currency": XTR, "prices": [{"label": title, "amount": product.price}],
                "reply_markup": {"inline_keyboard": [
                    [{"text": t("pay", lang, amount=product.price), "pay": True}],
                    [{"text": t("terms", lang), "callback_data": "terms"}]]}}

    def invoice(self, user_id: int, chat_id: int, product_id: str, lang: str = "en") -> Order:
        """A personal order and its invoice. The order exists before the invoice."""
        product = self._product(product_id)
        if product.kind == "subscription":
            raise ValueError("subscriptions are invoice links: use subscription_link()")
        order = self._new_order(user_id, chat_id, product, lang)
        self.tx.call("sendInvoice", self._invoice_params(chat_id, product, order.payload, lang))
        self.store.move_order(order.id, S.INVOICED, self.now())
        return self.store.get_order(order.id)

    def offer(self, chat_id: int, product_id: str, lang: str = "en", ttl_s: int = 7 * 86400) -> Offer:
        """A multi-use invoice (group, channel): anyone may pay, many times, and every
        payment becomes its own order. No start_parameter, so forwards keep the Pay button."""
        product = self._product(product_id)
        if product.kind == "subscription":
            raise ValueError("subscriptions are personal invoice links, not multi-use offers")
        oid = secrets.token_hex(6)
        offer = Offer(id=oid, product_id=product.id, chat_id=chat_id, amount=product.price,
                      payload=sign_payload(self._secret, "inv", oid), valid_until=self.now() + ttl_s)
        self.store.add_offer(offer)
        self.tx.call("sendInvoice", self._invoice_params(chat_id, product, offer.payload, lang))
        return offer

    def subscription_link(self, user_id: int, product_id: str, lang: str = "en") -> str:
        product = self._product(product_id)
        if product.kind != "subscription":
            raise ValueError("not a subscription product")
        order = self._new_order(user_id, user_id, product, lang)
        params = self._invoice_params(user_id, product, order.payload, lang)
        for key in ("chat_id", "reply_markup"):
            params.pop(key)
        link = self.tx.call("createInvoiceLink", {**params, "subscription_period": SUBSCRIPTION_PERIOD_S})
        self.store.move_order(order.id, S.INVOICED, self.now())
        return link

    def has_access(self, user_id: int, product_id: str) -> bool:
        return self.store.has_access(user_id, product_id, self.now())

    # ---------------------------------------------------------------- updates

    def handle(self, update: dict[str, Any]) -> bool:
        """Route one update; False when it is not a payment update. A repeated
        update_id is ignored (the charge id is still the real idempotency key).
        Pass only updates from getUpdates or a webhook checked with webhook_secret_ok()."""
        msg = update.get("message") or {}
        cq = update.get("callback_query") or {}
        if "pre_checkout_query" in update:
            kind, run = "pre_checkout_query", lambda: self.on_pre_checkout(update["pre_checkout_query"])
        elif "subscription" in update:
            kind, run = "subscription", lambda: self.on_subscription(update["subscription"])
        elif "successful_payment" in msg:
            kind, run = "successful_payment", lambda: self.on_successful_payment(msg)
        elif "refunded_payment" in msg:
            kind, run = "refunded_payment", lambda: self.on_refunded_payment(msg)
        elif str(cq.get("data", "")).startswith("rf:"):
            kind, run = "refund_callback", lambda: self.on_refund_callback(cq)
        else:
            return False
        key = f"u:{update['update_id']}" if "update_id" in update else None
        if key and self.store.has_event(key):
            return True
        run()
        if key:
            self.store.add_event(key, kind, self.now())      # after success: a crash gets a retry
        return True

    # ---------------------------------------------------------------- pre-checkout

    def on_pre_checkout(self, q: dict[str, Any]) -> None:
        """Local checks only, then the answer (10 s budget); slow work after it."""
        lang = lang_of(q.get("from"))
        try:
            reason, order, product = self._check(q, lang)
        except Exception:                                    # never leave the query unanswered
            reason, order, product = "error", None, None
        if reason is None:
            self.tx.call("answerPreCheckoutQuery", {"pre_checkout_query_id": q["id"], "ok": True})
            return
        personal = order is not None and order.offer_id is None
        key = "invalid" if reason == "price_changed" and not personal else reason
        self.tx.call("answerPreCheckoutQuery", {"pre_checkout_query_id": q["id"], "ok": False,
                                                "error_message": t(f"decline.{key}", lang,
                                                                   price=product.price if product else 0)})
        if key == "price_changed":
            try:
                self.invoice(order.user_id, order.chat_id, order.product_id, lang)   # after the answer
            except (OutcomeUnknown, TelegramError, LookupError):
                pass

    def _check(self, q: dict[str, Any], lang: str) -> tuple[str | None, Order | None, Product | None]:
        parsed = parse_payload(self._secret, q.get("invoice_payload", ""))
        if parsed is None or q.get("currency") != XTR:
            return "invalid", None, None
        kind, ident = parsed
        user_id, now = q["from"]["id"], self.now()
        order: Order | None = None
        if kind == "ord":
            order = self.store.get_order(ident)
            if order is None:
                return "invalid", None, None
            if order.user_id != user_id:
                return "not_yours", None, None               # someone else's order stays untouched
            if order.status in AFTER_PAYMENT:
                return "already_paid", order, None
            if order.status not in OPEN_VALUES or q.get("total_amount") != order.amount:
                return "invalid", order, None
            if order.valid_until <= now:
                self.store.move_order(order.id, S.EXPIRED, now, reason="expired")
                return "expired", order, None
            product_id, amount, chat_id = order.product_id, order.amount, order.chat_id
        else:
            offer = self.store.get_offer(ident)
            if offer is None or q.get("total_amount") != offer.amount:
                return "invalid", None, None
            if offer.valid_until <= now:
                return "expired", None, None
            product_id, amount, chat_id = offer.product_id, offer.amount, offer.chat_id
        product = self.catalog.get(product_id)
        with self.store.transaction():                        # check and hold atomically: no overselling
            exclude = order.id if order else None
            decline = None
            if product is None or not product.active:
                decline = "unavailable"
            elif product.price != amount:
                decline = "price_changed"
            elif product.stock is not None and self.store.taken_count(product.id, now, exclude) >= product.stock:
                decline = "sold_out"
            elif product.per_user_limit is not None and \
                    self.store.user_bought_count(user_id, product.id, now, exclude) >= product.per_user_limit:
                decline = "limit"
            if decline:
                if order is not None:
                    self.store.move_order(order.id, S.DECLINED, now, reason=decline)
                return decline, order, product
            if order is None:                                 # multi-use invoice: one order per payment
                order = self.store.open_child_order(ident, user_id) or self._new_order(
                    user_id, chat_id, product, lang, offer_id=ident, status=S.INVOICED)
            hold = now + self.ttl if order.offer_id else None   # a reused offer order gets a live hold
            self.store.move_order(order.id, S.PRE_CHECKOUT, now, valid_until=hold)
        return None, order, product

    # ---------------------------------------------------------------- payment and delivery

    def on_successful_payment(self, msg: dict[str, Any]) -> None:
        sp = msg["successful_payment"]
        if sp.get("currency") != XTR:
            return                                            # provider payments: not this rail
        user, now = msg["from"], self.now()
        problem = None
        with self.store.transaction():
            payment = self.store.get_payment(sp["telegram_payment_charge_id"])
            if payment is not None:                           # re-delivered: resume per payment, never repeat
                order = self.store.get_order(payment.order_id) if payment.order_id else None
            else:
                order = self._order_for_payment(sp.get("invoice_payload", ""), user, msg["chat"]["id"])
                payment = Payment(id=None, order_id=order.id if order else None, user_id=user["id"],
                                  currency=XTR, amount=sp["total_amount"], nano=0,
                                  charge_id=sp["telegram_payment_charge_id"],
                                  provider_charge_id=sp.get("provider_payment_charge_id", ""),
                                  is_recurring=int(bool(sp.get("is_recurring"))),
                                  paid_at=int(msg.get("date") or now))   # Telegram's clock, as in the statement
                problem = self._payment_problem(order, payment)
                if problem is not None:
                    payment.order_id = order = None           # never bind a stray charge to a fulfilled order
                if not self.store.add_payment(payment):       # another worker took it
                    return
                self.store.post(now, "bot:stars", f"user:{user['id']}", payment.total_nano, payment.charge_id)
                if order is not None and order.status != S.DELIVERED.value:
                    self.store.move_order(order.id, S.PAID, now)
                    order = self.store.get_order(order.id)
        if problem is not None:
            self._tell_admin(f"Payment {payment.charge_id} (⭐{payment.amount}) {problem}: nothing was "
                             "delivered; refund it from the admin chat if needed.")
            return
        if order is not None:
            self._deliver(order, self.catalog[order.product_id], payment, sp)

    def _payment_problem(self, order: Order | None, payment: Payment) -> str | None:
        """Why this payment must not be delivered, or None. Telegram's fields are trusted;
        they still have to match the order this bot issued."""
        if order is None:
            return "matches no order"
        if order.user_id != payment.user_id or order.amount != payment.amount:
            return f"does not match order {order.id} (payer or amount)"
        subscription = self.catalog[order.product_id].kind == "subscription"
        allowed = {S.PAID.value} | OPEN_VALUES | {S.DECLINED.value, S.EXPIRED.value}
        if subscription:
            allowed.add(S.DELIVERED.value)                    # renewals land on the delivered order
        if payment.id is not None and self.store.has_entitlement(payment.id):
            return None                                       # delivered already; _deliver is a no-op
        return None if order.status in allowed else f"arrived for order {order.id} in state {order.status}"

    def _deliver(self, order: Order, product: Product, payment: Payment, sp: dict[str, Any]) -> None:
        """Claim the delivery by inserting the entitlement (UNIQUE payment_id) in the same
        transaction as the `on_deliver` hook: a concurrent duplicate waits for the lock and
        then finds the claim taken; a hook that raises rolls the claim back for a retry.
        Write the hook's effects to the same database, or make it idempotent by charge id."""
        now = self.now()
        subscription = product.kind == "subscription"
        expires = int(sp.get("subscription_expiration_date") or now + SUBSCRIPTION_PERIOD_S) if subscription else None
        with self.store.transaction():
            current = self.store.get_order(order.id)          # re-read under the lock: a refund may have won
            if self._payment_problem(current, payment) is not None or self._settled(payment):
                return
            if not self.store.grant(payment.user_id, product.id, payment.id, now, expires):
                return                                        # another worker delivered this payment
            sub = self.store.subscription_for_order(order.id) if subscription else None
            if subscription and sub is None:
                self.store.add_subscription(Subscription(id=payment.charge_id, user_id=payment.user_id,
                                                         product_id=product.id, order_id=order.id,
                                                         state="active", expires_at=expires))
            elif sub is not None:
                self.store.update_subscription(sub.id, state="active", expires_at=max(sub.expires_at, expires),
                                               failed_notice_for=None)
            if self.on_deliver:
                self.on_deliver(order, product, payment)
            first = self.store.move_order(order.id, S.DELIVERED, now)
        title = self.title(product.id, order.lang)
        if first:
            self._send(payment.user_id, t("receipt", order.lang, amount=payment.amount, title=title, order=order.id))
        elif sub is not None:
            self._send(payment.user_id, t("renewed", order.lang, title=title, date=fmt_date(expires),
                                          amount=payment.amount))

    def _order_for_payment(self, payload: str, user: dict[str, Any], chat_id: int) -> Order | None:
        parsed = parse_payload(self._secret, payload)
        if parsed is None:
            return None
        kind, ident = parsed
        if kind == "ord":
            return self.store.get_order(ident)
        offer = self.store.get_offer(ident)
        if offer is None:
            return None
        return self.store.open_child_order(ident, user["id"]) or self._new_order(
            user["id"], chat_id, self.catalog[offer.product_id], lang_of(user), offer_id=ident, status=S.INVOICED)

    # ---------------------------------------------------------------- subscriptions

    def on_subscription(self, upd: dict[str, Any]) -> None:
        """BotSubscriptionUpdated carries user + payload + state only; the payload names the order."""
        parsed = parse_payload(self._secret, upd.get("invoice_payload", ""))
        sub = self.store.subscription_for_order(parsed[1]) if parsed and parsed[0] == "ord" else None
        user = upd["user"]
        if sub is None or sub.user_id != user["id"]:
            return
        state = upd["state"]
        if state == "canceled":
            self.store.update_subscription(sub.id, state="canceled_by_user")   # access lasts to expires_at
        elif state == "active":
            self.store.update_subscription(sub.id, state="active")
        elif state == "failed":
            self.store.update_subscription(sub.id, state="failed")
            if sub.failed_notice_for == sub.expires_at:
                return                                         # one message per period
            self.store.update_subscription(sub.id, failed_notice_for=sub.expires_at)
            lang = lang_of(user)
            product = self.catalog[sub.product_id]
            link = self.subscription_link(user["id"], product.id, lang)
            self._send(user["id"], t("sub.failed", lang, title=self.title(product.id, lang),
                                     date=fmt_date(sub.expires_at)),
                       {"inline_keyboard": [[{"text": t("sub.renew", lang, amount=product.price), "url": link}]]})

    def cancel_subscription(self, sub: Subscription) -> None:
        """Stop renewal from the bot side; access lasts to expires_at."""
        self.tx.call("editUserStarSubscription", {"user_id": sub.user_id, "telegram_payment_charge_id": sub.id,
                                                  "is_canceled": True})
        self.store.update_subscription(sub.id, state="canceled_by_bot")

    # ---------------------------------------------------------------- refunds

    def _settled(self, payment: Payment) -> bool:
        """The payment's money already went back (refund done or chargeback)."""
        refund = self.store.active_refund(payment.id)
        return refund is not None and refund.status == "done"

    def request_refund(self, charge_id: str, *, by: int, reason: str, lang: str = "en") -> Refund | None:
        """Step 1: an admin or the payer asks; the admin chat gets a confirmation card.
        None when there is nothing to refund (unknown, already refunded or already requested).
        Stars refunds are whole-payment only: there is no amount to choose. Refunds are per
        charge: one subscription order has a charge per period."""
        payment = self.store.get_payment(charge_id)
        if payment is None:
            return None
        if by not in self.admins and by != payment.user_id:
            raise PermissionError("refunds are requested by the payer or an admin")
        if by not in self.admins and self.admin_chat_id is None:
            raise ValueError("a payer's refund request needs admin_chat_id")
        reason = (reason or "-").strip()[:REASON_MAX]
        order = self.store.get_order(payment.order_id) if payment.order_id else None
        one_off = order is not None and self.catalog[order.product_id].kind != "subscription"
        if order is None and by not in self.admins:
            return None                                       # a stray charge: admins only
        if one_off and order.status not in (S.PAID.value, S.DELIVERED.value):
            return None
        if order is not None and not one_off and not self.store.has_entitlement(payment.id):
            return None
        now = self.now()
        with self.store.transaction():
            refund = self.store.add_refund(payment.id, payment.amount, reason, by, now)
            if refund is None:
                return None
            if one_off:
                self.store.move_order(order.id, S.REFUND_REQUESTED, now)
        p = self.policy
        if (by == payment.user_id and p.auto_within_s is not None and p.is_used is not None
                and now - payment.paid_at <= p.auto_within_s and not p.is_used(payment)):
            if self.store.move_refund(refund.id, ("requested",), "sending", now, approved_by=0):  # 0 = auto rule
                self._send_refund(refund, payment, lang)
            return self.store.get_refund(refund.id)
        title = self.title(order.product_id, lang) if order else payment.charge_id
        self._send(self.admin_chat_id if self.admin_chat_id is not None else by,
                   t("refund.ask", lang, amount=payment.amount, user=payment.user_id, title=title,
                     order=order.id if order else "-", reason=reason),
                   {"inline_keyboard": [
                       [{"text": t("refund.confirm", lang, amount=payment.amount),
                         "callback_data": f"rf:ok:{refund.id}", "style": "danger"}],
                       [{"text": t("refund.cancel", lang), "callback_data": f"rf:no:{refund.id}"}]]})
        return refund

    def on_refund_callback(self, cq: dict[str, Any]) -> None:
        """Step 2: the confirmation tap. The admin role is re-checked here."""
        lang = lang_of(cq.get("from"))
        if cq["from"]["id"] not in self.admins:
            self.tx.call("answerCallbackQuery", {"callback_query_id": cq["id"], "text": t("admins_only", lang),
                                                 "show_alert": True})
            return
        _, action, rid = (cq["data"].split(":", 2) + ["", ""])[:3]
        refund = self.store.get_refund(int(rid)) if re.fullmatch(r"[0-9]{1,18}", rid) else None
        payment = self.store.get_payment_by_id(refund.payment_id) if refund else None
        now, admin = self.now(), cq["from"]["id"]
        if refund is None or payment is None:
            text = t("refund.handled", lang)
        elif action == "no":
            if self.store.move_refund(refund.id, ("requested",), "canceled", now, approved_by=admin):
                self._restore_order(payment, now)
                text = t("refund.kept", lang, order=payment.order_id)
            else:
                text = t("refund.handled", lang)
        elif action == "ok" and self.store.move_refund(refund.id, ("requested",), "sending", now, approved_by=admin):
            text = self._send_refund(refund, payment, lang)
        else:
            text = t("refund.handled", lang)                  # double tap or already finished
        self.tx.call("answerCallbackQuery", {"callback_query_id": cq["id"], "text": text[:200]})
        message = cq.get("message")
        if message:
            self.tx.call("editMessageText", {"chat_id": message["chat"]["id"], "message_id": message["message_id"],
                                             "text": text})

    def _send_refund(self, refund: Refund, payment: Payment, lang: str) -> str:
        try:
            self.tx.call("refundStarPayment", {"user_id": payment.user_id,
                                               "telegram_payment_charge_id": payment.charge_id})
        except OutcomeUnknown:                                 # no blind retry: reconciliation settles it
            self.store.move_refund(refund.id, ("sending",), "unknown", self.now())
            return t("refund.unknown", lang, order=payment.order_id)
        except TelegramError as err:
            self.store.move_refund(refund.id, ("sending",), "failed", self.now())
            self._restore_order(payment, self.now())
            return t("refund.failed", lang, code=err.error_code, order=payment.order_id)
        self.finalize_refund(payment)
        return t("refund.sent", lang, amount=payment.amount, order=payment.order_id)

    def _restore_order(self, payment: Payment, now: int) -> None:
        """Back from refund_requested to where the order was: delivered only if it was."""
        if payment.order_id:
            back = S.DELIVERED if self.store.has_entitlement(payment.id) else S.PAID
            self.store.move_order(payment.order_id, back, now)

    def close_unknown_refund(self, refund_id: int, *, by: int) -> bool:
        """An admin closes a refund whose outcome stayed unknown after reconciliation showed no
        outgoing transaction for it; the payment can then be refunded again."""
        if by not in self.admins:
            raise PermissionError("admin only")
        refund = self.store.get_refund(refund_id)
        payment = self.store.get_payment_by_id(refund.payment_id) if refund else None
        if payment is None or not self.store.move_refund(refund.id, ("unknown",), "failed", self.now(), approved_by=by):
            return False
        self._restore_order(payment, self.now())
        return True

    def on_refunded_payment(self, msg: dict[str, Any]) -> None:
        charge = msg["refunded_payment"]["telegram_payment_charge_id"]
        payment = self.store.get_payment(charge)
        if payment is not None:
            self.finalize_refund(payment)
        else:
            self._tell_admin(f"Telegram reports a refund of {charge}, a charge this bot never recorded.")

    def finalize_refund(self, payment: Payment) -> bool:
        """Idempotent per charge: mark the refund done, revoke that charge's access, post the
        ledger, close a one-off order or stop the subscription's renewal, tell the user once."""
        now = self.now()
        with self.store.transaction():
            if self._settled(payment):
                return False
            refund = self.store.active_refund(payment.id) or \
                self.store.add_refund(payment.id, payment.amount, "external", 0, now)   # refunded elsewhere
            self.store.move_refund(refund.id, ("requested", "sending", "unknown"), "done", now)
            self.store.revoke(payment.id, now)
            self.store.post(now, "refunds", "bot:stars", payment.total_nano, f"refund:{payment.charge_id}")
            order = self.store.get_order(payment.order_id) if payment.order_id else None
            sub = self.store.subscription_for_order(order.id) if order else None
            if sub is not None and sub.state != "refunded":
                self.store.update_subscription(sub.id, state="refunded")
            elif sub is None and order is not None:
                self.store.move_order(order.id, S.REFUNDED, now)
        if sub is not None and sub.state != "refunded":
            try:
                self.tx.call("editUserStarSubscription", {"user_id": sub.user_id,
                                                          "telegram_payment_charge_id": sub.id, "is_canceled": True})
            except (OutcomeUnknown, TelegramError):
                self._tell_admin(f"Stop renewal of subscription {sub.id} by hand: the call failed.")
        lang = order.lang if order else "en"
        self._send(payment.user_id, t("refund.done", lang, amount=payment.amount,
                                      title=self.title(order.product_id, lang) if order else payment.charge_id,
                                      order=order.id if order else "-"))
        return True

    # ---------------------------------------------------------------- reconciliation

    def reconcile(self, *, since: int, until: int, offset: int = 0, page_size: int = 100) -> ReconReport:
        """Compare [since, until) of getStarTransactions with the store. Transactions are
        chronological: start from the previous run's `next_offset`."""
        report = ReconReport(since=since, until=until)
        seen: set[str] = set()
        incoming_nano, done = 0, False
        while not done:
            page = self.tx.call("getStarTransactions", {"offset": offset, "limit": page_size})["transactions"]
            for tx in page:
                if tx["date"] >= until:
                    done = True
                    break
                offset += 1
                if tx["date"] >= since:
                    incoming_nano += self._match(tx, report, seen)
            done = done or len(page) < page_size
        ours = self.store.payments_between(since, until)
        report.missing_there = [p.charge_id for p in ours if p.charge_id not in seen]
        report.diff_nano = incoming_nano - sum(p.total_nano for p in ours)
        report.next_offset = offset
        self.store.save_run(report, self.now())
        if not report.clean:
            self._tell_admin(f"Stars reconciliation {fmt_date(since)}: {report.matched} matched, "
                             f"{len(report.missing_here)} missing here, {len(report.missing_there)} missing in "
                             f"Telegram, {len(report.chargebacks)} chargeback(s), diff {report.diff_nano} nanostars.")
        return report

    def _match(self, tx: dict[str, Any], report: ReconReport, seen: set[str]) -> int:
        """Classify one transaction; returns the incoming user-payment amount in nanostars."""
        nano = tx["amount"] * NANO + tx.get("nanostar_amount", 0)
        partner = tx.get("source") or tx.get("receiver") or {}
        is_user = partner.get("type") == "user"
        if "source" in tx:
            if not (is_user and partner.get("transaction_type") == "invoice_payment"):
                report.other.append(tx["id"])                  # paid media, failed-withdrawal refunds, ...
                return 0
            payment = self.store.get_payment(tx["id"])
            if payment is None:
                report.missing_here.append(tx["id"])
            elif payment.total_nano != nano:
                report.amount_mismatch.append(tx["id"])
            else:
                report.matched += 1
            seen.add(tx["id"])
            return nano
        payment = self.store.get_payment(tx["id"]) if is_user else None
        if payment is None:
            report.other.append(tx["id"])                      # withdrawals, ads, paid broadcasts
            return 0
        refund = self.store.active_refund(payment.id)
        if refund is not None and refund.status == "done":
            report.refunds_matched += 1
        elif refund is not None and refund.status in ("sending", "unknown"):   # sent, answer lost
            self.finalize_refund(payment)
            report.refunds_settled += 1
        else:                                                  # nobody here refunded it
            report.chargebacks.append(tx["id"])
            self._chargeback(payment)
        return 0

    def _chargeback(self, payment: Payment) -> None:
        """Record the reversal as a done refund row (so a re-run sees it settled), cancel a
        refund that was only requested, revoke access by rule, post the ledger."""
        now = self.now()
        with self.store.transaction():
            active = self.store.active_refund(payment.id)
            if active is not None and active.status == "done":
                return
            if active is not None:
                self.store.move_refund(active.id, ("requested",), "canceled", now)
            row = self.store.add_refund(payment.id, payment.amount, "chargeback", 0, now)
            if row is not None:
                self.store.move_refund(row.id, ("requested",), "done", now)
            if self.policy.revoke_on_chargeback:
                self.store.revoke(payment.id, now)
            self.store.post(now, "refunds", "bot:stars", payment.total_nano, f"chargeback:{payment.charge_id}")
            order = self.store.get_order(payment.order_id) if payment.order_id else None
            if order is not None and self.catalog[order.product_id].kind != "subscription":
                self.store.move_order(order.id, S.CHARGEBACK, now)

    def audit_ledger(self, *, offset: int = 0, page_size: int = 100) -> LedgerAudit:
        """Read-only: page getStarTransactions from `offset` until a short page and compare it
        with the ledger. An outgoing `invoice_payment` to a user carries the refunded charge id
        (StarTransaction.id) and must have a `refund:` or `chargeback:` posting; a charge id is one
        incoming transaction, so income posted twice under it is a double credit. Pass the
        previous run's `next_offset` to read only the new part of the statement."""
        if not 1 <= page_size <= 100:
            raise ValueError("getStarTransactions takes a limit of 1-100")
        income: dict[str, int] = {}
        reversed_ids: set[str] = set()
        for ref, debit, credit in self.store.ledger_rows("bot:stars"):
            if debit:                                          # income: ref is the charge id
                income[ref] = income.get(ref, 0) + 1
            elif credit:                                       # only finalize_refund and _chargeback reverse a charge
                kind, sep, charge = ref.partition(":")
                if sep and kind in REVERSAL_REFS:
                    reversed_ids.add(charge)
        audit = LedgerAudit(double_credits=sorted(c for c, n in income.items() if n > 1))
        while True:
            page = self.tx.call("getStarTransactions", {"offset": offset, "limit": page_size})["transactions"]
            audit.pages += 1
            offset += len(page)
            for tx in page:
                partner = tx.get("receiver") or {}
                if (partner.get("type") == "user" and partner.get("transaction_type") == "invoice_payment"
                        and tx["id"] not in reversed_ids and tx["id"] not in audit.missing_refunds):
                    audit.missing_refunds.append(tx["id"])
            if len(page) < page_size:
                break
        audit.next_offset = offset
        return audit

    # ---------------------------------------------------------------- helpers

    def _send(self, chat_id: int, text: str, markup: dict[str, Any] | None = None) -> None:
        params: dict[str, Any] = {"chat_id": chat_id, "text": text}
        if markup:
            params["reply_markup"] = markup
        try:
            self.tx.call("sendMessage", params)
        except (OutcomeUnknown, TelegramError):
            pass    # the state is already stored; the user sees it in /purchases

    def _tell_admin(self, text: str) -> None:
        if self.admin_chat_id is not None:
            self._send(self.admin_chat_id, text)


__all__ = ["ALLOWED_UPDATES", "webhook_secret_ok", "NANO", "XTR", "LedgerAudit", "Offer", "Order", "OrderStatus", "Payment",
           "PaymentStore", "Product", "RailVerdict", "ReconReport", "Refund", "RefundPolicy", "SqliteStore", "StarsPayments",
           "Subscription", "TEXTS", "TRANSITIONS", "check_rail", "parse_payload", "sign_payload"]
