# VoiceMoat skills for Claude

21 free skills for LinkedIn and 21 for Twitter, as plain
`SKILL.md` files. They work in Claude, Claude Code, ChatGPT and Codex, and they
need no account.

Most of them are on both lists, so the total published here is 26.
Adding the two numbers together double-counts.

## Install

As a plugin, which is one command:

```
/plugin marketplace add prateeks367/voicemoat-skills
/plugin install voicemoat-skills@voicemoat
```

Or by hand, which works anywhere that reads the format:

```
git clone https://github.com/prateeks367/voicemoat-skills.git
cp -r voicemoat-skills/skills/* ~/.claude/skills/
```

Or one at a time: open any `SKILL.md` below, copy it, and paste it as a system
prompt. Each file declares only a name and a description, which is the portable
minimum, so they load on any surface that reads the format rather than only in
Claude Code.

## What these actually do

Each skill is instructions, not a program. It changes how the model approaches
one job: which question to ask first, what to refuse, and when to say the
evidence is too thin to answer.

On their own they work from whatever you paste. Paste five of your own posts and
a skill builds a sketch of how you write, then drafts against it. That is
genuinely useful and it is genuinely a sketch, which is why none of them will
give you a score: a number would claim a precision a read-through does not have.

Connected to [VoiceMoat](https://voicemoat.com) through its
[MCP connector](https://voicemoat.com/mcp), the sketch is replaced by a voice
profile trained on your own published posts, held separately per platform,
and a draft comes back with a Voice Match score from 0 to 100 and a note on
what is off. The connector needs a VoiceMoat account on the Pro or Enterprise
plan; the skills themselves never do.

## LinkedIn, 21 skills

| Skill | What it does | Category |
|---|---|---|
| [`write-in-my-voice`](skills/write-in-my-voice/SKILL.md) | Write it in my voice | Writing |
| [`fix-my-opening-line`](skills/fix-my-opening-line/SKILL.md) | Fix my opening line | Writing |
| [`audit-before-i-publish`](skills/audit-before-i-publish/SKILL.md) | Audit it before I publish | Writing |
| [`same-idea-both-platforms`](skills/same-idea-both-platforms/SKILL.md) | Same idea, both platforms | Writing |
| [`sound-less-like-ai`](skills/sound-less-like-ai/SKILL.md) | Make this sound less like AI | Writing |
| [`repurpose-into-a-post`](skills/repurpose-into-a-post/SKILL.md) | Repurpose this into a post | Writing |
| [`what-worked`](skills/what-worked/SKILL.md) | What worked, and more of it | Analytics |
| [`am-i-drifting`](skills/am-i-drifting/SKILL.md) | Am I drifting from my voice? | Analytics |
| [`why-did-this-post-flop`](skills/why-did-this-post-flop/SKILL.md) | Why did this post flop? | Analytics |
| [`plan-my-week`](skills/plan-my-week/SKILL.md) | Plan my week | Strategy |
| [`define-my-content-pillars`](skills/define-my-content-pillars/SKILL.md) | Define my content pillars | Strategy |
| [`fix-my-ending`](skills/fix-my-ending/SKILL.md) | Fix my ending | Writing |
| [`find-the-story`](skills/find-the-story/SKILL.md) | Find the story in it | Writing |
| [`draft-my-comments`](skills/draft-my-comments/SKILL.md) | Draft my comments | Writing |
| [`handle-my-replies`](skills/handle-my-replies/SKILL.md) | Handle my replies | Writing |
| [`extract-the-hook`](skills/extract-the-hook/SKILL.md) | Extract the hook | Writing |
| [`why-did-that-one-take-off`](skills/why-did-that-one-take-off/SKILL.md) | Why did that one take off? | Analytics |
| [`fix-my-linkedin-profile`](skills/fix-my-linkedin-profile/SKILL.md) | Fix my LinkedIn profile | Strategy |
| [`narrow-my-niche`](skills/narrow-my-niche/SKILL.md) | Narrow my niche | Strategy |
| [`who-am-i-writing-for`](skills/who-am-i-writing-for/SKILL.md) | Who am I writing for? | Strategy |
| [`get-my-team-posting`](skills/get-my-team-posting/SKILL.md) | Get my team posting | Strategy |

## Twitter, 21 skills

| Skill | What it does | Category |
|---|---|---|
| [`write-in-my-voice`](skills/write-in-my-voice/SKILL.md) | Write it in my voice | Writing |
| [`fix-my-opening-line`](skills/fix-my-opening-line/SKILL.md) | Fix my opening line | Writing |
| [`same-idea-both-platforms`](skills/same-idea-both-platforms/SKILL.md) | Same idea, both platforms | Writing |
| [`turn-this-into-a-thread`](skills/turn-this-into-a-thread/SKILL.md) | Turn this into a thread | Writing |
| [`sound-less-like-ai`](skills/sound-less-like-ai/SKILL.md) | Make this sound less like AI | Writing |
| [`repurpose-into-a-post`](skills/repurpose-into-a-post/SKILL.md) | Repurpose this into a post | Writing |
| [`what-worked`](skills/what-worked/SKILL.md) | What worked, and more of it | Analytics |
| [`am-i-drifting`](skills/am-i-drifting/SKILL.md) | Am I drifting from my voice? | Analytics |
| [`why-did-this-post-flop`](skills/why-did-this-post-flop/SKILL.md) | Why did this post flop? | Analytics |
| [`plan-my-week`](skills/plan-my-week/SKILL.md) | Plan my week | Strategy |
| [`define-my-content-pillars`](skills/define-my-content-pillars/SKILL.md) | Define my content pillars | Strategy |
| [`find-the-story`](skills/find-the-story/SKILL.md) | Find the story in it | Writing |
| [`handle-my-replies`](skills/handle-my-replies/SKILL.md) | Handle my replies | Writing |
| [`extract-the-hook`](skills/extract-the-hook/SKILL.md) | Extract the hook | Writing |
| [`why-did-that-one-take-off`](skills/why-did-that-one-take-off/SKILL.md) | Why did that one take off? | Analytics |
| [`narrow-my-niche`](skills/narrow-my-niche/SKILL.md) | Narrow my niche | Strategy |
| [`who-am-i-writing-for`](skills/who-am-i-writing-for/SKILL.md) | Who am I writing for? | Strategy |
| [`audit-before-i-tweet`](skills/audit-before-i-tweet/SKILL.md) | Audit it before I tweet | Writing |
| [`fix-my-last-line`](skills/fix-my-last-line/SKILL.md) | Fix my last line | Writing |
| [`get-seen-in-replies`](skills/get-seen-in-replies/SKILL.md) | Get seen in the replies | Writing |
| [`fix-my-twitter-profile`](skills/fix-my-twitter-profile/SKILL.md) | Fix my Twitter profile | Strategy |

## Reading other people's posts

Five of these skills read content somebody else wrote:

- [`draft-my-comments`](skills/draft-my-comments/SKILL.md)
- [`extract-the-hook`](skills/extract-the-hook/SKILL.md)
- [`get-seen-in-replies`](skills/get-seen-in-replies/SKILL.md)
- [`handle-my-replies`](skills/handle-my-replies/SKILL.md)
- [`why-did-that-one-take-off`](skills/why-did-that-one-take-off/SKILL.md)

Each one carries a rule saying that fetched text is data rather than
instructions, that text claiming to come from you is still just text, and that
quoting means quoting with the author named.

This matters more once a connector with publishing tools is attached. Nothing in
those skills can publish: on VoiceMoat, posting takes a second call you confirm,
and the preview shows the exact words first.

To report a security problem, see [SECURITY.md](SECURITY.md).

## What is not here

No statistics. Hook collections circulate with percentages attached, sourced to
vendors publishing research about their own category. Those numbers are somebody
else's sample of somebody else's accounts and are not measurements of what will
happen on yours, so the patterns are here and the percentages are not.

No promises about reach. Timing, audience, format and luck decide as much as the
words do.

## Licence

MIT. See [LICENSE](LICENSE). Written by VoiceMoat, against
VoiceMoat's own tools.
