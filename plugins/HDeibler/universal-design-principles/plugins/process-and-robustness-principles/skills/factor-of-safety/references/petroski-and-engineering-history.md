# Factor of Safety: engineering history and case reference

A reference complementing the `factor-of-safety` SKILL.md with deeper engineering history and case studies.

## Petroski's lineage of failure

Henry Petroski's *To Engineer Is Human* (1985), *Design Paradigms* (1994), and *The Evolution of Useful Things* (1992) form the canonical contemporary reference on engineering failure. Central thesis: every successful engineering design is informed by the failures that preceded it. Safety factors are the explicit acknowledgment that the next failure will look like something not yet seen.

A few of Petroski's case studies, summarized:

### The Tacoma Narrows Bridge (1940)

A suspension bridge that collapsed in moderate winds. Engineers hadn't accounted for aeroelastic flutter — the way wind interacts with a flexible structure. After the collapse, all subsequent suspension bridges incorporated extensive wind-tunnel testing and stiffer designs. The safety factor was effectively *increased* by adding a new dimension (wind dynamics) that hadn't been in the original analysis.

### The Hyatt Regency walkway (1981)

The hotel's suspended walkway collapsed during a tea dance, killing 114 people. The design change during construction (a single rod replaced with two rods) doubled the load on a single connection point — the safety factor was unintentionally cut from ~2 to ~1. Even a "well-engineered" design failed because a structural detail's safety factor was misunderstood by the field engineers who modified it.

### The Challenger O-rings (1986)

The book's central case. The O-rings were rated for a safety factor of 3 in past launches. At low temperatures, that factor eroded toward 1. Engineers warned about the cold morning launch; management overrode the warnings, citing the past safety factor without accounting for the temperature dependence. The shuttle exploded 73 seconds after launch.

The pattern: when systems perform reliably over time, organizational memory loses track of *why* they worked. The safety factor erodes through optimization or modification; the next unusual condition exposes the erosion.

## Safety factors in different engineering domains

| Domain | Typical safety factor | Reasoning |
|---|---|---|
| Steel buildings | 2–3 | Well-understood material, predictable loads |
| Wood structures | 4–6 | Variable material; moisture / insect / fire risk |
| Aircraft | 1.5 | Weight matters; compensated by extensive testing and redundancy |
| Pressure vessels | 4 | Catastrophic failure mode |
| Elevators | 8–12 | Heavily regulated; severe failure consequence |
| Climbing equipment | 5–10 | Personal safety; impossible to test in field |
| Software systems | varies; often 2–5x current load | Less regulated; safety factor often informal |

The pattern: higher consequence + more uncertainty → higher safety factor.

## The "factor of ignorance" framing

The book notes that "factor of safety" is sometimes called "factor of ignorance." This framing is illuminating because it reorients the question:

- **"How safe should this be?"** is a values question without a clear answer.
- **"How much don't we know about this?"** has a defensible answer based on testing, history, and analysis.

The size of the safety factor should track the size of the ignorance. The more you know about how the system will be used, the smaller the factor can be. The more novel or untested the system, the larger.

## Software examples of safety factors

### Performance budgets

Modern web-performance practice sets explicit performance budgets — page load < 2s, FCP < 1s, LCP < 2.5s, etc. These are factors of safety against:
- Slow networks (rural, mobile, throttled).
- Slow devices (older hardware, low-end Android).
- Heavy contemporaneous load on the server.

Designing to the budget at fast/light conditions ensures the user on slow conditions still has acceptable experience.

### Capacity planning

A SaaS app expected to handle 10K concurrent users is provisioned for 30K. Reasoning:
- Marketing campaigns can spike load.
- Single client misbehaviors can saturate.
- Auto-scaling has lag.

The 3x margin handles common spikes; auto-scaling handles sustained growth.

### Error budgets (SRE)

Google's Site Reliability Engineering practice defines explicit allowable downtime (e.g., 0.1% = 43 min/month). This is a safety factor on perfection — explicit acknowledgment that systems will fail and a budget for that failure.

### Code complexity and maintenance

A subtler safety factor: writing code that's easier than necessary so future engineers can modify it without errors. The "extra" simplicity is margin against future ignorance — the engineer modifying the code in two years won't have the original author's context.

## When safety factors get cut

A common pattern across domains: when a system performs reliably for a long time, pressure mounts to reduce its cost. The "wasted" capacity, redundancy, or polish gets trimmed. Each individual cut is justified — the system worked fine without it before. The cumulative effect: the safety factor that protected the system from the unprecedented is gone.

The next unusual event then causes failure — and the post-mortem inevitably recommends restoring the safety factor that had been cut. Until the cycle starts again.

The discipline: explicit documentation of why each safety factor exists, so future cost-cutters understand what they're trading off.

## Resources

- **Petroski, H.** *To Engineer Is Human* (1985); *Design Paradigms* (1994); *The Evolution of Useful Things* (1992).
- **Perrow, C.** *Normal Accidents: Living with High-Risk Technologies* (1984).
- **Reason, J.** *Human Error* (1990).
- **Vaughan, D.** *The Challenger Launch Decision* (1996) — detailed analysis of the Challenger case.
- **Google SRE Book** (sre.google) — modern software safety-factor practice.
