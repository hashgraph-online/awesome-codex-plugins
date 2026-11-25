"""Per-method request examples for the Bot API domain `payments`, recorded offline (Bot API 10.5).

Invoices, the shipping path, pre-checkout, the bot's Star balance and statement, refunds and
subscriptions: one small function per method makes the call the agent note points at. The values are
synthetic (a print shop bot: a photo book shipped through a payment provider, a Pro plan sold for
Stars). `run_all()` returns the FakeTransport whose `calls` `export_payloads.py --only api-payments`
writes to examples/payloads/api-payments.json.

The incoming updates (shipping_query, pre_checkout_query, successful_payment) are scripted inputs, not
calls; each answer is computed from the order the server keeps, never from the update alone. The
shipping path: sendInvoice with is_flexible and need_shipping_address -> shipping_query ->
answerShippingQuery with ShippingOption list -> pre_checkout_query carrying shipping_option_id ->
answerPreCheckoutQuery. Shipping exists only for provider invoices: Stars ignore those fields, so the
provider token is a placeholder read from the environment, never a real token. getStarTransactions is
paged with offset/limit until a short page. refundStarPayment and editUserStarSubscription are recorded
requests, never sent: a bot makes them on an admin's confirmation of the exact charge.

Run:  py -3 examples/python/recipes/api_payments.py
"""
from __future__ import annotations

import _common as c
from tgkit.transport import FakeTransport

STATUS = "production (refundStarPayment and editUserStarSubscription are recorded requests, never sent; " \
         "the provider token is a placeholder)"
CONTEXT = "private chat with the buyer; provider invoice for a physical good, Stars subscription link for a digital plan"

STEP_CONTEXT = {
    "sendInvoice": "any chat; physical good through a provider: provider_token from @BotFather (placeholder, "
                   "kept in the environment), ISO 4217 currency; shipping fields are ignored for Stars",
    "answerShippingQuery": "after a shipping_query update; only for invoices with is_flexible and need_shipping_address",
    "answerPreCheckoutQuery": "after a pre_checkout_query update; answer within 10 seconds",
    "createInvoiceLink": "no chat; Stars subscription link: XTR, subscription_period 2592000, at most 10000 Stars",
    "getMyStarBalance": "no parameters; the bot's own balance",
    "getStarTransactions": "the bot's statement, chronological; paged with offset and limit (1-100)",
    "refundStarPayment": "a Stars payment of this user, refunded whole; on an admin's confirmation; recorded, not sent",
    "editUserStarSubscription": "an active Stars subscription of this user; stops renewal, access lasts to the "
                                "period end; recorded, not sent",
}

NOW = 1763191000
DAY = 86400
BUYER = {"id": 111111111, "is_bot": False, "first_name": "Olena", "language_code": "uk"}
PROVIDER_TOKEN = "PROVIDER_TOKEN_FROM_ENV"      # the real token from @BotFather stays in the environment
BOOK_PAYLOAD = "ord:5b2e91c4d0aa.3f6c0e9a81d2b7c4"
PRO_PAYLOAD = "ord:8d1f0a7e6c3b.a90e2d4c7b15f638"
PRO_CHARGE = "stxPro7Q2wLm"
PRO_PRICES = [{"label": "Pro, 30 days", "amount": 300}]
PRO_ORDER = {"payload": PRO_PAYLOAD, "user_id": BUYER["id"], "currency": "XTR", "prices": PRO_PRICES}
BOOK_PRICES = [{"label": "Photo book A5, 40 pages", "amount": 2490}, {"label": "Gift wrap", "amount": 300}]
SHIPPING = {"UA": [{"id": "nova", "title": "Nova Poshta branch, 1-2 days", "prices": [{"label": "Delivery", "amount": 350}]},
                   {"id": "courier", "title": "Courier to the door, 1 day", "prices": [{"label": "Courier", "amount": 900}]}]}
ADDRESS = {"country_code": "UA", "state": "", "city": "Kyiv", "street_line1": "Khreshchatyk St 1",
           "street_line2": "apt 5", "post_code": "01001"}


def _total(prices: list[dict]) -> int:
    return sum(p["amount"] for p in prices)


# --- the shipping path (provider invoice) ------------------------------------------------------

