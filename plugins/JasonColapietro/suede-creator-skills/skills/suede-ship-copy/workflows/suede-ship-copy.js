export const meta = {
  name: 'suede-ship-copy',
  description: 'Copy-only DAG: intake -> multi-lens research -> claim audit -> angle panel -> section map with message ownership -> disjoint section writers -> assemble -> four-lens review -> adversarial refute -> deslop -> graphic spec + channel package -> publish-readiness gate -> evidence handoff',
  whenToUse: 'A piece of copy strangers will read and that has to be true. Pass args: { piece, surface, sources?, given?, audience?, liveUrl?, outDir?, mustSay?, wordBudget?, houseStyle? }. houseStyle accepts guidance and emDashes (allow or avoid). `given` is an array of facts the requester states themselves; they enter the permitted claim set and are never audited.',
  phases: [
    { title: 'Intake', detail: 'resolve sources, capture the currently published text, voice refs, format law, hazards' },
    { title: 'Research', detail: 'five blind lenses: product truth, audience, market, voice, surface law' },
    { title: 'Gaps', detail: 'completeness critic, one bounded fill round, then the claim audit that decides what may be asserted' },
    { title: 'Angles', detail: 'three independent postures, each carrying its own audited claims' },
    { title: 'Outline', detail: 'section map with one message per section, red team, deterministic collision check' },
    { title: 'Draft', detail: 'disjoint section writers, each bound to its cited claims' },
    { title: 'Assemble', detail: 'one voice, real transitions, no repeated phrasing' },
    { title: 'Review', detail: 'four lenses on the whole piece: stranger, claim, conversion, slop' },
    { title: 'Refute', detail: 'adversarial verifiers, refute by default, both must fail to refute' },
    { title: 'Polish', detail: 'blocker revision, deslop pass, graphic spec, channel package' },
    { title: 'Gate', detail: 'deterministic checks plus publish-readiness read against the live surface' },
    { title: 'Handoff', detail: 'write the deliverable and the evidence record' },
  ],
}

// Workflow({ scriptPath: 'suede-ship-copy/workflows/suede-ship-copy.js',
//            args: { piece: '...', surface: 'landing page', sources: [...] } })

// args can arrive as an object or as a JSON-encoded string depending on how the
// caller serialized it. Accept both — a stringified arg blob is otherwise an
// instant, zero-agent failure that reads like a script bug.
let A = args
if (typeof A === 'string') {
  try { A = JSON.parse(A) } catch (e) { throw new Error(`args arrived as an unparseable string: ${A.slice(0, 200)}`) }
}
const PIECE = (A && A.piece) || null
const SURFACE = (A && A.surface) || null
const SOURCES = (A && A.sources) || []
const AUDIENCE = (A && A.audience) || null
const LIVE = (A && A.liveUrl) || null
const OUT = (A && A.outDir) || null
const MUST_SAY = (A && A.mustSay) || []
const BUDGET = (A && A.wordBudget) || null
const HOUSE_STYLE = (A && A.houseStyle) ?? {}
if (!HOUSE_STYLE || typeof HOUSE_STYLE !== 'object' || Array.isArray(HOUSE_STYLE) ||
    (HOUSE_STYLE.guidance !== undefined && typeof HOUSE_STYLE.guidance !== 'string') ||
    (HOUSE_STYLE.emDashes !== undefined && !['allow', 'avoid'].includes(HOUSE_STYLE.emDashes))) {
  throw new Error('houseStyle must be { guidance?: string, emDashes?: "allow" | "avoid" }')
}
const EM_DASH_POLICY = HOUSE_STYLE.emDashes || 'avoid'
const STYLE_INSTRUCTIONS = `Active house style: ${JSON.stringify(HOUSE_STYLE)}.
Supplied guidance overrides inferred voice and Suede defaults. Em dashes: ${EM_DASH_POLICY}
in newly written prose. Preserve all protected strings, quotes, code, commands, links,
citations, paths, and requester-supplied wording regardless of punctuation policy.
Preserve deliberate fragments, humor, technical vocabulary, and meaning-bearing adverbs;
use passive voice when the actor is unknown, immaterial, or conventional for this genre.
Writing patterns describe quality, never evidence of human or machine authorship.`
// Total AGENT budget — distinct from the word budget above. The caller is required to
// ask the user which range they want before launching (see SKILL.md); this default
// exists so a caller that forgets gets the middle range rather than the widest.
const AGENT_BUDGETS = {
  light:    { angles: 2, gapFills: 1, refuteCap: 2 },
  standard: { angles: 3, gapFills: 2, refuteCap: 4 },
  deep:     { angles: 3, gapFills: 3, refuteCap: 6 },
}
const AGENT_BUDGET_NAME = AGENT_BUDGETS[(A && A.agentBudget) || ''] ? A.agentBudget : 'standard'
const AGENT_BUDGET = AGENT_BUDGETS[AGENT_BUDGET_NAME]
// Facts the requester states themselves. These are GIVEN. They are never
// audited, never narrowed, never dropped, and never become a review finding.
// The audit exists to catch agents inventing things, not to second-guess the
// person who owns the product and the liability.
const GIVEN = (A && A.given) || []
if (!PIECE || !SURFACE) {
  throw new Error(`Pass args: { piece: "<what to write, in the user's words>", surface: "<landing page | email | thread | docs page | listing | ad>" } — got ${JSON.stringify(A)}`)
}

// ---------------------------------------------------------------- schemas
// Intake returns a MANIFEST plus one verbatim capture. Everything else is a
// path or a URL — the writers open what they need. Threading source text
// through stage returns is what turns cache reads into most of the bill.
const INTAKE = {
  type: 'object',
  required: ['outDir', 'slug', 'sources', 'userClaims', 'publishedBaseline', 'voiceRefs', 'protectedVerbatim', 'surfaceLaw', 'hazards'],
  properties: {
    outDir: { type: 'string', description: 'directory the deliverable will be written to — a draft location, never a live published file' },
    slug: { type: 'string' },
    // Transcription, not evaluation. These go straight into the permitted set.
    userClaims: {
      type: 'array',
      maxItems: 30,
      items: {
        type: 'object',
        required: ['claim', 'whereStated'],
        properties: {
          claim: { type: 'string', description: 'the requester’s own statement, recorded exactly as they made it' },
          whereStated: { type: 'string', description: 'the brief, the given list, or a protected string' },
        },
      },
    },
    sources: {
      type: 'array',
      maxItems: 30,
      items: {
        type: 'object',
        required: ['ref', 'kind', 'whatItProves'],
        properties: {
          ref: { type: 'string', description: 'absolute path or url — PATH ONLY, do not paste contents' },
          kind: { type: 'string', enum: ['file', 'url', 'repo', 'transcript', 'other'] },
          whatItProves: { type: 'string' },
        },
      },
    },
    // The before-state. Without it, a rewrite that silently contradicts what is
    // already published is undetectable until a customer finds both versions.
    publishedBaseline: {
      type: 'object',
      required: ['exists', 'capturedHow'],
      properties: {
        exists: { type: 'boolean' },
        url: { type: 'string' },
        verbatim: { type: 'string', description: 'the exact current published text for this surface, trimmed to 2000 chars' },
        capturedHow: { type: 'string', description: 'the command or fetch that produced it, or why it could not be captured' },
      },
    },
    voiceRefs: { type: 'array', items: { type: 'string' }, maxItems: 10, description: 'paths/urls of ALREADY SHIPPED copy in the house voice — the voice lens reads these' },
    protectedVerbatim: { type: 'array', items: { type: 'string' }, description: 'strings that must survive byte-exact: product names, legal lines, prices, trademarks' },
    surfaceLaw: {
      type: 'object',
      required: ['fields'],
      properties: {
        fields: {
          type: 'array',
          maxItems: 12,
          items: {
            type: 'object',
            required: ['field', 'limit', 'unit'],
            properties: {
              field: { type: 'string', description: 'headline, subject, meta description, body, alt text, CTA…' },
              limit: { type: 'number' },
              unit: { type: 'string', enum: ['chars', 'words', 'lines'] },
            },
          },
        },
        notes: { type: 'string' },
      },
    },
    hazards: {
      type: 'array',
      items: {
        type: 'object',
        required: ['kind', 'blocking', 'detail'],
        properties: {
          kind: { type: 'string', enum: ['overwrite-published', 'regulated-language', 'trademark', 'missing-source', 'other'] },
          // `kind` is a TOPIC, not a verdict. All-clear reports are welcome and
          // useful — they must set blocking:false. Only an actually-present,
          // actually-dangerous condition sets blocking:true, and the only kind
          // that may ever be blocking is 'overwrite-published' — a file path,
          // not a judgement about anything the requester said.
          blocking: { type: 'boolean', description: 'true ONLY for overwrite-published, and only when the output path really does point at published copy. Everything else is blocking:false.' },
          detail: { type: 'string' },
        },
      },
    },
  },
}

// Research returns compressed, PROVENANCED facts. Every claim carries a
// file:line or a url, because a fact without a source cannot be published and
// the claim audit is about to delete it anyway.
const RESEARCH = {
  type: 'object',
  required: ['lens', 'facts', 'constraints', 'unread'],
  properties: {
    lens: { type: 'string' },
    facts: {
      type: 'array',
      maxItems: 12,
      items: {
        type: 'object',
        required: ['claim', 'source'],
        properties: {
          claim: { type: 'string', description: 'stated the way it could appear in copy — specific, checkable' },
          source: { type: 'string', description: 'file:line, url, commit sha, review/issue link, or transcript timestamp' },
        },
      },
    },
    constraints: {
      type: 'array',
      maxItems: 8,
      items: {
        type: 'object',
        required: ['rule', 'source', 'breakingItMeans'],
        properties: {
          rule: { type: 'string' },
          source: { type: 'string' },
          breakingItMeans: { type: 'string' },
        },
      },
    },
    unread: { type: 'array', items: { type: 'string' }, description: 'sources this lens knows exist and deliberately did not open' },
  },
}

