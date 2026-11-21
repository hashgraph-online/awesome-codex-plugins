# Routing: which layer makes each element, and what the previz feeds it

Decides, element by element, whether code, AI video or a hybrid (video reference plus image references) makes it; how
much the previz holds; what goes in each channel; and when the reference clip goes.

Legend: `[vendor]` = company selling or reselling it, or a paid partner; `[self]` = one person's own report; `[measured]` = varg's own measurement, usually one film; `[inference]` = our reasoning, nobody tested it; no tag = opened primary source (docs, standard, paper, book).

The evidence is young and thin: the method dates from June 2026, no named expert publishes a full routing rule, and no
researcher watched the videos, so every verdict on an output belongs to its author. [Dreamina pays for
views](https://x.com/dreamina_ai/status/2117243037835509798) of Seedance posts through 2026-12-31, so those posts are
not neutral (evidence.md). "translated" = our translation from Japanese or Chinese. Quotes from opened pages came
through a fetch tool: check the wording at the link before quoting onward.

## Route elements, not shots

The split that survives across sources is accuracy against plausibility [inference]. For each element, ask which one
the audience will judge.

| Layer | Owns | Evidence | Check |
|---|---|---|---|
| Code | What must be right to the character or frame; anything re-rendered alone | "For animation requiring this kind of precision, traditional CG methods are easier." ([Matsunaga](https://note.com/overhead_vfx/n/n501cf67cd115) [self], translated, part paywalled). "never ask the model to type your slogan" ([KRUX](https://x.com/kruxael/status/2117381314370224424) [self], promotes follow-gated giveaways). Each frame is a function of its number ([Higgsfield SKILL.md](https://raw.githubusercontent.com/higgsfield-ai/higgsfield-video-engineer/main/skills/code-based-films/SKILL.md)) | Higgsfield's project is [code only](https://github.com/higgsfield-ai/higgsfield-video-engineer) with no rule for choosing. Cite it for the code route, not for routing |
| AI video | Faces, skin, light, smoke, crowds, at the cost of re-rolls | Seedance 2.5 leads Artificial Analysis on human anatomy and photoreal prompts ([AA thread](https://x.com/ArtificialAnlys/status/2115483562921304316)). "let blender own the motion and seedance own the look" (KRUX) | AA ranks are preference votes, not fidelity scores |
| Text from a model | Nothing: do not rely on it | ByteDance on stray subtitles: "This issue cannot currently be eliminated completely." ([BytePlus guide](https://docs.byteplus.com/en/docs/modelark/seedance-2-5-prompt-guide)). Seedance 2.5 spelled short titles in one test where Kling 4 garbled one from a start frame ([Everypixel](https://journal.everypixel.com/kling-4-vs-kling-3) [self]). MiniMax H3 is first on Text Rendering in the AA votes | No 2026 test measures exact text, logo or product geometry on current models. [T2VTextBench](https://arxiv.org/abs/2505.04946) predates them (May 2025). One test and one vote do not show exact text. A search-summary claim that Seedance 2.5 holds printed lettering could not be traced to a page: unverified |
| Cloth, hair | Contested | "the most challenging output to solve" and "an absolute struggle" ([cloth](https://x.com/fatboypink/status/2070577334701473800), [hair](https://x.com/fatboypink/status/2074092766015983971), abokalypsis [self]) | "Better at cloth" means plausible and cheap, not directed. Name any specific hair or cloth beat as a risk [inference] |

Ask these of each element, in order, and stop at the first yes. The order and the thresholds are our synthesis
[inference], untested. Rows 3, 5 and 6 rest most heavily on inference.

| # | Ask of each element | Route | Traces to |
|---|---|---|---|
| 1 | Must it be exact? Text, numbers, charts, UI, logos, captions, lyrics | Code layer, never the model | [Matsunaga](https://note.com/overhead_vfx/n/n501cf67cd115) [self], [KRUX](https://x.com/kruxael/status/2117381314370224424) [self]. Closest published rule, zero engagement: "Code is where my logos, text and UI live. They never go through a video model" ([Johnson](https://x.com/Trevsthinktank/status/2117260089799434616) [self]) |
| 2 | Is motion defined by rule, not feel? Data, teardowns, diagrams, a fixed stylised look | Code, whole shot | Matsunaga, [Elvar](https://x.com/elvar_official/status/2116192984299344372) [self], [Higgsfield README](https://github.com/higgsfield-ai/higgsfield-video-engineer) |
| 3 | Will it be versioned or looped? Language, price, hook | Code for what varies, one reused plate | Higgsfield determinism, [jialiliang_](https://x.com/jialiliang_/status/2117580846446039520) [self]. Loops are [inference]: no source documents an AI loop failure |
| 4 | Rigid hero object filling the frame, curved labels, flexible packaging? | Locked packshot or code render over an AI plate. Wider or fast: clean mesh in the blockout, real product photos, titles in the edit | [DomoAI](https://domoai.app/blog/ai-product-videos-without-warping-the-product) [vendor], no measurements; KRUX |
| 5 | Must a hit land within a frame or two of the locked audio? | AI with handles, cut in the edit; code if it cannot be cut. Lip sync is a separate pass (sound-sync.md) | [nemopi](https://x.com/nemopi/status/2077741477565010406) [self, translated], [Eian](https://x.com/EianLu/status/2117469941364637983) [self, translated] |
| 6 | Must an AI plate register with a code layer while the camera moves? | Lock or simplify the camera, track the plate, or code the shot | One drift test (post-ready.md) [measured]; the rule is [inference] |
| 7 | Must physics be correct rather than plausible? | Code simulation or a real-element comp. If plausible is enough, go on to row 8 | [T2VPhysBench](https://arxiv.org/html/2505.00337v1), May 2025, older models: more detailed prompt hints generally did not help |
| 8 | Face, hair, cloth, weather, fire, crowd, photoreal world? | Hybrid: video reference plus images. **The default in this project** | [Reid](https://x.com/reidhannaford/status/2070145120658137385) [self], KRUX, [Alex G](https://x.com/alexgnewmedia/status/2097464460931981400) [self], Dreamina hashtag |
| 9 | Is the previz adding nothing, or giving stiff results? | Image-to-video without the video reference (last section) | [Manuel Peter via Dreamina](https://x.com/dreamina_ai/status/2100927228356026407) [vendor], [Higgsfield post](https://higgsfield.ai/blog/ai-vs-vfx) [vendor] |

| Rule | Do | Evidence |
|---|---|---|
| **Escalation, above the table** | On the second identical failure, stop re-rolling: split the shot, simplify the reference or change route | "if a shot fails the same way twice, I split it or build it in Blender" ([Johnson](https://x.com/Trevsthinktank/status/2117260089799434616) [self], cited for clarity, not authority). Matsunaga's roughly four failed takes ([post](https://x.com/sonicpower1970/status/2074322339391824012) [self], translated) and four failed batches from a source clip that lacked the moment ([Higgsfield post](https://higgsfield.ai/blog/ai-vs-vfx) [vendor]) suggest more batches rarely fix a structural failure |
| Decide the shot | A shot that mixes layers is one AI plate with no text in it, plus code layers added in the edit; run row 6 on it | Our wording, untested |
| Budget by acting, not camera | The previz cost is sunk. It reduces camera and blocking re-rolls and leaves performance re-rolls, so size each shot by its acting [inference]. Take counts: drafts-and-takes.md. Credits: models.md, confirm with `estimate_cost`; this file states no varg prices | No same-shot cost of code, AI and hybrid is published. Ariew's stated $27 against under $5, AI against his own Octane render, is one case, fast particles where motion blur matters ([Ariew](https://x.com/DavidAriew/status/2048918904400122077) [self]). Total effort is disputed: "3x cheaper" ([Pounds](https://x.com/pounddz/status/2104298509566693635) [self], promotes a workflow) against man-hours he expects to rise, not fall ([@craftcapitallab](https://x.com/craftcapitallab/status/2070640446423093759) [self, translated]) |

## How much the previz holds

Every direct comparison favours simple over detailed for the video reference. Warning: no source compares a fully
textured, lit render against grey on the same shot, nemopi's half-finished version is the closest, and few comparisons
use photoreal dialogue.

| Test | Result | Limits |
|---|---|---|
| [nemopi](https://x.com/nemopi/status/2076877246497976329) [self, translated]: same 15-camera structure, Seedance 2.0 | Half-finished 3D leaked CG shapes into 10 of 15 shots, colour-coded blocks into 0 of 15 | Cut timing slightly worse with blocks. A 2D target look may exaggerate it |
| [Grand Visions](https://x.com/GrandVisionsAI/status/2096993565599490465) [self]: same prompt, two previz versions, Seedance 2.5 | Barebones won. "The more detail you put into the previs, the more literally Seedance follows it." | One comparison |
| [David Israel](https://x.com/RealDavidIsrael/status/2097028838249079149) [self], ImagineArt-tagged | "the posed people gave it stiff motion to copy"; replaced with blocks plus image references | One stream |
| [BytePlus guide](https://docs.byteplus.com/en/docs/ModelArk/2607689), the model maker's own | "Simple, coarse-grained 3D clay-model video generally works better as a reference." | General advice |

**Model only what must be copied, in flat solids with a written mapping.** The rule is ours [inference].

| Element or check | Do | Source |
|---|---|---|
| Position, scale, camera, timing | Always in the clip | [inference] |
| Proportions, limb volume | Match the character design but not its shape, which pulls the output towards a cheap 3D look. "the further the anatomy differs, the more the model invents" | [@craftcapitallab on volume](https://x.com/craftcapitallab/status/2070512271391068287), [on shape](https://x.com/craftcapitallab/status/2071197700901699829) [self, translated], [@felixsanzm](https://x.com/felixsanzm/status/2085823110402457676) [self] |
| Limb poses | Only when contact or silhouette is the point | [inference] |
| Background | Simple where it does not have to match | [@craftcapitallab](https://x.com/craftcapitallab/status/2070512271391068287) [self, translated] |
| Surface, texture, baked light | Never, unless the final look stays CG. Send looks as images | [inference] |
| Solids and mapping | Always flat, unlit solids, each one named in the prompt, text consistent with the clay. Our lines, untested (skeleton in prompts.md): `@video1 is only camera, blocking, positions and timing. Do not copy its colours, materials, boxes or lighting. @image1 is Anna: she is the red model in @video1.` | "Map the man in gray clothing from [Image 1] to the red model in [Video 1]" ([BytePlus](https://docs.byteplus.com/en/docs/ModelArk/2607689)). Brown boxes are counters, red is a chandelier, blue is the character ([Reisner](https://x.com/magneticskiff/status/2070711040099103008) [self]) |
| Grey | The default, with subjects separated by luminance | [Ichel Park](https://x.com/ichelpark/status/2113258825142902829) [self] |
| Flat ID colours | When subjects of similar value share a frame. Our call, because grey and colour have not been compared directly: varg's colour previz that came back unchanged is one unexplained pass-through [measured], the only measured win did not isolate colour from geometry, and the official guide maps to a coloured model | [nemopi](https://x.com/nemopi/status/2076877246497976329) [self, translated], Reisner, [Reid](https://x.com/reidhannaford/status/2070181581998657923) [self], BytePlus's "red model" |
| Ignore clause | Tell the model not to copy colours, materials, boxes or lighting | "if you skip that line, seedance copies the cheap 3d render" ([rewind](https://x.com/rewind02/status/2110774943294070795) [self]) |
| Symbols | Write down the real form of a glowing sphere: symbols transfer as shapes | [Kashima](https://github.com/atsu-mada/previz-maker-public) [self] |
| Robotic in-betweens | They carry over, "jerky, robotic movement and all". One fix keeps only keyframes with black between them | [Cooper](https://x.com/thechriscooper/status/2076092824102240411) [self], single example |
| Animatic motion | Check each action take for whether it still moves like a clean animatic [inference] | "action scenes are replicating a potpourri of stuntman action reels or previz animatics." ([Kahn](https://x.com/JosephKahn/status/2070788059680194970) [self]) |
| Coarse or fine | Coarse is simple stand-ins, fine is a finished model re-rendered with new materials. Use fine only when the 3D is finished and only the look changes [inference] | [dev.to write-up](https://dev.to/super_lewis/the-seedance-25-prompting-guide-in-english-4hen) [self], secondary; the official Lark guide needs a login, not verified at source |

**Jointed figures only when the pose or contact is the point:**

| Case | Put in the clip | Source |
|---|---|---|
| Weapon or body contact | Jointed grey mannequin, clean key poses first, then impact points. A broken stance shows up in the output: check stance | [Maru999](https://x.com/maru_999_/status/2117586762730192975) [self, translated], low engagement |
| Several characters in dialogue | Poses matched to the start frame | [Reid](https://x.com/reidhannaford/status/2069420552394043625) [self] |
| Complex body motion | Mocap cleaned in Blender, keys set to constant, in-betweens deleted. Most controlled and slower; suits a small team | [abokalypsis](https://x.com/fatboypink/status/2070579839334039837), [team size](https://x.com/fatboypink/status/2070581545438478474) [self] |
| Directed eyeline | Keep a facial rig. He finds it effective for eye movement and is unsure about closed eyes | [@craftcapitallab](https://x.com/craftcapitallab/status/2070697446246945105) [self, translated] |
| Anime character heads | Faceless sphere, because faces in the reference distorted anime outlines | [tapehead.lab](https://x.com/tapehead_Lab/status/2109576509690462555) [self, translated] |
| A solid comes back as an object | Fix the mapping first, then go jointed (our order, untested). The logs may come from a missing mapping (our guess). The default above replaces this older line but is untested on varg | Older varg `threejs-animatic`: "Mannequins need real limbs, a head with a nose, and feet. Capsules come back as logs or bollards." |

## Video channel and image channel

Viewport, clay, colour blocks and depth all do one job: take appearance out of the motion channel and send it as
images [inference]. Approve the previz for camera and blocking, never for look.

| Channel | Owns | Do | Source |
|---|---|---|---|
| Video reference (`@video1`) | Camera, blocking, positions, timing | Flat solids or a depth pass, never looks. Put motion here: "Motion carries over from a video reference much better than it does from text." | [Chris via PJ Ace](https://x.com/PJaccetturo/status/2116160709180723486) [vendor] |
| Image references | Character, set, look | Finished looks go here. Character references answer only for looks. Real people's likeness only with their consent | [@nanyuan0412](https://x.com/nanyuan0412/status/2117440900670579119) [self, translated] |
| Start frame | First picture of the clip | Render it to match frame 1. "Seedance is scary accurate as long as the fully rendered image inputs match a frame of the vid." A textured previz render can feed an image edit for it [inference]; never send that render as the video reference | [abokalypsis](https://x.com/fatboypink/status/2070580437429149863), [Alex G](https://x.com/alexgnewmedia/status/2097464460931981400) [self] |
| End frame | Destination of a long move | Add it on long camera moves, or mannequins reappear in the crowd; fixed with an end frame and a request for real people | [Sharipov](https://x.com/aigenboss/status/2115587840704708984) [self] |
| No start frame | Environment image carries the look | One box and a staging block can work if the environment reference has enough discrete details | [Reisner](https://x.com/magneticskiff/status/2070711034793361559) [self] |
| Prompt | Acting, causes, what the blockout cannot show | Give each reference a job, say what to ignore, describe only what the clip lacks. Short when a reference video carries direction, long when only stills do; logical sections, no JSON. Our reading [inference], neither side tested the other's setup; prompts.md | [Pryce](https://x.com/second_bassoon/status/2117703324321694077) [self] long, [Shimura](https://x.com/ucmulleryu/status/2092925867978834314) [self] no difference over 300+ cuts, [Workman](https://x.com/mattworkman/status/2116204462263910473) [vendor] long on Kling, [kaigani](https://x.com/kaigani/status/2073005386668577098) [self] against JSON |
| Code layer and edit | Text, numbers, sync, final rhythm | Rows 1 and 5; sound-sync.md | |

## Pass types

Our call: viewport from a previz by default; depth for exact body motion from mocap or real footage, never for faces.
No source compares viewport, clay and depth from the same previz on the same shot.

| Pass | Use | Evidence | Limits |
|---|---|---|---|
| Viewport playblast, solid shading | **Default** | "It's just an mp4 viewport playblast" ([Reid](https://x.com/reidhannaford/status/2069787619337097234) [self]); [KRUX](https://x.com/kruxael/status/2117381314370224424) [self] | Self-report |
| Clay render | Same job as the playblast | Three.js clay for camera, clean painting for look, "splitting the signal before it hits the video model" ([Thapa](https://x.com/SThapa123456/status/2116534461214925118) [self]) | Zero likes, not compared with playblast |
| Depth | Exact body motion from mocap or real footage | "consistently produced the cleanest and most accurate motion transfer" ([Curious Refuge](https://x.com/CuriousRefuge/status/2079660231265824859) [self]); [Purz](https://x.com/PurzBeats/status/2078871985841475772), [OAK](https://x.com/_OAK200/status/2078916737895223698), [Nicky_42](https://x.com/NickyLi42/status/2117268836500336819) [self] | That test compared depth with raw footage, not clay. "the depth map can't really capture subtle facial motion" ([follow-up](https://x.com/CuriousRefuge/status/2087276113672475117) [self]) |
| Depth rendered from the 3D scene | One test shot first | A previz already holds true depth, so no estimator is needed [inference]; [Encodium](https://x.com/ModelCollapse38/status/2079567071168368959) [self] feeds Blender depth to LTX-2.3 | Shown only on LTX. Untested on Seedance |
| Pose, Canny, segmentation | Optional secondary layers | Depth plus pose may add a little ([Knightama](https://x.com/knightama/status/2073835012534010164) [self]). Optional in the [Curious Refuge test](https://x.com/CuriousRefuge/status/2079660231265824859) [self]. Canny blended from the clay movie in [MickMumpitz's pipeline](https://www.runcomfy.com/comfyui-workflows/3d-movie-pipeline-in-comfyui-ai-3d-scene-to-video-workflow) [vendor] | ComfyUI [strength lists](https://github.com/ismael-joffroy-chandoutis/comfyui-cinema-pipeline/blob/main/docs/02-cinema-workflows.md) show no test |
| Normals | Do not plan on them: unproven | No practitioner report of normals as a driver. Named only in a [course outline](https://www.fxphd.com/fxblog/generative-ai-for-vfx-with-comfyui-invokeai/) (search summary, page not opened) and a [Flick post](https://flick.art/blog/blender-ai-filmmaking) [vendor] | No output evidence |

## What goes in each channel, by shot type

| Shot | Route | Video channel | Image channel and prompt | Basis |
|---|---|---|---|---|
| Dialogue, performance | Hybrid | Solids with matched poses, clean camera | Start frame matching frame 1, acting in the prompt, lip-sync pass (sound-sync.md) | [Reid](https://x.com/reidhannaford/status/2069420552394043625) [self]; depth is weak on faces |
| Fight, dance, exact body motion | Hybrid | Depth from mocap, or jointed mannequin with clean key poses | Sheets, written mapping | [Curious Refuge](https://x.com/CuriousRefuge/status/2079660231265824859), [Nicky_42](https://x.com/NickyLi42/status/2117268836500336819), [Maru999](https://x.com/maru_999_/status/2117586762730192975) [self] |
| Impossible camera, one-take, object POV | Hybrid | Primitives, camera only | Start and end frames on long moves | [Benhamo](https://x.com/dan4kmp4/status/2106437726103113999), [Sharipov](https://x.com/aigenboss/status/2115587840704708984) [self] |
| Crowds, weather, big environments | Hybrid, loose | Very simple blockout | Rich environment image, let the model invent | [Reisner](https://x.com/magneticskiff/status/2070711034793361559), [Alex G](https://x.com/alexgnewmedia/status/2097464460931981400) [self] |
| Product, mid or wide | Hybrid | Grey mesh, camera only | 1 or 2 real product photos, title in the edit | [KRUX](https://x.com/kruxael/status/2117381314370224424) [self] |
| Product close-up with label | Composite | AI plate only | Locked product layer: "The product never moves, so there is nothing to warp." | [DomoAI](https://domoai.app/blog/ai-product-videos-without-warping-the-product) [vendor], no measurements |
| Title, chart, UI, map, lyric | Code | None | None | Row 1 |
| Teardown, explainer, stylised film | Code | None | AI image as a comparison target only: "The AI images are only a guide to compare against." | [Elvar](https://x.com/elvar_official/status/2116192984299344372) [self], [Higgsfield README](https://github.com/higgsfield-ai/higgsfield-video-engineer) |

## Reference clip settings (our conclusions from vendor docs [inference])

| Setting | Value | Why | Source |
|---|---|---|---|
| Size and frame rate | 1280x720 or higher, at least 24 fps | Clears Seedance's pixel floor and Kling's 700 px floor on the edit route | [BytePlus tutorial](https://docs.byteplus.com/en/docs/ModelArk/2607688), [varg Kling spec](https://varg.ai/models/kling_v4.md) |
| Task type | `omni_reference_task_type: "reference"`; read the live model spec first. If a take comes back as the previz re-encoded, check this first (our order, untested) | Edit mode locks ratio and duration, which may explain varg's run that returned the previz re-encoded (untested guess) | Same docs; varg run [measured] |
| Input images | No larger than the output resolution | Avoids fingerprint-like textures | [BytePlus](https://docs.byteplus.com/en/docs/ModelArk/2607689) |
| Moves | In the clip rather than the text, and simple | Motion carries over from a video better than from text | [Chris via PJ Ace](https://x.com/PJaccetturo/status/2116160709180723486) [vendor] |
| Length | One recipe uses 4 to 6 s at 24 fps. Long or short by job: drafts-and-takes.md | One vendor post matches a 4 s output to the clip: "anything longer and the AI starts guessing" | [KRUX](https://x.com/kruxael/status/2117381314370224424) [self], [Higgsfield post](https://higgsfield.ai/blog/ai-vs-vfx) [vendor] |

## What the previz cannot do

| It cannot | What is reported | Do this |
|---|---|---|
| Hold the camera exactly | "Seedance still isn't perfect at matching the reference but it's close." ([Reid](https://x.com/reidhannaford/status/2071595581508563168) [self]). Matsunaga: acceptable if roughly right, quite hard if exact ([post](https://x.com/sonicpower1970/status/2074322339391824012), [reply](https://x.com/sonicpower1970/status/2074325868613423110) [self], translated). Opposing: "Seedance 2 has insane motion adherence." ([JMS.vid](https://x.com/JMSvid/status/2070258132840796579) [self]) | Exact match required: code the shot. No benchmark measures adherence to a clip; [AA's Camera Control board](https://x.com/ArtificialAnlys/status/2115483573482635410) tests prompted moves |
| Land cuts exactly by itself | Depends on model, input and density. Our call: Seedance 2.5 with `@video1` and about 3 cuts per run, expect within a frame [measured, one film]. Text timestamps, about a second. Dense previz, ±0.6 s ([nemopi](https://x.com/nemopi/status/2077741477565010406) [self, translated]: about 73% of planned cut boundaries, 16 cameras, Seedance 2.0). varg's older [note](https://github.com/vargHQ/skills/blob/main/varg-previz/references/seedance-v2v.md) says "kept exactly"; [fal's guide copy](https://fal.ai/learn/devs/how-to-use-seedance-2-5) [vendor] says not frame-accurate. These cases vary model, density and input at once, so treat them as rough | Always measure from keyframes, which costs no credits, and write real in-points. Generate handles: [Eian](https://x.com/EianLu/status/2117469941364637983) [self, translated] makes 4 to 5 s and keeps 2 to 3 s |
| Direct the performance | Re-rolls are usually about performance, not camera ([Reid](https://x.com/reidhannaford/status/2071942383768351005) [self]). "AI dialogue is still flat" ([Reid](https://x.com/reidhannaford/status/2071956990847295855) [self]). Depth misses subtle facial motion ([Curious Refuge](https://x.com/CuriousRefuge/status/2087276113672475117) [self]) | Put acting in the prompt and start frame, add a lip-sync pass [inference]. Budget takes for it |
| Direct hair, skirt sway, expression | Outside the previz, so pure prompt re-rolls ([@craftcapitallab](https://x.com/craftcapitallab/status/2070520271539409149) [self, translated]). A drawn sway in the input frame drove style and cloth over stiff mocap ([abokalypsis](https://x.com/fatboypink/status/2074087401887039740) [self]), and hair still failed in his test | Name any specific beat as a risk before generating |
| Plant feet | Feet slid across a full grid of Seedance models, boxes and prompts. Foot-locked motion such as Mixamo is the author's untested hypothesis ([AI Doga Lab](https://x.com/aidoga_lab/status/2070864753120129057) [self, translated]) | Treat foot contact as a risk and test one shot |
| Get staging right the first time | A white model does not guarantee it ([@nanyuan0412](https://x.com/nanyuan0412/status/2117440900670579119) [self, translated]) | Check head count, facing, occlusion and prop ownership on every take |
| Supply a moment the clip lacks | Four failed batches on a dragon catch, because the source had no jump moment ([Higgsfield post](https://higgsfield.ai/blog/ai-vs-vfx) [vendor]) | Add the beat to the clip [inference], or go to image-to-video |
| Keep full image quality | "there is of course a noticeable quality drop whenever a video reference is used" at 720p ([Reisner](https://x.com/magneticskiff/status/2070711040099103008) [self]) | Expect it on any hybrid shot and inspect at final size (post-ready.md) |
| Carry over between models | Wan 3.0 was unstable with a three.js previz over about 2 days of tests ([Akakumaya](https://x.com/akakuma0219/status/2115731605998190994) [self, translated]) | Test any new model on one shot first (models.md) |
| Fix framing | An older varg skill says output frames looser than the previz. We found no outside report for or against | Compare the first take's framing with the previz |

## When to delete the reference

If the clip adds nothing or makes the result worse, generate from images and prompt alone. "So maybe sometimes
consider deleting a reference." ([Peter via Dreamina](https://x.com/dreamina_ai/status/2100927228356026407) [vendor]).
Support is thin: one sponsored post, one vendor post, and no same-shot run with and without the clip.

| Case | Do | Source |
|---|---|---|
| Simple camera, clip holds nothing the prompt and start frame cannot give | Delete `@video1` | Row 9 |
| Results are stiff | Strip the clip first: "Reducing complexity in the 3D blockout can also help to get more natural movements and more realism." Still stiff: delete `@video1` | Peter, same post [vendor] |
| Clip lacks the moment and video-reference batches keep failing | Delete `@video1`; the dragon catch moved to image-to-video | [Higgsfield post](https://higgsfield.ai/blog/ai-vs-vfx) [vendor] |
| Same failure twice, order to try | Strip posed figures, keep only keyframes with black between them, delete the clip, then build the element in code. Another reported option: "maybe consider taking the generated AI video as the new reference video in a new prompt" | Order is ours, untested; quote from Peter, same post [vendor] |
| After deleting | Camera and timing are no longer locked: expect text timestamps to land within about a second and fix the cut in the edit | Our call; sound-sync.md |
| Image references not in frame | Delete them: one author reports mix-ups with many references. Limits per route: models.md | [kan:mi](https://x.com/kan_mi_no9/status/2071964948314607704) [self] |
