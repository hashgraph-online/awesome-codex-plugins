"""R33 - Poll and quiz posts in a channel.

Quiz with an explanation, voting limited to channel members (members_only) and
to some countries (country_codes) - both channel-only since Bot API 10.0; a
regular poll that closes itself (close_date). Polls are refused for channel
direct-messages chats, a sent poll can't be edited (only stopped).

Run:  py -3 examples/python/recipes/r33_poll_quiz_post.py
"""
from __future__ import annotations

import _common as c
from tgkit.errors import call_with_policy
from tgkit.publish import Post, Publisher, validate
from tgkit.transport import FakeTransport

CHANNEL = -1001500000001
NOW = 1_763_200_000


def quiz() -> Post:
    return Post(poll={
        "question": "Which district fixed potholes fastest in Q3?",
        "options": ["Old Town", "Riverside", "Harbour", "Northgate"],
        "type": "quiz", "correct_option_ids": [1],
        "explanation": "Riverside: median 3.1 days. Full table in the pinned long read.",
        "members_only": True, "country_codes": ["UA", "PL", "FT"],
        "open_period": 86400,
        "description": "Answer before the long read comes out tomorrow.",
    })


def survey() -> Post:
    return Post(poll={
        "question": "What should the next issue cover?",
        "options": ["Bike lanes", "Night buses", "Parks", "Street lighting"],
        "allows_multiple_answers": True, "close_date": NOW + 3 * 86400,
    }, silent=True)


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport()
    pub = Publisher(t, sleep=lambda s: None, clock=lambda: float(NOW))
    r1 = pub.publish(quiz(), CHANNEL, "poll:quiz:q3")
    r2 = pub.publish(survey(), CHANNEL, "poll:survey:next")
    # Close the survey early: stopPoll is the only change a sent poll accepts.
    call_with_policy(t, "stopPoll", {"chat_id": CHANNEL, "message_id": r2.message_ids[0]})
    edit = pub.edit("poll:survey:next", survey().with_changes(poll={**survey().poll, "question": "Next topic?"}))
    return t, r1, r2, edit


def main() -> None:
    t, r1, r2, edit = run()
    c.dump(t, "Poll and quiz posts")
    q, s = t.params_of("sendPoll")
    c.check(q["type"] == "quiz" and q["correct_option_ids"] == [1] and q["options"][1] == {"text": "Riverside"},
            "quiz: InputPollOption objects, increasing correct_option_ids")
    c.check(q["members_only"] is True and q["country_codes"] == ["UA", "PL", "FT"],
            "members_only + country_codes ('FT' = anonymous numbers), channel chats only")
    c.check(s["allows_multiple_answers"] is True and s["close_date"] == NOW + 3 * 86400 and
            s["disable_notification"] is True, "survey: multiple answers, closes itself, silent")
    c.check(t.methods()[-1] == "stopPoll" and edit.status == "repost_required",
            "a sent poll is stopped, never edited")
    issues = {i.code for i in validate(quiz(), context="channel_dm")}
    c.check({"poll_context", "poll_channel_only"} <= issues, "refused for a channel DM chat")
    bad = quiz().with_changes(poll={**quiz().poll, "correct_option_ids": [7], "explanation": "a\nb\nc\nd"})
    codes = {i.code for i in validate(bad)}
    c.check({"poll_quiz", "poll_explanation"} <= codes, "invalid answer id and a 3-line-feed explanation refused")
    both = survey().with_changes(poll={**survey().poll, "open_period": 600})
    c.check(any(i.code == "poll_period" for i in validate(both)), "open_period and close_date are exclusive")
    c.check(r1.status == r2.status == "sent", "both polls sent once")


if __name__ == "__main__":
    main()
