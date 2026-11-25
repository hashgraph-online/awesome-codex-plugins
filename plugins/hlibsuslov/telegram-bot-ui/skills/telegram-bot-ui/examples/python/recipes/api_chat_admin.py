"""Chat administration: one request per method (members, rights, invite links, join requests).

Run:  py -3 examples/python/recipes/api_chat_admin.py        (offline; nothing is sent)
Written to payloads/api-chat-admin.json by export_payloads.py. Ids and links are synthetic. Bans,
restrictions, promotions and revocations are recorded requests only: a bot sends them on a human
admin's decision, with the actor and the reason logged. Where a call needs a value an earlier call
returned (an invite link), FakeTransport.script supplies that result.
"""
from __future__ import annotations

import _common as c
from tgkit.transport import FakeTransport

STATUS = "production (moderation calls are recorded requests, never sent)"
CONTEXT = "supergroup, group and channel where the bot is an administrator"

NOT_NAMED = "bot admin with the appropriate administrator rights (the method text names no right)"
STEP_CONTEXT = {
    "banChatMember": f"group, supergroup or channel; {NOT_NAMED}",
    "unbanChatMember": "supergroup or channel; bot is an administrator (the method text names no right)",
    "banChatSenderChat": f"supergroup or channel; {NOT_NAMED}",
    "unbanChatSenderChat": f"supergroup or channel; {NOT_NAMED}",
    "restrictChatMember": f"supergroup; {NOT_NAMED}",
    "promoteChatMember": f"supergroup or channel; {NOT_NAMED}",
    "setChatAdministratorCustomTitle": "supergroup; the administrator was promoted by the bot",
    "setChatMemberTag": "group or supergroup; bot admin with can_manage_tags",
    "setChatPermissions": "group or supergroup; bot admin with can_restrict_members",
    "createChatInviteLink": f"chat; {NOT_NAMED}",
    "editChatInviteLink": f"chat; non-primary link created by the bot; {NOT_NAMED}",
    "createChatSubscriptionInviteLink": "channel; bot with can_invite_users",
    "editChatSubscriptionInviteLink": "subscription link created by the bot; bot with can_invite_users",
    "revokeChatInviteLink": f"chat; link created by the bot; {NOT_NAMED}",
    "exportChatInviteLink": f"chat; {NOT_NAMED}",
    "approveChatJoinRequest": "chat; request without query_id; bot admin with can_invite_users",
    "declineChatJoinRequest": "chat; request without query_id; bot admin with can_invite_users",
    "sendChatJoinRequestWebApp": "bot assigned to process join requests; the request carries query_id; within 10 seconds",
    "answerChatJoinRequestQuery": "bot assigned to process join requests; the request carries query_id; within 10 seconds",
}

SUPERGROUP = -1001234567890
CHANNEL = -1009876543210
SPAM_CHANNEL = -1001112223334
NOW = 1763191000
DAY = 86400
BOT = {"id": 777000111, "is_bot": True, "first_name": "Community Guard", "username": "community_guard_bot"}
SPAMMER = 222222222
NEWCOMER = 444444444
MODERATOR = 555555555
MENTOR = 666666666


def _chat_invite_link(url: str, **fields) -> dict:
    """The ChatInviteLink object Telegram returns, required fields filled."""
    return {"invite_link": url, "creator": BOT, "creates_join_request": False, "is_primary": False,
            "is_revoked": False, **fields}


def _join_request(user_id: int, first_name: str, **fields) -> dict:
    """An incoming ChatJoinRequest as the bot receives it."""
    return {"chat": {"id": SUPERGROUP, "type": "supergroup", "title": "Foodies of Kyiv"},
            "from": {"id": user_id, "is_bot": False, "first_name": first_name},
            "user_chat_id": user_id, "date": NOW, **fields}


# Plain requests are decided with approve/decline; a request with query_id belongs to a bot assigned
# to process join requests and is answered through the query methods.
APPROVED = _join_request(333000111, "Olena")
DECLINED = _join_request(333000222, "Promo Bot Fan", bio="Free followers, DM me")
GUARDED = _join_request(333000333, "Taras", query_id="jrq-7781")


# --- members -----------------------------------------------------------------------------------

def ban_chat_member(t: FakeTransport) -> None:
    t.call("banChatMember", {"chat_id": SUPERGROUP, "user_id": SPAMMER, "until_date": NOW + DAY})


def unban_chat_member(t: FakeTransport) -> None:
    t.call("unbanChatMember", {"chat_id": SUPERGROUP, "user_id": SPAMMER, "only_if_banned": True})


def ban_chat_sender_chat(t: FakeTransport) -> None:
    t.call("banChatSenderChat", {"chat_id": SUPERGROUP, "sender_chat_id": SPAM_CHANNEL})


def unban_chat_sender_chat(t: FakeTransport) -> None:
    t.call("unbanChatSenderChat", {"chat_id": SUPERGROUP, "sender_chat_id": SPAM_CHANNEL})


# --- rights ------------------------------------------------------------------------------------

def restrict_chat_member(t: FakeTransport) -> None:
    t.call("restrictChatMember", {
        "chat_id": SUPERGROUP, "user_id": NEWCOMER,
        "permissions": {"can_send_messages": True, "can_send_photos": False, "can_send_videos": False,
                        "can_send_other_messages": False, "can_add_web_page_previews": False},
        "use_independent_chat_permissions": True,
        "until_date": NOW + DAY,
    })


