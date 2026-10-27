---
name: client-communications-research
description: Use when turning client calls, chats, CRM notes, call recordings, messenger exports, transcripts, or support/sales conversations into an advertising, positioning, objection, FAQ, or customer-language research package.
---

# Client Communications Research

Use this skill when the task is to analyze real client communications and produce conclusions, quotes, objections, audience language, sales insights, ad angles, or positioning.

This skill starts after source acquisition is planned or under way. For amoCRM access and corpus acquisition, use `amocrm-api-control` first. For calls and meetings, first look for a ready transcript or meeting notes from the user's existing tools (meeting recorder, messenger bot, voice-memo transcripts). Start a paid transcription only when no ready transcript exists, and only with the service the user approved. This skill governs the research package and final synthesis boundary.

## Required Inputs

Before synthesis, create or read a compact corpus ledger with:

- source systems and source types: amoCRM notes, calls, recordings, chats, email, messenger exports, telephony exports, support tickets, or files;
- requested date window and actual acquired date window;
- event counts by source type;
- audio file count, transcript count, empty/missing/failed count, and duplicate count;
- speaker or channel attribution method and confidence;
- privacy boundary: what raw personal data stays local, what is redacted, and what may appear in the final report.

If these counts are missing or disagree, stop before final synthesis and repair the corpus ledger or mark a clear blocker. A polished narrative cannot substitute for count reconciliation.

## Quote And Attribution Rules

1. Do not quote a client, manager, or operator unless the exact transcript segment has a source id, timestamp or segment id, and speaker/channel confidence.
2. If two-channel audio has not been calibrated across representative inbound, outbound, and no-answer examples when available, use neutral wording such as "speaker" or "participant" instead of party-attributed quotes.
3. Overlapping speech, channel bleed, silence, provider mixing, or low-confidence diarization blocks party-attributed quoting for that fragment.
4. Use short paraphrases in working reports when raw personal data, phone numbers, names, addresses, payments, tokens, or private URLs appear in transcripts. Keep raw values out of chat and proposal artifacts.

## Complete Reading And Uncertain Speakers

When full conversation analysis is promised, bind findings to the exact input
version and record continuous reading coverage through the end of each source.
Opening every filename or reconciling transcript counts does not prove that all
dialogue content was read. Re-read missing or truncated sections before claiming
complete analysis; mechanical range checks establish coverage, not understanding.

For recurring translation and analysis pipelines, bind queues, accepted results
and downstream inputs to the exact source versions: a result is current only for
the source content and rule version it was produced from.

For question inventories or conversation analysis, uncertain speaker identity
must not silently remove a substantive question. Preserve the question with
unknown attribution and its context. Exclude it as manager-only only with
positive contextual evidence; phrase style alone is insufficient, especially
when it contradicts the source speaker label. This does not relax the quote
rules above: unknown-speaker material must not be presented as a verified client
quote or merged into customer-attributed counts.

## Task And Agreement Extraction

When extracting tasks, decisions, responsibilities, or next steps from calls,
chats, transcripts, or meeting notes, separate confirmed agreement from
hypothesis, suggestion, unresolved question, and personal or off-scope topic.
Do not turn a discussion idea into an assigned task unless the source shows a
responsible person, action, acceptance condition, deadline or trigger, and
agreement confidence.

A phrase said by a third party to someone else (for example the client talking on the phone during the call) is never our task. Before proposing a plan from a transcript, first list "what we already know" from the project's existing research, then only tasks from explicit agreements with a quote; do not build a plan from a fragment of someone's phrase. Questions to the user from a transcript: at most 5–7, only ones whose answer changes the next action or document.

If the communication contains personal topics, private details, or side
conversations, keep them out of task lists and client-facing summaries unless
the user explicitly asked to include them and the privacy boundary allows it.

## Question And Request Outcomes

Separate the overall conversation disposition from each question or request's
outcome: answered, partly answered, action promised, fulfillment confirmed, or
unknown. Treat these as semantic distinctions, not mandatory database labels.
Include substantive requests without a question mark. A promise to send a
document is not evidence that it was sent; a participant's payment or delivery
claim remains attributed unless independent fulfillment evidence is available.

When consolidating questions, preserve their object, quantity units and final
agreement. Bind the answer to its actual respondent when several company staff
participate. Do not count products mentioned only by a recorded greeting as
discussed products, or split inflections of the same product into new entities.

## Final Package Gate

Before a final research package, verify:

1. expected event count equals included plus excluded plus missing or blocked events;
2. transcript count matches the accepted audio/text corpus;
3. duplicate scan is complete and duplicates are either merged or listed;
4. every exclusion has a reason such as out of window, empty recording, inaccessible source, duplicate, privacy block, or failed transcription;
5. conclusions are separated by evidence strength: direct quote, repeated paraphrased pattern, weak signal, or hypothesis;
6. any claim used for ads or positioning has a source route back to the corpus ledger.

If the package will feed Yandex Direct, Google Ads, VK Ads, site copy, or a client presentation, hand off only the redacted findings and keep the raw corpus path local.

## Public discussions used for customer journeys

Keep the original poster, other commenters and later follow-ups separate. Before paraphrasing an observation, re-read the initial post and relevant replies: advice from a commenter is not an action or choice by the original poster. Do not claim a cause was unknown when the initial post names it. Record only the stage actually evidenced; label proposed agreement, acceptance and payment stages as hypotheses. A mature profile is a screening signal, not proof of identity, independence or payment.
