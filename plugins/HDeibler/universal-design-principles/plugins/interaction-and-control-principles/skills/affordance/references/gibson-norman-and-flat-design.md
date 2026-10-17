# Affordance: Gibson, Norman, and the flat-design history

A reference complementing the `affordance` SKILL.md with deeper grounding in the perceptual-psychology origins and the recent design-history shifts.

## Gibson's ecological theory

James J. Gibson coined "affordance" in *The Senses Considered as Perceptual Systems* (1966) and developed it fully in *The Ecological Approach to Visual Perception* (1979). His radical claim: perception isn't a matter of taking sensory data and inferring what's there; it's a direct pickup of *affordances* — what the environment offers an animal.

A horizontal surface affords standing for a creature of the right size and weight. Water affords drinking, washing, and swimming. A graspable object affords carrying. The affordance exists in the relationship between the object and the perceiver — it's not purely "in" the object, and not purely "in" the perceiver.

Gibson's framing was disruptive in psychology because it shifted explanation from internal mental representations to environmental properties. Whether his strong claim is right is still debated; but for design, the concept is enormously useful: design objects to *afford* their intended uses, and the intended uses become perceptually obvious.

## Norman's translation

Donald Norman introduced affordance to the design world in *The Psychology of Everyday Things* (1988, retitled *The Design of Everyday Things*). His door-handle examples became canonical:

- A door with a handle affords pulling.
- A door with a flat plate affords pushing.
- A door that requires pushing but has a handle is *misdesigned* — the affordance contradicts the intended use.

The book's wider message: the world is full of well-meaning designs that violate affordance, forcing users to read signs, ask for help, or learn the hard way. The book made "affordance" common vocabulary in design, software UX, and product engineering.

## Norman's later refinement: signifiers

In a 2008 essay ("Signifiers, not affordances") and the 2013 revised edition of *Design of Everyday Things*, Norman clarified an important distinction:

- An **affordance** is a relationship — an action the object/environment makes possible for some user.
- A **signifier** is a perceivable cue that tells the user about the affordance.

In screen design, the affordance often exists regardless of the visual treatment (a `<button>` is clickable whether or not you style it). What designers control is the *signifier* — the visual treatment that tells users "this is clickable."

Norman's clarification matters for screens because:

- A bare `<button>` element has the affordance of clickability but may have weak signifiers (no styling).
- Adding a background color, border, hover state — these are all signifiers.
- A `<div onclick>` has the affordance of clickability (because of the onclick) but no native signifiers; you must add them all manually, plus accessibility scaffolding.

The book's principle (and most casual usage in the design field) collapses the two terms; the distinction matters when you're auditing why an interactive element isn't working.

## The flat-design recession of signifiers (2013–2018)

The shift from skeuomorphic to flat design, kicked off by iOS 7 (2013) and Microsoft's Metro/Modern style earlier, stripped many traditional signifiers:

- Drop shadows reduced to subtle or eliminated.
- Bezels and gradients on buttons flattened.
- Fewer iconographic-style 3D illustrations.
- Borders thinner or removed.

For aesthetic reasons, the result was cleaner, more modern-feeling UIs. For affordance, the result was widespread regression: users couldn't tell what was clickable. NN/g and other usability research bodies documented this regression in articles like "Flat UI Elements Attract Less Attention and Cause Uncertainty" (2017).

The course-correction since ~2018 has been "almost flat" or "soft flat" or "neumorphism" — keeping the visual lightness while restoring just enough signifier (subtle shadow, hover response, more bordered chrome) to keep affordance perceivable.

The lesson: aesthetic style trends can erode usability when they remove signifiers. Affordance discipline must be re-asserted on every project, against every style fad.

## Cross-domain examples

### Tools and instruments

A hammer affords striking; a screwdriver affords turning; a saw affords cutting. The shapes evolved over centuries to make their uses obvious. Modern industrial designers can short-circuit this evolution by deliberately matching shape to action.

### Children's toys (Lego, shape sorters)

Lego studs and cavities are pure affordance: the bricks teach themselves. Shape sorters teach affordance through fail-fast: wrong shapes don't fit, right ones do.

### Apple's product design

Jonathan Ive's industrial designs at Apple (iPod, iPhone, MacBook) are exercises in affordance discipline: the physical buttons and surfaces signal their use without labels. The unibody MacBook's hinge is shaped to invite opening. The iPhone's home button (in versions that had one) is shaped to invite pressing.

### Architecture: doors, paths, stairs

The doors-vs-handles example generalizes:

- Stairs afford climbing only when the riser height is in a comfortable range.
- A path afford walking only when its width and surface are appropriate.
- A handrail affords gripping at the right height.

Architects work with affordance constantly; software designers can borrow the discipline.

## Anti-pattern history: skeuomorphism's overreach

The pendulum swung the other way before the flat-design recession. iOS 1–6 (2007–2013) leaned hard into literal skeuomorphism:

- iCal looked like a leather-bound calendar.
- Game Center had felt-textured backgrounds.
- Notes looked like a yellow legal pad.
- iBooks had a wooden bookshelf.

Critics argued this was decoration without affordance benefit (the leather doesn't help you use the calendar). Defenders argued the metaphors *did* help with affordance — the bookshelf taught users that books had spines they could pull.

The middle ground: borrow *behavioral* affordances from physical objects (sliding, pressing, sticking) without literal *visual* mimicry.

## Resources

- **Gibson, J. J.** *The Ecological Approach to Visual Perception* (1979).
- **Norman, D.** *The Design of Everyday Things* (1988, revised 2013).
- **Norman, D.** "Signifiers, not affordances" (jnd.org, 2008).
- **NN/g** — multiple articles on flat design and affordance regression.
- **Apple HIG** and **Material Design** — both extensively document signifier conventions for their platforms.

## Closing

Affordance is one of those principles that sits beneath nearly every interaction-design decision. The discipline isn't in knowing the principle; it's in noticing every interactive element on every screen and asking: does it look interactive in the still state? Does it respond when engaged? Does it stay consistent across the product? Three small audits, repeated, that catch most affordance failures.
