"""Bridge to the rest of the telegram-bot-ui skill (validators, widget builder, tgkit) and to
the optional Studio web client.

This package lives inside the skill (`scripts/bot_ui/`), so the skill root is two levels up.
The web client lives only in a clone or a plugin install of the repository (`studio/web`).
BOT_UI_SKILL_DIR and BOT_UI_STUDIO_DIR override either location.
"""
from __future__ import annotations

import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SKILL = os.path.normpath(os.path.join(HERE, "..", ".."))
# skills/telegram-bot-ui/scripts/bot_ui -> repository root -> studio
DEFAULT_STUDIO = os.path.normpath(os.path.join(DEFAULT_SKILL, "..", "..", "studio"))


def skill_dir() -> str:
    path = os.environ.get("BOT_UI_SKILL_DIR") or DEFAULT_SKILL
    if not os.path.isfile(os.path.join(path, "SKILL.md")):
        raise RuntimeError(f"telegram-bot-ui skill not found at {path}; set BOT_UI_SKILL_DIR")
    return path


def studio_dir() -> str:
    """Folder that holds `web/` (the Studio client); may not exist in a skill-only install."""
    return os.environ.get("BOT_UI_STUDIO_DIR") or DEFAULT_STUDIO


def web_dir(*parts: str) -> str:
    return os.path.join(studio_dir(), "web", *parts)


def _is_git(folder: str) -> bool:
    """A real repository marker: a .git folder with HEAD, or a .git file pointing elsewhere (worktrees,
    submodules). An empty `.git` stub (one in a home folder, say) does not make the folder a repository."""
    dot = os.path.join(folder, ".git")
    if os.path.isdir(dot):
        return os.path.isfile(os.path.join(dot, "HEAD"))
    if os.path.isfile(dot):
        try:
            with open(dot, encoding="utf-8", errors="replace") as fh:
                return fh.read(200).startswith("gitdir:")
        except OSError:
            return False
    return False


def project_repo(project_root: str) -> str:
    """The repository holding a bot-ui folder: the nearest parent that is a git repository, else the
    folder's parent."""
    start = os.path.dirname(os.path.realpath(project_root))
    cur = start
    while not _is_git(cur):
        parent = os.path.dirname(cur)
        if parent == cur:
            return start
        cur = parent
    return cur


def trusted_web_dir(project_root: str, *parts: str) -> str | None:
    """studio/web/<parts>, or None when that folder lies inside the repository being opened.

    A bot repository can carry its own `web/dist/index.html` (a project-scope install puts the default
    folder at <repo>/.claude/studio), and the Studio hands the page it serves a token for its whole API.
    Naming the Studio folder in BOT_UI_STUDIO_DIR is the operator's own choice and always accepted."""
    path = web_dir(*parts)
    if os.environ.get("BOT_UI_STUDIO_DIR"):
        return path
    repo, real = os.path.normcase(project_repo(project_root)), os.path.normcase(os.path.realpath(path))
    return None if real == repo or real.startswith(repo.rstrip(os.sep) + os.sep) else path


def _ensure_path() -> None:
    root = skill_dir()
    for sub in ("scripts", os.path.join("examples", "python")):
        p = os.path.join(root, sub)
        if p not in sys.path:
            sys.path.insert(0, p)


def load(name: str):
    """Import a skill module by name: 'validate_keyboard', 'build_widget', 'tgkit.transport', ..."""
    _ensure_path()
    return importlib.import_module(name)


def kit_dir() -> str:
    return os.path.join(skill_dir(), "examples", "widgets", "_kit")