def send_invoice(t: FakeTransport) -> dict:
    return t.call("sendInvoice", {
        "chat_id": BUYER["id"], "title": "Photo book A5", "description": "40 pages, hardcover, printed from your album.",
        "payload": BOOK_PAYLOAD, "provider_token": PROVIDER_TOKEN, "currency": "EUR", "prices": BOOK_PRICES,
        "start_parameter": "photobook", "need_name": True, "need_shipping_address": True, "is_flexible": True,
        "reply_markup": {"inline_keyboard": [[{"text": "Pay", "pay": True}]]}})


SHIPPING_QUERY = {"update_id": 700001, "shipping_query": {
    "id": "sq-7711", "from": BUYER, "invoice_payload": BOOK_PAYLOAD, "shipping_address": ADDRESS}}


def answer_shipping_query(t: FakeTransport, update: dict) -> list[dict]:
    query = update["shipping_query"]
    options = SHIPPING.get(query["shipping_address"]["country_code"])
    if query["invoice_payload"] != BOOK_PAYLOAD or not options:
        t.call("answerShippingQuery", {"shipping_query_id": query["id"], "ok": False,
                                       "error_message": "Sorry, we can't deliver to this address yet."})
        return []
    t.call("answerShippingQuery", {"shipping_query_id": query["id"], "ok": True, "shipping_options": options})
    return options


def book_pre_checkout(options: list[dict]) -> dict:
    nova = next(o for o in options if o["id"] == "nova")
    return {"update_id": 700002, "pre_checkout_query": {
        "id": "pcq-7712", "from": BUYER, "currency": "EUR", "total_amount": _total(BOOK_PRICES) + _total(nova["prices"]),
        "invoice_payload": BOOK_PAYLOAD, "shipping_option_id": "nova",
        "order_info": {"name": "Olena Koval", "shipping_address": ADDRESS}}}


def book_order(options: list[dict]) -> dict:
    """The order the server stored when it sent the invoice, plus the ShippingOptions it offered."""
    return {"payload": BOOK_PAYLOAD, "user_id": BUYER["id"], "currency": "EUR", "prices": BOOK_PRICES,
            "shipping_options": options}


def pre_checkout_mismatch(q: dict, order: dict) -> str | None:
    """The first field of the query that disagrees with the server-side order, or None. The amount
    is checked last: a matching total proves nothing when the payload, payer, currency or shipping
    option belongs to another order."""
    if q.get("invoice_payload") != order["payload"]:
        return "invoice_payload"
    if (q.get("from") or {}).get("id") != order["user_id"]:
        return "from"
    if q.get("currency") != order["currency"]:
        return "currency"
    offered = {o["id"]: o for o in order.get("shipping_options") or []}
    chosen = q.get("shipping_option_id")
    if offered and chosen not in offered or not offered and chosen is not None:
        return "shipping_option_id"
    shipping = _total(offered[chosen]["prices"]) if offered else 0
    if q.get("total_amount") != _total(order["prices"]) + shipping:
        return "total_amount"
    return None


def answer_pre_checkout_query(t: FakeTransport, update: dict, order: dict) -> bool:
    """Local checks against the stored order only, then the answer: the 10-second deadline leaves no
    room for slow work."""
    q = update["pre_checkout_query"]
    mismatch = pre_checkout_mismatch(q, order)
    if mismatch is None:
        t.call("answerPreCheckoutQuery", {"pre_checkout_query_id": q["id"], "ok": True})
        return True
    message = ("The price has changed. A new invoice is below; nothing was charged." if mismatch == "total_amount"
               else "This checkout doesn't match your order, so nothing was charged. Please open the invoice again.")
    t.call("answerPreCheckoutQuery", {"pre_checkout_query_id": q["id"], "ok": False, "error_message": message})
    return False


# --- the Stars subscription --------------------------------------------------------------------

def create_invoice_link(t: FakeTransport) -> str:
    t.script("createInvoiceLink", "https://t.me/$pro_plan_link")
    return t.call("createInvoiceLink", {
        "title": "Pro plan", "description": "Unlimited layouts and a priority print queue. Renews every 30 days.",
        "payload": PRO_PAYLOAD, "currency": "XTR", "prices": PRO_PRICES, "subscription_period": 2592000})


PRO_PRE_CHECKOUT = {"update_id": 700003, "pre_checkout_query": {
    "id": "pcq-7713", "from": BUYER, "currency": "XTR", "total_amount": 300, "invoice_payload": PRO_PAYLOAD}}

