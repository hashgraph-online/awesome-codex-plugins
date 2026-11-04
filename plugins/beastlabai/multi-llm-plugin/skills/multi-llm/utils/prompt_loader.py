"""Prompt loader utility for loading prompt templates."""

from functools import lru_cache
from pathlib import Path

# Skill directory is the parent of utils/
SKILL_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = SKILL_DIR / "prompts"


@lru_cache(maxsize=32)
def load_prompt(prompt_name: str) -> str:
    """
    Load a prompt template from the skill's prompts directory.

    Args:
        prompt_name: Prompt filename (e.g., "code_review.txt")

    Returns:
        Prompt template content as string

    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    full_path = PROMPTS_DIR / prompt_name

    if not full_path.exists():
        raise FileNotFoundError(f"Prompt not found: {full_path}")

    return full_path.read_text(encoding="utf-8")


def clear_cache() -> None:
    """Clear the prompt cache (useful for testing)."""
    load_prompt.cache_clear()
