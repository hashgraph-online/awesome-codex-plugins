"""Offline product models for R80–R87; no Telegram calls or external services.

These deliberately small, single-process models demonstrate product invariants.
Replace storage with transactions/unique constraints before using multiple workers.
Do not mistake an in-memory return value for CRM delivery, a payment or a file job.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar

from .flows import Machine, Scheduler


class Refused(ValueError):
    """Expected refusal with a stable code for localization."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise Refused(code)


@dataclass
class Lead:
    owner: int
    answers: dict[str, str] = field(default_factory=dict)
    consent: bool = False
    status: str = "draft"
    submission: dict | None = None

    def edit(self, actor: int, topic: str, contact: str) -> None:
        require(actor == self.owner, "not_yours")
        require(self.status == "draft", "closed")
        require(0 < len(topic.strip()) <= 200 and 0 < len(contact.strip()) <= 200, "invalid")
        self.answers = {"topic": topic.strip(), "contact": contact.strip()}
        self.consent = False  # edits invalidate consent to the previous preview

    def give_consent(self, actor: int) -> None:
        require(actor == self.owner, "not_yours")
        require(self.status == "draft", "closed")
        require(bool(self.answers), "invalid")
        self.consent = True

    def submit(self, actor: int) -> dict:
        require(actor == self.owner, "not_yours")
        if self.status == "submitted":
            return dict(self.submission)
        require(self.status == "draft", "closed")
        require(bool(self.answers) and self.consent, "consent_required")
        self.submission = dict(self.answers)
        self.status = "submitted"
        return dict(self.submission)

    def cancel(self, actor: int) -> None:
        require(actor == self.owner, "not_yours")
        require(self.status == "draft", "closed")
        self.answers.clear()
        self.consent = False
        self.status = "cancelled"


@dataclass
class Event:
    capacity: int
    attendees: list[int] = field(default_factory=list)
    waitlist: list[int] = field(default_factory=list)
    checked_in: set[int] = field(default_factory=set)

    def __post_init__(self) -> None:
        require(self.capacity > 0, "invalid")

    def join(self, actor: int) -> str:
        if actor in self.attendees:
            return "confirmed"
        if actor in self.waitlist:
            return "waitlisted"
        target = self.attendees if len(self.attendees) < self.capacity else self.waitlist
        target.append(actor)
        return "confirmed" if target is self.attendees else "waitlisted"

    def cancel(self, actor: int) -> int | None:
        require(actor not in self.checked_in, "closed")
        if actor in self.waitlist:
            self.waitlist.remove(actor)
        if actor not in self.attendees:
            return None
        self.attendees.remove(actor)
        if self.waitlist:
            promoted = self.waitlist.pop(0)
            self.attendees.append(promoted)
            return promoted
        return None

    def check_in(self, actor: int, attendee: int, staff: set[int]) -> bool:
        require(actor in staff, "forbidden")
        require(attendee in self.attendees, "not_confirmed")
        fresh = attendee not in self.checked_in
        self.checked_in.add(attendee)
        return fresh


@dataclass
class Reminder:
    owner: int
    key: str
    scheduler: Scheduler = field(default_factory=Scheduler)
    generation: int = 0
    status: str = "draft"
    due: datetime | None = None

    def schedule(self, actor: int, when: datetime, now: datetime) -> None:
        require(actor == self.owner, "not_yours")
        # A claimed reminder is being sent; a new time needs a new reminder record.
        require(self.status != "claimed", "closed")
        require(when.utcoffset() is not None and now.utcoffset() is not None, "timezone_required")
        require(when.timestamp() > now.timestamp(), "past")
        self.generation += 1
        self.scheduler.at(when.timestamp(), self.key, generation=self.generation)
        self.due = when
        self.status = "scheduled"

    def cancel(self, actor: int) -> None:
        require(actor == self.owner, "not_yours")
        require(self.status != "claimed", "closed")  # too late: the worker owns delivery
        self.generation += 1  # invalidates jobs already leased by a worker
        self.scheduler.jobs.pop(self.key, None)
        self.status = "cancelled"

    def claim(self, generation: int) -> bool:
        if generation != self.generation or self.status != "scheduled":
            return False
        self.status = "claimed"  # not "delivered": sending is a separate boundary
        return True


