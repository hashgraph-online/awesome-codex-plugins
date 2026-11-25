"""Bot API requests for the bot-settings domain: commands, menu button, bot profile, callback answers.

One small function per method, synthetic ids, offline (FakeTransport records each request after a JSON
round trip; nothing is sent to Telegram). Written to examples/payloads/api-bot-settings.json by
`py -3 examples/python/export_payloads.py --only api-bot-settings`.

Run:  py -3 examples/python/recipes/api_bot_settings.py
"""
from __future__ import annotations

import _common as c
from tgkit.transport import FakeTransport

STATUS = "production (destructive and one-off calls are recorded requests, never sent)"
CONTEXT = "bot-wide settings (no chat needed); menu button per private chat; callback answers from any chat with an inline keyboard"
STEP_CONTEXT = {
    "logOut": "one-off, cloud Bot API server only: run once before moving the bot to a local server; "
              "no login back to the cloud server for 10 minutes",
    "close": "one-off, local Bot API server: run once before moving the bot to another local server; "
             "delete the webhook first; error 429 in the first 10 minutes after launch",
    "setMyCommands": "private, group or supergroup scopes; scope chat and chat_member need such a chat_id "
                     "(channels and channel direct messages chats aren't supported)",
    "getMyCommands": "same scopes as setMyCommands; an unset scope answers with an empty list",
    "deleteMyCommands": "same scopes as setMyCommands; broader lists apply to the affected users afterwards",
    "setChatMenuButton": "chat_id of a private chat; without it the default menu button changes",
    "getChatMenuButton": "chat_id of a private chat; without it the default menu button is returned",
    "setMyDefaultAdministratorRights": "suggestion for groups and supergroups (for_channels true: channels); "
                                       "users may change the rights before adding the bot",
    "getMyDefaultAdministratorRights": "for_channels true reads the channel rights, otherwise groups and supergroups",
    "setMyProfilePhoto": "multipart/form-data upload: the file travels in the form field named in attach://; "
                         "a profile photo can't be reused by id or URL",
    "answerCallbackQuery": "any chat where the bot sent an inline keyboard or rich message with a callback button",
    "savePreparedKeyboardButton": "for a Mini App user; the button must be request_users, request_chat or request_managed_bot",
}

USER_ID = 111111111
CALLBACK_QUERY_ID = "4382000000000000101"
COMMANDS = [
    {"command": "start", "description": "Open the main menu"},
    {"command": "orders", "description": "Your orders"},
    {"command": "help", "description": "How it works"},
]
PRIVATE_CHATS = {"type": "all_private_chats"}


def get_me(t: FakeTransport) -> dict:
    t.script("getMe", c.fixture("get_me_bot_full_info.json")["result"])
    return t.call("getMe", {})


def set_my_commands(t: FakeTransport) -> bool:
    return t.call("setMyCommands", {"commands": COMMANDS, "scope": PRIVATE_CHATS, "language_code": "en"})


def get_my_commands(t: FakeTransport) -> list:
    t.script("getMyCommands", COMMANDS)
    return t.call("getMyCommands", {"scope": PRIVATE_CHATS, "language_code": "en"})


def delete_my_commands(t: FakeTransport) -> bool:
    return t.call("deleteMyCommands", {"scope": {"type": "all_group_chats"}, "language_code": "de"})


def set_my_name(t: FakeTransport) -> bool:
    return t.call("setMyName", {"name": "Pizza Place Orders", "language_code": "en"})


def get_my_name(t: FakeTransport) -> dict:
    t.script("getMyName", {"name": "Pizza Place Orders"})
    return t.call("getMyName", {"language_code": "en"})


def set_my_description(t: FakeTransport) -> bool:
    return t.call("setMyDescription", {"description": "I take pizza orders and tell you where they are. "
                                                      "Send /start to begin.", "language_code": "en"})


def get_my_description(t: FakeTransport) -> dict:
    t.script("getMyDescription", {"description": "I take pizza orders and tell you where they are. "
                                                 "Send /start to begin."})
    return t.call("getMyDescription", {"language_code": "en"})


