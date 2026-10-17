# Prototyping tools and research findings

A reference complementing `iteration-prototype-fidelity` with practical tools and research on prototype effectiveness.

## Prototyping tools by fidelity

### Paper / sketching

- **Paper, pencil, sticky notes** — the original. Cheap, infinitely revisable.
- **Whiteboards** — collaborative; great for early co-design.

### Wireframes (low-fidelity digital)

- **Balsamiq** — explicitly low-fidelity look; discourages detail polish.
- **Figma / Sketch / Adobe XD** — can do low-fi; risk is creep toward higher fidelity.

### Mockups (high-fidelity static)

- **Figma** — current industry standard.
- **Sketch** — Mac-only; declining share but still used.
- **Adobe XD** — Adobe's tool; less popular than Figma.

### Clickable prototypes

- **Figma prototyping** — built-in.
- **Framer** — more sophisticated interactions and animations.
- **ProtoPie** — high-fidelity interactions including device sensors.
- **InVision** — declining but still in use at large enterprises.

### Code prototypes

- **HTML / CSS / JS** with sample data — closest to production.
- **React / Vue / Svelte** — with the actual component library.
- **Vercel / Netlify** — quick deploy of prototypes for sharing.
- **Storybook** — component-level prototyping.

## Research on prototype-fidelity effects

Multiple studies (Wong 1992; Walker, Takayama, Landay 2002) have compared user-research outcomes across prototype fidelities:

- **Low-fidelity prototypes** elicit more structural and functional feedback ("I don't see how to do X") and less surface feedback.
- **High-fidelity prototypes** elicit more surface feedback ("I don't like the color") and less structural challenge.
- **Mixed-fidelity** can be the worst: users react to the polished parts as polished and the rough parts as unfinished.

The practical implication: pick a consistent fidelity per study; if you want structural feedback, stay low.

## Common prototype-fidelity mistakes

- **Polishing too early.** Spending hours on visual design before structure is settled. The polish has to be redone.
- **Pretending production prototypes are throwaway.** Building something at production fidelity, calling it a prototype. Eventually it becomes the actual product despite never being designed for production reliability.
- **Skipping clickable prototypes.** Going straight from static mockup to code. Misses the interaction-feel feedback that clickables provide.
- **Over-investing in interaction fidelity.** Spending a week perfecting micro-animations in a prototype that will be redone in code. The animations should be specced separately.

## Worked example: an effective prototype escalation

A team designs a new chat feature.

1. **Day 1**: paper sketches; team agrees on structure.
2. **Day 2**: Balsamiq wireframes; design crit.
3. **Day 3-4**: Figma mockup of one critical screen; visual style review.
4. **Week 2**: Figma clickable prototype of full flow; 5 user interviews.
5. **Week 3**: refined prototype; 5 more interviews.
6. **Week 4-5**: code prototype with real backend; performance check.
7. **Week 6+**: production build.

Each stage uses the cheapest fidelity that answers the cycle's question. The final code build is informed by 5 weeks of iteration but only requires production-quality work for the last 2 weeks.

## Resources

- **Walker, M., Takayama, L., Landay, J.** "High-Fidelity or Low-Fidelity, Paper or Computer?" (2002).
- **Snyder, C.** *Paper Prototyping* (2003).
- **Warfel, T.** *Prototyping: A Practitioner's Guide* (2009).
- **NN/g** — articles on prototyping methodology.