const GAPS = {
  type: 'object',
  required: ['gaps'],
  properties: {
    gaps: {
      type: 'array',
      maxItems: 3,
      items: {
        type: 'object',
        required: ['missing', 'whyItMatters', 'howToClose'],
        properties: {
          missing: { type: 'string' },
          whyItMatters: { type: 'string' },
          howToClose: { type: 'string', description: 'the specific file, url, command, or search that closes it' },
        },
      },
    },
  },
}

// The claim audit is the spine of this DAG. Everything downstream may only
// assert what survives here.
const AUDIT = {
  type: 'object',
  required: ['audited'],
  properties: {
    audited: {
      type: 'array',
      items: {
        type: 'object',
        required: ['claim', 'verdict', 'why'],
        properties: {
          claim: { type: 'string' },
          verdict: { type: 'string', enum: ['holds', 'overstated', 'unsourceable', 'stale'] },
          why: { type: 'string' },
          safeRewording: { type: 'string', description: 'for "overstated" only: the version the source actually supports' },
        },
      },
    },
  },
}

const ANGLE = {
  type: 'object',
  required: ['posture', 'headline', 'promise', 'why', 'claimsUsed', 'competitorCanSayThis', 'killerObjection', 'objectionAnswer'],
  properties: {
    posture: { type: 'string' },
    headline: { type: 'string' },
    promise: { type: 'string', description: 'one sentence: what the reader gets, stated concretely' },
    why: { type: 'string', description: 'why this angle beats the other two for THIS audience on THIS surface' },
    claimsUsed: { type: 'array', items: { type: 'string' }, description: 'the exact audited claims this angle rests on' },
    competitorCanSayThis: { type: 'boolean', description: 'true if a named competitor could publish the same headline without lying — that is a failing grade' },
    killerObjection: { type: 'string' },
    objectionAnswer: { type: 'string' },
  },
}

const PLAN = {
  type: 'object',
  required: ['angle', 'sections'],
  properties: {
    angle: {
      type: 'object',
      required: ['headline', 'promise', 'why'],
      properties: { headline: { type: 'string' }, promise: { type: 'string' }, why: { type: 'string' }, grafted: { type: 'string' } },
    },
    sections: {
      type: 'array',
      maxItems: 7,
      items: {
        type: 'object',
        required: ['name', 'job', 'ownsMessage', 'cites', 'wordBudget', 'acceptance', 'tier'],
        properties: {
          name: { type: 'string' },
          job: { type: 'string', description: 'what this section does to the reader' },
          ownsMessage: { type: 'string', description: 'the ONE idea this section owns. No other section may make this point.' },
          cites: { type: 'array', items: { type: 'string' }, description: 'exact audited claims this section may assert — it may assert nothing else' },
          mustSayVerbatim: { type: 'array', items: { type: 'string' } },
          wordBudget: { type: 'number' },
          acceptance: { type: 'string', description: 'observable: a question a reader of ONLY this section can answer' },
          tier: { type: 'string', enum: ['mechanical', 'craft', 'judgment'] },
        },
      },
    },
  },
}

const REDTEAM = {
  type: 'object',
  required: ['objections'],
  properties: {
    objections: {
      type: 'array',
      maxItems: 6,
      items: {
        type: 'object',
        required: ['section', 'objection', 'severity'],
        properties: {
          section: { type: 'string' },
          objection: { type: 'string' },
          severity: { type: 'string', enum: ['fatal', 'serious', 'noted'] },
        },
      },
    },
  },
}

const SECTION = {
  type: 'object',
  required: ['state', 'text', 'claimsUsed', 'placeholders'],
  properties: {
    state: { type: 'string', enum: ['done', 'done-with-concerns', 'needs-context', 'blocked'] },
    text: { type: 'string', description: 'the prose itself, markdown, no commentary' },
    claimsUsed: { type: 'array', items: { type: 'string' } },
    placeholders: { type: 'array', items: { type: 'string' }, description: 'every [AUTHOR: supply X] this section had to leave' },
    notes: { type: 'string' },
  },
}

const ASSEMBLED = {
  type: 'object',
  required: ['text', 'wordCount', 'notes'],
  properties: {
    text: { type: 'string' },
    wordCount: { type: 'number' },
    notes: { type: 'string', description: 'what was cut for repetition, which transitions were written, what still reads thin' },
  },
}

// A finding anchors to a QUOTE. In prose there is no file:line — the quoted
// string is the only address a verifier can go check.
const FINDINGS = {
  type: 'object',
  required: ['findings'],
  properties: {
    findings: {
      type: 'array',
      maxItems: 10,
      items: {
        type: 'object',
        required: ['quote', 'claim', 'whyItFails', 'severity'],
        properties: {
          quote: { type: 'string', description: 'the exact string in the draft this is about' },
          claim: { type: 'string' },
          whyItFails: { type: 'string', description: 'the concrete reader or the concrete source that makes this wrong' },
          severity: { type: 'string', enum: ['blocker', 'major', 'minor'] },
          fix: { type: 'string' },
        },
      },
    },
  },
}

const VERDICT = {
  type: 'object',
  required: ['refuted', 'why'],
  properties: { refuted: { type: 'boolean' }, why: { type: 'string' } },
}

const DESLOP = {
  type: 'object',
  required: ['text', 'total', 'verdict', 'removed'],
  properties: {
    text: { type: 'string' },
    total: { type: 'number', description: 'the deslop score out of 50' },
    verdict: { type: 'string', enum: ['CLEAN', 'REVISE'] },
    removed: { type: 'string', description: 'counts by category: filler, structure, passive, vague, em dashes' },
    stillGenerating: { type: 'string', description: 'if under 35, what is still producing the score and why it needs the author' },
  },
}

const GRAPHIC = {
  type: 'object',
  required: ['visuals', 'suedeMark'],
  properties: {
    visuals: {
      type: 'array',
      maxItems: 6,
      items: {
        type: 'object',
        required: ['section', 'concept', 'onImageText', 'aspect', 'altText', 'buildWith'],
        properties: {
          section: { type: 'string' },
          concept: { type: 'string', description: 'what the image shows — one sentence a designer could execute' },
          onImageText: { type: 'string', description: 'the exact words that appear in the image. This is copy and it obeys every rule the body obeys.' },
          aspect: { type: 'string', description: 'the ratio and pixel size this surface actually requires' },
          sourceAsset: { type: 'string', description: 'existing screenshot/photo path if one exists, else "generate"' },
          altText: { type: 'string' },
          buildWith: { type: 'string', description: 'screenshot | existing asset | suede-image | media-use | designer' },
        },
      },
    },
    suedeMark: {
      type: 'object',
      required: ['needed', 'approvedAssetPresent'],
      properties: {
        needed: { type: 'boolean' },
        approvedAssetPresent: { type: 'boolean' },
        path: { type: 'string' },
        note: { type: 'string' },
      },
    },
  },
}

const PACKAGE = {
  type: 'object',
  required: ['fields', 'headlineVariants', 'cta'],
  properties: {
    fields: {
      type: 'array',
      items: {
        type: 'object',
        required: ['field', 'value', 'chars', 'limit', 'passes'],
        properties: {
          field: { type: 'string' },
          value: { type: 'string' },
          chars: { type: 'number' },
          limit: { type: 'number' },
          passes: { type: 'boolean' },
        },
      },
    },
    headlineVariants: { type: 'array', items: { type: 'string' }, maxItems: 3 },
    cta: { type: 'string' },
  },
}

const READINESS = {
  type: 'object',
  required: ['risks', 'readback'],
  properties: {
    risks: {
      type: 'array',
      maxItems: 8,
      items: {
        type: 'object',
        required: ['risk', 'evidence', 'severity', 'reversible'],
        properties: {
          risk: { type: 'string' },
          evidence: { type: 'string', description: 'a quoted line from the draft plus the source or url that contradicts it — not an assertion' },
          severity: { type: 'string', enum: ['blocker', 'major', 'minor'] },
          reversible: { type: 'string', enum: ['edit', 'repost', 'correction-notice', 'irreversible'] },
          mitigation: { type: 'string' },
        },
      },
    },
    readback: { type: 'string', description: 'what the live surface says RIGHT NOW for everything this piece changes; "not attempted" if there is no live surface' },
  },
}

