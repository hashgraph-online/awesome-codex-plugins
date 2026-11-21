# Demo and launch video

For a product launch film (X, Product Hunt, a site hero) or a product demo. Two shapes:

| Shape | Length | Use when |
|---|---|---|
| Launch film | 45–90 s | announcing a product or a feature to a feed |
| Value demo | 2–5 min | a viewer who is already curious and wants to see it work |

Keep the key content in the first half; engagement holds to about 2 minutes, then drops
([Wistia 2025](https://wistia.com/blog/optimal-video-length)).

## Rules

1. **Open on a change in the world, never on the company.** Name the shift or the pain that makes the product
   necessary now. No logo card, history or team
   ([Andy Raskin](https://medium.com/the-mission/the-greatest-sales-deck-ive-ever-seen-4f4ef3391ba0);
   [Peter Cohan, Death by Corporate Overview](https://greatdemo.blogspot.com/2023/08/death-by-corporate-overview-never-stop.html)).
2. **Show the result first.** "Start by presenting the highest impact, most compelling screen relevant to the
   audience at hand, then 'Peel Back the Layers'" (Peter Cohan,
   [Great Demo!](https://greatdemo.blogspot.com/2017/06/disasters-neatly-averted-dealing-with.html)). The first
   frame of a launch film is the finished output, the after state. Skip the boring middle like a cooking show.
3. **Name the villain, and reject the obvious fix out loud.** "Oh, a stylus, right? ... Who wants a stylus?"
   ([Steve Jobs, iPhone 2007 transcript](https://singjupost.com/steve-jobs-iphone-2007-presentation-full-transcript/)).
4. **Write the headline first.** "Can you describe your product or service in 140 characters?" Say it once, on
   screen and spoken, right after the reveal. Plan exactly one showstopper moment and script it
   ([Carmine Gallo](https://www.forbes.com/2009/10/08/steve-jobs-presentations-technology-meetings-09-tips_slide.html)).
5. **Demo by value, not by menu.** Two or three value moments, each one action and its payoff; for a longer demo
   first set up the insight, the alternatives and a "perfect world" the viewer agrees with
   ([April Dunford, Lenny's Podcast](https://www.lennysnewsletter.com/p/a-step-by-step-guide-to-crafting)).
6. **Keep it moving and human.** "Smth should be happening every 2-3 seconds", run 45 s to 1:30, make it obvious it
   is a launch, avoid a corporate feel ([Roy Lee, X](https://x.com/im_roy_lee/status/1965859119728046433)). Write like
   you talk, no marketing voice ([Kat Mañalac, YC](https://blog.ycombinator.com/startup-school-week-4-recap-kat-manalac-and-gustaf-alstromer/)).
7. **Use the real product.** Screen recordings of the real UI; AI shots for the world around it, never a fake UI
   doing things the product cannot do. The tagline says what it does with no hype
   ([Product Hunt, preparing for launch](https://www.producthunt.com/launch/preparing-for-launch)).

Word budget: leave room for the product to be watched. A 60 s launch film carries 90–120 spoken words, not 150.

## Beats: launch film (60 s)

| Beat | Time | What it does |
|---|---|---|
| First frame | 0–3 s | the finished result, no logo |
| Shift / villain | 3–10 s | the pain or change, shown |
| Obvious fix, rejected | 10–16 s | one line |
| Headline | 16–20 s | name + one sentence, spoken and on screen |
| Value demo | 20–50 s | 2–3 moments, action then payoff, a cut every 2–3 s; the showstopper inside |
| Ask | last 5 s | one action, the URL |

## Beats: value demo (2–5 min)

Shift → winners and losers → today's alternatives and where each falls short → the perfect world → value demo in
2–3 buckets, each result screen first (more than half the time) → proof from a customer like the viewer → one objection
→ one next step.

## Example: Patchwork launch film

Brief: Patchwork (fictional) reads a GitHub issue and writes a failing test that reproduces the bug, then opens a
draft PR with it. Works with Jest and pytest. Free for open source. 60 s, 16:9, X launch.

```
format: demo
length: 60s
ratio: 16:9
viewer: developers who lose mornings reproducing vague bug reports
promise: paste a bug report, get a failing test
strategy: result first
cta: try it on your oldest bug
```

| # | time | spoken | on screen | visual | sound |
|---|---|---|---|---|---|
| 1 | 0:00-0:03 | | Issue #4127 → FAIL checkout.test.ts | a GitHub issue page snaps into a red failing test run in one cut | key tap, error buzz |
| 2 | 0:03-0:10 | "Most of fixing a bug is making it happen again." | | dev scrolls a vague issue, clicks through the app, nothing breaks; cut, cut, cut | clock ticking |
| 3 | 0:10-0:16 | "You could ask the reporter for steps. They'll answer Tuesday." | Seen 9:14 | chat bubble "can you share steps?" marked seen, no reply | notification ping, silence |
| 4 | 0:16-0:21 | "This is Patchwork. It turns a bug report into a failing test." | PATCHWORK · bug report → failing test | logo resolves over the issue page | soft sting |
| 5 | 0:21-0:26 | "Paste the issue link." | | screen recording: the link drops into Patchwork | paste click |
| 6 | 0:26-0:33 | "It reads the report, finds the code path, and writes the test." | | three progress lines, then a test file types itself | quiet clicks |
| 7 | 0:33-0:40 | "Run it. Red. Now you're not guessing." | FAIL 1 of 1 | terminal turns red on the exact line | error tone |
| 8 | 0:40-0:48 | "Fix one line. Green." | PASS | dev edits one line, terminal flips green | bright ding |
| 9 | 0:48-0:55 | "And it opens the pull request with the test inside, so this bug never comes back." | Draft PR #4128 · test included | draft PR page, test file highlighted (showstopper) | music lifts |
| 10 | 0:55-1:00 | "Patchwork. Free for open source. Try it on your oldest bug." | patchwork.dev | logo, URL, cursor on Try it | music out |

Why it works: the first frame is the result; beats 2–3 are the villain and the rejected fix; beat 4 is the
headline; 5–9 are value moments with one showstopper; 86 words in 60 s.
