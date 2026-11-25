"""Per-method request examples for the Bot API domain `platform`, recorded offline (Bot API 10.5).

Getting updates and webhooks, managed bots, games and Telegram Passport errors. One small function per
method makes the call the agent note points at; ids, URLs, hashes and tokens are synthetic. `run_all()`
returns the FakeTransport whose `calls` `export_payloads.py --only api-platform` writes to
examples/payloads/api-platform.json. A call that needs an earlier answer reads it from the scripted
result: getUpdates delivers the managed_bot update whose bot id the managed-bot methods take, sendGame
returns the message_id the score methods take. deleteWebhook and replaceManagedBotToken are recorded
requests, never sent. A managed bot's token is a secret: it goes to the secret store and is never
printed, logged or put in a request. Server setup (TLS, certificates, hosting) is outside this file.

Run:  py -3 examples/python/recipes/api_platform.py
"""
from __future__ import annotations

import re

import _common as c
from tgkit.transport import FakeTransport

STATUS = ("production (deleteWebhook and replaceManagedBotToken are recorded requests, never sent; "
          "managed bot tokens are stored, never printed)")
CONTEXT = ("bot-wide: update intake and managed bots take no chat; games in private chats, groups and "
           "supergroups; Passport errors go to the user who shared the data")
STEP_CONTEXT = {
    "getUpdates": "any bot while no webhook is set; offset = highest update_id received + 1",
    "setWebhook": "the bot's deploy step; HTTPS url on port 443, 80, 88 or 8443; secret_token is 1-256 "
                  "characters of A-Z, a-z, 0-9, _ and -, loaded from the environment (here a placeholder)",
    "getWebhookInfo": "any bot; url is empty while the bot uses getUpdates; secret_token is never returned",
    "deleteWebhook": "the bot's deploy step, switching back to getUpdates; recorded request, never sent",
    "getManagedBotToken": "the manager bot, for a bot it manages (user_id = ManagedBotUpdated.bot.id); "
                          "the token goes to the secret store, never to logs, chats or URLs",
    "getManagedBotAccessSettings": "the manager bot, for a bot it manages",
    "setManagedBotAccessSettings": "the manager bot, on the managed bot owner's decision; up to 10 "
                                   "added_user_ids, ignored unless is_access_restricted is true",
    "replaceManagedBotToken": "the manager bot, on the owner's decision; revokes the current token; "
                              "recorded request, never sent",
    "sendGame": "private chat, group or supergroup (not channels or channel direct messages chats); "
                "a game created in @BotFather with /newgame",
    "setGameScore": "a game message the bot sent (chat_id + message_id) or inline_message_id; "
                    "the score comes from the bot's server",
    "getGameHighScores": "a game message the bot sent (chat_id + message_id) or inline_message_id",
    "setPassportDataErrors": "the user who shared Telegram Passport data with the bot; hashes come from "
                             "the decrypted credentials (core.telegram.org/passport)",
}

# --- updates and webhook -----------------------------------------------------------------------

WEBHOOK_URL = "https://bot.example.com/tg/webhook"
# A placeholder that passes the catalog's rule for secret_token; a real one is random and read from env.
SECRET_TOKEN = "FAKE-webhook-secret_replace-from-env"
SECRET_TOKEN_RULE = re.compile(r"^[A-Za-z0-9_-]{1,256}$")
ALLOWED_UPDATES = ["message", "callback_query", "my_chat_member", "managed_bot"]
LAST_SEEN_UPDATE_ID = 900000400

# --- managed bots --------------------------------------------------------------------------------

OWNER = {"id": 111111111, "is_bot": False, "first_name": "Olena"}
MANAGED_BOT = {"id": 7000000001, "is_bot": True, "first_name": "Olena's Shop", "username": "olena_shop_bot"}
TEAMMATE = 222222222
# Offline stand-ins for the strings Telegram returns; they are not real tokens and are never printed.
FAKE_TOKEN = "FAKE-managed-bot-token-offline"
FAKE_NEW_TOKEN = "FAKE-managed-bot-token-rotated"

