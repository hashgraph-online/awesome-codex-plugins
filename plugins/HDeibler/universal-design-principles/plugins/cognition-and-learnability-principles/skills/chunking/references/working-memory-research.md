# Working memory research and chunking depth

A reference complementing the `chunking` SKILL.md with the cognitive-psychology background.

## Miller (1956): the magical number seven

George Miller's 1956 paper proposed that human short-term memory has a roughly fixed capacity of about 7 ± 2 items. The paper compiled evidence from many tasks: digit recall, word recall, tone discrimination, judgment of quantity. Across all of them, the limit landed around the same number.

The paper's key contribution was the concept of *chunk*: the unit of measurement isn't bits or letters but meaningful chunks. A practiced reader holds whole words, not letters; an experienced chess player holds positions, not pieces.

Miller also noted that experts can effectively expand capacity by chunking more efficiently — not by expanding raw capacity, but by recoding information into larger chunks.

## Cowan (2001): the magical number four

Nelson Cowan's *Behavioral and Brain Sciences* paper revisited Miller's number with the benefit of decades of follow-up research. Cowan's analysis: when you control for rehearsal, grouping, and other strategies that effectively cheat the limit, raw working memory capacity is closer to 4 ± 1.

The "7±2" number is what people achieve with chunking and rehearsal; the "4±1" number is the underlying capacity.

For design, this means:

- The user's *unaided* working memory holds about 4 chunks.
- With chunking aid (visual grouping, named sections), users can manage more.
- Pushing past 4 chunks visible at once relies on the user doing the chunking themselves — reasonable for trained users, less so for casual.

## Baddeley's working memory model

Alan Baddeley's model (1986, refined since) breaks working memory into:

- **Phonological loop**: holds verbal/auditory information for ~2 seconds; refresh by rehearsal.
- **Visuospatial sketchpad**: holds visual/spatial information.
- **Central executive**: coordinates and switches attention.
- **Episodic buffer**: integrates information into coherent episodes.

The model explains why visual chunking and verbal chunking are partly independent (you can hold roughly 4 visual chunks *and* 4 verbal chunks). Designs that exploit both modalities (a numbered list with visual structure) outperform purely-textual or purely-visual chunked content.

## Expert vs. novice chunking

Classic chess studies (de Groot 1965, Chase and Simon 1973) showed that:

- Experts and novices recall random chess positions equally — both at ~4–7 pieces.
- Experts recall *meaningful* positions (an opening, a checkmate setup) far better than novices.

The expert advantage is entirely in chunk recognition. Years of practice teach the expert to recode many pieces into a single meaningful chunk.

For UI design: the patterns your users learn become chunks. A daily user of your dashboard sees "the revenue panel" as one chunk; a new user sees ten distinct numbers. Familiar layouts let users hold more.

## Cross-domain examples of chunking failures

### Memorization of long passwords

Users asked to remember a 12-character password (a wall of characters) struggle. Chunked passphrases ("correct horse battery staple" — XKCD's classic example) are easier because each word is one chunk and only 4 chunks total are needed.

### Long phone trees ("press 1 for...")

Phone IVR systems that present 7+ options exceed working memory. Users either pick wrong or ask the operator. Best practice: cap at 4–5 options per level; nest.

### Wall-of-text user agreements

A 20-page Terms of Service is a working-memory disaster. Users either don't read or skim and miss. Chunked summaries ("Here's what this agreement says: 1. We can change pricing with 30 days notice. 2. ...") move toward usability.

### Driving directions

"In 0.3 miles, turn right onto Elm Street, then immediately bear left onto Maple, then take the second right onto Oak" — multiple chunks, but each turn is a chunk. Modern GPS apps deliver one turn at a time precisely to avoid working-memory overload.

## Design implications

- **Estimate working memory budget per surface.** How many independent items must the user hold while completing this task? > 4 → restructure.
- **Use perceptual grouping (proximity, similarity)** so chunking is automatic, not effortful.
- **Use conventional chunkings** (phone-number formatting, OTP groups) so users don't have to compute the structure.
- **Don't chunk reference content.** Working memory limits don't apply when users are scanning or searching, only when they're *holding*.

## Resources

- **Miller, G.** "The Magical Number Seven, Plus or Minus Two" (1956). *Psychological Review*.
- **Cowan, N.** "The Magical Number Four in Short-Term Memory" (2001). *Behavioral and Brain Sciences*.
- **Baddeley, A.** *Working Memory, Thought, and Action* (2007).
- **Chase, W. G. & Simon, H. A.** "Perception in Chess" (1973). *Cognitive Psychology*.
- **Sweller, J.** Cognitive load theory papers (1988 onward).
