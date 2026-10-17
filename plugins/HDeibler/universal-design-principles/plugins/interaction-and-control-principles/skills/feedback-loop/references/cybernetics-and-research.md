# Feedback loops: research and history reference

A reference complementing the `feedback-loop` SKILL.md with deeper grounding in cybernetics and HCI feedback research.

## Cybernetics: the foundational discipline

Norbert Wiener coined the term *cybernetics* in 1948 as the study of control and communication in animals and machines. The central concept: *feedback* — a system's response to its own previous output — was identified as the mechanism that enabled adaptation, equilibrium, and learning across biological, mechanical, and social systems alike.

Wiener's *Cybernetics: Or Control and Communication in the Animal and the Machine* (MIT Press, 1948) introduced the mathematical formalism that underpins control theory, modern robotics, and most reactive software systems.

## Forrester and system dynamics

Jay Forrester at MIT extended cybernetics into *system dynamics* — the study of complex systems whose behavior arises from feedback loops over time:

- **Industrial Dynamics** (1961) — applied to corporate decision-making.
- **Urban Dynamics** (1969) — applied to city growth and decline.
- **World Dynamics** (1971) — applied to global resource and population trajectories (precursor to *Limits to Growth*).

Forrester's diagrammatic conventions (causal-loop diagrams, stock-and-flow diagrams) are still used in systems analysis. The core insight: complex system behavior is rarely caused by single events; it's produced by the interaction of feedback loops.

## HCI feedback research

### Doherty Threshold (1982)

Walter Doherty and Arvind Thadani at IBM published research showing that response times under approximately 400ms keep users engaged at peak productivity. Above this threshold, attention drifts, errors increase, and engagement drops. The "Doherty Threshold" became a benchmark for system responsiveness.

Modern web-performance budgets (LCP < 2.5s, INP < 200ms) inherit this lineage.

### Card, Robertson, Mackinlay (1991)

Stuart Card and colleagues at Xerox PARC formalized the now-standard latency thresholds:

- < 100ms: perceived as instantaneous.
- < 1s: perceived as continuous flow.
- < 10s: keeps user attention.
- > 10s: user attention departs; needs progress indicator.

Their *The Information Visualizer* paper documented these and influenced decades of HCI design.

### Norman's gulfs (1986)

Donald Norman introduced the concepts of:
- **Gulf of execution**: the gap between what the user wants to do and the actions the system permits.
- **Gulf of evaluation**: the gap between the system's state and the user's perception of it.

Both gulfs are bridged by feedback. Good feedback closes the gulf of evaluation — the user perceives what the system did. Good affordance closes the gulf of execution — the user perceives what the system permits.

### Nielsen's heuristics (1994)

Jakob Nielsen's first usability heuristic: **"Visibility of system status."** The system should keep users informed about what is going on, through appropriate feedback within reasonable time. This restates Norman's principle as a usability rule.

## Modern web-performance feedback

The Core Web Vitals metrics (Google, 2020+) operationalize feedback latency:

- **Largest Contentful Paint (LCP)**: time to render the largest visible content. Target < 2.5s.
- **Interaction to Next Paint (INP)**: latency between user interaction and next visual update. Target < 200ms.
- **Cumulative Layout Shift (CLS)**: visual stability — feedback shouldn't cause unexpected layout jumps.

Each is a measurable feedback property. Sites that hit them feel responsive; sites that don't feel broken regardless of feature quality.

## Cross-domain examples

### Aircraft fly-by-wire

Modern aircraft replace mechanical control linkages with electronic feedback systems. The pilot moves the stick; sensors detect the input; computers calculate the appropriate control-surface deflection; actuators apply it. Multiple negative feedback loops (stability augmentation, envelope protection) keep the plane within safe operating bounds.

The same pattern in software: input layers → validation → controlled state change → visible response.

### Thermostatic systems

The canonical negative-feedback loop. The system maintains a setpoint by responding to deviations. Modern smart thermostats add positive feedback (learning user patterns and pre-empting demand) while preserving the negative-feedback core.

### Biological systems

Every regulatory mechanism in biology is a feedback loop: blood-glucose regulation, body temperature, blood pressure, cell-cycle checkpoints. Failure modes (diabetes, fever, hypertension) are loops gone wrong.

The lesson: feedback isn't just a UI concept; it's a property of any system that maintains itself over time.

## Anti-patterns from system-dynamics literature

- **Shifting the burden**: addressing symptoms with fast feedback (a temporary fix) while underlying problems compound. The football-helmet case.
- **Tragedy of the commons**: many positive loops sharing a finite resource; resource collapses.
- **Eroding goals**: when the metric used by a feedback loop is itself relaxed when missed, the system drifts toward lower standards.
- **Success to the successful**: positive loops that amplify initial advantages; rich-get-richer dynamics.

## Resources

- **Wiener, N.** *Cybernetics* (1948).
- **Forrester, J. W.** *Industrial Dynamics* (1961); *Urban Dynamics* (1969).
- **Senge, P.** *The Fifth Discipline* (1990).
- **Meadows, D.** *Thinking in Systems* (2008) — accessible introduction to system-dynamics thinking.
- **Doherty, W. & Thadani, A.** "The Economic Value of Rapid Response Time" (IBM, 1982).
- **Norman, D.** *The Design of Everyday Things* (1988, 2013).
- **web.dev / web-vitals docs** — modern web-performance feedback metrics.