// --------------------------------------------------------------- 0. intake
phase('Intake')
const intake = await agent(
  `Piece to write: ${PIECE}
Surface: ${SURFACE}
${AUDIENCE ? `Audience named by the requester: ${AUDIENCE}` : 'Audience: not named — infer it from the sources and say what you inferred.'}
${SOURCES.length ? `Sources the requester supplied: ${SOURCES.join(', ')}` : 'Sources: none supplied — find them.'}
${LIVE ? `Live surface: ${LIVE}` : 'Live surface: not supplied — discover it if one exists.'}
${MUST_SAY.length ? `Strings that must survive byte-exact: ${JSON.stringify(MUST_SAY)}` : ''}
${GIVEN.length ? `Facts the requester states as given: ${JSON.stringify(GIVEN)}` : ''}
${OUT ? `Requested output directory: ${OUT}` : ''}
${STYLE_INSTRUCTIONS}

You are INTAKE. Read-only reconnaissance. Write nothing except by reporting where output will go.

1. SOURCES. Assemble the evidence base this copy will be built from: product code or
   README, pricing config, changelog, docs, existing decks, transcripts, support threads,
   the live site. Report PATHS AND URLS ONLY with what each one proves. Do not paste contents.
   If the piece needs a fact that neither the requester supplied nor any source carries, that
   is hazard "missing-source", advisory only.

2. THE REQUESTER'S OWN CLAIMS. Transcribe every factual statement the requester made — in
   the brief above, in the given list, in the protected strings — into userClaims, exactly
   as they said it. This is transcription, not evaluation.

   These are GIVEN. Do not verify them, do not look for a source, do not soften them, do not
   mark them unsourced, do not flag them as a hazard, and do not rewrite them into something
   you find more defensible. The requester owns this product and this liability; they are not
   an agent whose output needs auditing. If a source you happen to read disagrees with one of
   their statements, the statement stands and you say nothing about it.

   The audit that runs later never sees this list.

3. PUBLISHED BASELINE. If this surface already has published text, capture it VERBATIM now
   (curl the url, or read the file). This is the before-state: without it, a new draft that
   contradicts what is already live is invisible until a reader finds both. Trim to 2000
   chars. If there is nothing published yet, say so and set exists:false.

4. VOICE REFS. Find 3-8 pieces of ALREADY SHIPPED copy in this brand's voice — the live
   site, a merged README, a sent email, a published post. Paths only. Prefer shipped text
   over any style guide: a style guide says what someone intended, shipped copy says what
   the brand actually sounds like.

5. PROTECTED VERBATIM. Strings that must survive byte-exact into the final draft: the legal
   product name, trademark forms, price strings, license lines, disclaimer sentences, plus
   anything the requester listed above. Include quotations, qualifiers attached to exact
   claims, code, commands, links, citations, and paths that the piece must reproduce.

6. SURFACE LAW. The hard format limits for a ${SURFACE}: every field and its real limit
   (chars/words/lines). Meta description, subject line, preview text, App Store subtitle,
   ad headline, alt text, thread post length — whatever this surface actually has. Get the
   current numbers; do not answer from memory when a doc or the platform states them.

7. OUTPUT LOCATION AND SLUG. Return a "slug": a short kebab-case identifier for this piece,
   derived from the brief (for example "agent-studio-landing"). It names both output files,
   so a missing or generic slug is a file called "undefined.md".
   Then choose a DRAFT path. ${OUT ? `Use ${OUT}.` : 'Default to a .suede-copy/<slug>/ directory beside the primary source, or the cwd.'}
   If the requested output path is an already-published file (a live page source, a shipped
   README, a sent template), that is hazard "overwrite-published" with blocking:true — this
   workflow produces a draft for a human to place, it does not edit live copy in place.
   This is the ONLY hazard that may ever be blocking, and it is about a file path.

8. HAZARDS. Report only, fix nothing. Every one of these is blocking:FALSE.
   - The piece will carry regulated language — health, medical, financial return, earnings,
     safety, legal status, hiring or credit eligibility: kind "regulated-language". Note it
     for the record so it appears in the evidence file. Do NOT treat it as a problem to
     solve, do not ask for a source, and do not gate anything on it. If the requester stated
     it, it is stated.
   - The brief names a competitor or uses another company's mark: "trademark", with what
     would make it safe.
   - The piece needs a number, a testimonial, or a result that the requester did NOT supply
     and no source carries: "missing-source". The writers will use an [AUTHOR: supply X]
     placeholder. This never applies to something the requester told you.

   \`kind\` is the TOPIC you examined; \`blocking\` is the verdict, and only
   "overwrite-published" can carry it. All-clear reports are valuable and set blocking:false.

Return the manifest. Do NOT paste source contents beyond the published baseline capture.`,
  { schema: INTAKE, phase: 'Intake', effort: 'low' }
)

if (!intake) throw new Error('Intake failed — no evidence base, so nothing here would be checkable. Stop.')

// Backfill anything the schema marked required that came back absent. Trusting
// `required` and then reading a nested field bare is how a run dies one agent
// in, on a TypeError, with the whole cost of the intake already paid.
intake.hazards = intake.hazards || []
intake.sources = intake.sources || []
intake.voiceRefs = intake.voiceRefs || []
intake.userClaims = intake.userClaims || []
intake.surfaceLaw = intake.surfaceLaw || { fields: [] }
intake.publishedBaseline = intake.publishedBaseline || { exists: false, capturedHow: 'intake returned no baseline object' }
intake.slug = intake.slug || 'draft'
intake.outDir = intake.outDir || '.suede-copy/draft'

// Halt on the VERDICT, never on the topic label — and only ever on the output
// path. Nothing the requester SAID can stop this run. An intake agent that
// marks a regulated-language or missing-source hazard as blocking is overriding
// the person who owns the product, so the filter refuses to honour it.
const blockingHazards = intake.hazards.filter(h => h.blocking === true && h.kind === 'overwrite-published')
if (blockingHazards.length) {
  log(`HALT: ${blockingHazards.map(h => `${h.kind}: ${h.detail}`).join(' | ')}`)
  return { halted: true, reason: 'output path points at published copy', intake }
}
const overreach = intake.hazards.filter(h => h.blocking === true && h.kind !== 'overwrite-published')
if (overreach.length) log(`intake tried to block on ${overreach.map(h => h.kind).join(', ')} — downgraded to advisory, the requester's own statements are not gated`)
// Rewrite the downgraded ones rather than only logging them. Every advisory
// reader downstream selects on !blocking, so a hazard left at blocking:true
// after being downgraded is silently absent from the evidence record — the one
// place the intake prompt promised it would appear.
intake.hazards = intake.hazards.map(h =>
  (h.blocking === true && h.kind !== 'overwrite-published') ? { ...h, blocking: false, downgraded: true } : h)

const protectedVerbatim = [...new Set([...(intake.protectedVerbatim || []), ...MUST_SAY])]

// Normalization used by every deterministic check in this script.
const norm = s => String(s).toLowerCase().normalize('NFKC').replace(/[^a-z0-9 ]+/g, ' ').replace(/\s+/g, ' ').trim()

// The requester's claims, assembled before any agent gets an opinion about
// them. Everything here enters the permitted set untouched and skips the audit.
const userClaims = [
  ...(intake.userClaims || []).map(c => ({ claim: c.claim, source: `stated by the requester (${c.whereStated})`, origin: 'user' })),
  ...GIVEN.map(g => ({ claim: typeof g === 'string' ? g : g.claim, source: 'stated by the requester (given)', origin: 'user' })),
].filter(c => c.claim)
// Does this text touch something the requester said? Used everywhere a given
// has to be pulled out of an agent's reach.
//
// Containment runs BOTH directions on purpose. A review lens quotes a FRAGMENT
// of the draft, so its quote is usually SHORTER than the given it came from —
// a one-directional `quote.includes(given)` check lets every fragment-quoted
// finding straight through, which is the opposite of the intent. The raw
// substring pass catches short-but-distinctive givens like "$49/mo" that
// normalization would flatten to five generic characters.
//
// This errs toward dropping. A legitimate finding lost because it brushed a
// given is a cost; a given rewritten by a reviser because a filter was too
// clever is the thing this workflow promises cannot happen.
// Protected strings are NOT claims. A product name or a legal line is a string to
// preserve byte-exact, not an assertion to exempt from review. Treating one as a
// claim lets a single `mustSay` entry void the entire review stage, because the
// product name appears in half the draft and every quoted line would match it.
const protectedKeys = new Set(protectedVerbatim.map(norm))
const givenClaims = userClaims.filter(c => !protectedKeys.has(norm(c.claim)))

// Overlap is PROPORTIONAL, not a flat character floor. The shorter string has to
// be most of the longer one for the two to be the same claim. A six-character
// fragment of a long given is not evidence that a finding is about that given —
// it is how a review of the whole piece gets deleted two words at a time, and
// how a compound sentence ("<given clause> and <invented clause>") launders an
// agent's invention behind something the requester actually said.
const GIVEN_MIN = 6
const SHARE = 0.6
const overlaps = (a, b) => {
  if (!a || !b) return false
  if (a === b) return true
  const [short, long] = a.length <= b.length ? [a, b] : [b, a]
  if (short.length < GIVEN_MIN) return false
  return long.includes(short) && short.length >= long.length * SHARE
}
const touchesGiven = (...parts) => {
  const texts = parts.filter(Boolean).map(String)
  return givenClaims.some(u => {
    const raw = String(u.claim).trim()
    const k = norm(raw)
    if (!k) return false
    return texts.some(s => overlaps(raw.toLowerCase(), s.toLowerCase()) || overlaps(k, norm(s)))
  })
}
log(`${intake.sources.length} sources · baseline ${intake.publishedBaseline.exists ? 'captured' : 'none published'} · ${userClaims.length} claims given by the requester (never audited) · ${intake.voiceRefs.length} voice refs · ${protectedVerbatim.length} protected strings · ${intake.hazards.filter(h => !h.blocking).length} advisory hazards`)

// ------------------------------------------------------------- 1. research
// Multi-modal sweep. Each lens searches a DIFFERENT way and is blind to the
// others — one angle never finds everything. A genuine barrier: the angle
// panel needs all five at once, and the gap critic needs the full `unread`
// union to know what was skipped.
phase('Research')
const BASE = `Piece: ${PIECE}
Surface: ${SURFACE}${AUDIENCE ? `\nAudience: ${AUDIENCE}` : ''}
Sources: ${intake.sources.map(s => `${s.ref} (${s.whatItProves})`).join(' | ')}
${intake.publishedBaseline.exists ? `Currently published on this surface:\n"""${(intake.publishedBaseline.verbatim || '').slice(0, 1200)}"""` : 'Nothing is published on this surface yet.'}

GIVEN BY THE REQUESTER — already established, already in the permitted set, not your
business to check, confirm, disprove, or re-source:
${JSON.stringify(givenClaims.map(c => c.claim))}
Do not return these as facts of your own. Do not return a constraint that contradicts one.
If something you read disagrees with a given, the given stands and you say nothing about it.

Return compressed, provenanced facts. EVERY fact carries a file:line, url, sha, or
timestamp. A fact you cannot source cannot be published, and the claim audit that runs
next will delete it. State each fact the way it could appear in copy — specific and
checkable, not "the product is fast" but "cold start drops from 900ms to 40ms (bench.ts:22)".
Do not paste source text back; the writers re-read what they need. List in "unread"
anything you know exists and deliberately did not open.`