@dataclass
class FileJob:
    owner: int
    status: str = "waiting"
    file_id: str | None = None
    result: str | None = None
    generation: int = 0
    machine: ClassVar[Machine] = Machine({"waiting": {"upload": "queued"}, "queued": {"start": "running", "cancel": "cancelled"},
                       "running": {"finish": "ready", "fail": "failed", "cancel": "cancelled"}}, "waiting")

    def upload(self, actor: int, file_id: str, size: int, mime: str) -> None:
        require(actor == self.owner, "not_yours")
        # Product policy, NOT Telegram's upload/download limit. MIME is only a hint.
        require(bool(file_id) and 0 < size <= 5_000_000 and mime == "application/pdf", "invalid_file")
        require(self.status == "waiting", "closed")
        self.status = self.machine.next(self.status, "upload")
        self.file_id = file_id

    def start(self) -> int:
        self.status = self.machine.next(self.status, "start")
        self.generation += 1
        return self.generation

    def cancel(self, actor: int) -> None:
        require(actor == self.owner, "not_yours")
        if self.status == "cancelled":
            return
        require(self.status in {"queued", "running"}, "closed")
        self.status = self.machine.next(self.status, "cancel")
        self.generation += 1
        self.file_id = None

    def finish(self, generation: int, result: str) -> bool:
        if self.status != "running" or generation != self.generation:
            return False
        require(bool(result), "invalid")
        self.status = self.machine.next(self.status, "finish")
        self.result = result
        self.file_id = None
        return True

    def fail(self, generation: int) -> bool:
        if self.status != "running" or generation != self.generation:
            return False
        self.status = self.machine.next(self.status, "fail")
        self.file_id = None
        return True


@dataclass
class Moderation:
    chat_id: int
    message_id: int
    status: str = "pending"
    revision: int = 0
    decision: dict | None = None

    def add_report(self) -> int:
        """A new report or edit changes the case; open review screens become stale."""
        require(self.status == "pending", "closed")
        self.revision += 1
        return self.revision

    def decide(self, actor: int, staff: set[int], chat_id: int, revision: int, action: str) -> dict:
        require(actor in staff and chat_id == self.chat_id, "forbidden")
        require(self.status == "pending" and revision == self.revision, "stale")
        require(action in {"dismiss", "remove"}, "invalid")
        # Plan only. A transport timeout must become unknown, not an automatic retry.
        self.decision = {"actor": actor, "action": action, "chat_id": self.chat_id,
                         "message_id": self.message_id}
        self.status = "planned"
        self.revision += 1
        return dict(self.decision)


@dataclass
class Survey:
    owner: int
    answers: dict[str, str] = field(default_factory=dict)
    status: str = "draft"

    def answer(self, actor: int, question: str, value: str) -> None:
        require(actor == self.owner, "not_yours")
        require(self.status == "draft", "closed")
        require(question in {"rating", "comment"}, "invalid")
        require((question == "rating" and value in {"1", "2", "3", "4", "5"}) or
                (question == "comment" and len(value) <= 500), "invalid")
        self.answers[question] = value

    def submit(self, actor: int) -> dict:
        require(actor == self.owner, "not_yours")
        require(self.status in {"draft", "submitted"}, "closed")
        require("rating" in self.answers, "incomplete")
        self.status = "submitted"
        return dict(self.answers)

    def withdraw(self, actor: int) -> None:
        require(actor == self.owner, "not_yours")
        self.answers.clear()
        self.status = "withdrawn"


@dataclass
class Loyalty:
    owner: int
    balance: int = 0
    credits: dict[str, int] = field(default_factory=dict)
    redemptions: dict[str, int] = field(default_factory=dict)

    def credit(self, receipt: str, points: int) -> bool:
        """Trusted settled-order event only; never route this method to user input."""
        require(bool(receipt) and type(points) is int and points > 0, "invalid")
        if receipt in self.credits:
            require(self.credits[receipt] == points, "conflict")
            return False
        self.credits[receipt] = points
        self.balance += points
        return True

    def redeem(self, actor: int, request: str, cost: int) -> bool:
        require(actor == self.owner, "not_yours")
        require(bool(request) and type(cost) is int and cost > 0, "invalid")
        if request in self.redemptions:
            require(self.redemptions[request] == cost, "conflict")
            return False
        require(self.balance >= cost, "insufficient")
        self.redemptions[request] = cost
        self.balance -= cost
        return True


@dataclass
class ServiceQueue:
    waiting: list[int] = field(default_factory=list)
    active: int | None = None
    closed: bool = False

    def join(self, actor: int) -> int:
        require(not self.closed, "closed")
        if actor == self.active:
            return 0
        if actor not in self.waiting:
            self.waiting.append(actor)
        return self.waiting.index(actor) + 1

    def cancel(self, actor: int) -> None:
        require(actor != self.active, "already_called")
        if actor in self.waiting:
            self.waiting.remove(actor)

    def call_next(self, actor: int, staff: set[int]) -> int | None:
        require(actor in staff, "forbidden")
        if self.active is not None:
            return self.active
        if self.waiting:
            self.active = self.waiting.pop(0)
        return self.active

    def complete(self, actor: int, staff: set[int], expected: int) -> None:
        require(actor in staff, "forbidden")
        require(self.active is not None and self.active == expected, "stale")
        self.active = None
