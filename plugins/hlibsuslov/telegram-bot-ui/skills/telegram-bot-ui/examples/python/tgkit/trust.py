"""Trust signals for anti-abuse decisions about a Telegram user. Rules: references/user-trust.md.

Standard library only, no network. The caller fetches signals (its own records, the Bot API, an optional
blocklist it disclosed in its privacy policy) and passes them in; this module only weighs them.

Design:
- a signal adds friction, never a verdict on its own: the result is a tier (trusted / normal / watch /
  restricted) with the reasons, and only "restricted" limits anything;
- a blocklist hit or the bot's own confirmed reports can restrict; account age, a missing username or a
  missing photo can at most move a user to "watch" (extra checks), because many honest people have them;
- every result carries the reasons in plain words, for the moderator and for the user's appeal.
"""
from __future__ import annotations

import bisect
from dataclasses import dataclass, field
from datetime import date

TIERS = ("trusted", "normal", "watch", "restricted")


@dataclass(frozen=True)
class AgeAnchor:
    """A known point about one account id.

    kind="created": the account was registered on `day` (accounts your team registered, with the date).
    kind="seen": the account already existed on `day` (the first time your bot saw it): an upper bound only.
    Build anchors from your own records, never from guesses or scraped tables."""
    user_id: int
    day: date
    kind: str = "seen"


class IdAgeEstimator:
    """A coarse creation bracket for an id, from your own anchors.

    Telegram does not publish creation dates. Ids grow over time on average but are handed out in blocks,
    so neighbours in time can be millions apart and the order is not strict. The bracket is therefore an
    assumption, not a fact:
    - created after the "created" anchor with the largest id below it (a lower bound);
    - created on or before the earliest day of any anchor with an id at or above it (an upper bound).
    Either side is None when no anchor supports it. Only a lower bound can say an account is new.
    """

    def __init__(self, anchors: list[AgeAnchor]):
        pts = sorted(anchors, key=lambda a: a.user_id)
        self._created = [(a.user_id, a.day) for a in pts if a.kind == "created"]
        ids: list[int] = []
        days: list[date] = []
        best: date | None = None
        for a in reversed(pts):  # earliest day at or above each id
            best = a.day if best is None or a.day < best else best
            ids.append(a.user_id)
            days.append(best)
        self._ids, self._upper = ids[::-1], days[::-1]

    def bracket(self, user_id: int) -> tuple[date | None, date | None]:
        lower = None
        for uid, day in self._created:
            if uid < user_id and (lower is None or day > lower):
                lower = day
        i = bisect.bisect_left(self._ids, user_id)
        upper = self._upper[i] if i < len(self._ids) else None
        return lower, upper


@dataclass
class Signals:
    """Inputs the caller already has. None means unknown; unknown never counts against the user."""
    first_seen_by_bot: date | None = None       # your own records
    created_after: date | None = None           # IdAgeEstimator.bracket()[0], coarse; None = unknown
    has_username: bool | None = None            # User.username
    has_photo: bool | None = None               # getUserProfilePhotos total_count > 0
    is_premium: bool | None = None              # User.is_premium
    stars_rating_level: int | None = None       # ChatFullInfo.rating.level
    completed_orders: int = 0                   # your own records: paid and not disputed
    confirmed_reports: int = 0                  # reports your moderators upheld
    blocklist_hit: bool | None = None           # an external list you disclosed (e.g. CAS), with the date checked
    manual_allow: bool = False                  # a moderator cleared the user (an appeal won)


@dataclass
class Assessment:
    tier: str
    reasons: list[str] = field(default_factory=list)


def assess(s: Signals, today: date, new_days: int = 30) -> Assessment:
    """Weighs the signals into a tier. Thresholds are defaults to tune per bot (user-trust.md section 4)."""
    if s.manual_allow:
        return Assessment("trusted", ["cleared by a moderator"])
    reasons: list[str] = []
    if s.blocklist_hit:
        reasons.append("listed in the anti-spam blocklist")
    if s.confirmed_reports >= 2:
        reasons.append(f"{s.confirmed_reports} reports upheld by moderators")
    if reasons:
        return Assessment("restricted", reasons)

    good = 0
    if s.completed_orders >= 3:
        good += 2
        reasons.append(f"{s.completed_orders} completed orders")
    if s.stars_rating_level is not None and s.stars_rating_level >= 3:
        good += 1
        reasons.append(f"Stars rating level {s.stars_rating_level}")
    if s.first_seen_by_bot and (today - s.first_seen_by_bot).days >= 180:
        good += 1
        reasons.append("known to the bot for 6 months or more")
    if good >= 2:
        return Assessment("trusted", reasons)

    watch: list[str] = []
    if s.confirmed_reports == 1:
        watch.append("1 report upheld by moderators")
    if s.created_after and (today - s.created_after).days < new_days:
        watch.append(f"account probably created in the last {new_days} days (estimate from the id)")
    thin = [n for n, v in (("no username", s.has_username), ("no profile photo", s.has_photo)) if v is False]
    if len(thin) == 2 and watch:
        watch.extend(thin)  # thin profiles only add weight to another signal, never on their own
    if watch:
        return Assessment("watch", watch)
    return Assessment("normal", reasons or ["no signal either way"])