const LENSES = [
  {
    key: 'product-truth',
    effort: 'medium',
    prompt: `Lens: PRODUCT TRUTH. What does the thing actually do, right now, in the shipped version?
Read the code, the config, the pricing, the changelog, the live surface — not the marketing.
For every capability the piece will want to claim: does it exist, is it on by default, what
are its limits, what breaks it, what does it cost. A feature behind a flag defaulted off is
not a shipped feature and must be recorded as such. Constraints here are the things the copy
must not say: the capability that is planned rather than shipped, the number that was true
one release ago, the integration that exists only in a branch.`,
  },
  {
    key: 'audience',
    effort: 'medium',
    prompt: `Lens: AUDIENCE. Who reads this and what is already in their head?
Find their OWN words, verbatim, sourced: issue titles, support threads, reviews, testimonials,
sales-call notes, community posts, competitor complaint threads. What have they already tried
and abandoned? What do they believe that is wrong? What is the single objection that kills the
decision — the one they do not say out loud? Facts here are quoted reader language with a link.
A constraint is a belief the copy must clear before it can be believed at all. If you cannot
reach real reader language, say so in "unread" rather than inventing a persona.`,
  },
  {
    key: 'market',
    effort: 'low',
    prompt: `Lens: MARKET. How does everyone else already say this?
Read 3-5 direct competitors' live copy for this same surface. Separate table stakes (what
everyone claims, so claiming it wins nothing) from what only this product can honestly say.
Record the exact phrases the category has worn out — those become banned phrases for this
piece, because a sentence a competitor could publish verbatim is a sentence that does not
sell. Constraints here are: do not claim X, three rivals already own that sentence.`,
  },
  {
    key: 'voice',
    effort: 'low',
    prompt: `Lens: VOICE. Extract the house voice from ALREADY SHIPPED copy — these files and urls:
${intake.voiceRefs.join(', ') || '(none found by intake — search the repo and the live site for shipped copy before giving up)'}
Measure, do not describe: typical sentence length and its range, paragraph length, whether it
uses contractions, second person, questions, lists, headers, humor. Find the recurring house
constructions and the words this brand never uses. Record punctuation law.
${STYLE_INSTRUCTIONS}
Facts are "average sentence 13 words, range 4-26 (index.html:40-70)".
Constraints are the constructions that would read as someone else writing.`,
  },
  {
    key: 'surface',
    effort: 'low',
    prompt: `Lens: SURFACE LAW. What does a ${SURFACE} mechanically require?
Intake reported: ${JSON.stringify(intake.surfaceLaw)}. Verify those numbers against the
current platform docs or the actual template, and add what it missed: required metadata
fields, what is visible before the fold or before the "more" cut, preview/subject truncation,
link and image behavior, platform content policy for this format, accessibility requirements
including alt text. Where the piece will be indexed or read by a model as well as a person,
say what that adds. Constraints are hard limits with the number attached.`,
  },
]

const sweep = (await parallel(LENSES.map(l => () => agent(
  `${BASE}\n\n${l.prompt}`,
  { label: `research:${l.key}`, phase: 'Research', schema: RESEARCH, effort: l.effort }
)))).filter(Boolean)

// -------------------------------------------------------------- 2. gap fill
// What a sweep misses is invisible to the sweep. One critic, one bounded round.
phase('Gaps')
const critic = await agent(
  `Piece: ${PIECE} (${SURFACE})
Research so far: ${JSON.stringify(sweep)}
Everything the lenses flagged as unread: ${JSON.stringify([...new Set(sweep.flatMap(r => r.unread))])}

You are the COMPLETENESS CRITIC. You do not add findings — you name what is MISSING.
Ask: which modality was not run? Which fact rests on a single source? Is there a claim the
piece obviously needs that no lens found evidence for? Did the audience lens reach real
reader language or fall back to a persona? Do two lenses contradict each other about what
the product does? Return at most 3 gaps, each with the specific file, url, command, or
search that closes it. An unresolved contradiction between two lenses is always a gap.
If coverage is genuinely sufficient, return an empty array — padding costs a round of agents.`,
  { schema: GAPS, phase: 'Gaps', effort: 'high' }
)

const gapFills = critic && critic.gaps.length
  ? (await parallel(critic.gaps.slice(0, AGENT_BUDGET.gapFills).map(g => () => agent(
      `${BASE}\n\nLens: GAP FILL. Close exactly this gap and nothing else.
Missing: ${g.missing}
Why it matters: ${g.whyItMatters}
How to close it: ${g.howToClose}`,
      { label: `gap:${g.missing.slice(0, 30)}`, phase: 'Gaps', schema: RESEARCH, effort: 'medium' }
    )))).filter(Boolean)
  : []
if (critic && critic.gaps.length > AGENT_BUDGET.gapFills) log(`gap critic raised ${critic.gaps.length}; filling the first ${AGENT_BUDGET.gapFills}, carrying the rest to the handoff as unread`)

const research = [...sweep, ...gapFills]
// Only AGENT-GENERATED facts reach the audit. A lens that echoed one of the
// requester's givens back as its own finding is filtered out here rather than
// audited, because auditing it would audit the requester through a proxy.
// Not just exact restatements: a lens that paraphrases a given ("pricing begins
// at forty-nine dollars monthly" for the given "price is $49/mo") would
// otherwise reach the audit, come back unsourceable, and land in the evidence
// record as a claim nobody may republish. That is the requester's own fact
// being refused through a proxy.
const rawFacts = research.flatMap(r => r.facts)
const allFacts = rawFacts.filter(f => !touchesGiven(f.claim))
// These are REMOVED, not passed through. The given itself already carries the
// content into the permitted set, so nothing is lost — but say "removed", because
// a log that claims a fact survived when it did not is a lie in the run record.
const restated = rawFacts.filter(f => touchesGiven(f.claim))
if (restated.length) log(`${restated.length} research fact(s) restated a given and were removed before the audit — the given carries the fact`)
const constraints = research.flatMap(r => r.constraints)
const stillUnread = [...new Set([
  ...research.flatMap(r => r.unread),
  ...(critic ? critic.gaps.slice(AGENT_BUDGET.gapFills).map(g => g.missing) : []),
])]

// THE CLAIM AUDIT. The load-bearing skeptic of this DAG, and it has exactly one
// target: things an agent made up. In code, a hallucinated constraint wastes a
// lane; in copy, a hallucinated fact is a published lie with the brand's name on
// it. The requester's own statements are not in this list and never will be.
const audit = allFacts.length
  ? await agent(
      `These facts were ASSERTED BY RESEARCH AGENTS — not by the requester — and are about to be
published to strangers under this brand's name. Audit every one against its cited source.
OPEN THE SOURCE — read the file, fetch the url. Do not reason about whether it sounds plausible.

SCOPE, absolute: you are auditing machine output. The requester's own statements were filtered
out before this list was built and are not yours to evaluate. If a fact below rests on
something the requester said, the verdict is "holds" — your job is to catch an agent that
invented a number, not to check the person who owns the product.

${JSON.stringify(allFacts)}

Verdicts:
- holds: the source says exactly this, and it is true of the current shipped product
- overstated: the source supports something WEAKER. Give the version it does support in
  "safeRewording" — this is the most common and most dangerous verdict, because the claim
  survives review by sounding almost right
- unsourceable: the cited file/line/url does not exist, or does not contain this
- stale: true when written, contradicted now by current code, current pricing, or the live site

Be adversarial. A number with no unit, a comparative with no baseline ("2x faster" than what),
a superlative, and a capability that is real but not on by default are all overstated at best.
You are the last checkpoint before this reaches a reader.`,
      { schema: AUDIT, phase: 'Gaps', label: 'audit:claims', effort: 'high' }
    )
  : null

// Deterministic. An agent never arbitrates which claims survive — and the
// audit's verdicts are applied ONLY to agent facts. A verdict returned against
// something the requester said is discarded unread.
const audited = (audit ? audit.audited : []).filter(a => !touchesGiven(a.claim))
// Match on the NORMALIZED claim, never the raw string. The audit agent re-emits
// claim text as free-form output, so a trailing period is enough to make a raw
// `===` miss — and a missed drop means an unsourceable claim sails into the
// permitted set while the evidence record simultaneously lists it as forbidden.
const auditByClaim = new Map(audited.map(a => [norm(a.claim), a]))
const droppedClaims = audited.filter(a => a.verdict === 'unsourceable' || a.verdict === 'stale')
const droppedSet = new Set(droppedClaims.map(a => norm(a.claim)))
const agentClaims = allFacts
  .filter(f => !droppedSet.has(norm(f.claim)))
  .map(f => {
    const a = auditByClaim.get(norm(f.claim))
    return (a && a.verdict === 'overstated' && a.safeRewording)
      ? { claim: a.safeRewording, source: f.source, origin: 'agent', note: `narrowed from "${f.claim}" — the source did not support the stronger version` }
      : { ...f, origin: 'agent' }
  })
const reworded = audited.filter(a => a.verdict === 'overstated')

// The permitted set. Givens first: they are established, and putting them at the
// head of every prompt makes it obvious they are not up for debate.
const claims = [...userClaims, ...agentClaims]
if (droppedClaims.length || reworded.length) {
  log(`claim audit (agent facts only): ${droppedClaims.length} dropped, ${reworded.length} narrowed`)
}
log(`research: ${research.length} lenses · ${allFacts.length} agent facts · ${agentClaims.length} survived the audit · ${userClaims.length} givens carried untouched · ${claims.length} claims available · ${constraints.length} constraints · ${stillUnread.length} unread`)

// ---------------------------------------------------------------- 3. angles
// Three independent postures, generated blind to each other. One attempt
// iterated is worse than three attempts judged when the solution space is
// this wide — and the planner does the judging, so no separate judge agent.
phase('Angles')
const ANGLE_BASE = `Piece: ${PIECE}
Surface: ${SURFACE}${AUDIENCE ? `\nAudience: ${AUDIENCE}` : ''}

CLAIMS YOU MAY USE. This is the complete set. A claim that is not on this list does not
exist for the purposes of this piece. Entries marked origin "user" were stated by the
requester and are established fact here — build on them, never hedge them, never add
"reportedly" or "according to", never ask them to be softened:
${JSON.stringify(claims)}

CONSTRAINTS from research (voice, market, surface law, what the product cannot claim):
${JSON.stringify(constraints)}

${intake.publishedBaseline.exists ? `Currently published here:\n"""${(intake.publishedBaseline.verbatim || '').slice(0, 800)}"""\n` : ''}
Rules for every angle:
- The promise must rest on at least one claim from the list above, named in claimsUsed.
- Test it: could a named competitor publish your headline verbatim without lying? If yes,
  set competitorCanSayThis:true and say why you could not do better. That is a failing grade,
  not a formatting field.
- Name the objection that actually kills this decision, and answer it with a claim from the list.
- ${STYLE_INSTRUCTIONS}
- No superlatives you cannot source.`