# --- games and Passport ------------------------------------------------------------------------

GAME_CHAT = -1001234567890
PLAYER = 333333333
GAME = "pizza_runner"
# Base64 SHA-256 values as DataCredentials.data_hash and FileCredentials.file_hash carry them after
# decryption; these are computed from synthetic strings.
DATA_HASH = "rE2DAEJ1IAoM1oR9zmrW2tctp1dfgOF+iTCk4+rUPOE="
FRONT_SIDE_HASH = "VTWs8tNYPRamtorGdTP9NjDMb1WUcGUwdMpvyVFhHF8="


class SecretStore:
    """Holds managed bot tokens by bot id; repr and str never show a value."""

    def __init__(self) -> None:
        self._values: dict[int, str] = {}

    def put(self, bot_id: int, token: str) -> None:
        self._values[bot_id] = token

    def get(self, bot_id: int) -> str | None:
        return self._values.get(bot_id)

    def __repr__(self) -> str:
        return f"SecretStore(<{len(self._values)} tokens hidden>)"

    __str__ = __repr__


def get_updates(t: FakeTransport) -> list:
    t.script("getUpdates", [
        {"update_id": LAST_SEEN_UPDATE_ID + 1, "managed_bot": {"user": OWNER, "bot": MANAGED_BOT}},
        {"update_id": LAST_SEEN_UPDATE_ID + 2, "message": {
            "message_id": 51, "date": 1763191000, "chat": {"id": OWNER["id"], "type": "private", "first_name": "Olena"},
            "from": OWNER, "managed_bot_created": {"bot": MANAGED_BOT}}},
    ])
    return t.call("getUpdates", {"offset": LAST_SEEN_UPDATE_ID + 1, "limit": 100, "timeout": 50,
                                 "allowed_updates": ALLOWED_UPDATES})


def set_webhook(t: FakeTransport) -> bool:
    return t.call("setWebhook", {"url": WEBHOOK_URL, "secret_token": SECRET_TOKEN, "max_connections": 40,
                                 "allowed_updates": ALLOWED_UPDATES, "drop_pending_updates": False})


def get_webhook_info(t: FakeTransport) -> dict:
    t.script("getWebhookInfo", {"url": WEBHOOK_URL, "has_custom_certificate": False, "pending_update_count": 0,
                                "max_connections": 40, "allowed_updates": ALLOWED_UPDATES})
    return t.call("getWebhookInfo", {})


def delete_webhook(t: FakeTransport) -> bool:
    return t.call("deleteWebhook", {"drop_pending_updates": False})


# --- managed bots --------------------------------------------------------------------------------

def get_managed_bot_token(t: FakeTransport, bot_id: int, store: SecretStore) -> None:
    t.script("getManagedBotToken", FAKE_TOKEN)
    store.put(bot_id, t.call("getManagedBotToken", {"user_id": bot_id}))


def get_managed_bot_access_settings(t: FakeTransport, bot_id: int) -> dict:
    t.script("getManagedBotAccessSettings", {"is_access_restricted": False})
    return t.call("getManagedBotAccessSettings", {"user_id": bot_id})


def set_managed_bot_access_settings(t: FakeTransport, bot_id: int) -> bool:
    return t.call("setManagedBotAccessSettings", {"user_id": bot_id, "is_access_restricted": True,
                                                  "added_user_ids": [TEAMMATE]})


def replace_managed_bot_token(t: FakeTransport, bot_id: int, store: SecretStore) -> None:
    t.script("replaceManagedBotToken", FAKE_NEW_TOKEN)
    store.put(bot_id, t.call("replaceManagedBotToken", {"user_id": bot_id}))


# --- games ---------------------------------------------------------------------------------------

