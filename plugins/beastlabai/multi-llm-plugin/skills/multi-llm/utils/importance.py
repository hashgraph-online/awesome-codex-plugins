"""The one owner of importance: its spelling, its order and its score table.

Reviewers answer in lower case (the enum in ``schemas/review_suggestions.schema.json``
and ``schemas/code_review_issues.schema.json``), and artifacts written before this
module owned the value carry either case: the plan lane wrote upper case, the code
lane lower case. Every reader folds a value through :func:`normalize` (or one of the
helpers built on it), so both spellings read the same; the plugin writes the
canonical spelling, :data:`LEVELS`. See ``docs/development/review-results.md``
(Importance levels).
"""

from typing import Any, Dict, Iterable, List, Optional, Tuple

#: The canonical spelling, most important first.
LEVELS: Tuple[str, ...] = ("HIGH", "MEDIUM", "LOW")

#: The same order as a list (the name older callers import).
IMPORTANCE_ORDER: List[str] = list(LEVELS)

#: The spelling reviewers are asked to answer in: the schemas' enum, in order.
MODEL_VALUES: Tuple[str, ...] = tuple(level.lower() for level in LEVELS)

#: What a missing or unrecognised value means unless a caller says otherwise.
DEFAULT = "MEDIUM"

#: Sort key: 0 is the most important. A value that names no level sorts after LOW.
RANK: Dict[str, int] = {level: position for position, level in enumerate(LEVELS)}
UNKNOWN_RANK = len(LEVELS)

#: The one score table: what a level adds to a priority score.
WEIGHT: Dict[str, int] = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}


def canonical(value: Any) -> Optional[str]:
    """The level *value* names, in canonical spelling, or ``None`` if it names none.

    Case and surrounding whitespace are ignored; a non-string names nothing.
    """
    if not isinstance(value, str):
        return None
    folded = value.strip().upper()
    return folded if folded in RANK else None


def normalize(value: Any, default: str = DEFAULT) -> str:
    """*value* in canonical spelling, or *default* when it names no level.

    *default* is returned as given, so ``""`` asks for "no level" rather than a
    guess (the HTML report's empty badge).
    """
    level = canonical(value)
    return level if level is not None else default


def rank(value: Any, default: str = DEFAULT) -> int:
    """Sort key of *value*, 0 for HIGH; :data:`UNKNOWN_RANK` when neither
    *value* nor *default* names a level."""
    return RANK.get(normalize(value, default), UNKNOWN_RANK)


def weight(value: Any, default: str = DEFAULT) -> int:
    """What *value* adds to a priority score (:data:`WEIGHT`); 0 when neither
    *value* nor *default* names a level."""
    return WEIGHT.get(normalize(value, default), 0)


def is_high(value: Any) -> bool:
    """True when *value* names HIGH, in any case."""
    return canonical(value) == "HIGH"


def at_least(value: Any, minimum: Any, default: str = DEFAULT) -> bool:
    """True when *value* is as important as *minimum* or more."""
    return rank(value, default) <= rank(minimum, default)


def canonicalize(records: Optional[Iterable[Any]]) -> None:
    """Rewrite each record's ``importance`` in canonical spelling, in place.

    For records arriving from a reviewer or read back from disk. A value that
    names no level is left as written (readers treat it as :data:`DEFAULT`);
    a non-record is skipped. Rewriting an existing key keeps the record's key
    order, so a regrouped file's bytes move only by the spelling.
    """
    for record in records or ():
        if isinstance(record, dict):
            level = canonical(record.get("importance"))
            if level is not None:
                record["importance"] = level


def _value_of(item: Any) -> Any:
    """An item's importance: a record's ``importance`` field (absent reads as
    ``None``), or the item itself when it is already a value."""
    if isinstance(item, dict):
        return item.get("importance")
    return item


def highest(items: Optional[Iterable[Any]], default: str = DEFAULT) -> str:
    """The most important level among *items*, in canonical spelling.

    Each item is a record carrying ``importance`` (a suggestion or an issue) or a
    bare value. An item that names no level counts as *default*, and *default*
    is the answer when *items* is empty. With ``default=""`` such items are
    passed over and ``""`` means none of them named a level.
    """
    best = default
    best_rank = RANK.get(default, UNKNOWN_RANK)
    seen = False
    for item in items or ():
        level = normalize(_value_of(item), default)
        level_rank = RANK.get(level, UNKNOWN_RANK)
        if not seen or level_rank < best_rank:
            best, best_rank, seen = level, level_rank, True
    return best


def group_members(group: Dict[str, Any]) -> List[Any]:
    """A group's members: its ``suggestions`` (plan lane) or ``issues``."""
    return group.get("suggestions", group.get("issues", [])) or []


def members_importance(members: Optional[Iterable[Any]], empty: str = DEFAULT) -> str:
    """The importance of a group (or a report bucket) holding *members*.

    The one rule for a group's importance: the highest among its members, a
    member naming no level counting as :data:`DEFAULT`, which is the level that
    member's own data reads as; *empty* only when there are no members. The
    HTML report's ``maxImportance`` and priority sorts pass ``empty=""`` (no
    badge, sorts after LOW); apply filtering and validation batching keep
    :data:`DEFAULT`, which reads the same wherever ``""`` is folded.
    """
    members = list(members or ())
    return highest(members) if members else empty


def group_importance(group: Dict[str, Any], empty: str = DEFAULT) -> str:
    """The importance of *group* (:func:`members_importance` of its members).

    A group record carries no importance of its own (``SuggestionGroup.to_dict``
    has none), so this is the one derivation every reader of a group's importance
    uses.
    """
    return members_importance(group_members(group), empty)


# --- Older names, kept as thin wrappers over the helpers above ---------------

def get_highest_importance(group: Dict[str, Any]) -> str:
    """The highest importance level of a group (:func:`group_importance`);
    MEDIUM for a group with no members."""
    return group_importance(group)


def normalize_importance(level: str) -> str:
    """*level* in canonical spelling, MEDIUM when it names none (:func:`normalize`)."""
    return normalize(level)
