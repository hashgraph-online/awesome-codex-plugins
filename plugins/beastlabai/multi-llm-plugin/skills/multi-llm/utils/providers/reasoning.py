"""The canonical reasoning-effort ladder (M12, §6.1).

:data:`REASONING_LADDER` is the one vocabulary; an adapter declares the rungs
its CLI takes through :class:`ReasoningLadder`, and
:func:`split_reasoning_effort` reads an ``:effort`` suffix off a model string.
``base`` re-exports every name here for reading
(docs/development/providers.md#the-provider-base-modules).
"""

from dataclasses import dataclass
from typing import Collection, Dict, Optional, Tuple


def split_reasoning_effort(model: str, efforts: Collection[str]) -> Tuple[str, Optional[str]]:
    """Split an optional trailing ``:effort`` suffix off a model string.

    Returns ``(base_model, effort)`` when the substring after the LAST colon
    is a member of ``efforts`` and the part before it is non-empty; otherwise
    ``(model, None)`` and the model string passes through verbatim. Splitting
    on the last colon keeps model ids that legitimately contain colons (e.g.
    openrouter ``:free`` variants) intact unless the suffix is whitelisted.
    """
    base, _, suffix = model.rpartition(":")
    if base and suffix in efforts:
        return base, suffix
    return model, None


# ---------------------------------------------------------------------------
# M12 (§6.1) — the canonical reasoning-effort ladder
# ---------------------------------------------------------------------------
#
# Before this region every adapter carried a private ``REASONING_EFFORTS`` set
# with no shared vocabulary behind it, so the tree had no answer to "is ``off``
# the same rung as ``none``", "is ``ultra`` a rung at all" or "is ``thinking``
# weaker than ``high``". Each set is now *expressed through* one ladder instead
# of being restated beside it: an adapter declares which canonical rungs its CLI
# takes, what that CLI calls them locally, and which off-ladder names it must let
# through — and its ``REASONING_EFFORTS`` is **derived** from that declaration.
#
# Nothing about :func:`split_reasoning_effort` moves. It still takes an arbitrary
# ``Collection[str]`` and every adapter still hands it ``REASONING_EFFORTS``; the
# value is computed now rather than typed out, which is the whole difference.
#
# Three rules the plan states normatively, each measured, and each pinned by
# ``tests/test_reasoning_effort_ladder.py`` over the **registry** rather than
# over a list of adapter names:
#
#   1. Seven rungs, one total order, and nothing else joins it.
#   2. ``thinking``/``instant`` are a SECOND AXIS, not rungs (21 models each in
#      kilocode and opencode). They are accepted and passed through verbatim,
#      never compared to a rung and never coerced onto one — which is why
#      acceptance is "is this name accepted *here*", not "is it on the ladder".
#   3. ``none`` and ``minimal`` are taken on the wire by CLIs whose own catalogs
#      advertise neither. An unadvertised rung may be *passed through* when a
#      user names it, never *chosen* by a default or by a rung-down.
#
# The two alias pairs run in both directions and are per-provider *spellings*,
# never ladder members: ``off`` ≡ ``none`` (goose, pi, vibe) and ``ultra`` ≡
# ``max`` — outbound for muse, which has no ``max`` and wants the word ``ultra``,
# and inbound-only for codex, which takes ``max`` verbatim, so codex's own
# client-side ``ultra → max`` normalization is an unused backstop rather than a
# dependency.
#
# Caps are per MODEL, never per provider: ``max → xhigh`` is something a
# particular model's ``supported_reasoning_levels``/``variants`` list says, not
# something a provider name implies. :attr:`ReasoningLadder.model_caps` is where
# a measured per-model narrowing lives, including the one combination measured to
# hang forever rather than fail.

#: The canonical rungs, weakest → strongest. One vocabulary for every adapter.
REASONING_LADDER: Tuple[str, ...] = (
    "none",
    "minimal",
    "low",
    "medium",
    "high",
    "xhigh",
    "max",
)

