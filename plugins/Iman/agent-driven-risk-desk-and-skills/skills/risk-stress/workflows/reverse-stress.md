# Workflow: reverse stress and scenario scaling

## Reverse stress: which joint move produces loss L

1. Get the target loss in the book's base currency, and the horizon.
2. Get the covariance of simple returns over that horizon from the user,
   ordered like `assets`, naming each portfolio asset once. Ask where it
   came from and quote that source. Do not estimate or remember one.
3. Ask whether any asset needs a floor tighter than -100% (for example a
   pegged or capped price). Every shock is floored at -100% regardless.
4. Call `risk_reverse_stress` (CLI `riskdesk reverse-stress --input PATH`).
5. Read `solution`. `closed form` means `s* = -L Sigma w / (w' Sigma w)`.
   A `bounded` solution means a floor binds; name `binding_floors`.
6. Save the result and run `scripts/check_artifact.py RESULT.json`.

Report the shocks, the Mahalanobis distance (smaller is more plausible
under that covariance), the unbounded distance when a floor binds, and the
loss contributions. If you quote `loss_exceedance_probability_if_normal`,
say in the same sentence that it assumes jointly normal, zero-mean returns
with this covariance, which real returns usually violate.

A refusal that the target exceeds the largest reachable loss means a
long-only book cannot lose that much within the floors. Say so; do not
lower the target without asking.

## Scaling: what multiple of a scenario reaches loss L

1. Take one scenario naming every portfolio asset, and the target loss.
2. Call `risk_scenario_scale` (CLI `riskdesk scale-scenario --input PATH`).
3. Report `multiple`, `base_loss` and the scaled scenario's loss and
   contributions.

A refusal that the scenario does not lose money means no positive multiple
reaches a loss. A refusal naming assets below -100% means the target is
out of reach along that scenario's direction; reverse stress may still find
a shock that reaches it.

The multiple is a distance along one direction, not a probability.
