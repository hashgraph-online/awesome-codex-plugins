"""Eight product journeys, offline only. Run all, or --scenario R81 --lang ru.

--write-payload exports deterministic EN wire transcripts to examples/payloads/.
No CRM, payment, file processing, scheduling daemon or Telegram server is called.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

import _common as c
from tgkit.flows import callback, payload_doc, user, write_payload
from tgkit.journey_panel import Action, JourneyPanel
from tgkit.journeys import Event, FileJob, Lead, Loyalty, Moderation, Reminder, ServiceQueue, Survey
from tgkit.transport import FakeTransport

OWNER, OTHER, STAFF = 101, 202, 303


def choose(lang, en, ru):
    return ru if lang == "ru" else en


def state_label(state, lang):
    labels = {
        "draft": ("draft", "черновик"), "submitted": ("accepted locally", "принято локально"),
        "cancelled": ("cancelled", "отменено"), "scheduled": ("scheduled", "запланировано"),
        "claimed": ("claimed by worker", "взято в работу"), "waiting": ("waiting for a file", "ожидание файла"),
        "queued": ("queued", "в очереди"), "running": ("processing", "обработка"),
        "ready": ("ready", "готово"), "failed": ("failed", "ошибка"),
        "pending": ("awaiting review", "ожидает проверки"), "planned": ("decision recorded", "решение сохранено"),
        "withdrawn": ("withdrawn", "ответ удалён"),
    }
    return labels[state][int(lang == "ru")]


def build(scenario: str, lang="en"):
    transport = FakeTransport()
    started = []  # R83: generations leased by the simulated worker
    if scenario == "R80":
        model = Lead(OWNER)
        title = ("Request a quote", "Запросить расчёт")
        def body(lang):
            details = model.submission or model.answers
            review = (choose(lang, "Review: {topic}. Contact: {contact}.\n", "Проверьте: {topic}. Контакт: {contact}.\n").format(**details)
                      if details else choose(lang, "No details yet.\n", "Данные ещё не заполнены.\n"))
            consent = choose(lang, "yes", "да") if model.consent else choose(lang, "no", "нет")
            return review + choose(lang, f"Consent: {consent}. Request: {state_label(model.status, lang)}.",
                                   f"Согласие: {consent}. Заявка: {state_label(model.status, lang)}.")
        def fill():
            model.edit(OWNER, "Website consultation", "demo@example.invalid")
        actions = {"review": Action(("Use sample details", "Заполнить пример"), fill, lambda: model.status == "draft"),
                   "consent": Action(("Allow contact about this request", "Согласен на связь по заявке"), lambda: model.give_consent(OWNER), lambda: bool(model.answers) and model.status == "draft" and not model.consent),
                   "submit": Action(("Submit request", "Отправить заявку"), lambda: model.submit(OWNER), lambda: model.status == "draft"),
                   "cancel": Action(("Discard draft", "Удалить черновик"), lambda: model.cancel(OWNER), lambda: model.status == "draft")}
        taps = ["submit", "review", "consent", "submit"]
    elif scenario == "R81":
        model = Event(1)
        model.join(OTHER)
        title = ("Workshop · one seat", "Мастер-класс · одно место")
        def body(lang):
            state = ("checked in", "отмечен на входе") if OWNER in model.checked_in else ("confirmed", "подтверждено") if OWNER in model.attendees else (("waitlisted", "лист ожидания") if OWNER in model.waitlist else ("not registered", "нет регистрации"))
            return choose(lang, f"Your registration: {state[0]}. No payment is taken.", f"Ваша регистрация: {state[1]}. Оплата не взимается.")
        def registered():
            return OWNER in model.attendees or OWNER in model.waitlist
        actions = {"join": Action(("Join / waitlist", "Записаться / лист ожидания"), lambda: model.join(OWNER), lambda: not registered()),
                   "cancel": Action(("Cancel registration", "Отменить регистрацию"), lambda: model.cancel(OWNER), lambda: registered() and OWNER not in model.checked_in)}
        taps = ["join", "cancel", "join"]
    elif scenario == "R82":
        model = Reminder(OWNER, "reminder:101:1")
        now = datetime(2026, 11, 15, 9, tzinfo=timezone.utc)
        title = ("Reminder", "Напоминание")
        def body(lang):
            when = model.due.strftime("%H:%M UTC") if model.due and model.status == "scheduled" else choose(lang, "not set", "не задано")
            return choose(lang, f"Date: 15 Nov 2026. Time: {when}. State: {state_label(model.status, lang)}.\nConfirm your time zone before creating a real reminder.", f"Дата: 15 ноября 2026. Время: {when}. Состояние: {state_label(model.status, lang)}.\nПеред созданием выберите часовой пояс.")
        actions = {"save": Action(("Schedule for 10:00 UTC", "Запланировать на 10:00 UTC"), lambda: model.schedule(OWNER, now + timedelta(hours=1), now), lambda: model.status in {"draft", "cancelled"}),
                   "snooze": Action(("Move to 11:00 UTC", "Перенести на 11:00 UTC"), lambda: model.schedule(OWNER, now + timedelta(hours=2), now), lambda: model.status == "scheduled"),
                   "cancel": Action(("Cancel reminder", "Отменить напоминание"), lambda: model.cancel(OWNER), lambda: model.status == "scheduled")}
        taps = ["save", "snooze", "cancel"]
    elif scenario == "R83":
        model = FileJob(OWNER)
        title = ("PDF summary", "Краткое содержание PDF")
        def body(lang):
            return choose(lang, f"PDF up to 5 MB (sample policy). Job: {state_label(model.status, lang)}.\nCancel stops delivery of late results.", f"PDF до 5 МБ (лимит примера). Задача: {state_label(model.status, lang)}.\nПосле отмены поздний результат не отправляется.")
        def upload():
            model.upload(OWNER, "sample_pdf_id", 1200, "application/pdf")
            started.append(model.start())  # a worker leases the job right away
        actions = {"upload": Action(("Use sample PDF", "Использовать пример PDF"), upload, lambda: model.status == "waiting"),
                   "cancel": Action(("Cancel processing", "Отменить обработку"), lambda: model.cancel(OWNER), lambda: model.status in {"queued", "running"})}
        taps = ["upload", "cancel"]
    elif scenario == "R84":
        model = Moderation(-100123, 17)
        model.add_report()  # a second report arrives before review
        title = ("Review reported message", "Проверить жалобу")
        shown = [model.revision]  # the revision the moderator actually saw
        def body(lang):
            shown[0] = model.revision
            return choose(lang, f"Case 17 · group -100123. State: {state_label(model.status, lang)}.\nThis demo records a decision; it does not delete messages.", f"Жалоба 17 · группа -100123. Состояние: {state_label(model.status, lang)}.\nПример сохраняет решение, не удаляя сообщения.")
        # Decide against the rendered revision, not the live one: a report that
        # arrives after the screen was drawn must make this tap stale.
        actions = {"dismiss": Action(("Dismiss report", "Отклонить жалобу"), lambda: model.decide(OWNER, {OWNER}, -100123, shown[0], "dismiss"), lambda: model.status == "pending")}
        taps = ["dismiss"]
    elif scenario == "R85":
        model = Survey(OWNER)
        title = ("Service feedback", "Отзыв об обслуживании")
        def body(lang):
            return choose(lang, f"Rating: {model.answers.get('rating', 'not selected')}. Comment is optional. State: {state_label(model.status, lang)}.\nThis response is linked to your account, not anonymous.", f"Оценка: {model.answers.get('rating', 'не выбрана')}. Комментарий необязателен. Состояние: {state_label(model.status, lang)}.\nОтвет привязан к аккаунту, он не анонимный.")
        actions = {"rate": Action(("Rate 5 / 5", "Поставить 5 / 5"), lambda: model.answer(OWNER, "rating", "5"), lambda: model.status == "draft"),
                   "submit": Action(("Submit without comment", "Отправить без комментария"), lambda: model.submit(OWNER), lambda: model.status == "draft"),
                   "withdraw": Action(("Withdraw response", "Удалить ответ"), lambda: model.withdraw(OWNER), lambda: model.status == "submitted")}
        taps = ["submit", "rate", "submit", "withdraw"]
    elif scenario == "R86":
        model = Loyalty(OWNER)
        model.credit("settled-order-1", 100)
        title = ("Your reward points", "Ваши бонусные баллы")
        def body(lang):
            return choose(lang, f"Balance: {model.balance} points. Reward costs 80.\nPoints are a demo ledger, not money or Telegram Stars.", f"Баланс: {model.balance} баллов. Награда стоит 80.\nЭто учебный учёт баллов, не деньги и не Telegram Stars.")
        actions = {"redeem": Action(("Redeem 80 points", "Потратить 80 баллов"), lambda: model.redeem(OWNER, "reward-1", 80), lambda: model.balance >= 80)}
        taps = ["redeem"]
    elif scenario == "R87":
        model = ServiceQueue()
        model.join(OTHER)
        title = ("Service desk queue", "Очередь к специалисту")
        def body(lang):
            if model.active == OWNER:
                return choose(lang, "It is your turn. Please go to the desk.", "Ваша очередь. Подойдите к специалисту.")
            position = model.waiting.index(OWNER) + 1 if OWNER in model.waiting else "—"
            return choose(lang, f"Your position: {position}.\nPosition is not an estimated waiting time.", f"Ваше место: {position}.\nНомер в очереди не означает время ожидания.")
        actions = {"join": Action(("Take a ticket", "Встать в очередь"), lambda: model.join(OWNER), lambda: OWNER not in model.waiting and model.active != OWNER),
                   "cancel": Action(("Leave queue", "Выйти из очереди"), lambda: model.cancel(OWNER), lambda: OWNER in model.waiting)}
        taps = ["join", "cancel", "join"]
    else:
        raise ValueError(f"unknown scenario {scenario}")
    panel = JourneyPanel(transport, scenario.lower(), OWNER, title, body, actions, lang)
    panel.open()
    panel.started = started
    return model, panel, transport, taps


def tap(panel, key, query_id, actor=OWNER, data=None):
    s = panel.session
    return panel.flow.handle(callback(query_id, user(actor, lang=s.lang),
                                     data or panel.flow.cb(s, key), chat_id=s.chat_id, message_id=s.message_id))


def check(condition, what):
    # Not `assert`: python -O would strip it while the summary still says "checked".
    if not condition:
        raise AssertionError(f"guard failed: {what}")


def run(scenario, lang="en"):
    model, panel, transport, taps = build(scenario, lang)
    first = panel.flow.cb(panel.session, taps[0])
    check(tap(panel, taps[0], "foreign-user", OTHER) == "not_yours", "foreign user refused")
    for index, key in enumerate(taps):
        check(tap(panel, key, f"tap-{index}") == "ok", f"tap {key}")
    check(tap(panel, taps[0], "old-screen", data=first) == "stale", "old screen refused")
    if scenario == "R80":
        check(model.status == "submitted" and model.submit(OWNER) == model.submission, "stable submission")
    elif scenario == "R81":
        check(model.cancel(OTHER) == OWNER and model.check_in(STAFF, OWNER, {STAFF}), "promotion and check-in")
        panel.flow.refresh(panel.session)
    elif scenario == "R82":
        check(model.status == "cancelled" and not model.scheduler.jobs, "cancel removes the job")
    elif scenario == "R83":
        check(not model.finish(panel.started[0], "late result") and model.result is None, "late result dropped")
    elif scenario == "R84":
        check(model.status == "planned" and model.decision["action"] == "dismiss", "decision recorded")
    elif scenario == "R85":
        check(model.status == "withdrawn" and not model.answers, "withdrawal clears answers")
    elif scenario == "R86":
        check(model.balance == 20 and not model.redeem(OWNER, "reward-1", 80), "redeem once")
    elif scenario == "R87":
        check(model.call_next(STAFF, {STAFF}) == OTHER, "FIFO")
        model.complete(STAFF, {STAFF}, OTHER)
        check(model.call_next(STAFF, {STAFF}) == OWNER, "next customer")
        panel.flow.refresh(panel.session)
    return payload_doc(scenario.lower() + "-journey", transport, status="offline-model", context="private")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=[f"R{i}" for i in range(80, 88)])
    parser.add_argument("--lang", choices=["en", "ru"], default="en")
    parser.add_argument("--write-payload", action="store_true")
    args = parser.parse_args(argv)
    if args.write_payload and args.lang != "en":
        parser.error("checked-in transcripts use --lang en")
    for scenario in ([args.scenario] if args.scenario else [f"R{i}" for i in range(80, 88)]):
        doc = run(scenario, args.lang)
        if args.write_payload:
            write_payload(doc)
        print(f"{scenario}: {len(doc['steps'])} offline calls; guards and outcome checked")


if __name__ == "__main__":
    main()