const ANGLE_POSTURES = [
  `Posture: PROBLEM FIRST. Open on the reader's current failing situation and the cost of
leaving it alone. The product arrives late, as the resolution. This posture wins when the
reader does not yet know they have a problem worth paying to fix. It fails when the pain is
already obvious — then it reads as condescending. Say which case this is.`,
  `Posture: OUTCOME FIRST. Open on the specific after-state, concrete enough to picture, and
back it immediately with proof from the claims list. No setup, no scene-setting. This posture
wins when the reader is already shopping and comparing. It fails when the outcome is not
credible without context — if that is the case here, say so rather than forcing it.`,
  `Posture: WEDGE. Find the one true thing only this product can say, and build the whole
piece on it, even if it is smaller than the full pitch. This posture wins when the category is
crowded and every rival page reads the same. It fails when the wedge is real but nobody cares —
so name who specifically cares, and what they were doing instead.`,
]

const angles = (await parallel(ANGLE_POSTURES.slice(0, AGENT_BUDGET.angles).map((p, i) => () => agent(
  `${ANGLE_BASE}\n\n${p}`,
  { label: `angle:${i + 1}`, phase: 'Angles', schema: ANGLE, effort: 'high' }
)))).filter(Boolean)

const ownable = angles.filter(a => !a.competitorCanSayThis)
log(`${angles.length} angles · ${ownable.length} a competitor could not publish verbatim`)

// --------------------------------------------------------------- 4. outline
phase('Outline')
let plan = await agent(
  `Piece: ${PIECE}
Surface: ${SURFACE}${AUDIENCE ? `\nAudience: ${AUDIENCE}` : ''}
${BUDGET ? `Total word budget: ${BUDGET}` : ''}
Surface law (hard limits): ${JSON.stringify(intake.surfaceLaw)}
Protected verbatim — these strings must appear byte-exact somewhere in the piece: ${JSON.stringify(protectedVerbatim)}

THREE ANGLES, generated independently:
${JSON.stringify(angles)}

CLAIMS YOU MAY ASSIGN. Complete and closed. Anything not here cannot be said:
${JSON.stringify(claims)}

CONSTRAINTS: ${JSON.stringify(constraints)}
Sources never read — if a section you write depends on one, that section is underspecified:
${JSON.stringify(stillUnread)}

You are the PLANNER. First judge the three angles, then produce a section map.

Judging: pick the one that wins for THIS audience on THIS surface, and graft the best
element from the runners-up into it — a better objection answer, a sharper proof, a
headline line. An angle whose competitorCanSayThis is true starts at a disadvantage and
needs a stated reason to win anyway. Put the reasoning in angle.why and the borrowed
element in angle.grafted.

Then the section map. Hard rules:
- Each section owns exactly ONE message. No two sections may make the same point — a
  repeated point is a planning bug, and it reads as padding.
- A section may only assert claims listed in its "cites", and every entry there must be
  a claim from the list above, quoted exactly. This is what stops a writer improvising a
  number under deadline.
- Every protected verbatim string is assigned to exactly one section's mustSayVerbatim.
- Word budgets sum to the total budget or below${BUDGET ? ` (${BUDGET})` : ''}. Surface limits are law.
- Acceptance is a question a reader of ONLY that section can answer. Never "sets the tone".
- Tier honestly: mechanical (the claim writes itself), craft (needs rhythm and word choice),
  judgment (the objection answer, the price section, anything a lawyer or a skeptic reads).
- Prefer 3-5 sections. Seven is the ceiling and it is rarely right.`,
  { schema: PLAN, phase: 'Outline', effort: 'high' }
)

if (!plan) throw new Error('Planner returned nothing — no section map, nothing to write. Stop.')

// RED TEAM the section map BEFORE any writer opens a document. Cheapest
// adversary in the DAG: one agent here can void a dozen downstream.
const redTeam = await agent(
  `Piece: ${PIECE} (${SURFACE})${AUDIENCE ? `\nAudience: ${AUDIENCE}` : ''}
Chosen angle: ${JSON.stringify(plan.angle)}
Section map: ${JSON.stringify(plan.sections)}
Claims available: ${JSON.stringify(claims)}
${intake.publishedBaseline.exists ? `Currently published:\n"""${(intake.publishedBaseline.verbatim || '').slice(0, 800)}"""` : ''}

You are attacking this outline. Assume it ships and does nothing — write why.

- Does the piece answer the killer objection anywhere, or did it get planned out?
- Does any section have a job it cannot do with only the claims it cites?
- Is a section tiered "mechanical" when it is actually the paragraph a skeptic reads twice?
- Does the reader learn what to DO, and is that action reachable on this surface?
- Two sections that both "build credibility" are one section. Name any pair like that.
- Does the opening earn the second line, given what is already published here?
- Is the whole piece just the currently published copy rearranged? That is fatal.

"fatal" means: if a writer starts on this, the words are wasted. Ground every objection in
the actual outline and the actual claims. If the outline is sound, return an empty array —
you are not required to find something, and a noise objection costs a full replan.`,
  { label: 'redteam:outline', phase: 'Outline', schema: REDTEAM, effort: 'high' }
)

let objections = redTeam ? redTeam.objections : []
const fatal = objections.filter(o => o.severity === 'fatal')
const serious = objections.filter(o => o.severity === 'serious')

// Exactly one revision round. A plan/critique loop with no bound never converges.
if (fatal.length || serious.length >= 2) {
  log(`red team: ${fatal.length} fatal, ${serious.length} serious — one revision round`)
  const revised = await agent(
    `Your section map was red-teamed and did not survive. Revise it.

Original: ${JSON.stringify(plan)}
Objections: ${JSON.stringify([...fatal, ...serious])}
Claims available (unchanged, still closed): ${JSON.stringify(claims)}
Protected verbatim: ${JSON.stringify(protectedVerbatim)}

Address every fatal objection. You may merge sections, re-tier them, cut one, or change the
angle — but do not answer an objection by deleting the work it applies to. If an objection is
simply wrong, keep your structure and say why in that section's acceptance criterion so it
surfaces at review instead of after publication. Same hard rules: one message per section,
cites drawn only from the claim list, every protected string assigned once, budgets hold.`,
    { schema: PLAN, phase: 'Outline', effort: 'high' }
  )
  if (revised) plan = revised
  objections = objections.map(o => ({ ...o, status: 'sent to revision' }))
} else if (objections.length) {
  log(`red team: ${objections.length} noted objection(s), proceeding — carried to handoff`)
}

// Collision detection is a PURE FUNCTION. Never spend an agent arbitrating
// whether two sections say the same thing or whether a citation is real — a
// deterministic check cannot hallucinate consensus.
const claimSet = new Set(claims.map(c => norm(c.claim)))
const collisions = []

const messageOwner = new Map()
for (const s of plan.sections) {
  const key = norm(s.ownsMessage)
  if (messageOwner.has(key)) collisions.push(`message "${s.ownsMessage}" owned by both ${messageOwner.get(key)} and ${s.name}`)
  else messageOwner.set(key, s.name)

  for (const c of s.cites || []) {
    if (!claimSet.has(norm(c))) collisions.push(`${s.name} cites a claim that did not survive the audit or was never sourced: "${c}"`)
  }
}

// Every protected string must land in exactly one section. Zero is how a legal
// line quietly disappears in a rewrite; two is how it ends up contradicting itself.
for (const v of protectedVerbatim) {
  const owners = plan.sections.filter(s => (s.mustSayVerbatim || []).some(m => norm(m) === norm(v)))
  if (owners.length === 0) collisions.push(`protected string is unassigned and will be lost: "${v}"`)
  if (owners.length > 1) collisions.push(`protected string assigned to ${owners.length} sections (${owners.map(o => o.name).join(', ')}): "${v}"`)
}

const plannedWords = plan.sections.reduce((n, s) => n + (Number(s.wordBudget) || 0), 0)
if (BUDGET && plannedWords > BUDGET * 1.1) collisions.push(`section budgets total ${plannedWords} against a ${BUDGET} word budget`)

if (collisions.length) {
  log(`HALT: section map has ${collisions.length} collision(s) — ${collisions.join(' | ')}`)
  return { halted: true, reason: 'section map collision', collisions, plan, claims, droppedClaims }
}
log(`${plan.sections.length} sections, ${plannedWords} words planned: ${plan.sections.map(s => `${s.name}[${s.tier}]`).join(', ')}`)

// ----------------------------------------------------------------- 5. draft
// Disjoint writers. A section writer sees the JOBS of its neighbours so
// transitions are possible, and never their TEXT — shared prose is how five
// agents converge on the same three metaphors.
phase('Draft')
const EFFORT = { mechanical: 'low', craft: 'medium', judgment: 'high' }
const voiceRules = constraints.filter(c => /voice|tone|sentence|word|phrase|em dash|punctuation|never say|avoid/i.test(c.rule))