def send_game(t: FakeTransport) -> dict:
    t.script("sendGame", {
        "message_id": 4101, "date": 1763191200,
        "chat": {"id": GAME_CHAT, "type": "supergroup", "title": "Pizza night"},
        "game": {"title": "Pizza Runner", "description": "Deliver as many pizzas as you can in 60 seconds.",
                 "photo": [{"file_id": "AgACAgIAAxkBAAIBgGameCover", "file_unique_id": "AQADgame",
                            "width": 640, "height": 360}]},
    })
    return t.call("sendGame", {
        "chat_id": GAME_CHAT, "game_short_name": GAME,
        "reply_markup": {"inline_keyboard": [[{"text": "Play Pizza Runner", "callback_game": {}}],
                                             [{"text": "How to play", "callback_data": "game:rules"}]]},
    })


def set_game_score(t: FakeTransport, message: dict) -> dict:
    t.script("setGameScore", {**message, "game": {**message["game"], "text": "1. Taras: 4200"}})
    return t.call("setGameScore", {"user_id": PLAYER, "score": 4200, "chat_id": GAME_CHAT,
                                   "message_id": message["message_id"]})


def get_game_high_scores(t: FakeTransport, message: dict) -> list:
    t.script("getGameHighScores", [
        {"position": 1, "user": {"id": PLAYER, "is_bot": False, "first_name": "Taras"}, "score": 4200},
        {"position": 2, "user": {"id": TEAMMATE, "is_bot": False, "first_name": "Ira"}, "score": 3900},
    ])
    return t.call("getGameHighScores", {"user_id": PLAYER, "chat_id": GAME_CHAT,
                                        "message_id": message["message_id"]})


# --- Telegram Passport ---------------------------------------------------------------------------

def set_passport_data_errors(t: FakeTransport) -> bool:
    return t.call("setPassportDataErrors", {"user_id": OWNER["id"], "errors": [
        {"source": "data", "type": "personal_details", "field_name": "birth_date", "data_hash": DATA_HASH,
         "message": "The date of birth is in the future. Enter it as on your passport."},
        {"source": "front_side", "type": "passport", "file_hash": FRONT_SIDE_HASH,
         "message": "The photo of the front side is blurry. Take a new one in good light."},
    ]})


def run_all() -> FakeTransport:
    t = FakeTransport()
    updates = get_updates(t)
    next_offset = max(u["update_id"] for u in updates) + 1
    c.check(next_offset == LAST_SEEN_UPDATE_ID + 3, "the next getUpdates offset is the highest update_id + 1")
    c.check(SECRET_TOKEN_RULE.fullmatch(SECRET_TOKEN) is not None,
            "the placeholder secret_token passes the catalog rule (1-256 of A-Z, a-z, 0-9, _ and -)")
    set_webhook(t)
    info = get_webhook_info(t)
    c.check(info["url"] == WEBHOOK_URL and "secret_token" not in info,
            "getWebhookInfo shows the url and never returns the secret_token")
    delete_webhook(t)

    bot_id = next(u["managed_bot"]["bot"]["id"] for u in updates if "managed_bot" in u)
    store = SecretStore()
    get_managed_bot_token(t, bot_id, store)
    c.check(store.get(bot_id) is not None, "the managed bot's token is in the secret store, not in any output")
    access = get_managed_bot_access_settings(t, bot_id)
    c.check(access["is_access_restricted"] is False, "the managed bot is open before the owner restricts it")
    set_managed_bot_access_settings(t, bot_id)
    old = store.get(bot_id)
    replace_managed_bot_token(t, bot_id, store)
    c.check(store.get(bot_id) != old, "replaceManagedBotToken's new token replaced the revoked one in the store")
    c.check(all(FAKE_TOKEN not in str(p) and FAKE_NEW_TOKEN not in str(p) for _, p in t.calls),
            "no request carries a managed bot token")

    game_message = send_game(t)
    set_game_score(t, game_message)
    rows = get_game_high_scores(t, game_message)
    c.check(rows[0]["user"]["id"] == PLAYER, "getGameHighScores reads the rows of the message sendGame returned")
    set_passport_data_errors(t)
    c.check(sorted(t.methods()) == sorted(STEP_CONTEXT), "every platform method is called exactly once")
    return t


if __name__ == "__main__":
    c.dump(run_all(), "Platform: updates, webhook, managed bots, games, Passport errors")
