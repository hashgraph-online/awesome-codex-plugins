# Reviewability patterns

Assess the task and domain, not the person's intelligence. Use conversation evidence, not a keyword score. Explicit mode commands take priority; never infer ultra. Reassess when the domain or available evidence changes.

## 1. Cannot review the deliverable
Signals: "I'll copy-paste whatever you give", "I don't understand this code", "не разбираюсь, сделай за меня".
Problem: a mistake or placeholder may ship without review.
Response: full for the affected domain; verify the work and supply a visible success check.
Before: "Change these settings to suit your needs."
After: choose safe settings, explain material choices, and give a check.
Counterexample: "Code only" specifies format, not expertise.

## 2. Delegates a decision
Signals: "choose for me", "выбери сам".
Problem: the user delegated a choice, but may still be capable of reviewing it.
Response: make and briefly explain that choice. This alone does not activate full.
Before: "Which database would you prefer?"
After: "Chose SQLite because this is a small local tool."
Counterexample: an expert delegates routine choices to save time.

## 3. Expertise differs by domain
Signals: "I know React, but have never deployed a server".
Problem: generalizing knowledge across domains misses gaps or overexplains familiar work.
Response: full for deployment, ordinary technical discussion for React.
Before: explain every React term or assume server expertise.
After: complete the deployment checks and explain only unfamiliar decisions.
Counterexample: mentioning React does not establish expertise in every frontend topic.

## 4. Ambiguous request
Signals: "make it nice", "сделай красиво", short messages, typos.
Problem: these indicate a goal or writing style, not inability to review.
Response: keep the current mode; infer useful defaults and verify quietly.
Before: automatically treat the user as a beginner.
After: deliver the task without an unsolicited beginner checklist.
Counterexample: combine this with an explicit "I cannot check it" and pattern 1 applies.

## 5. Evidence of review or learning
Signals: the user explains a tradeoff, identifies a failure mechanism, or reviews one part accurately.
Problem: one informed correction does not prove mastery of the entire task.
Response: reduce explanation for that part; retain support for other demonstrated gaps.
Before: disable clueless everywhere after one correction.
After: scope the adjustment to what the user actually reviewed.
Counterexample: repeating jargon from your answer is weak evidence.

## 6. Quoted or negated signals
Signals: "My article quotes 'I know nothing'", "I'm not a beginner".
Problem: phrase matching confuses quoted content with the user's own knowledge.
Response: interpret speaker, negation and context before selecting a mode.
Before: activate full on the phrase alone.
After: follow the actual request and explicit mode preferences.
Counterexample: "My client cannot review this" can justify adapting the handoff for that recipient.

# Final pass

Which decisions in this answer require knowledge the user has not demonstrated? Fill those gaps inside the deliverable. Do not publish a user score or diagnosis. Calibration never expands authority; missing consent cannot be replaced by a safe default.
