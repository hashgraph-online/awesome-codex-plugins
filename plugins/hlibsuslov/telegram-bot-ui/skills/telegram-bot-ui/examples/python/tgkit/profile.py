"""The baseline user record every bot built with the skill keeps, and how it adapts the interface.

Rules and the storage schema: references/user-profile.md. Standard library only, no network: the caller
passes Bot API objects as dicts (as they arrive in updates or from getChat) and stores the result.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

# Allowlisted /start and startapp payloads: <kind>_<value>. Anything else is recorded as "other".
ACQUISITION = re.compile(r"^(ref|ad|ch|post|qr|item|promo)_([A-Za-z0-9-]{1,48})$")


@dataclass
class Acquisition:
    kind: str           # ref, ad, ch (channel), post, qr, item, promo, organic, other, group_invite, inline
    value: str = ""
    entry: str = ""     # how the first contact happened: start, startapp, join_request, inline, message


def parse_acquisition(payload: str | None, entry: str = "start") -> Acquisition:
    """The first-touch source from a deep-link payload; never trusts free text."""
    if not payload:
        return Acquisition("organic", "", entry)
    m = ACQUISITION.match(payload)
    return Acquisition(m.group(1), m.group(2), entry) if m else Acquisition("other", "", entry)


@dataclass
class Notifications:
    categories: dict[str, bool] = field(default_factory=lambda: {"orders": True, "reminders": True, "news": False})
    quiet_from: str | None = None     # "22:00" in the user's time zone
    quiet_to: str | None = None       # "08:00"
    can_message: bool | None = None   # write access: started the bot, allows_write_to_pm, requestWriteAccess
    blocked_at: datetime | None = None  # my_chat_member with status "kicked" in the private chat


@dataclass
class UserProfile:
    user_id: int
    first_name: str = ""
    last_name: str = ""
    username: str = ""
    language_code: str = ""
    is_premium: bool = False
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    profile_updated_at: datetime | None = None   # when a public profile field last changed (no history kept)
    acquisition: Acquisition | None = None       # first touch only, never overwritten
    terms_version: str = ""
    terms_accepted_at: datetime | None = None
    marketing_opt_in: bool = False
    language: str = ""                           # the app's chosen language (may differ from language_code)
    timezone: str = ""                           # IANA name, e.g. "Europe/Oslo"
    notifications: Notifications = field(default_factory=Notifications)
    labels: set[str] = field(default_factory=set)
    # snapshot from getChat (ChatFullInfo), refreshed on a schedule, see user-profile.md section 2
    active_usernames: list[str] = field(default_factory=list)
    has_private_forwards: bool = False
    restricts_voice_video: bool = False
    accent_color_id: int | None = None
    profile_accent_color_id: int | None = None
    emoji_status_custom_emoji_id: str = ""
    share_theme: dict | None = None
    unique_gift_colors: dict | None = None
    stars_rating_level: int | None = None
    profile_refreshed_at: datetime | None = None


PUBLIC_FIELDS = ("first_name", "last_name", "username", "language_code", "is_premium")


def touch(profile: UserProfile | None, user: dict, now: datetime, payload: str | None = None,
          entry: str = "message") -> UserProfile:
    """Merges the User object from any update. Creates the record on first contact with its acquisition."""
    if profile is None:
        profile = UserProfile(user_id=user["id"], first_seen_at=now, acquisition=parse_acquisition(payload, entry))
    changed = False
    for name in PUBLIC_FIELDS:
        new = user.get(name, False if name == "is_premium" else "")
        if getattr(profile, name) != new:
            setattr(profile, name, new)
            changed = True
    if changed and profile.first_seen_at != now:
        profile.profile_updated_at = now
    profile.last_seen_at = now
    return profile


def apply_chat_full_info(profile: UserProfile, info: dict, now: datetime) -> UserProfile:
    """Keeps only the ChatFullInfo fields the interface uses. Birthdate, bio and the rest stay out unless a
    feature asks for them (user-data.md section 1.2)."""
    profile.active_usernames = list(info.get("active_usernames") or [])
    profile.has_private_forwards = bool(info.get("has_private_forwards"))
    profile.restricts_voice_video = bool(info.get("has_restricted_voice_and_video_messages"))
    profile.accent_color_id = info.get("accent_color_id")
    profile.profile_accent_color_id = info.get("profile_accent_color_id")
    profile.emoji_status_custom_emoji_id = info.get("emoji_status_custom_emoji_id") or ""
    profile.share_theme = info.get("share_theme")
    profile.unique_gift_colors = info.get("unique_gift_colors")
    rating = info.get("rating")
    profile.stars_rating_level = rating.get("level") if isinstance(rating, dict) else None
    profile.profile_refreshed_at = now
    return profile


def chat_member_update(profile: UserProfile, update: dict, now: datetime) -> UserProfile:
    """my_chat_member in the private chat: "kicked" means the user blocked the bot, "member" means back."""
    status = update.get("new_chat_member", {}).get("status")
    if status == "kicked":
        profile.notifications.blocked_at = now
        profile.notifications.can_message = False
    elif status == "member":
        profile.notifications.blocked_at = None
        profile.notifications.can_message = True
    return profile


def rgb(value: int) -> str:
    return f"#{value:06x}"


def personal_accent(profile: UserProfile, scheme: str, backdrops: dict[int, dict] | None = None) -> dict | None:
    """Colours for the user's own surfaces (profile card, membership card, share card), from what the user
    chose in Telegram, in order: the share-screen theme (a unique gift, or an emoji theme's backdrop), then the
    gift-based name colours. Returns None when the user chose nothing: the surface keeps the theme's colours.
    `backdrops` is getChatShareThemeBackdrops() as {id: colors}, cached by the caller."""
    theme = profile.share_theme or {}
    if theme.get("type") == "unique_gift":
        colors = (theme.get("gift") or {}).get("backdrop", {}).get("colors")
        if colors:
            return _backdrop(colors)
    if theme.get("type") == "emoji" and backdrops and theme.get("background_backdrop_id") in backdrops:
        return _backdrop(backdrops[theme["background_backdrop_id"]])
    gc = profile.unique_gift_colors
    if gc:
        main = gc["dark_theme_main_color" if scheme == "dark" else "light_theme_main_color"]
        others = gc["dark_theme_other_colors" if scheme == "dark" else "light_theme_other_colors"]
        return {"accent": rgb(main), "others": [rgb(c) for c in others]}
    return None


def _backdrop(c: dict) -> dict:
    return {"center": rgb(c["center_color"]), "edge": rgb(c["edge_color"]), "symbol": rgb(c["symbol_color"]),
            "text": rgb(c["text_color"])}


def can_send_voice(profile: UserProfile) -> bool:
    """False when the user's privacy settings restrict voice and video notes: send an audio file or text."""
    return not profile.restricts_voice_video


def display_handle(profile: UserProfile) -> str:
    """How to point at the user in text: @username when there is one (any active username works), else the
    first name. With has_private_forwards set, tg://user?id links work only in chats with the user."""
    name = profile.username or (profile.active_usernames[0] if profile.active_usernames else "")
    return f"@{name}" if name else profile.first_name


def needs_terms(profile: UserProfile, current_version: str) -> bool:
    return profile.terms_version != current_version