def set_my_short_description(t: FakeTransport) -> bool:
    return t.call("setMyShortDescription", {"short_description": "Order pizza and follow it to your door",
                                            "language_code": "en"})


def get_my_short_description(t: FakeTransport) -> dict:
    t.script("getMyShortDescription", {"short_description": "Order pizza and follow it to your door"})
    return t.call("getMyShortDescription", {"language_code": "en"})


def set_chat_menu_button(t: FakeTransport) -> bool:
    return t.call("setChatMenuButton", {"chat_id": USER_ID,
                                        "menu_button": {"type": "web_app", "text": "Open shop",
                                                        "web_app": {"url": "https://example.com/shop"}}})


def get_chat_menu_button(t: FakeTransport) -> dict:
    t.script("getChatMenuButton", {"type": "commands"})
    return t.call("getChatMenuButton", {"chat_id": USER_ID})


def set_my_default_administrator_rights(t: FakeTransport) -> bool:
    rights = {"is_anonymous": False, "can_manage_chat": True, "can_delete_messages": True,
              "can_manage_video_chats": False, "can_restrict_members": True, "can_promote_members": False,
              "can_change_info": False, "can_invite_users": False, "can_post_stories": False,
              "can_edit_stories": False, "can_delete_stories": False, "can_send_welcome_messages": False,
              "can_pin_messages": True}
    return t.call("setMyDefaultAdministratorRights", {"rights": rights, "for_channels": False})


def get_my_default_administrator_rights(t: FakeTransport) -> dict:
    t.script("getMyDefaultAdministratorRights", {"is_anonymous": False, "can_manage_chat": True})
    return t.call("getMyDefaultAdministratorRights", {"for_channels": False})


def set_my_settings(t: FakeTransport) -> bool:
    return t.call("setMySettings", {"supports_inline_queries": True, "inline_query_placeholder": "Search orders...",
                                    "has_topics_enabled": True, "has_topic_sidebar": True,
                                    "callback_query_mode": "auto"})


def set_my_profile_photo(t: FakeTransport) -> bool:
    return t.call("setMyProfilePhoto", {"photo": {"type": "static", "photo": "attach://bot_avatar"}})


def remove_my_profile_photo(t: FakeTransport) -> bool:
    return t.call("removeMyProfilePhoto", {})


def answer_callback_query(t: FakeTransport) -> bool:
    return t.call("answerCallbackQuery", {"callback_query_id": CALLBACK_QUERY_ID, "text": "Order confirmed"})


def save_prepared_keyboard_button(t: FakeTransport) -> dict:
    t.script("savePreparedKeyboardButton", {"id": "prepared-btn-1"})
    return t.call("savePreparedKeyboardButton", {
        "user_id": USER_ID,
        "button": {"text": "Choose a group", "request_chat": {"request_id": 7, "chat_is_channel": False,
                                                              "bot_is_member": True}}})


def log_out(t: FakeTransport) -> bool:
    return t.call("logOut", {})


def close_instance(t: FakeTransport) -> bool:
    return t.call("close", {})


def run_all() -> FakeTransport:
    t = FakeTransport()
    for step in (get_me, set_my_commands, get_my_commands, delete_my_commands,
                 set_my_name, get_my_name, set_my_description, get_my_description,
                 set_my_short_description, get_my_short_description,
                 set_chat_menu_button, get_chat_menu_button,
                 set_my_default_administrator_rights, get_my_default_administrator_rights,
                 set_my_settings, set_my_profile_photo, remove_my_profile_photo,
                 answer_callback_query, save_prepared_keyboard_button,
                 log_out, close_instance):  # one-off server moves last: after logOut the bot cannot use the cloud server for 10 minutes
        step(t)
    return t


def main() -> None:
    t = run_all()
    c.dump(t, "Bot settings: one request per method")
    c.check(len(t.calls) == 21, "21 requests, one per method")


if __name__ == "__main__":
    main()