const drafted = (await parallel(plan.sections.map((s, i) => () => agent(
  `Piece: ${PIECE} (${SURFACE})${AUDIENCE ? `\nAudience: ${AUDIENCE}` : ''}
Angle the whole piece is built on: ${JSON.stringify(plan.angle)}

YOUR SECTION: ${s.name}
Its job: ${s.job}
The ONE message it owns: ${s.ownsMessage}
Acceptance — a reader of only this section can answer this: ${s.acceptance}
Word budget: ${s.wordBudget}
${(s.mustSayVerbatim || []).length ? `Must appear BYTE-EXACT in your text: ${JSON.stringify((s.mustSayVerbatim || []).map(m => protectedVerbatim.find(v => norm(v) === norm(m)) || m))}` : ''}

CLAIMS YOU MAY ASSERT — this list is closed:
${JSON.stringify((s.cites || []).map(c => claims.find(x => norm(x.claim) === norm(c)) || { claim: c }))}

Anything else is off limits. If your section needs a fact that is not on that list — a
number, a name, a customer result, a date — write [AUTHOR: supply X] inline and list it in
placeholders. Never invent the specific. An invented number is the failure this entire
workflow exists to prevent.

The sections around you, so your transitions work. Do not write their material:
${JSON.stringify(plan.sections.filter((_, j) => j !== i).map(x => ({ name: x.name, job: x.job, owns: x.ownsMessage })))}

VOICE — measured from this brand's shipped copy:
${JSON.stringify(voiceRules)}

${STYLE_INSTRUCTIONS}
Write concrete actions supported by the permitted claims, with varied sentence lengths.
The later Suede Slop Stop pass owns pattern cleanup; do not force word substitutions
that alter technical meaning, source wording, or the supplied voice.

Return only the prose in "text". No headings-about-headings, no commentary, no "in this section".

Also return:
- claimsUsed: every claim from your list that your text actually asserts.
- placeholders: every [AUTHOR: supply X] you had to leave, verbatim.
- state: "done" if the section meets its acceptance criterion; "done-with-concerns" if it
  does but you had to leave a placeholder or stretch the word budget; "needs-context" if the
  section map did not give you enough to write it; "blocked" if you cannot write it without
  material that belongs to another section. Never return "done" for a section you could not
  finish — a stalled section stops the run's verdict, and a false "done" ships a hole.`,
  { label: `write:${s.name}`, phase: 'Draft', schema: SECTION, effort: EFFORT[s.tier] || 'medium' }
))))

const sections = plan.sections.map((s, i) => ({ section: s, out: drafted[i] }))
const stalled = sections.filter(x => !x.out || (x.out.state !== 'done' && x.out.state !== 'done-with-concerns'))
const placeholders = sections.flatMap(x => [
  ...((x.out && x.out.placeholders) || []),
  ...(((x.out && x.out.text) || '').match(/\[AUTHOR[^\]]*\]/gi) || []),
])
if (stalled.length) log(`${stalled.length} section(s) stalled: ${stalled.map(x => `${x.section.name}(${x.out ? x.out.state : 'no return'})`).join(', ')}`)
if (placeholders.length) log(`${placeholders.length} author placeholder(s) left by writers`)

// -------------------------------------------------------------- 6. assemble
// A genuine barrier: a piece is read end to end, and repetition between two
// sections is invisible to either writer.
phase('Assemble')
const assembled = await agent(
  `Assemble these sections into one ${SURFACE}. You are the only agent that sees all of it.

Angle: ${JSON.stringify(plan.angle)}
Order and jobs: ${JSON.stringify(plan.sections.map(s => ({ name: s.name, job: s.job, owns: s.ownsMessage })))}
${BUDGET ? `Total word budget: ${BUDGET}` : ''}
Surface law: ${JSON.stringify(intake.surfaceLaw)}
Must survive byte-exact: ${JSON.stringify(protectedVerbatim)}
${STYLE_INSTRUCTIONS}

Sections:
${sections.map(x => `--- ${x.section.name} ---\n${(x.out && x.out.text) || '[SECTION MISSING — writer returned ' + ((x.out && x.out.state) || 'nothing') + ']'}`).join('\n\n')}

Your job:
- Write the transitions. Sections were written blind to each other and will not join themselves.
- Cut repetition. Where two sections reach for the same phrase, image, or statistic, the later
  one loses it. Report what you cut in notes.
- One voice throughout. A reader must not be able to feel the seams.
- Enforce the budget and the surface limits. Cutting is preferred to compressing into mush.
- Preserve every [AUTHOR: supply X] placeholder exactly as written. They are the record of
  what nobody could source; silently smoothing one away is a fabrication.
- Preserve every protected string byte-exact.
- Change no fact and no number. You are joining, not rewriting.

Return the full assembled text in "text" and an honest word count.`,
  { schema: ASSEMBLED, phase: 'Assemble', effort: 'medium' }
)

if (!assembled || !assembled.text) throw new Error('Assembly returned no text — nothing to review. Stop.')
let text = assembled.text
log(`assembled ${assembled.wordCount} words`)

// ---------------------------------------------------------------- 7. review
// Four lenses on the WHOLE piece. Each asks a different question and would
// miss what the others catch.
phase('Review')
const REVIEW_BASE = `Piece: ${PIECE} (${SURFACE})${AUDIENCE ? `\nAudience: ${AUDIENCE}` : ''}
Promise it makes: ${plan.angle.promise}

DRAFT:
"""
${text}
"""

Anchor every finding to an exact quoted string from the draft — that quote is the only
address a verifier can go check. Report only defects you can point at. No style preferences,
no "consider adding". If the piece is clean on your lens, return an empty findings array.`

const REVIEW_LENSES = [
  {
    key: 'stranger',
    effort: 'medium',
    prompt: `Lens: COLD READ. You have never heard of this product. Read once, at normal speed.
Then answer, before re-reading: what is it, who is it for, what do I do next, and why now?
Any of those you cannot answer is a finding, quoted at the line where you needed the answer
and did not get it. Also report every place you stalled, re-read, or had to hold two things
in your head at once. Jargon you had to decode is a finding. A sentence you had to read
twice is a finding even if it is technically correct.`,
  },
  {
    key: 'claim',
    effort: 'high',
    prompt: `Lens: ASSERTION AUDIT. Every factual assertion in this draft, tested against the permitted set.

OUT OF SCOPE, absolutely. These were stated by the requester. They are established, they are
not evidence you get to weigh, and a finding against one of them will be discarded before it
reaches a verifier. Do not quote them, do not ask for a source, do not call them overstated:
${JSON.stringify(givenClaims.map(c => c.claim))}

IN SCOPE — claims that came from research agents and passed the audit:
${JSON.stringify(agentClaims)}
Claims DROPPED by the audit, which must not appear in any form: ${JSON.stringify(droppedClaims.map(d => ({ claim: d.claim, why: d.why })))}
${intake.publishedBaseline.exists ? `Currently published on this surface — an agent-sourced claim that contradicts it without saying so is a finding:\n"""${(intake.publishedBaseline.verbatim || '').slice(0, 1000)}"""` : ''}

Walk the draft sentence by sentence. For each in-scope assertion: is it on the permitted
list, and does the draft state it at the same strength the source supports? A claim that
drifted stronger during writing is a blocker. Watch for: numbers without units, comparatives
without a baseline, superlatives, implied guarantees, a capability described as shipped that
is behind a flag, and a dropped claim smuggled back in as an implication. An invented
specific that should have been [AUTHOR: supply X] is a blocker.`,
  },
  {
    key: 'conversion',
    effort: 'medium',
    prompt: `Lens: DOES IT EARN THE NEXT ACTION. The reader owes this piece nothing.
Is the promise in the first two lines concrete enough to be worth the third? Is the killer
objection answered where the reader raises it, not three sections later? Is proof adjacent to
the claim it supports, or stranded at the bottom? Is the call to action a specific thing a
specific person does next, and is it reachable from this surface? Is there a paragraph that
could be deleted with no loss — quote it. Is anything here a sentence a competitor could
publish verbatim? Quote that too.`,
  },
  {
    key: 'slop',
    effort: 'medium',
    prompt: `Lens: SLOP AND VOICE. Use Suede Slop Stop in findings-only mode.
Load the canonical suede-deslop/SKILL.md and its references/kill-list.md from the installed
Suede pack (repository paths: skills/suede-deslop/SKILL.md and
skills/suede-deslop/references/kill-list.md). Apply that method; do not invent a substitute
if it is unavailable. Report the missing reference as a review limitation.
Quote actual weaknesses in context, distinguish clear defects from voice judgment calls,
and leave the draft unchanged. Return this workflow's findings schema.
${STYLE_INSTRUCTIONS}

Against this brand's measured voice: ${JSON.stringify(voiceRules)}
And the phrases the market has worn out, per the market lens: ${JSON.stringify(constraints.filter(c => /competitor|rival|everyone|table stakes|category/i.test(c.rule)))}

Severity: style findings are major or minor. A factual objection requires source evidence
and belongs to the assertion audit; sounding generated is not evidence of fabrication.`,
  },
]

const reviews = (await parallel(REVIEW_LENSES.map(l => () => agent(
  `${REVIEW_BASE}\n\n${l.prompt}`,
  { label: `review:${l.key}`, phase: 'Review', schema: FINDINGS, effort: l.effort }
)))).filter(Boolean)

// A finding aimed at something the requester said is dropped here, before any
// verifier is spent on it. This is a pure function on purpose: a review lens
// that was told to stay out of scope and wandered in anyway does not get to
// turn the requester's own statement into a caveat by being persuasive.
const rawFindings = reviews.flatMap(r => r.findings)
const findings = rawFindings.filter(f => !touchesGiven(f.quote, f.claim))
const outOfScopeFindings = rawFindings.filter(f => touchesGiven(f.quote, f.claim))
if (outOfScopeFindings.length) log(`${outOfScopeFindings.length} finding(s) targeted a claim the requester supplied — discarded unverified, as scoped`)

const minor = findings.filter(f => f.severity === 'minor')
const toRefute = findings.filter(f => f.severity !== 'minor')
const REFUTE_CAP = AGENT_BUDGET.refuteCap
const refuting = toRefute.slice(0, REFUTE_CAP)
if (toRefute.length > REFUTE_CAP) {
  log(`${toRefute.length} blocker/major findings, refuting the first ${REFUTE_CAP}; the remaining ${toRefute.length - REFUTE_CAP} ride to the handoff as unverified caveats`)
}

