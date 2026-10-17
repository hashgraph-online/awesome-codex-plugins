# Iconic Representation — origins and research lineage

## Roots in semiotics

The classification of signs into similar (iconic), example (indexical), and arbitrary (symbolic) comes from Charles Sanders Peirce's semiotics in the late 19th century. Peirce distinguished three kinds of relationships between a sign and what it signifies:

- **Iconic:** the sign resembles the signified (a portrait resembles the person).
- **Indexical:** the sign points to or is associated with the signified (smoke indexes fire; a footprint indexes a foot).
- **Symbolic:** the relationship is arbitrary, established by convention (the word "tree" doesn't resemble or point to a tree; we just agreed it means tree).

The Lidwell-Holden-Butler taxonomy of "similar / example / arbitrary or symbolic" maps loosely onto Peirce's categories: similar = iconic, example = indexical, arbitrary = symbolic. The terms differ but the underlying distinction is the same.

The semiotic framework is useful because it tells you what each kind of icon needs to work. Iconic signs work without prior learning because the resemblance does the work. Indexical signs require knowing the association (smoke means fire because we know fire produces smoke). Symbolic signs require prior training in the convention.

## In wayfinding and signage

The use of iconic representation in signage long predates digital design. International airport pictograms — the silhouettes for restroom, baggage claim, customs, etc. — are the result of a 1974 American Institute of Graphic Arts (AIGA) and U.S. Department of Transportation collaboration that produced a standardized set of 50 pictograms intended to be universally interpretable across languages.

The AIGA / DOT set was rigorously researched: candidate symbols were tested with diverse audiences for recognition rate, and only those that crossed a high threshold were adopted. The set is still widely used worldwide and has shaped subsequent pictogram standards (ISO, IEC).

The lesson from this work: even ostensibly "universal" pictograms vary widely in actual recognition. Some symbols (the male/female restroom figures, the airplane for "departures") test very high; others (the symbol for "lost and found," the symbol for "currency exchange") test much lower and rely on context to be interpretable.

## In early HCI: the Star icon set

The Xerox Star (1981) is generally credited as introducing the modern icon-based desktop. The Star team designed icons for documents, folders, the trash can, the printer, and various other objects. Their research showed that iconic representations dramatically reduced the learning curve for new computer users compared to command-line systems.

The Star team's approach was conservative: they preferred icons that depicted real-world objects (a folder that looked like a folder, a document that looked like a document with a folded corner) and tested icon designs with users to verify recognition. This emphasis on tested similarity carried forward into the Macintosh, Windows, and the broader convention of icon-based UI.

## In modern UI: the convention era

By the 2000s and 2010s, many digital icons had stabilized into conventions that no longer required (or could no longer afford) literal resemblance. The hamburger menu, the kebab menu, the share icon, the gear, the sparkle for AI — all became broadly recognized through repeated exposure rather than through visual similarity to anything in the physical world.

This shift produced what some designers call "icon literacy": the ability to recognize and interpret a vocabulary of conventional symbols, much like reading. Users who've used many apps can read an icon-only toolbar with little difficulty; users new to digital interfaces struggle with the same toolbar.

The implication: as the audience for digital products has matured, designers can lean more on convention and less on literal resemblance. But this doesn't extend to all audiences — children, older users, users in regions with less digital saturation, and accessibility audiences may still depend on literal resemblance or text labels.

## Empirical findings on icon recognition

Several studies, notably those by Rod Black and others on "icon comprehension," have produced stable findings:

- **Recognition rates vary widely.** Even for ostensibly conventional icons, recognition rates in tested audiences typically range from 30% to 95%. Designers consistently overestimate how recognizable their icons are.
- **Icon + label outperforms icon-only or label-only for first-time use.** The combination provides redundancy for the user to interpret.
- **Icon-only outperforms icon + label for expert speed.** Once users have learned the icons, the label becomes redundant cognitive load.
- **Color helps when the audience can perceive it.** Color-coded icon variants (a red trash for delete, a blue checkmark for confirm) improve recognition speed but fail for color-blind users without a non-color cue.
- **Icon style consistency aids learning.** Mixed icon styles (some outlined, some filled, some skeuomorphic) are harder to learn than a coherent set.
- **Domain-specific conventions are strong within the domain.** Code editors, design tools, music software, and other specialty applications have icon vocabularies that are nearly opaque to outsiders but immediately readable to insiders.

## The accessibility dimension

Icon-only interfaces present accessibility challenges:

- **Screen readers** need text alternatives for icons (`aria-label`, alt text). An icon without text is invisible to non-sighted users.
- **Low-vision users** may need larger icons or larger associated text.
- **Cognitive accessibility** benefits from text labels because text disambiguates and slows down the requirement for fast pattern recognition.
- **Cultural accessibility** can fail when icons reference objects unfamiliar to a user's culture.

The accessibility considerations push toward icon+text for primary navigation and major actions, with icon-only reserved for compact contexts where space is genuinely scarce.

## Modern conventions stabilizing in real time

Some icon conventions are still actively stabilizing:

- The "share" icon has multiple competing conventions (Apple's upward-arrow-from-box, Android's network-graph) that have not yet converged.
- The "AI" icon is currently coalescing around a sparkle/star symbol, but variations exist.
- The "voice input" icon has stabilized around a microphone but with various stylizations.
- "Notifications" has converged on a bell across most platforms.

When designing new icons, especially for new categories of function, you can sometimes contribute to which convention stabilizes. But more often, the safe path is to follow the dominant convention even if you have a design opinion.

## Conventions that have faded

Some conventions have actively faded over time:

- The floppy disk for "save" — increasingly anachronistic for users who've never used floppies.
- The mailing-envelope for "email" — recognized but losing strength as physical mail fades.
- The CD/DVD icon for media — once standard, now mostly disappeared.
- The wheel-knob for "tune" or "rotate" — depended on familiar physical knobs that have largely vanished.

When a convention is fading, the safe path is to label the icon (or use a more current alternative) rather than relying on the dying convention.

## Sources informing this principle

- Peirce, C. S. (Late 19th century writings on semiotics; see *Collected Papers* vols. 2 & 4).
- AIGA / U.S. DOT (1974). *Symbol Signs*.
- Lidwell, W., Holden, K., & Butler, J. (2003). *Universal Principles of Design*.
- Lodding, K. N. (1983). Iconic interfacing.
- Norman, D. (1988). *The Design of Everyday Things*.
- Horton, W. (1994). *The Icon Book: Visual Symbols for Computer Systems and Documentation*.
- ISO 7001 and successor standards on public information symbols.
- Modern platform icon guidelines (Apple SF Symbols, Material Symbols, Carbon Icons, etc.).
