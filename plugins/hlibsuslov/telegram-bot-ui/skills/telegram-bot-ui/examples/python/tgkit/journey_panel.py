"""Small private-chat adapter reused by the R80–R87 product demonstrations.

Uses the existing ScreenFlow, I18n, button builders and FakeTransport contract.
`actions` are server-owned closures, never commands supplied in callback_data.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .flows import I18n, ScreenFlow, btn, kb
from .journeys import Refused

COPY = {
    "en": {"screen": "<b>{title}</b>\n{body}", "refused": "The action could not be completed: {reason}.",
           "sys_stale": "This screen changed. Use the latest buttons.",
           "sys_not_yours": "Open your own menu with /start.", "sys_expired": "Send /start to reopen this menu."},
    "ru": {"screen": "<b>{title}</b>\n{body}", "refused": "Не удалось выполнить действие: {reason}.",
           "sys_stale": "Экран изменился. Используйте новые кнопки.",
           "sys_not_yours": "Откройте своё меню через /start.", "sys_expired": "Откройте меню снова через /start."},
}
REASONS = {
    "not_yours": ("this belongs to another user", "это данные другого пользователя"),
    "closed": ("this operation is closed", "операция завершена"),
    "invalid": ("check the entered values", "проверьте введённые данные"),
    "consent_required": ("review the details and give consent", "проверьте данные и подтвердите согласие"),
    "timezone_required": ("choose a time zone", "выберите часовой пояс"),
    "past": ("choose a future time", "выберите время в будущем"),
    "invalid_file": ("use a PDF up to 5 MB", "используйте PDF размером до 5 МБ"),
    "forbidden": ("staff access is required", "нужны права сотрудника"),
    "stale": ("the state changed; reopen the screen", "состояние изменилось, откройте экран снова"),
    "not_confirmed": ("registration is not confirmed", "регистрация не подтверждена"),
    "incomplete": ("answer the required question", "ответьте на обязательный вопрос"),
    "conflict": ("the request changed; contact support", "запрос изменился, обратитесь в поддержку"),
    "insufficient": ("not enough points", "недостаточно баллов"),
    "already_called": ("you have been called; contact staff", "вас уже вызвали, обратитесь к сотруднику"),
}


@dataclass
class Action:
    label: tuple[str, str]
    run: Callable[[], object]
    enabled: Callable[[], bool] = lambda: True


class JourneyPanel:
    def __init__(self, transport, app: str, owner: int, title: tuple[str, str],
                 body: Callable[[str], str], actions: dict[str, Action], lang: str = "en"):
        self.flow = ScreenFlow(transport, app, i18n=I18n(COPY))
        self.session = self.flow.session(owner, owner, lang=self.flow.i18n.lang_for(lang))
        self.notice = ""
        self.actions = actions

        @self.flow.screen("main")
        def render(flow, session):
            index = int(session.lang == "ru")
            rows = []
            for key, action in actions.items():
                # Omit actions that are not available. Reasons belong in the body.
                if action.enabled():
                    rows.append([btn(action.label[index], flow.cb(session, key))])
            if not rows:
                rows.append([btn(("Show status", "Показать статус")[index], flow.cb(session, "status"))])
            # A refusal is shown once; the next render reflects only the current state.
            notice, self.notice = self.notice, ""
            return {"text": flow.tr(session, "screen", title=title[index],
                                     body=body(session.lang) + notice), "reply_markup": kb(*rows)}

        for key in actions:
            self.flow.action(key)(self._handler(key))

        @self.flow.action("status")
        def status(flow, session, args, query):
            flow.answer(query)
            flow.refresh(session)

    def _handler(self, key):
        def handle(flow, session, args, query):
            flow.answer(query)  # spinner ends before any domain work or edit
            action = self.actions[key]
            try:
                if args or not action.enabled():
                    raise Refused("stale")
                action.run()
            except Refused as error:
                reason = REASONS.get(str(error), REASONS["invalid"])[int(session.lang == "ru")]
                # The entire body is escaped by render(); no nested HTML escaping.
                self.notice = "\n" + COPY[session.lang]["refused"].format(reason=reason)
            flow.refresh(session)
        return handle

    def open(self):
        return self.flow.open(self.session, "main")