// ---------------------------------------------------------------- 8. refute
// Two independent verifiers per finding, refute by default. Both must fail to
// refute for it to survive. A plausible-sounding review note that cannot be
// reproduced is worse than no note: it costs a rewrite of a line that was fine.
phase('Refute')
const judged = refuting.length
  ? await parallel(refuting.map(f => () =>
      parallel([0, 1].map(i => () => agent(
        `Draft under review:
"""
${text}
"""

You are verifier #${i + 1} of 2 on ONE finding. Claim against the draft: ${f.claim}
Quoted line: "${f.quote}"
Alleged failure: ${f.whyItFails}
Severity claimed: ${f.severity}

Your job is to REFUTE this. Find the quoted string in the draft and read what surrounds it.

OUT OF SCOPE AT EVERY SEVERITY. The requester stated these themselves. They are established.
If this finding turns out to be aimed at one of them, or at a line carrying one, it is
REFUTED — no further analysis, whatever the finding's stated severity:
${JSON.stringify(givenClaims.map(c => c.claim))}
${f.severity === 'blocker' ? `If this is a factual assertion about something else, verify it against the permitted set: ${JSON.stringify(agentClaims)}` : ''}
Refute it if: the quote is not actually in the draft, the surrounding text already handles
the objection, the reader the finding imagines is not this piece's audience, or the "failure"
is a style preference wearing a severity label. Default to refuted:true when uncertain.
Sustain it only when you can state the concrete reader or the concrete source that makes it wrong.`,
        { label: `refute:${f.quote.slice(0, 24)}`, phase: 'Refute', schema: VERDICT, effort: 'medium' }
      ))).then(vs => {
        const votes = vs.filter(Boolean)
        // Two verifiers, both must fail to refute. Unanimity, not majority:
        // rewriting a line that was fine has a real cost in a short piece.
        const survives = votes.length === 2 && votes.every(v => !v.refuted)
        return survives ? { ...f, evidence: votes[0].why } : null
      })
    ))
  : []

// Second deterministic pass. A verifier that sustained a finding against a given
// anyway does not get to hand it to the reviser — belt and braces, because the
// reviser is the one stage that would rewrite the requester's own words.
const lateOutOfScope = judged.filter(Boolean).filter(f => touchesGiven(f.quote, f.claim))
outOfScopeFindings.push(...lateOutOfScope)
const confirmed = judged.filter(Boolean).filter(f => !touchesGiven(f.quote, f.claim))
const blockers = confirmed.filter(f => f.severity === 'blocker')
log(`${findings.length} findings · ${confirmed.length} survived refutation (${blockers.length} blockers) · ${minor.length} minor carried as caveats`)

// ---------------------------------------------------------------- 9. polish
// One reviser, not one per blocker. Prose has no file-level disjointness —
// parallel editors of a single string produce a merge conflict with no merge tool.
phase('Polish')
if (blockers.length) {
  const fixed = await agent(
    `Revise this draft to resolve every confirmed blocker. Nothing else.

DRAFT:
"""
${text}
"""

CONFIRMED BLOCKERS — each survived two adversarial verifiers:
${JSON.stringify(blockers.map(b => ({ quote: b.quote, problem: b.whyItFails, suggestedFix: b.fix, evidence: b.evidence })))}

Claims you may assert (unchanged and still closed): ${JSON.stringify(claims)}
Protected strings that must survive byte-exact: ${JSON.stringify(protectedVerbatim)}
${STYLE_INSTRUCTIONS}

Minimum viable edit. Do not restructure, do not improve adjacent lines you happen to dislike,
do not resolve an [AUTHOR: supply X] placeholder by inventing the value. If a blocker can only
be fixed by asserting something not on the claims list, replace the line with an
[AUTHOR: supply X] placeholder instead and say so in notes. Return the full revised text.`,
    { schema: ASSEMBLED, phase: 'Polish', label: 'revise:blockers', effort: 'high' }
  )
  if (fixed && fixed.text) text = fixed.text
}

// Deslop runs after the fixes, because a fix written under deadline is exactly
// where the filler comes back.
const deslopped = await agent(
  `Run Suede Slop Stop on this ${SURFACE}. Style only.
Load the canonical suede-deslop/SKILL.md and its references/kill-list.md from the installed
Suede pack (repository paths: skills/suede-deslop/SKILL.md and
skills/suede-deslop/references/kill-list.md). Use that method, not a separate cleanup recipe.
If unavailable, preserve the input, return REVISE with total 0, and name the missing
reference in stillGenerating; do not pretend the pass ran.

"""
${text}
"""

${STYLE_INSTRUCTIONS}
Measured voice: ${JSON.stringify(voiceRules)}
Make the minimum effective edit. Preserve facts, numbers, dates, names, prices, claims,
qualifiers, and all source spans covered by the canonical method. If a style edit would
need a missing specific, leave the factual wording unchanged and report the gap in
stillGenerating. Invent no actor, metric, anecdote, customer, quote, or experience.
Leave every existing [AUTHOR: supply X] placeholder exactly as it is.
Preserve these byte-exact:
${JSON.stringify(protectedVerbatim)}

Score out of 50: directness, rhythm, trust, authenticity, density, 1-10 each. Below 35 is
REVISE — say what is still generating the score and why it cannot be resolved without the author.
Return the cleaned prose in "text", and in "removed" the counts by category: filler phrases,
structural patterns, passive-to-active, vague declaratives, em dashes.`,
  { schema: DESLOP, phase: 'Polish', label: 'deslop', effort: 'medium' }
)

if (deslopped && deslopped.text) text = deslopped.text
if (deslopped) log(`deslop ${deslopped.total}/50 — ${deslopped.verdict}`)

// Graphic spec and channel package both need the FINAL text, and neither needs
// the other. The graphic builder writes copy too: the words on an image are read
// more than the body, and they obey every rule the body obeys.
const [graphic, pack] = await parallel([
  () => agent(
    `Piece: ${PIECE} (${SURFACE})
Angle: ${JSON.stringify(plan.angle)}
Sections: ${JSON.stringify(plan.sections.map(s => ({ name: s.name, owns: s.ownsMessage })))}
Surface law: ${JSON.stringify(intake.surfaceLaw)}

FINAL COPY:
"""
${text}
"""

You are the GRAPHIC BUILDER. You do not generate images. You produce the spec a designer or
an image model executes, and you write the words that appear in them.

For each visual this piece actually needs — and "none" is a legitimate answer for a docs page:
- concept: one sentence a designer could execute without asking a question
- onImageText: the exact words on the image. Same voice and active house style as the body;
  it may assert ONLY claims from this list: ${JSON.stringify(claims)}
- aspect: the real ratio and pixel size THIS surface requires, not a generic 16:9
- sourceAsset: if a real screenshot or photo already exists, its path. A real product
  screenshot beats a generated illustration on every surface where the product is the subject.
- altText: describes the information the image carries, not "image of a dashboard"
- buildWith: screenshot | existing asset | suede-image | media-use | designer

A visual that repeats a section's sentence in a box is not a visual. Cut it.
${STYLE_INSTRUCTIONS}

THE SUEDE MARK, hard rule: never redraw, trace, typeset, recolor, distort, or generate a
replacement Suede S. The only permitted mark is the approved asset at
docs/assets/suede-ai-logo-transparent.png (sha256
83a7ee0317e4debe2e7b076c20ba067feb76a587f9e829dc6310ae4be4b44dfa). Check whether that file
is present. If the piece needs the mark and the approved file is not available, set
approvedAssetPresent:false and specify the visual WITHOUT the mark, noting that the approved
asset must be supplied. Do not improvise one. suede-skill-icon.png is a Passport icon and is
not the brand mark.`,
    { schema: GRAPHIC, phase: 'Polish', label: 'graphic-spec', effort: 'medium' }
  ),
  () => agent(
    `Piece: ${PIECE} (${SURFACE})
Angle: ${JSON.stringify(plan.angle)}
Claims available: ${JSON.stringify(claims)}

FINAL COPY:
"""
${text}
"""

SURFACE LAW — every field and its hard limit: ${JSON.stringify(intake.surfaceLaw)}

You are the CHANNEL PACKAGE. Produce every field this ${SURFACE} needs around the body copy
and count the characters of each one yourself. Typically: headline, subhead, meta title, meta
description, OG title, OG description, subject line, preview text, CTA button string, and any
platform-specific field the surface law names.

Rules:
- Every field draws only on claims from the list. No new promises in a meta description.
- Count characters honestly and report chars against limit with a real pass/fail. A field
  over its limit gets truncated by the platform, usually mid-word, usually in the part that
  mattered.
- Three headline variants, genuinely different in approach rather than three rewordings.
- The CTA names the action and what happens after it.
- Same voice as the body. ${STYLE_INSTRUCTIONS}`,
    { schema: PACKAGE, phase: 'Polish', label: 'channel-package', effort: 'medium' }
  ),
])

// ----------------------------------------------------------------- 10. gate
// Deterministic checks first. These cannot be argued with, hallucinated, or
// talked out of a failure, so no agent gets to run them.
phase('Gate')
// The bracket form is matched loosely on purpose: a writer that returns
// "[AUTHOR supply X]" or "[Author — supply X]" left a placeholder just as
// surely as one that used the canonical colon, and a gate that misses it
// reports a fabrication as finished copy.
const PLACEHOLDER = /\[AUTHOR[^\]]*\]/gi
const openPlaceholders = text.match(PLACEHOLDER) || []
// A placeholder that existed at draft time and is gone now was resolved by the
// assembler or the deslop pass — both of which are forbidden from doing that,
// because the only way to resolve one without the author is to invent the value.
// Regexing the final text alone cannot see this; it needs the draft-time count.
// Compare the STRINGS, not the counts. A writer that listed one placeholder twice,
// or two sections whose identical placeholder legitimately collapsed during
// assembly, are not fabrications — and a count subtraction calls them both one.
const finalNorm = norm(text)
const vanishedList = [...new Set(placeholders.map(norm).filter(Boolean))].filter(p => !finalNorm.includes(p))
const vanishedPlaceholders = vanishedList.length
const missingVerbatim = protectedVerbatim.filter(v => !text.includes(v))
// Count only em dashes the WRITERS introduced. One inside a protected string or a
// given is the requester's own punctuation, and gating on it produces a run that
// can never pass: the same string is also required to appear byte-exact.
const requesterText = [...protectedVerbatim, ...userClaims.map(c => c.claim)].filter(Boolean)
let scrubbed = text
for (const r of requesterText) scrubbed = scrubbed.split(r).join(' ')
const emDashes = (scrubbed.match(/—/g) || []).length
const emDashViolations = EM_DASH_POLICY === 'avoid' ? emDashes : 0
const finalWords = text.trim().split(/\s+/).filter(Boolean).length
const overBudget = BUDGET ? finalWords > BUDGET * 1.1 : false
const failedFields = ((pack && pack.fields) || []).filter(f => !f.passes)
const mechanical = {
  openPlaceholders: openPlaceholders.length,
  vanishedPlaceholders,
  vanishedPlaceholderText: vanishedList,
  missingProtectedStrings: missingVerbatim,
  emDashes,
  emDashPolicy: EM_DASH_POLICY,
  emDashViolations,
  words: finalWords,
  budget: BUDGET,
  agentBudget: AGENT_BUDGET_NAME,
  overBudget,
  fieldsOverLimit: failedFields.map(f => `${f.field} ${f.chars}/${f.limit}`),
  stalledSections: stalled.map(x => x.section.name),
  channelPackageReturned: !!pack,
  deslopScore: deslopped ? deslopped.total : null,
}
log(`mechanical: ${openPlaceholders.length} placeholders${vanishedPlaceholders ? ` (${vanishedPlaceholders} vanished since draft)` : ''} · ${missingVerbatim.length} protected strings missing · ${emDashes} em dashes · ${finalWords} words${BUDGET ? `/${BUDGET}` : ''}${overBudget ? ' OVER' : ''} · ${failedFields.length} fields over limit · ${stalled.length} stalled sections`)

