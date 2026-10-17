# Control — origins and research lineage

## Roots in human-factors engineering

The principle of control entered design thinking through aviation and industrial-process control rooms. In a cockpit or a power-plant control room, the operator's level of autonomy directly affects safety. Early autopilot systems gave the pilot full manual control or full automatic control, with no middle ground; this turned out to be unsafe in failure modes where the autopilot disengaged unexpectedly and the pilot was suddenly handed full control of an aircraft they had not been actively flying. The literature on this — including the famous Air France Flight 447 accident and the broader literature on "automation surprise" — established that the right level of control is not the maximum or the minimum, but a calibrated intermediate that keeps the human informed and engaged.

This produced the framework of "supervisory control" (a term from Tom Sheridan's 1992 work *Telerobotics, Automation, and Human Supervisory Control*). The human is not the moment-to-moment operator and not a passive observer, but a supervisor of an automated system, intervening when needed and informed enough to do so. Sheridan and others ranked control on a 10-level scale from "human does it all" to "computer does it all and tells the human nothing." Most well-designed control systems sit around levels 3–6: the computer suggests, the human selects, the computer executes; or the computer executes and reports back. Pure extremes generate problems.

## In HCI: user agency and direct manipulation

The HCI literature picked up the same threads in the 1980s. Ben Shneiderman's work on direct manipulation argued that the most usable interfaces are those where the user appears to act directly on visible objects (drag a file, resize a window, type in a document). Direct manipulation is, at one level, a control argument: it gives the user a strong sense of agency by making the connection between action and effect immediate and visible.

Don Norman's work on "the seven stages of action" (1988) provided a complementary framework: every interaction involves forming a goal, planning an action, executing it, perceiving the result, interpreting it, and evaluating it. Each stage can be supported or sabotaged by the level of control. Too much control burdens the planning stage; too little burdens the perception and interpretation stages (because the user has no idea what the system did or why).

The 1990s and 2000s produced a substantial literature on "user empowerment" in software and "perceived control" in consumer products. Key findings:

- Users with higher perceived control report higher satisfaction even when objective task performance is the same.
- Users with very low perceived control attribute outcomes (good or bad) to luck or to the system, not to themselves, which reduces engagement and learning.
- Users with very high control without adequate scaffolding (no defaults, no guidance) report higher frustration and abandon tasks more often.

The sweet spot is high *perceived* control coupled with sufficient scaffolding to make the choices manageable.

## In consumer software

The shift from desktop software to mobile and consumer-internet products in the 2000s generated a renewed debate about control. The "design for the dumbest user" school argued for aggressive simplification — fewer options, more defaults, stronger opinions. The "respect your power users" school argued the opposite. The empirical record suggests both extremes are wrong: products that win sustained use almost always layer their controls, with simple defaults for newcomers and depth available for committed users.

The successful examples — Lightroom, Notion, VS Code, Figma — all give the user substantial control while making it discoverable rather than obligatory. The unsuccessful examples — products that aggressively simplified, removed parameters, or hid settings to "improve UX" — frequently lost their power users, who departed for tools that respected their expertise.

## Locus of control and self-determination theory

A separate line of psychological research, originating with Julian Rotter in 1954 and elaborated by Edward Deci and Richard Ryan as Self-Determination Theory, distinguishes "internal" from "external" locus of control. An internal locus is the belief that outcomes depend on one's own actions; an external locus is the belief that outcomes depend on external forces (fate, system, others). People with a stable internal locus tend to be more motivated, more persistent, and more satisfied; people with a stable external locus tend to be more passive and less satisfied.

Software design can shift a user's situational locus of control. A product that does things on the user's behalf — autocorrect, auto-categorization, AI-suggested actions — moves the locus toward external. A product that asks for choices — confirmation dialogs, manual configuration — moves the locus toward internal. Neither is universally right, but the choice has psychological consequences worth being aware of. AI-heavy interfaces in particular can drift toward an external locus that, while convenient, leaves users feeling they are not in charge of their own work.

## In automation and AI design

The current generation of AI tools has revived all the old debates about control. Should the AI act on the user's behalf (high automation, low control) or suggest options that the user picks (medium automation, medium control) or provide capabilities that the user invokes when they want (low automation, high control)? Different products land in different places, and the right answer varies by audience and stakes.

The supervisory-control literature is directly applicable. An AI that does too much without informing the user creates the same "automation surprise" problem the cockpits did. An AI that does nothing without explicit instruction is less useful than it could be. The well-designed AI tool sits in the middle, doing useful things by default while making its actions visible, undoable, and adjustable.

## Empirical regularities worth remembering

The literature on control converges on a few stable findings.

- Users prefer interfaces that give them perceived control, even at some cost to objective task efficiency.
- The cost of removing control from experts is much higher than the benefit of adding it for novices, because experts churn out of products that constrain them, while novices simply find the simpler products.
- Defaults are extremely powerful. Most users accept defaults most of the time, regardless of what those defaults are. This means the defaults function as a hidden control system — they're doing most of the work — and should be chosen carefully.
- Reversibility expands the safe range of control. A system with full undo can afford to give users more control than a system with permanent actions.
- Confirmation friction should be calibrated to the stakes, not to the control level. Easy actions don't need confirmation; high-stakes actions do.

## Sources informing this principle

- Sheridan, T. B. (1992). *Telerobotics, Automation, and Human Supervisory Control*.
- Shneiderman, B. (1983). Direct manipulation: A step beyond programming languages.
- Norman, D. (1988). *The Design of Everyday Things*. (Particularly the seven stages of action.)
- Rotter, J. B. (1954). *Social Learning and Clinical Psychology*. (On locus of control.)
- Deci, E. L., & Ryan, R. M. (1985). *Intrinsic Motivation and Self-Determination in Human Behavior*.
- Bainbridge, L. (1983). Ironies of automation. *Automatica*. (Foundational paper on the costs of pure automation.)
- Lee, J. D., & See, K. A. (2004). Trust in automation: Designing for appropriate reliance. *Human Factors*.