def promote_chat_member(t: FakeTransport) -> None:
    t.call("promoteChatMember", {
        "chat_id": SUPERGROUP, "user_id": MODERATOR,
        "can_delete_messages": True, "can_pin_messages": True, "can_manage_topics": True,
        "can_restrict_members": False,
    })


def set_chat_administrator_custom_title(t: FakeTransport) -> None:
    t.call("setChatAdministratorCustomTitle", {"chat_id": SUPERGROUP, "user_id": MODERATOR, "custom_title": "Moderator"})


def set_chat_member_tag(t: FakeTransport) -> None:
    t.call("setChatMemberTag", {"chat_id": SUPERGROUP, "user_id": MENTOR, "tag": "Mentor"})


def set_chat_permissions(t: FakeTransport) -> None:
    t.call("setChatPermissions", {
        "chat_id": SUPERGROUP,
        "permissions": {"can_send_messages": True, "can_send_photos": True, "can_send_polls": False,
                        "can_send_other_messages": False, "can_add_web_page_previews": True,
                        "can_invite_users": True, "can_pin_messages": False},
        "use_independent_chat_permissions": True,
    })


# --- invite links ------------------------------------------------------------------------------

def create_chat_invite_link(t: FakeTransport) -> dict:
    params = {"chat_id": SUPERGROUP, "name": "Spring promo", "expire_date": NOW + 7 * DAY, "member_limit": 100}
    t.script("createChatInviteLink", _chat_invite_link(
        "https://t.me/+AbCdEfGh1234", name=params["name"], expire_date=params["expire_date"],
        member_limit=params["member_limit"]))
    return t.call("createChatInviteLink", params)


def edit_chat_invite_link(t: FakeTransport, link: dict) -> dict:
    changes = {"name": "Spring promo (extended)", "member_limit": 250}
    t.script("editChatInviteLink", {**link, **changes})
    return t.call("editChatInviteLink", {"chat_id": SUPERGROUP, "invite_link": link["invite_link"], **changes})


def revoke_chat_invite_link(t: FakeTransport, link: dict) -> dict:
    t.script("revokeChatInviteLink", {**link, "is_revoked": True})
    return t.call("revokeChatInviteLink", {"chat_id": SUPERGROUP, "invite_link": link["invite_link"]})


def export_chat_invite_link(t: FakeTransport) -> str:
    t.script("exportChatInviteLink", "https://t.me/+PrImArYlInKwXyZ")
    return t.call("exportChatInviteLink", {"chat_id": SUPERGROUP})


def create_chat_subscription_invite_link(t: FakeTransport) -> dict:
    params = {"chat_id": CHANNEL, "name": "Premium digest", "subscription_period": 2592000, "subscription_price": 250}
    t.script("createChatSubscriptionInviteLink", _chat_invite_link(
        "https://t.me/+SuBsCrIbEr5678", name=params["name"], subscription_period=params["subscription_period"],
        subscription_price=params["subscription_price"]))
    return t.call("createChatSubscriptionInviteLink", params)


def edit_chat_subscription_invite_link(t: FakeTransport, link: dict) -> dict:
    name = "Premium digest (monthly)"
    t.script("editChatSubscriptionInviteLink", {**link, "name": name})
    return t.call("editChatSubscriptionInviteLink", {"chat_id": CHANNEL, "invite_link": link["invite_link"], "name": name})


# --- join requests -----------------------------------------------------------------------------

def approve_chat_join_request(t: FakeTransport) -> None:
    t.call("approveChatJoinRequest", {"chat_id": APPROVED["chat"]["id"], "user_id": APPROVED["from"]["id"]})


def decline_chat_join_request(t: FakeTransport) -> None:
    t.call("declineChatJoinRequest", {"chat_id": DECLINED["chat"]["id"], "user_id": DECLINED["from"]["id"]})


def send_chat_join_request_web_app(t: FakeTransport) -> None:
    t.call("sendChatJoinRequestWebApp", {"chat_join_request_query_id": GUARDED["query_id"],
                                         "web_app_url": "https://example.com/verify?lang=uk"})


def answer_chat_join_request_query(t: FakeTransport) -> None:
    t.call("answerChatJoinRequestQuery", {"chat_join_request_query_id": GUARDED["query_id"], "result": "approve"})


def run_all() -> FakeTransport:
    t = FakeTransport()
    for fn in (ban_chat_member, unban_chat_member, ban_chat_sender_chat, unban_chat_sender_chat,
               restrict_chat_member, promote_chat_member, set_chat_administrator_custom_title,
               set_chat_member_tag, set_chat_permissions):
        fn(t)
    link = create_chat_invite_link(t)
    c.check(link["invite_link"].startswith("https://t.me/+") and link["member_limit"] == 100,
            "createChatInviteLink returns the ChatInviteLink that editChatInviteLink and revoke act on")
    edit_chat_invite_link(t, link)
    revoke_chat_invite_link(t, link)
    export_chat_invite_link(t)
    subscription = create_chat_subscription_invite_link(t)
    edit_chat_subscription_invite_link(t, subscription)
    for fn in (approve_chat_join_request, decline_chat_join_request, send_chat_join_request_web_app,
               answer_chat_join_request_query):
        fn(t)
    c.check(sorted(t.methods()) == sorted(STEP_CONTEXT), "every chat-admin method is called exactly once")
    return t


if __name__ == "__main__":
    c.dump(run_all(), "Chat administration")