const readiness = await agent(
  `Piece: ${PIECE} (${SURFACE})${LIVE ? `\nLive surface: ${LIVE}` : ''}

FINAL COPY:
"""
${text}
"""

Channel package: ${JSON.stringify(pack)}
${intake.publishedBaseline.exists ? `What is published on this surface RIGHT NOW:\n"""${(intake.publishedBaseline.verbatim || '').slice(0, 1200)}"""` : 'Nothing is currently published on this surface.'}

OUT OF SCOPE. The requester stated these themselves. They are established. Do not verify
them, do not spot-check them, do not raise a risk against them, and do not report them as
drift if a page somewhere disagrees — the requester knows their own product better than a
stale page does. If you catch yourself building a case against one, stop:
${JSON.stringify(givenClaims.map(c => c.claim))}

IN SCOPE — claims that came from research agents: ${JSON.stringify(agentClaims)}
Claims dropped by the audit, which must not appear: ${JSON.stringify(droppedClaims.map(d => d.claim))}
Mechanical check results: ${JSON.stringify(mechanical)}

You are the PUBLISH-READINESS VERIFIER. READ-ONLY. You may fetch urls, read files, and run
read-only git and gh commands. You may NOT publish, post, send, commit, deploy, or edit any
live surface. If answering a question would require a mutation, report it as unverifiable.

Check, with evidence:
1. DRIFT, agent-sourced claims only. Does an in-scope claim contradict what is currently
   published elsewhere — this surface, the pricing page, the docs, the README, the store
   listing? Quote both sides.
2. TRUTH AT THE SOURCE, agent-sourced claims only. Spot-check the three most load-bearing
   in-scope claims against their sources one more time. This is the last read before a
   stranger sees machine-generated text.
3. RIGHTS AND MARKS, third-party material only. Competitor names, trademarks, reviews you
   found published elsewhere, screenshots containing another user's data, borrowed phrasing.
   Name what needs permission. A customer result or quote the REQUESTER supplied is out of
   scope here too: do not file a permissions risk that is really a doubt about their claim
   wearing a rights label. If they told you it, they have the relation to the customer.
4. REVERSIBILITY. If this is wrong after publication, what does the undo cost — edit the page,
   repost, issue a correction, or nothing (an email already sent, an app store listing in
   review, a syndicated post). Rate it honestly.

Every risk carries evidence: a quoted line from the draft plus the url, file:line, or command
output that contradicts it. "Probably fine" is not evidence. Readback is the deliverable even
when you find zero risks: state what the live surface says right now, so someone can diff it
after publication and know whether this piece did what it claimed.`,
  { schema: READINESS, phase: 'Gate', effort: 'high' }
)

// The verdict is computed, not argued. It is advice attached to the work: it
// changes what gets reported, never what the run produced. This workflow
// writes a draft file and publishes nothing in any case.
const risks = (readiness && readiness.risks) || []
const riskBlockers = risks.filter(r => r.severity === 'blocker')
// Every threshold this skill publishes is enforced here. A gate that is computed
// and reported but never scored is a comment, and a dead section writer or a
// missing channel package must not be indistinguishable from a passing one.
const hardMechanical =
  openPlaceholders.length > 0 ||
  vanishedPlaceholders > 0 ||
  missingVerbatim.length > 0 ||
  failedFields.length > 0 ||
  emDashViolations > 0 ||
  overBudget ||
  stalled.length > 0 ||
  !pack ||
  !deslopped
const copyVerdict = (riskBlockers.length || hardMechanical)
  ? 'hold'
  : (risks.some(r => r.severity === 'major') || confirmed.length || (deslopped && deslopped.total < 35))
    ? 'ship-with-caveats'
    : 'ship'
log(`readiness: ${risks.length} risks · ${riskBlockers.length} blockers · verdict ${copyVerdict.toUpperCase()} (advisory)`)

// The one case that goes to a human immediately rather than into a report:
// something already published, right now, that is wrong independent of this draft.
const liveExposure = risks.filter(r =>
  r.severity === 'blocker' && /already published|currently live|live page|in production|shipped copy/i.test(r.evidence))
if (liveExposure.length) {
  log(`ATTENTION — a problem observed in ALREADY PUBLISHED copy, independent of this draft: ${liveExposure.map(r => r.risk).join(' | ')}`)
}

// -------------------------------------------------------------- 11. handoff
phase('Handoff')
const handoff = await agent(
  `Write the deliverable and the evidence record for this run, then report what you wrote.

Write exactly two files into ${intake.outDir} (create the directory if needed; never write
into an already-published file):
1. ${intake.slug}.md — the final copy, and nothing else. No metadata header, no commentary.
   The body is exactly this, byte for byte:
"""
${text}
"""
2. ${intake.slug}.evidence.md — the record below.

The evidence record uses exactly these headings: Piece, Angle, Copy, Claims, Verification,
Publish Risk, Status, Caveats, Next.

Piece: ${PIECE} · surface ${SURFACE}${AUDIENCE ? ` · audience ${AUDIENCE}` : ''}
Angle chosen and why: ${JSON.stringify(plan.angle)}
Sections: ${JSON.stringify(plan.sections.map(s => ({ name: s.name, owns: s.ownsMessage, words: s.wordBudget, tier: s.tier })))}
Stalled sections: ${JSON.stringify(stalled.map(x => ({ section: x.section.name, state: x.out && x.out.state, notes: x.out && x.out.notes })))}
Channel package: ${JSON.stringify(pack)}
Graphic spec: ${JSON.stringify(graphic)}

Claims given by the requester and carried as stated. These were not audited and are not
open questions; list them under Claims as given, with no hedging language and no "unverified"
label: ${JSON.stringify(givenClaims.map(c => c.claim))}
Claims from research agents, each with its source: ${JSON.stringify(agentClaims)}
Agent claims DROPPED by the audit — asserted by a research lens and did not survive; anyone
editing this copy later must not put them back: ${JSON.stringify(droppedClaims)}
Agent claims NARROWED because the source supported something weaker: ${JSON.stringify(reworded)}
Research facts removed before the audit because they restated a given: ${JSON.stringify(restated.map(f => f.claim))}
Review findings discarded because they targeted a claim the requester supplied. Report the
COUNT under Caveats so a reader can see how much of the review was scoped out, and say plainly
that these were not verified either way: ${JSON.stringify(outOfScopeFindings.map(f => ({ quote: f.quote, claim: f.claim, severity: f.severity })))}
Open [AUTHOR: supply X] placeholders — the copy is not publishable until a human fills these:
${JSON.stringify(openPlaceholders)}

Mechanical checks: ${JSON.stringify(mechanical)}
Deslop: ${JSON.stringify(deslopped ? { total: deslopped.total, verdict: deslopped.verdict, removed: deslopped.removed, stillGenerating: deslopped.stillGenerating } : null)}
Confirmed findings that survived two verifiers: ${JSON.stringify(confirmed)}
Minor findings left unfixed: ${JSON.stringify(minor)}
Outline objections from the red team: ${JSON.stringify(objections)}
Publish readiness (${copyVerdict}): ${JSON.stringify(readiness)}
Sources never read: ${JSON.stringify(stillUnread)}
Advisory hazards from intake, NOT resolved by this run: ${JSON.stringify(intake.hazards.filter(h => !h.blocking))}

Under Publish Risk: the advisory verdict, every blocker with its evidence, what the undo costs
for anything not reversible by an edit, and the live readback so the change is diffable after
publication.

Status must be one of: drafted | reviewed | ready for author | held | blocked. THIS RUN DOES
NOT PUBLISH. Never write "published", "posted", "sent", "live", or "shipped" — those states
require an action nobody has taken here. Open placeholders mean "ready for author" at best,
never "reviewed".

List every unfixed finding under Caveats. Omitting a caveat to make the record look clean is
the failure this section exists to prevent.

Report back the two paths you wrote and the Status line.`,
  { phase: 'Handoff', effort: 'low' }
)

return {
  outDir: intake.outDir,
  deliverable: `${intake.outDir}/${intake.slug}.md`,
  copyVerdict,
  angle: plan.angle,
  sections: plan.sections.map(s => s.name),
  stalled: stalled.map(x => x.section.name),
  words: finalWords,
  mechanical,
  openPlaceholders,
  claims,
  givenClaims: userClaims,
  agentClaims,
  droppedClaims,
  narrowedClaims: reworded,
  findingsDiscardedAsOutOfScope: outOfScopeFindings,
  factsRestatingAGiven: restated.map(f => f.claim),
  confirmedFindings: confirmed,
  minorFindings: minor,
  outlineObjections: objections,
  deslop: deslopped ? { total: deslopped.total, verdict: deslopped.verdict } : null,
  graphic,
  channelPackage: pack,
  readiness,
  unread: stillUnread,
  hazards: intake.hazards,
  handoff,
}