PRO_PAID = {"update_id": 700004, "message": {
    "message_id": 4410, "date": NOW + 60, "chat": {"id": BUYER["id"], "type": "private", "first_name": "Olena"},
    "from": BUYER, "successful_payment": {
        "currency": "XTR", "total_amount": 300, "invoice_payload": PRO_PAYLOAD,
        "subscription_expiration_date": NOW + 60 + 30 * DAY, "is_recurring": True, "is_first_recurring": True,
        "telegram_payment_charge_id": PRO_CHARGE, "provider_payment_charge_id": PRO_CHARGE}}}


# --- the bot's Stars: balance and statement ----------------------------------------------------

def get_my_star_balance(t: FakeTransport) -> dict:
    t.script("getMyStarBalance", {"amount": 1297, "nanostar_amount": 500000000})
    return t.call("getMyStarBalance", {})


STATEMENT = [
    {"id": PRO_CHARGE, "amount": 300, "date": NOW + 60,
     "source": {"type": "user", "transaction_type": "invoice_payment", "user": BUYER,
                "invoice_payload": PRO_PAYLOAD, "subscription_period": 2592000}},
    {"id": "bc-2201", "amount": 2, "nanostar_amount": 500000000, "date": NOW + 3600,
     "receiver": {"type": "telegram_api", "request_count": 25}},
    {"id": "wd-3301", "amount": 1000, "date": NOW + 2 * DAY,
     "receiver": {"type": "fragment", "withdrawal_state": {"type": "pending"}}},
]


def get_star_transactions(t: FakeTransport, page_size: int = 2) -> list[dict]:
    """Page from offset 0 until a page shorter than the limit (100 in production; 2 shows the paging)."""
    t.script("getStarTransactions", *[{"transactions": STATEMENT[i:i + page_size]}
                                      for i in range(0, len(STATEMENT) + 1, page_size)])
    rows, offset = [], 0
    while True:
        page = t.call("getStarTransactions", {"offset": offset, "limit": page_size})["transactions"]
        rows += page
        offset += len(page)
        if len(page) < page_size:
            return rows


# --- refund and renewal ------------------------------------------------------------------------

def refund_star_payment(t: FakeTransport, rows: list[dict]) -> None:
    paid = next(r for r in rows if r["id"] == PRO_CHARGE and r.get("source", {}).get("type") == "user")
    t.call("refundStarPayment", {"user_id": paid["source"]["user"]["id"], "telegram_payment_charge_id": paid["id"]})


def edit_user_star_subscription(t: FakeTransport) -> None:
    t.call("editUserStarSubscription", {"user_id": BUYER["id"], "telegram_payment_charge_id": PRO_CHARGE,
                                        "is_canceled": True})


def run_all() -> FakeTransport:
    t = FakeTransport()
    send_invoice(t)
    options = answer_shipping_query(t, SHIPPING_QUERY)
    c.check([o["id"] for o in options] == ["nova", "courier"], "answerShippingQuery offers the options for the address")
    c.check(answer_pre_checkout_query(t, book_pre_checkout(options), book_order(options)),
            "pre-checkout matches the stored order: payload, payer, currency, offered ShippingOption, "
            "then total = invoice prices + that option")
    link = create_invoice_link(t)
    c.check(link.startswith("https://t.me/"), "createInvoiceLink returns the subscription link to send in a button")
    c.check(answer_pre_checkout_query(t, PRO_PRE_CHECKOUT, PRO_ORDER), "the Stars pre-checkout is answered the same way")
    paid = PRO_PAID["message"]["successful_payment"]
    c.check(paid["is_first_recurring"] and paid["telegram_payment_charge_id"] == PRO_CHARGE,
            "successful_payment carries the charge id that refunds and the statement use")
    balance = get_my_star_balance(t)
    c.check(isinstance(balance["amount"], int), "getMyStarBalance is a StarAmount: integers, never floats")
    rows = get_star_transactions(t)
    c.check([p["offset"] for p in t.params_of("getStarTransactions")] == [0, 2],
            "getStarTransactions is paged until a short page")
    refund_star_payment(t, rows)
    edit_user_star_subscription(t)
    c.check(set(t.methods()) == set(STEP_CONTEXT), "every payments method is called")
    return t


if __name__ == "__main__":
    c.dump(run_all(), "Payments: invoices, shipping, pre-checkout, Stars balance and statement, refunds, subscriptions")