#: Membership, for "is this name a rung at all" — asked separately from "does
#: this CLI accept it", because rule 2 turns on exactly that distinction.
LADDER_RUNGS = frozenset(REASONING_LADDER)

#: Rung → position, so "weaker than" and "one rung down" are arithmetic on a
#: shared order rather than a comparison between two adapters' private lists.
LADDER_POSITION: Dict[str, int] = {
    rung: index for index, rung in enumerate(REASONING_LADDER)
}

#: Rungs that CLIs accept on the wire while advertising them in no catalog
#: entry (rule 3). They stay in the accepted sets — the CLIs really do take
#: them — but :meth:`ReasoningLadder.rung_down` steps over them, because a rung
#: nothing advertises may never be the one the harness picks on a user's behalf.
UNADVERTISED_RUNGS = frozenset({"none", "minimal"})

#: Off-ladder names that select a *mode* rather than an amount of effort
#: (rule 2). Declared here so an adapter listing one is visibly declaring a
#: second-axis variant rather than inventing an eighth rung.
SECOND_AXIS_VARIANTS = frozenset({"thinking", "instant"})


@dataclass(frozen=True)
class ReasoningLadder:
    """One CLI's accepted effort vocabulary, expressed against the ladder.

    Every field is a *measurement* of what the CLI takes, never a preference.
    The mapping fields are tuples of pairs rather than dicts so the whole
    declaration stays immutable and hashable.

    :attr:`rungs`
        The canonical rungs this CLI accepts, stated in ladder order and emitted
        verbatim.
    :attr:`spellings`
        ``local name → canonical rung`` for a rung this CLI calls something else.
        Accepted **and emitted**: muse wants ``ultra`` where the ladder says
        ``max``; goose, pi and vibe want ``off`` where the ladder says ``none``.
    :attr:`inbound_aliases`
        ``local name → canonical rung`` accepted at the harness boundary and
        rewritten *before* argv is built, so the emitted value is always a name
        this adapter states. codex's ``ultra`` is the only entry.
    :attr:`variants`
        Off-ladder second-axis names (:data:`SECOND_AXIS_VARIANTS`) passed
        through verbatim.
    :attr:`model_caps`
        ``model id → the names accepted for that model``. An empty tuple means
        *no* effort value is safe on that model. This is the per-model half of
        §6.1 and the only place a cap may live.
    :attr:`declined`
        Non-empty when the CLI has no per-run effort mechanism at all. The
        reason, not a flag: four adapters are in this state and each is there
        for a different measured reason.
    """

    provider: str = ""
    rungs: Tuple[str, ...] = ()
    spellings: Tuple[Tuple[str, str], ...] = ()
    inbound_aliases: Tuple[Tuple[str, str], ...] = ()
    variants: Tuple[str, ...] = ()
    model_caps: Tuple[Tuple[str, Tuple[str, ...]], ...] = ()
    declined: str = ""

    # -- the declaration, read back ---------------------------------------

    @property
    def local_names(self) -> Dict[str, str]:
        """``spellings`` as a mapping: local name → canonical rung."""
        return dict(self.spellings)

    @property
    def aliases(self) -> Dict[str, str]:
        """``inbound_aliases`` as a mapping: local name → canonical rung."""
        return dict(self.inbound_aliases)

    @property
    def accepted(self) -> "frozenset":
        """Every name this CLI accepts **and may be handed back**.

        This is what an adapter's ``REASONING_EFFORTS`` is, and therefore what
        :func:`split_reasoning_effort` is called with. Inbound-only aliases are
        deliberately absent: they are accepted on a *spec* and rewritten, never
        emitted.
        """
        return frozenset(self.rungs) | set(self.local_names) | set(self.variants)

    @property
    def accepted_inbound(self) -> "frozenset":
        """:attr:`accepted` plus the inbound-only aliases — what a spec may say."""
        return self.accepted | set(self.aliases)

    @property
    def caps(self) -> Dict[str, Tuple[str, ...]]:
        """``model_caps`` as a mapping: model id → accepted names."""
        return dict(self.model_caps)

    # -- the questions the dispatch path asks ------------------------------

    def normalize(self, name: str) -> Optional[str]:
        """Which canonical rung ``name`` denotes, or ``None``.

        Answers "what rung is this word", independent of whether this CLI
        accepts it — a second-axis variant and an unknown word both answer
        ``None``, which is rule 2 in one line.
        """
        if name in LADDER_RUNGS:
            return name
        return self.local_names.get(name) or self.aliases.get(name)

    def render(self, rung: str) -> Optional[str]:
        """The word this CLI wants for canonical ``rung``, or ``None``.

        The canonical spelling wins whenever the CLI takes it (goose accepts
        both ``none`` and ``off`` and gets ``none``); the local spelling is used
        only where the canonical one is not accepted at all (muse has no ``max``
        and gets ``ultra``; pi and vibe have no ``none`` and get ``off``).
        """
        if rung in self.rungs:
            return rung
        for local, canonical in self.spellings:
            if canonical == rung:
                return local
        return None

    def accepted_for(self, model: Optional[str] = None) -> "frozenset":
        """:attr:`accepted`, narrowed by any declared cap for ``model``.

        ``model`` may carry its own ``:effort`` suffix; it is split off with the
        adapter's own inbound set first, so a caller can pass the spec it has.
        """
        if not model:
            return self.accepted
        base, _ = split_reasoning_effort(model, self.accepted_inbound)
        caps = self.caps
        if base in caps:
            return frozenset(caps[base]) & self.accepted
        return self.accepted

    def accepts(self, name: str, model: Optional[str] = None) -> bool:
        """Whether ``name`` may be handed to this CLI (for ``model``, if given)."""
        return name in self.accepted_for(model)

    def refuses_for_model(self, model: str, name: str) -> bool:
        """``name`` is fine for this provider but declared unsafe on ``model``."""
        return name in self.accepted and name not in self.accepted_for(model)

    def resolve(self, raw: str, model: Optional[str] = None) -> Optional[str]:
        """The value to emit for a requested ``raw`` effort — ``None`` to refuse.

        §6.1's coercion rule, exactly: an alias is applied **only when the raw
        value is unsupported but the canonical one is**. A name this CLI already
        accepts is therefore returned untouched, and a name that maps to no rung
        this CLI has is refused rather than being rounded onto a neighbour — a
        silent downgrade is the worse of the two failures, because the effort a
        run actually used is invisible in almost every CLI's output.
        """
        name = (raw or "").strip()
        if not name:
            return None
        allowed = self.accepted_for(model)
        if name in allowed:
            return name
        rung = self.normalize(name)
        if rung is None:
            return None
        spelled = self.render(rung)
        if spelled is not None and spelled in allowed:
            return spelled
        return None

    def rung_down(self, rung: str) -> Optional[str]:
        """The next weaker rung this CLI accepts — never an unadvertised one.

        Rule 3 lives here: ``none``/``minimal`` are reachable only by a user
        naming them, so a rung-down that runs out of advertised rungs returns
        ``None`` instead of stepping onto one.
        """
        position = LADDER_POSITION.get(rung)
        if position is None:
            return None
        for candidate in reversed(REASONING_LADDER[:position]):
            if candidate in self.rungs and candidate not in UNADVERTISED_RUNGS:
                return candidate
        return None


#: The declaration a provider makes when its CLI has no per-run effort
#: mechanism at all. Adapters in that state name their own reason; this exists
#: so :class:`LLMProvider`-adjacent code has a falsy default that is visibly
#: *undeclared* rather than visibly "declines".
NO_REASONING_LADDER = ReasoningLadder()
