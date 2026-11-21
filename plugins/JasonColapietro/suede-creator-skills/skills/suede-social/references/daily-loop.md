# Daily Content Loop

The daily loop produces decisions and approval-ready assets. It does not imply
automatic publishing or autonomous engagement.

## Inputs

- refreshed Account Evidence Pack;
- current content ledger and queue;
- prior post readback and due measurement checkpoints;
- active offer and conversion destination;
- audience comments, questions, DMs, search terms, and support themes the user
  is authorized to access;
- current official platform guidance and account status;
- lawful trend sources and cleared media library.

## Run

1. **Read yesterday.** Record post status, early measures, comments needing
   human review, and any broken link or render issue. Do not draw a performance
   conclusion before the named checkpoint.
2. **Refresh signals.** Capture only relevant audience questions, account
   insights, product events, owned proof, and current trends. Date every signal.
3. **Protect the queue.** Remove stale claims, expired links, duplicated angles,
   rights-unclear media, and posts whose context materially changed.
4. **Select candidates.** Score ideas on audience recognition, payoff, evidence,
   voice fit, and business bridge. Select 1–3 candidates with different jobs.
5. **Produce packages.** Use the short-video, carousel, Story, text, or static
   contract in [content-production.md](content-production.md) and
   [post-templates.md](post-templates.md).
6. **QA.** Verify exact claims, source rights, identity, accessibility, CTA,
   destination, disclosure, and brand voice.
7. **Request exact approval.** Show the final copy, media list, visible identity,
   destination, timing hypothesis, and any collaborator or tag.
8. **Publish only if authorized.** Use the authenticated native surface or an
   approved API/tool permitted for the account.
9. **Read back.** Confirm permalink, identity, rendered media, caption, tags,
   collaborator state, CTA destination, and public availability.
10. **Log.** Record post ID, publish time, experiment variable, primary metric,
    measurement checkpoint, and permalink.

## Approval packet

```text
Account / visible identity:
Format:
Final media and rights source:
Final caption:
Tags / collaborators / location:
CTA and destination:
Publish time hypothesis:
Experiment variable:
Primary metric and checkpoint:
Approval status: draft | exact-content approved | published and read back
```

## Failure handling

- **No authenticated access:** return drafts and the audit worksheet.
- **Metrics missing:** label performance class `unknown` and request Insights or
  attribution evidence.
- **Composer differs from plan:** stop before publish and show the rendered
  difference.
- **Publish succeeds but readback fails:** report `publish state unknown`; do
  not retry blindly.
- **Rights or disclosure unclear:** use the halt contract and omit the asset.
- **Comments or DMs contain threats, medical/legal/financial claims, private
  data, or account-security issues:** escalate for human review; do not reply.
