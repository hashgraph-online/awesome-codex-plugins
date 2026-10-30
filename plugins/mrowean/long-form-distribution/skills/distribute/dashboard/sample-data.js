/* sample-data.js: the three bundled sample issues, for when index.html is opened
   straight from disk with no server running. Same content as ../sample/issues/. */
window.LFD_SAMPLE = [
 {
  "slug": "sample-shortcuts-06",
  "title": "SHORTCUTS #06: Housekeeping",
  "url": "",
  "published": "",
  "series": "SHORTCUTS",
  "cover": "covers/shortcuts-06.jpg",
  "sample": true,
  "sections": [
   {
    "id": "s1",
    "title": "Housekeeping"
   },
   {
    "id": "s2",
    "title": "Trending this week"
   },
   {
    "id": "s3",
    "title": "If you write long, a strategy for distribution"
   },
   {
    "id": "s4",
    "title": "The rules file"
   },
   {
    "id": "s5",
    "title": "Jev"
   },
   {
    "id": "s6",
    "title": "Instinct"
   },
   {
    "id": "s7",
    "title": "This week's trending repo"
   }
  ],
  "items": [
   {
    "id": "s1-x",
    "section": "s1",
    "platform": "x",
    "format": "post",
    "label": "The 2% stat",
    "copy": "a16z published State of Markets II, 100+ charts on the first half of 2026.\n\nOne stood out: as of April, only about 2% of US households were paying for an AI subscription.\n\nIf you're reading this, you're likely in that 2%, and it's easy to forget how small that is.",
    "source": "First, a stat, a16z published State of Markets II, 100+ charts on the first half of 2026. One stood out: as of April, only about 2% of US households were paying for an AI subscription.\n\nIf you're reading this, you're likely in that 2%, and it's easy to forget how small that is. Learn these tools well now; it's still early."
   },
   {
    "id": "s3-li",
    "section": "s3",
    "platform": "linkedin",
    "format": "post",
    "label": "Hook: the unposted backlog",
    "copy": "On October 1 the dashboard read 144 sections across my last 8 issues. 35 had been posted. 109 never had.\n\nThat's 76% of my work that only ever lived inside a newsletter.\n\nSHORTCUTS is mostly tools and methods that keep, so issues #01 through #06 are a stockpile.\n\nFull issue: [link]",
    "source": "On October 1 the dashboard read 144 sections across my last 8 issues. 35 had been posted. 109 never had. That's 76% of my work that only ever lived inside a newsletter.\n\nSHORTCUTS is mostly tools and methods that keep, so issues #01 through #06 are a stockpile."
   },
   {
    "id": "s3-x",
    "section": "s3",
    "platform": "x",
    "format": "post",
    "label": "The method in one line",
    "copy": "Write for yourself, at length. Then let a tool find the hooks, break the piece down by platform, and hand you a plan and a checklist you can see.\n\nFull issue: [link]",
    "source": "Write for yourself, at length. Then let a tool find the hooks, break the piece down by platform, and hand you a plan and a checklist you can see."
   },
   {
    "id": "s3-xt",
    "section": "s3",
    "platform": "x",
    "format": "thread",
    "label": "4-post thread: X's small-account boost",
    "copy": "1/ On September 30, X changed its ranking code to lift smaller accounts.\n\n2/ Under 50,000 followers, one eligible new post per feed load can be placed near the top of some feeds, but only in its first two hours and until it passes about 200 views.\n\n3/ Early reactions decide how far it goes from there, and X's ranking code weights a reply ten times a like.\n\n4/ So answer replies for those two hours.",
    "source": "One timing note for X. On September 30, X changed its ranking code to lift smaller accounts. Under 50,000 followers, one eligible new post per feed load can be placed near the top of some feeds, but only in its first two hours and until it passes about 200 views.\n\nEarly reactions decide how far it goes from there, and X's ranking code weights a reply ten times a like. So answer replies for those two hours."
   },
   {
    "id": "s3-note",
    "section": "s3",
    "platform": "substack",
    "format": "note",
    "label": "The dashboard",
    "copy": "I'm a visual person, this changed my behavior. The dashboard shows every issue, section, and where each has been posted, with a tick and a link for logging. At a glance I can see my progress across each issue.",
    "source": "I'm a visual person, this changed my behavior. The dashboard shows every issue, section, and where each has been posted, with a tick and a link for logging. At a glance I can see my progress across each issue."
   },
   {
    "id": "s4-li",
    "section": "s4",
    "platform": "linkedin",
    "format": "post",
    "label": "Hook: 15 of 394 rules",
    "copy": "Of 394 rules, about 15 reached a session at startup.\n\nI found out the hard way, most of my rules never reached the agent at all.\n\nClaude caps what a hook can load at 10,000 characters; past that, the model gets a 2,000-character preview and a file path, the rest sits unread.\n\nIf you load anything into an agent at the start (a rules file, a project brief, a style guide), keep what a hook prints under 10,000 characters and put the rest somewhere the agent can search.\n\nFull issue: [link]",
    "source": "I found out the hard way, most of my rules never reached the agent at all.\n\nThe problem is accumulation. The more your setup learns, the longer its instructions get. Claude caps what a hook can load at 10,000 characters; past that, the model gets a 2,000-character preview and a file path, the rest sits unread.\n\nOf 394 rules, about 15 reached a session at startup. Between July and late September, 41 of 111 retros, 37%, rediscovered a lesson already in the file. One lesson had been written down five separate times. 67% of the rules had never been cited once.\n\nIf you load anything into an agent at the start (a rules file, a project brief, a style guide), keep what a hook prints under 10,000 characters and put the rest somewhere the agent can search."
   },
   {
    "id": "s4-x",
    "section": "s4",
    "platform": "x",
    "format": "post",
    "label": "Green lights on broken work",
    "copy": "In one week I found four monitors saying everything was fine when it wasn't.\n\nA check that only confirms a job ran is not a check. Make it confirm the job delivered.",
    "source": "Green lights on broken work. In one week I found four monitors saying everything was fine when it wasn't. One machine sat frozen for about 42 hours with every light green. A data collector reported success while every request was being refused. A check that only confirms a job ran is not a check. Make it confirm the job delivered."
   },
   {
    "id": "s4-note",
    "section": "s4",
    "platform": "substack",
    "format": "note",
    "label": "The honest wait",
    "copy": "Fixing delivery took a day. By next quarter I'll know the impact.",
    "source": "Fixing delivery took a day. By next quarter I'll know the impact."
   },
   {
    "id": "s5-li",
    "section": "s5",
    "platform": "linkedin",
    "format": "post",
    "label": "Hook: what passed, what failed",
    "copy": "Jev is a decision model, not a writer.\n\nI tested it on my own work over the past two weeks. One kind of task passed and three failed.\n\nWhy it failed: the information it needed can't be written. Taste lives in my head. Judgment needs context from elsewhere. A sorter can't go get it.\n\nEligibility lives in the listing and runs at volume, so it worked.\n\nFull issue: [link]",
    "source": "Jev is a decision model, not a writer. TechCrunch called it a model for \"calibrated decisions\"; one developer called it \"a really smart switch statement.\" You give it an item (an email, a lead, a contract clause, a support ticket, a social post) and one of three kinds of question:\n\nI tested it on my own work over the past two weeks:\n\nWe tested the strongest against my own past data. One kind of task passed and three failed. Time after time, the answer was: don't use it here.\n\nWhy it failed: the information it needed can't be written. Taste lives in my head. Judgment needs context from elsewhere. A sorter can't go get it. Where it was confident, it was mostly on the easy calls I didn't need help with. Eligibility lives in the listing and runs at volume, so it worked."
   },
   {
    "id": "s5-x",
    "section": "s5",
    "platform": "x",
    "format": "post",
    "label": "What it is",
    "copy": "Jev is a decision model, not a writer.\n\nIt hands back the answer and a confidence number.\n\nEach decision costs a fraction of a cent and usually takes under a second.",
    "source": "Jev is a decision model, not a writer. TechCrunch called it a model for \"calibrated decisions\"; one developer called it \"a really smart switch statement.\" You give it an item (an email, a lead, a contract clause, a support ticket, a social post) and one of three kinds of question:\n\nIt hands back the answer and a confidence number.\n\nEach decision costs a fraction of a cent and usually takes under a second. This is something best used on large databases and thousand of decisions."
   },
   {
    "id": "s6-li",
    "section": "s6",
    "platform": "linkedin",
    "format": "post",
    "label": "Hook: agentic buying",
    "copy": "Instinct is a personal assistant you text or call.\n\n40% of users handed it a credit card within three weeks, Shinn said on Patrick O'Shaughnessy's podcast.\n\nWhen agents hold your card, can access your accounts and know your preferences to decide where you buy, it opens a whole new arms race for customer acquisition.\n\nIf you sell, your next customer may be an agent reading your page: price, stock, shipping and returns it can understand, or it moves on.\n\nFull issue: [link]",
    "source": "Instinct is a personal assistant you text or call. Say \"I need to be in New York tonight\" and it books the flight, hotel and ride, updates your calendar and uses any travel credit you have. It also answers email, chases refunds and argues with customer support. It's invite-only, five invites per user (Fortune).\n\n40% of users handed it a credit card within three weeks, Shinn said on Patrick O'Shaughnessy's podcast.\n\nWhen agents hold your card, can access your accounts and know your preferences to decide where you buy, it opens a whole new arms race for customer acquisition.\n\nIf you sell, your next customer may be an agent reading your page: price, stock, shipping and returns it can understand, or it moves on. Making pages readable to AI agents and answer engines (often called AEO, answer engine optimization) is becoming a massive business."
   },
   {
    "id": "s6-note",
    "section": "s6",
    "platform": "substack",
    "format": "note",
    "label": "The terms",
    "copy": "From this week's SHORTCUTS:\n\nThe terms put the risk on you. What Instinct agrees to for you is \"binding on you as if entered into directly by you,\" so a nonrefundable booking it makes counts as one you made.",
    "source": "The terms put the risk on you. What Instinct agrees to for you is \"binding on you as if entered into directly by you,\" so a nonrefundable booking it makes counts as one you made."
   }
  ]
 },
 {
  "slug": "sample-shortcuts-05",
  "title": "SHORTCUTS #05: Blender, Flora, Images 2.5",
  "url": "",
  "published": "2026-09-19",
  "series": "SHORTCUTS",
  "cover": "covers/shortcuts-05.jpg",
  "sample": true,
  "sections": [
   {
    "id": "s1",
    "title": "Vibe coding became vibe building"
   },
   {
    "id": "s2",
    "title": "Cost meters moved this week"
   },
   {
    "id": "s3",
    "title": "Images 2.5, one week in"
   },
   {
    "id": "s4",
    "title": "Flora: one canvas, all the tools"
   }
  ],
  "items": [
   {
    "id": "s1-li",
    "section": "s1",
    "platform": "linkedin",
    "format": "post",
    "label": "Hook: dimensional building",
    "copy": "Astra's ability to perform long complex tasks has changed the vibe from coding to dimensional building, which is exciting because it unlocks a crazy amount of surfaces.\n\nWant to make a complex product? Create plans a contractor could work with? Build game worlds? Make 3D assets you can move a camera through?\n\nUntil last month, that kind of work was a highly specialized realm, and extremely time consuming. I'm now building 3D assets of real quality FAST.\n\nFull issue: [link]",
    "source": "Astra’s ability to perform long complex tasks has changed the vibe from coding to dimensional building, which is exciting because it unlocks a crazy amount of surfaces. Want to make a complex product? Create plans a contractor could work with? Build game worlds? Make 3D assets you can move a camera through? Until last month, that kind of work was a highly specialized realm, and extremely time consuming. I’m now building 3D assets of real quality FAST."
   },
   {
    "id": "s1-x",
    "section": "s1",
    "platform": "x",
    "format": "post",
    "label": "The cost of trying",
    "copy": "Blender is free, so the only cost of trying this is tokens.",
    "source": "Blender is free, so the only cost of trying this is tokens."
   },
   {
    "id": "s1-note",
    "section": "s1",
    "platform": "substack",
    "format": "note",
    "label": "Push harder",
    "copy": "PUSH HARDER. My initial ideas tend to be very direct and simple, where I'm constantly impressed is when I throw something really abstract, difficult or complicated at the machine.\n\nTry pushing way beyond what seems reasonable, that's the realm where things get interesting.",
    "source": "PUSH HARDER. My initial ideas tend to be very direct and simple, where I'm constantly impressed is when I throw something really abstract, difficult or complicated at the machine.\n\nTry pushing way beyond what seems reasonable, that's the realm where things get interesting."
   },
   {
    "id": "s2-li",
    "section": "s2",
    "platform": "linkedin",
    "format": "post",
    "label": "Hook: check the usage rates",
    "copy": "I pasted that email into Code to see which of my automations were affected. My daily social scrub makes 57 searches a run and pulls about 435 posts. Today costs $0.39 a run, about $12 a month. On the new meter it is $38 to $68 a month.\n\nThat led me to figure out I could move the whole thing off Grok and run it a different way for free.\n\nLesson here: check the usage rates. Companies love to get you in with a lot of freeness, then slowly boil the water.\n\nFull issue: [link]",
    "source": "I pasted that email into Code to see which of my automations were affected. My daily social scrub makes 57 searches a run and pulls about 435 posts. Today costs $0.39 a run, about $12 a month. On the new meter it is $38 to $68 a month. I checked it on Grok and it’s unfortunately true. If you run any automated Grok searches through the API, ask your model what the price change does to your bill before the 21st.\n\nThat led me to figure out I could move the whole thing off Grok and run it a different way for free. Lesson here: check the usage rates. Companies love to get you in with a lot of freeness, then slowly boil the water."
   },
   {
    "id": "s3-x",
    "section": "s3",
    "platform": "x",
    "format": "post",
    "label": "Control, not quality",
    "copy": "The leap in ChatGPT Images 2.5 is not prettier pictures, it's that the model holds a huge leap in consistency across scenes.\n\nIt is not a photographer; location plates should still go to Nano Banana Pro.",
    "source": "The leap in ChatGPT Images 2.5 is not prettier pictures, it’s that the model holds a huge leap in consistency across scenes.\n\nIt is not a photographer; location plates should still go to Nano Banana Pro."
   },
   {
    "id": "s4-li",
    "section": "s4",
    "platform": "linkedin",
    "format": "post",
    "label": "Hook: one canvas",
    "copy": "Every image in SHORTCUTS is made in Flora now, mostly as a forcing mechanism to learn its potential.\n\nFigma for design, vector and layout work; Flora for every asset that goes into it. If you are laying something out, Figma. If you are making imagery, Flora.\n\nInside Flora: Explore on a sub-cent model, iterate on one under $0.20, finish on the stronger models.\n\nFull issue: [link]",
    "source": "Every image in SHORTCUTS is made in Flora now, mostly as a forcing mechanism to learn its potential. The biggest change I see is that rather than looking for swipe, or the perfect image, I can look for different aspects of exactly the type of image I want, and then create it.\n\nFigma for design, vector and layout work; Flora for every asset that goes into it. Flora is not for infographics or anything with type in it, because image models still garble text. If you are laying something out, Figma. If you are making imagery, Flora.\n\nInside Flora: Explore on a sub-cent model, iterate on one under $0.20, finish on the stronger models."
   },
   {
    "id": "s4-x",
    "section": "s4",
    "platform": "x",
    "format": "post",
    "label": "Grain is not dirt",
    "copy": "\"Clean this up\" strips the grain. The model treats grain as dirt. A cleanup instruction has to name what to keep.",
    "source": "“Clean this up” strips the grain. The model treats grain as dirt. A cleanup instruction has to name what to keep: “remove the marks, keep the grain and the paper colour” is a different node from “clean this up.”"
   },
   {
    "id": "s4-xt",
    "section": "s4",
    "platform": "x",
    "format": "thread",
    "label": "3-post thread: text nodes",
    "copy": "1/ Put the prompt in a text node, not in the image node.\n\n2/ My boards run an image with a text box beneath it; drag both into a new image node and press Run.\n\n3/ Changing the words never touches the source, and one text node can drive many images.",
    "source": "Put the prompt in a text node, not in the image node. My boards run an image with a text box beneath it; drag both into a new image node and press Run. Changing the words never touches the source, and one text node can drive many images."
   },
   {
    "id": "s4-note",
    "section": "s4",
    "platform": "substack",
    "format": "note",
    "label": "Storyboards move now",
    "copy": "Where it has already changed our work is pre-production. Storyboards are now dynamic; they move and we can iterate a LOT more for experiential renderings.",
    "source": "Where it has already changed our work is pre-production. Storyboards are now dynamic; they move and we can iterate a LOT more for experiential renderings. You can board a spot in the exact visual style you are going for, then bring the style frames to life, I’m moving completely off swipe for storyboarding."
   }
  ]
 },
 {
  "slug": "sample-shortcuts-04",
  "title": "SHORTCUTS #04: Voice, Figma, Sepia",
  "url": "",
  "published": "2026-09-04",
  "series": "SHORTCUTS",
  "cover": "covers/shortcuts-04.jpg",
  "sample": true,
  "sections": [
   {
    "id": "s1",
    "title": "Persistence is the next frontier"
   },
   {
    "id": "s2",
    "title": "Fable 5.1 dropped"
   },
   {
    "id": "s3",
    "title": "Atlas: camera control in image or video"
   },
   {
    "id": "s4",
    "title": "Talking instead of typing"
   },
   {
    "id": "s5",
    "title": "Figma integration"
   }
  ],
  "items": [
   {
    "id": "s1-li",
    "section": "s1",
    "platform": "linkedin",
    "format": "post",
    "label": "Hook: the third chapter",
    "copy": "Agents that don't stop when you close your laptop, you can now run jobs for hours or days, or be 'always on,' unlocking a plethora of new ways to leverage AI.\n\nIt's gone from prompting, to agentic, now persistence.\n\nTo summarize, Grok is furthest ahead on letting one agent run indefinitely without you. OpenAI's got the most ambitious version, they just haven't shipped it. Anthropic has shipped pieces one at a time, they haven't done a good job marketing persistence.\n\nFull issue: [link]",
    "source": "Agents that don’t stop when you close your laptop , you can now run jobs for hours or days, or be ‘always on,’ unlocking a plethora of new ways to leverage AI. This is more than a product update, it’s the beginning of the third chapter in the AI story.\n\nIt’s gone from prompting, to agentic, now persistence. Early 26’ we saw agentic go mainstream with normal people starting to use programs like Code and Codex for agentic tools. Sumer brought us better models and multi agent workflows, but unless you went the lengths to set them up on sandboxed burner computers, you’ve been tethered to the wake state of your computer.\n\nTo summarize, Grok is furthest ahead on letting one agent run indefinitely without you. OpenAI’s got the most ambitious version, they just haven’t shipped it. Anthropic has shipped pieces one at a time, they haven’t done a good job marketing persistence."
   },
   {
    "id": "s1-x",
    "section": "s1",
    "platform": "x",
    "format": "post",
    "label": "Forever timelines",
    "copy": "Regardless, start playing with what you can do by running agents across 'forever' timelines, it changes the way you think about use.",
    "source": "Regardless, start playing with what you can do by running agents across ‘forever’ timelines, it changes the way you think about use."
   },
   {
    "id": "s2-x",
    "section": "s2",
    "platform": "x",
    "format": "post",
    "label": "Better at finishing",
    "copy": "Plainly: it is not significantly smarter, but it is much better at finishing. Gains are on working for hours and recovering from mistakes.",
    "source": "Plainly: it is not significantly smarter, but it is much better at finishing. Gains are on working for hours and recovering from mistakes."
   },
   {
    "id": "s2-xt",
    "section": "s2",
    "platform": "x",
    "format": "thread",
    "label": "3-post thread: two reviewers",
    "copy": "1/ Before execution, I currently run 2x second opinions, all from Claude code, which runs Codex and GrokBuild straight through the terminal.\n\n2/ Before I execute on any build they beat up the plan and improve it.\n\n3/ If you run two reviewers, move the first one's write-up out of the folder before you start the second. Mine read the other's report and started agreeing with it.",
    "source": "Before execution, I currently run 2x second opinions, all from Claude code, which runs Codex and GrokBuild straight through the terminal. Before I execute on any build they beat up the plan and improve it. Read shortcuts 03 to set up a codex second opinion, to do the same with grok steal the prompt below.\n\nIf you run two reviewers, move the first one’s write-up out of the folder before you start the second. Mine read the other’s report and started agreeing with it."
   },
   {
    "id": "s2-note",
    "section": "s2",
    "platform": "substack",
    "format": "note",
    "label": "Scope, then the last mile",
    "copy": "Scope with 5.1, hand the plan to something cheap, then bring 5.1 back for the final pass. The last mile is where the recovery behaviour earns its price.",
    "source": "Scope with 5.1, hand the plan to something cheap, then bring 5.1 back for the final pass. The last mile is where the recovery behaviour earns its price."
   },
   {
    "id": "s3-x",
    "section": "s3",
    "platform": "x",
    "format": "post",
    "label": "Twenty-four frames",
    "copy": "Feed it a handful of ground-level shots and it rebuilds the space in 3D, including angles not captured. Twenty-four frames of phone video, about a second of walking, is enough to build an environment.",
    "source": "Feed it a handful of ground-level shots and it rebuilds the space in 3D, including angles not captured. Twenty-four frames of phone video, about a second of walking, is enough to build an environment."
   },
   {
    "id": "s4-li",
    "section": "s4",
    "platform": "linkedin",
    "format": "post",
    "label": "Hook: two to three times faster",
    "copy": "The average adult types 52 words a minute at a desk, 36 on a phone.\n\nDictation studies clock people between 90 and 160 words a minute, two to three times faster (Testing caveat, most of those measures are people reading prepared text aloud on a phone).\n\nIt is not for writing. Spoken sentences are longer, looser and more repetitive than written ones, good writing requires sitting and thinking, but ideation and capturing thoughts is where transcription excels.\n\nApple's dictation is already on your Mac, it costs nothing, and it is good enough to find out whether you like working this way.\n\nFull issue: [link]",
    "source": "I set this up two weeks ago, the day to day interaction with Code has been amazing. It is not for writing. Spoken sentences are longer, looser and more repetitive than written ones, good writing requires sitting and thinking, but ideation and capturing thoughts is where transcription excels.\n\nThe average adult types 52 words a minute at a desk, 36 on a phone, measured across two Aalto University studies of 168,000 and 37,000 volunteers. Dictation studies clock people between 90 and 160 words a minute, two to three times faster (Testing caveat, most of those measures are people reading prepared text aloud on a phone).\n\nApple’s dictation is already on your Mac, it costs nothing, and it is good enough to find out whether you like working this way. Turn it on in System Settings / Keyboard / Dictation, and set a shortcut you can hit without thinking about it."
   },
   {
    "id": "s4-xt",
    "section": "s4",
    "platform": "x",
    "format": "thread",
    "label": "3-post thread: Whisper vs Wispr",
    "copy": "1/ Whisper is a speech-recognition model OpenAI released for free in 2022. It is not an app. Anyone can run it on their own machine.\n\n2/ Wispr Flow is a paid app from a different company. It runs in the cloud.\n\n3/ MacWhisper is a paid Mac app that runs Whisper locally on your own machine.",
    "source": "Whisper is a speech-recognition model OpenAI released for free in 2022. It is not an app. Anyone can run it on their own machine.\n\nWispr Flow is a paid app from a different company. It runs in the cloud.\n\nMacWhisper is a paid Mac app that runs Whisper locally on your own machine."
   },
   {
    "id": "s5-li",
    "section": "s5",
    "platform": "linkedin",
    "format": "post",
    "label": "Hook: build the templates first",
    "copy": "I started by building the things I needed, social assets and layouts, and it was so iterative on the smallest details that it was slower than doing it myself. The fix is to build the templates first.\n\nPoint Claude at your best previous work alongside your references and have it build templates from both, iterating for variety.\n\nEvery INTAKE issue now turns into social assets for LinkedIn, stories and Pinterest, three sets of dimensions, in minutes. Work that used to take me a few hours.\n\nFull issue: [link]",
    "source": "I started by building the things I needed, social assets and layouts, and it was so iterative on the smallest details that it was slower than doing it myself. The fix is to build the templates first.\n\nPoint Claude at your best previous work alongside your references and have it build templates from both, iterating for variety. You’ll now have a whole folder to pull from.\n\nEvery INTAKE issue now turns into social assets for LinkedIn, stories and Pinterest, three sets of dimensions, in minutes. Work that used to take me a few hours."
   },
   {
    "id": "s5-x",
    "section": "s5",
    "platform": "x",
    "format": "post",
    "label": "Outline first",
    "copy": "Big files break the pipe.\n\nAsk for the outline first, then pull only the frames you need.",
    "source": "Big files break the pipe. Claude Code caps a single MCP tool response at 25,000 tokens by default, a full design pull on a real file hits that easily. It’s just a default, you can raise it with the MAXMCPOUTPUTTOKENS environment variable.\n\nAsk for the outline first, then pull only the frames you need."
   },
   {
    "id": "s5-note",
    "section": "s5",
    "platform": "substack",
    "format": "note",
    "label": "Decks become cleanup",
    "copy": "Use it for decks. Slides is writable now, decks are a huge waste of time that now become a cleanup pass.",
    "source": "Use it for decks. Slides is writable now, decks are a huge waste of time that now become a cleanup pass."
   }
  ]
 }
];
