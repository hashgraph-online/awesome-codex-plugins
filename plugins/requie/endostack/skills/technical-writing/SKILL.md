---
name: technical-writing
description: Write or review technical prose (docs, design RFCs, READMEs, PR bodies, commit messages) against four stacked public standards, then run unslop. Use on /technical-writing or any request to write, edit, or review documentation or a PR or commit message.
disable-model-invocation: true
---

# technical-writing

Apply four layers of public writing guidance, each answering a different question, then pass the result through the `unslop` skill ([../unslop/SKILL.md](../unslop/SKILL.md)), which owns the catalog of AI-writing tells. The layers are:

1. Document type: what kind of document is this? (Diátaxis)
2. Reader address: how do sentences speak to the reader? (Google developer documentation style guide)
3. Statement size: does each sentence carry one thing? (ASD-STE100 Simplified Technical English)
4. Syntax: can a non-native reader misparse it? (Microsoft and other Global English guidance)

The rule wording below is EndoStack's own summary of those sources.

Do not use this skill for product UI strings (follow the product's copy guide), code comments (see the `no-comments` skill, [../no-comments/SKILL.md](../no-comments/SKILL.md)), or casual chat replies.

## Three rules above the layers

1. Delete every word whose removal leaves the meaning unchanged.
2. Prefer the short common word. A longer word stays only if it adds precision.
3. The rules serve the reader. When applying one damages a specific sentence, repair that sentence by other means or keep it as it was. A document that satisfies every rule yet sounds machine-generated still counts as a failure.

## Vocabulary comes from the code

Name things by their identifier, file path, flag, or command, exactly as the repo spells them. Do not paraphrase `retryBudgetMs` as "the retry time allowance". Do not coin jargon; use the words an engineer on the project would say out loud. A named pattern is fine if you define it where it first appears.

When you find a metaphor-jargon word that `unslop` rule U11 lacks, propose it in your reply as a diff against `skills/unslop/SKILL.md` with the plain replacement. Do not edit the unslop skill yourself.

## Rhythm

Rules applied mechanically produce flat text. Check rhythm before you finish.

- Vary sentence length on purpose. Use a short sentence to land a point. Use a longer one when a fact needs its condition or result attached.
- The one-idea rule counts ideas, not words. Split a sentence that carries two ideas. Leave a long sentence alone if it carries one.
- Take a position where the document type allows it. An explanation that weighs tradeoffs ends with a conclusion. Reference stays neutral.
- Prefer a specific consequence to a general warning. "Deleting the lock file makes the next install pick new minor versions" beats "be careful with the lock file".

## Layer 1: pick one document type

Classify the document on two axes. Does it serve doing or understanding? Does the reader meet it while studying or while working? The four answers:

**Tutorial** (doing, studying). You own the learner's success. Open by saying what they will build. Every step produces something visible, starting with the first, and you say what output to expect. Keep explanation to a clause and a link. Use "we" and imperative steps.

**How-to guide** (doing, working). Solves a real user problem, framed as the user's goal rather than a machine operation. Assume competence. Include only actions; link out for background. Branching on what the user wants is fine. Title it with a verb phrase naming the task.

**Reference** (understanding, working). Describes and nothing else: no instructions, no opinions. Give every fact, option, limit and error in full, with no hedging. Organize the page the same way the described thing is organized. Generate it from code where you can.

**Explanation** (understanding, studying). One bounded subject that makes sense away from the product, with a title that reads naturally after an implied "About". Anchor it on a real "why" question: why the design is this way, its history, its constraints, what was rejected. This is the only type that carries opinion.

Never mix types in one document. Split and cross-link. You can apply the same two-axis test to a single sentence to find the one that wandered in from another type.

## Layer 2: address the reader

- Use second person and present tense. Use future tense only for events that really happen later.
- Use active voice that names the actor. Use passive only when nobody knows or cares who acts.
- Write instructions as imperatives and facts as plain statements. Never "the flag should be set"; write "set the flag" or "the flag is set by `init`".
- Put the condition or purpose before the instruction: "To rotate the key, run...".
- Lead with the common case, then the exceptions.
- Sound like a colleague who knows the system. No trendy words, no figures of speech, no "please" inside instructions, and never "simply", "just", "easy", or "quick".
- Do not announce future features. Do not start consecutive sentences with the same word.
- Link text names the destination. Never "click here". Prefer giving the needed context inline to sending the reader away.
- Headings state the point, in sentence case. Task headings are bare verb phrases ("Rotate the signing key"); concept headings are noun phrases. One top-level heading per page. Never skip a heading level.
- Number a list only when its items happen in sequence, and use bullets otherwise. A complete sentence comes before every list. Keep items grammatically parallel.
- Put code, paths, and commands in code font. Put UI labels in bold. Use the serial comma. Do not end a list with "etc."; say up front that the list is partial.

## Layer 3: one statement per sentence

- An instruction sentence holds one instruction. Any other sentence holds one idea.
- Keep instructions to about 20 words and other sentences to about 25.
- Any warning or condition goes ahead of the step it applies to, so the reader sees it before acting.
- Keep articles. "Restart server after update" can be read three ways; "Restart the server after the update" cannot.
- Give each word one meaning and each action one verb for the whole document. If you wrote "remove" for a file, do not switch to "delete" two paragraphs later.
- Write procedure steps as imperatives, not narration ("The user then opens...") or passive statements.
- Use "-ing" forms sparingly. They blur who does what and when.

## Layer 4: syntax a non-native reader cannot misparse

- Put "only", "not", and "just" directly next to the word they limit.
- Break noun stacks. "Cache invalidation retry policy override" becomes "an override for the retry policy that cache invalidation uses".
- Give every pronoun one obvious antecedent. If in doubt, repeat the noun. Never let "this" or "which" point at a whole clause.
- Give every clause its own verb. No gapping ("Alice wrote the parser and Bob the tests").
- Keep "that" after verbs such as ensure, verify, and confirm.
- Repeat the article for each distinct item in a series ("the client, the proxy, and the server").
- Use paired conjunctions to show grouping ("either A or B and C" is ambiguous; "either A, or both B and C" is not).
- End clauses with periods instead of semicolons, and split at a period wherever an em dash would go.
- Make anything in parentheses a complete grammatical unit. No "(s)" plurals.
- No slashes between alternatives. Write "read access, write access, or both".
- Keep one name per concept across the whole document. Do not rename something that did not change.
- No idioms, colloquialisms, Latin abbreviations (e.g., i.e., etc., via as a preposition), or metaphors.

## Voice and repo conventions

- Run the `unslop` skill on every document you write or edit.
- PR bodies and commit messages follow every layer except the document-type choice. A PR body is a summary a reviewer reads in under a minute. Link to logs, commit lists, and metric tables; do not paste them. The opening-a-pr playbook in `tarique-mode` sets the rest of the PR body rules.
- Use real paths in code snippets, and indent them the way the repo's formatter does.
- Every count, file list, or directory tree you quote must be true at the commit that introduces it. Put the command that reproduces it next to it (`git ls-files skills | wc -l`).
- Do not paste secrets, tokens, internal hostnames, or customer data into docs or PR bodies. If an example needs a credential, use an obvious placeholder such as `YOUR_API_KEY` and say where the real value lives.

## A before and after

This draft describes a migration guard:

> It should be noted that, prior to the deployment process being initiated, a verification of the schema migration ordering is performed by the pipeline, which may potentially result in the build being failed in the event that out-of-order migration files are detected, and this check should not be bypassed by developers.

Problems: passive voice hides the actor; "should be noted" and "may potentially" are filler and stacked hedges; the noun stack "schema migration ordering" makes the reader unpack it; "this" points at a whole clause; the script is never named.

Rewrite:

> Before each deploy, CI runs `scripts/check-migration-order.ts`. The script fails the build if any file in `db/migrations/` has a timestamp older than the newest migration already on `main`. Do not skip it with `--no-verify`; rename the file with a current timestamp instead.

Three sentences, each with one idea. The actor (CI), the script, the folder, the failure condition, and the one forbidden workaround are all named, and the reader gets the fix along with the rule.

## Done when

The document has exactly one type; every sentence passes layers 2 to 4 or was left on purpose because a rule made it worse; `unslop` finds nothing; every identifier, path, count, and tree is accurate at the commit; and any proposed U11 additions appear as a diff in your reply.
