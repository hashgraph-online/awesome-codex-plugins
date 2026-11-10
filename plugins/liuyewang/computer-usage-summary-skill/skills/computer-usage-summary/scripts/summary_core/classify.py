"""Explainable, local-only activity classification."""

from .models import BROWSER_APP_PATTERN

CATEGORY_ORDER = (
    "development",
    "communication",
    "research",
    "email",
    "creative",
    "system",
    "other",
)


def _contains(text, terms):
    return any(term in text for term in terms)


def classify_activity(app, title):
    """Classify sanitized foreground evidence without guessing intent."""
    app_text = (app or "").casefold()
    title_text = (title or "").casefold()
    combined = f"{app_text} {title_text}"

    if _contains(
        app_text,
        ("code", "cursor", "xcode", "pycharm", "intellij", "terminal", "iterm", "warp", "git"),
    ):
        return {"category": "development", "confidence": "confirmed"}
    if _contains(
        app_text,
        ("微信", "wechat", "telegram", "whatsapp", "slack", "teams", "discord", "飞书", "lark", "messenger"),
    ):
        return {"category": "communication", "confidence": "confirmed"}
    if _contains(app_text, ("mail", "outlook", "gmail", "thunderbird", "邮箱")):
        return {"category": "email", "confidence": "confirmed"}
    if _contains(app_text, ("preview", "预览", "figma", "sketch", "photoshop", "illustrator", "keynote")):
        return {"category": "creative", "confidence": "confirmed"}
    if _contains(app_text, ("finder", "访达", "setting", "系统设置", "loginwindow", "clash")):
        return {"category": "system", "confidence": "confirmed"}

    if BROWSER_APP_PATTERN.search(app or ""):
        if title_text in ("", "(untitled)", "新标签页", "new tab", "[url omitted]"):
            return {"category": "other", "confidence": "unknown context"}
        if _contains(
            combined,
            ("github", "documentation", "docs", "stackoverflow", "search", "research", "youtube", "论文"),
        ):
            return {"category": "research", "confidence": "confirmed"}
        return {"category": "research", "confidence": "unknown context"}

    if _contains(combined, ("github", "documentation", "docs", "论文", "research")):
        return {"category": "research", "confidence": "unknown context"}
    return {"category": "other", "confidence": "unknown context"}


def choose_main_focus(category_totals):
    candidates = [
        (category, seconds)
        for category, seconds in category_totals.items()
        if seconds > 0
    ]
    if not candidates:
        return "unknown context"
    order = {category: index for index, category in enumerate(CATEGORY_ORDER)}
    return max(candidates, key=lambda item: (item[1], -order.get(item[0], len(order))))[0]
