# Evidence for judge.md: LLM/VLM-as-a-judge biases, metrics and protocol (sources with quotes)

Research date: 2026-11-04. Plain-English guide section. Every source below was opened. Each one has a URL, a short quote and its key number in the **Sources** list at the end.

How the quotes were checked. **[V]** means I checked the quote against the raw page text (curl + grep). **[T]** means it came from a page-reading tool that pulls quotes out of the opened page. Numbers marked [T] are likely right but should be spot-checked before they go into a public text. Anything I could not confirm in a source is marked **UNVERIFIED**.

---

## 0. Short answer

- Holistic 1-10 scores from a vision model are the weakest setup there is. On generated images and video, MLLM judges agree with people far better when they pick the better of two (pairwise) than when they score: GPT-4V gets 79.3% agreement on pairs but only 0.490 Pearson when scoring. In 2025, judging *generated* content in any modality still gave only 53.37% (pairs) and 30.05% (scores).
- The biggest measured biases:
  - **Order of the two options.** GPT-4 kept its verdict after a swap only 65% of the time, and Claude-v1 only 23.8% of the time.
  - **Labels and provenance.** A fake "Expert" label moved GPT-4o's verdicts by +18%. Model-name labels moved preference by up to 50 points. Judges never mention the label in their reasoning: the rate at which they admit it is exactly 0.
  - **Length.** A padded answer fooled Claude-v1 and GPT-3.5 91.3% of the time. Longer text raised GPT-4V and Gemini scores by 0.6 and 0.75 points.
  - **Self-preference.** Claude-v1 gave itself +25% win rate and GPT-4 gave itself +10%. GPT-4 recognises its own outputs 73.5% of the time.
  - **Score bunching.** "One digit usually dominates", and MLLM video judges give "the same (typically average) score to all videos".
  - **Leniency and yes-bias.** LLaVA-1.5 answers "Yes" to 80% of questions whose answer should be "No".
  - **Visual tricks.** Brightness, gamma, overlays and bounding boxes raise scores, up to +109.6%, and warning the judge in the prompt does not fix it.
- Vision models are weak on exactly our passport details. Accuracy drops 7-24 points on small objects, while a human-style crop takes LLaVA from 39% to 70%. Spatial left/right is near chance (56% vs 99% for humans). Counting and overlapping shapes are poor (58% average). Claude's own docs warn about images under 200 px and about approximate counting and spatial output.
- **Protocol in one line:**
  1. Run code checks first: face identity embedding, landmark-based side crops, action-unit traces, words per minute, lip sync.
  2. Then ask 3 blind judges from different model families one binary (or 0-2 anchored) question each, with the reference sheet first and the crop given.
  3. The judge writes what it sees before the verdict, in JSON, and may answer "cannot_determine".
  4. Run pairwise in both orders. A disagreement between the two orders counts as a tie.
  5. Calibrate against 60-200 human labels per criterion and report TPR/TNR and kappa.
  6. Correct pass rates for judge error and report cluster-bootstrap CIs.

---

## 1. Known LLM-judge biases and how big they are

| Bias | What it is | Measured size | Source | Fix that worked |
|---|---|---|---|---|
| **Position bias** (pairwise) | Judge prefers answer A or B because of its slot | Verdict unchanged after swapping: GPT-4 **65.0%**, GPT-3.5 **46.2%**, Claude-v1 **23.8%**. Claude-v1 favoured the first slot **75.0%** of the time [V] | Zheng et al. 2023 | Call twice with swapped order. A win counts only if both orders agree, otherwise it is a tie [V]. Three few-shot examples raised GPT-4 consistency from 65.0% to 77.5% [T] |
| Position bias (same) | Order alone flips the outcome | With ChatGPT as judge, Vicuna-13B "could beat ChatGPT on 66 over 80 tested queries" just by reordering. Conflict rate after swap: GPT-4 **46.3%**, ChatGPT **82.5%** (Vicuna vs ChatGPT) [T] | Wang et al. 2023 | Multiple Evidence Calibration (critique before score) plus Balanced Position Calibration (average both orders): GPT-4 accuracy vs humans 52.7% → 62.5%. Sending the hardest 20% to humans gave 73.8%, vs 71.7% for the average human [T] |
| Position bias (cause) | Bias is strongest when the two options are close in quality | 15 judges, >150,000 instances; "position bias is strongly affected by the quality gap between solutions" [T] | Shi et al. 2024 | Expect most order flips on near-equal takes, which are exactly the takes we compare |
| **Verbosity bias** | Longer answer wins | "Repetitive list" attack (same content, longer): failure rate Claude-v1 **91.3%**, GPT-3.5 **91.3%**, GPT-4 **8.7%** [V] | Zheng et al. 2023 | Control length (OpenAI guide). For us the image equivalent is "more stuff in frame" or a more detailed critique |
| Verbosity (multimodal) | Same effect in MLLM judges | Longer answers with the same meaning: GPT-4V **+0.6** points, Gemini **+0.75** points [V] | Chen et al. 2024 (MLLM-as-a-Judge) | |
| **Self-enhancement / self-preference** | Judge likes its own model's outputs | GPT-4 **+10%** win rate for itself, Claude-v1 **+25%** [V]. GPT-4 recognises its own text **73.5%** of the time. Kendall τ = 0.41 between recognising itself and preferring itself (GPT-3.5, XSUM) [T] | Zheng 2023; Panickssery et al. 2024 | "Authorship obfuscation" (hide who made what). Use judges from other families |
| Self-preference (training lineage) | "Preference leakage": the judge favours a generator that is the same model, a fine-tune of it, or the same family | Qualitative: "harder to detect" than other biases [T] | Li et al. 2025 | Do not use a judge from the generator's family, or measure the effect per family |
| LLM-text preference | G-Eval-4 "always gives higher scores to GPT-3.5 summaries than human-written summaries, even when human judges prefer human-written summaries" [T] | | Liu et al. 2023 (G-Eval) | |
| **Label / provenance leakage** | Judge sees who or what made the output | Provenance cue: "Expert" label **+18%** verdict shift (GPT-4o, ELI5); Human vs LLM label **+16%** (LitBench); Gemini-2.5-Flash **+22%**. "Cue Acknowledgment Rate (CAR) is exactly zero" [T]. Model-name labels: "swings of up to 50 percentage points" in preference; up to 12 pp on point ratings [T] | "The Silent Judge" 2025; "Label-induced bias" 2025 | Strict blinding: random IDs, no model, method or prompt names, no metadata. The judge's rationale will **not** reveal the bias, because it never admits it |
| **Scale / score anchoring** | Scores bunch on one value. The rubric's format moves scores | "One digit usually dominates the distribution of the scores, such as 3 for a 1-5 scale" [T]. DeepSeek-V3 gave a 5 to "more than half" of pairs [T]. Rubric order, the score labels (1-5 vs A-E vs i-v) and the score of a reference answer all shift results [T] | G-Eval 2023; Li et al. 2025 (Scoring bias); Stureborg et al. 2024 (skewed ratings, "anchoring effects for multi-attribute judgments") | Binary or anchored 0-2 with examples. If a reference answer is given, give a full-mark one. G-Eval used the probability-weighted score Σ p(s)·s, with n=20 samples at temperature 1 for GPT-4 |
| Scale (multimodal) | | "VLM judges can generally provide more accurate and stable feedback in natural language (Likert-scale) than numerical scales" [T] | MJ-Bench 2024 | Word labels with anchors, not 1-10 |
| Score bunching on video | | "the model often assigns the same (typically average) score to all videos" [V]. Showing the judge other takes as references raised correlation with humans by **10.33%** [V] | Video-Bench 2025 | Comparative or few-shot scoring, or pairwise |
| **Leniency** | Judge says "pass" too easily | Best judges reach Scott's π 88 vs 96.2 between humans. Judges with >90% raw agreement can still be >10 points off on the total score. "True negatives drop off quickly as judge quality decreases" [T]. Scores can differ "up to 5 points" from human scores [T] | Thakur et al. 2024 | Report TNR (does it catch failures?) and kappa, never raw agreement alone |
| Yes-bias (VQA) | | LLaVA-1.5 "biases towards answering 'Yes' to 80% of the questions should be answered with 'No'" [T] | Lin et al. 2024 (VQAScore) | Ask about absence too (control questions). Allow "cannot_determine" |
| **Order effects in lists** (batch ranking) | Ranking many items in one prompt | MLLM batch ranking is the worst setting (GPT-4V normalised Levenshtein 0.361). LLaVA copies the "ABCD" order from the prompt in **88.2%** of answers [V]. Listwise reranking is "highly sensitive to input ordering" [T] | Chen et al. 2024; Qin et al. 2023 | Do not rank N takes in one prompt. Use pairwise |
| Prompt sensitivity | | GPT-4 "relatively weak judge, exhibiting high variance with minor changes to the prompt". Kappa 0.627 → 0.725 from a prompt tweak [T] | Verga et al. 2024 | Freeze the prompt, version it, re-calibrate after any change |
| **Single judge vs jury** | | PoLL (Command R + Haiku + GPT-3.5) Cohen's κ vs humans: NQ **0.763** vs GPT-4 0.627; TriviaQA 0.906 vs 0.841; HotpotQA 0.867 vs 0.830. "seven to eight times less expensive" [T] | Verga et al. 2024 (PoLL) | Jury from different families. **But** for video judges "incorporating collective judgments from such a mixed pool does not necessarily improve the accuracy" [T] (Liu & Zhang 2025), so calibrate each juror first and drop weak ones |
| Rubric + reference helps | | Prometheus 13B with custom rubrics: Pearson **0.897** with humans, GPT-4 0.882 (45 rubrics) [T] | Kim et al. 2023 | Write a rubric for each criterion and give a reference |
| Math / precision tasks | | Reference-guided grading cut the failure rate **70% → 15%** [V] | Zheng et al. 2023 | Show the reference first (our character sheet) |
| **Criteria drift** | People's criteria change once they see outputs | 9 practitioners: "it is impossible to completely determine evaluation criteria prior to human judging of LLM outputs" [T] | Shankar et al. 2024 (EvalGen) | Label 20-30 outputs before freezing the rubric, then freeze and version it |
| Human ceiling | | GPT-4 vs humans 85% vs human-human 81% (MT-Bench, no ties) [V] | Zheng 2023 | On *video quality*, humans agree only at Krippendorff α 0.52 (Video-Bench) [V]. Measure our own human-human ceiling |

Surveys that cover these (2024-2026): Gu et al., "A Survey on LLM-as-a-Judge" (2411.15594, v5 March 2025), which centres on consistency, bias mitigation and adapting to the scenario; Ye et al. 2024 CALM, with "12 key potential biases" (authority, bandwagon, position, verbosity, self-enhancement, sentiment and more); MM-JudgeBias 2026, with nine bias types across 26 MLLMs and "systematic modality neglect".

---

## 2. Vision-model (MLLM/VLM) judges specifically

### 2.1 How well they agree with people, by format

- **Chen et al. 2024, MLLM-as-a-Judge (ICML).**
  - Pairwise is the best format: GPT-4V reaches about 0.8 accuracy (no ties) and 79.3% human agreement [V].
  - Scoring is weak: GPT-4V Pearson **0.490**, Gemini **0.304** [V].
  - Batch ranking is the worst format.
  - "Multi-steps CoT Do Not Enhance Performance" (section title) [V].
  - Conclusion: "proficiency … in pair comparison tasks, they require further improvement in score evaluation and batch ranking" [T].
- **Judge Anything 2025** (GPT-4o, Gemini 2.0-Flash). Judging *generation* tasks gives "only 53.37% in Pair Comparison setting and 30.05% in Score Evaluation setting". For understanding tasks the figures are 66.55% and 42.79% [T]. Our task is judging generation, which is the harder case.
- **VideoScore 2024.** Asked zero-shot, GPT-4o reaches Spearman **23.0** with human video ratings and Gemini-1.5-Pro **16.9**. A fine-tuned scorer reaches **77.1** [V]. "These multimodal language models also achieve very low agreement with human raters" [V].
- **Video-Bench (CVPR 2025).**
  - Method: chain-of-query (describe → ask dimension questions → answer → score) plus few-shot scoring.
  - Results: Spearman 0.70-0.75 on most dimensions, but only **0.402** on temporal consistency [T].
  - Agreement (α): human-human 0.52, human-Video-Bench 0.50, human-single GPT 0.41 [V].
- **Liu & Zhang 2025 (ICLR), "Is your video language model a reliable judge?"** Better video understanding "alone is insufficient to make VLM judges more reliable" [T].

### 2.2 Image failure modes that hit our checklist

| Failure mode | Evidence | What it means for us |
|---|---|---|
| **Small details** | Accuracy falls with object size: BLIP-2 −24 pp, InstructBLIP −23, Qwen-VL −12, LLaVA-1.5 −11, GPT-4o −7 (medium → small). A human-style crop took LLaVA-1.5 on small objects from **39.38% → 69.95%** and BLIP-2 from 12.13% → 55.76% [T] (Zhang et al. 2025, ICLR) | Passport details (a scar, a mole, a ring) must be **cropped and enlarged** before the judge sees them |
| **Left/right and spatial terms** | 18 VLMs. BLIP-VQAv2 gets **56%** on What'sUp vs **99%** for humans. Models struggle with "right" vs "left" and "on" vs "under" [T] (Kamath et al. 2023) | Never ask "is the scar on the left?" on a full frame. Decide the side **in code** with face landmarks and ask only "is it present in this crop?" |
| **Counting, overlapping shapes** | Four frontier VLMs are "only 58.07% accurate on average". Claude 3.5 Sonnet is best at 77.84%. They "struggle … when geometric primitives overlap or are close" [V] (Rahmanzadehgervi et al. 2024) | Fingers, teeth and buttons: crop and use a dedicated check (hand keypoints) |
| **CLIP-blind pairs** | "state-of-the-art systems, including GPT-4V, struggle with straightforward questions across nine basic visual patterns" [T] (Tong et al. 2024, MMVP) | Images that look the same in embedding space can differ in orientation, state or side |
| **Vendor-stated limits (Claude)** | "might hallucinate or make mistakes when interpreting low-quality, rotated, or very small images under 200 pixels". Counting is "approximate", spatial output "approximate". Standard models downscale to a 1,568 px long edge; Claude 4.7+ to 2,576 px [V] | Crops ≥ 200 px on the short side. A 4K frame is downscaled anyway, so crop instead of sending the full frame |
| **Vendor-stated limits (Gemini video)** | Default **1 frame per second**; "fast action sequences might lose detail due to the 1 FPS sampling rate"; about 66 tokens per frame at low media resolution [T] | Acting and timing judged at 1 fps misses blinks and micro-timing. Raise fps or send frame strips |
| **Hallucination** | LVLMs "tend to generate objects that are inconsistent with the target images", especially frequent or co-occurring objects [T] (POPE) | Ask for observation before verdict and include absence questions |
| **Visual tricks inflate scores** | "all tested LVLM judges exhibit vulnerability across all domains, consistently inflating scores for manipulated images … pairwise evaluations are similarly susceptible … visual biases persist under prompt-based mitigation strategies" [V]. Up to **+109.6%** (LLaVA-1.5-13B, one manipulation, Animal domain) [V] | Normalise every take the same way: same size, no borders, no overlays or captions, no burned-in prompt text. Do not rely on "ignore brightness" in the prompt |
| **Aesthetic preference** | Reward models "penalize anti-aesthetic images even when they perfectly match explicit user prompts" (MJ-Bench / related, search summary) [T, partly UNVERIFIED] | "Film-like" and "pretty" are not the same thing. Anchor with reference frames from real films |
| **Judging without looking** | VLM judges "often pays limited attention to the image … blindly favor the more informative answer" [T] (informativeness bias, 2026) | Make the judge describe the specific region before deciding. Keep critiques short |
| **Self-preference (MLLM)** | "GPT-4V exhibits a slight degree of Egocentricity" [V] | Use judges from other families than the generator |
| **Faces and emotions** | GPT-4V "cannot recognize micro-expressions that require specialized knowledge" [T] (Lian et al. 2023, 21 datasets). FaceXBench: GPT-4o and Gemini 1.5 Pro "show significant room for improvement" across 14 face tasks [T] | "Genuine vs posed" from one still is low-reliability. Use video, AU evidence and human calibration |

### 2.3 Question-decomposition evaluation (atomic yes/no questions)

How it works: an LLM turns the prompt (or our character sheet) into small yes/no questions, and a VQA model answers them on the image. This is the closest research analogue to our passport checklist.

- **TIFA (Hu et al. 2023, ICCV).**
  - Method: an LLM generates question-answer pairs from the text, and UnifiedQA filters them ("keep the question if Ai=Aimc and the word-level F1 … greater than 0.7") [T].
  - Benchmark: 4,000 prompts, 25,000 questions, 12 categories.
  - Agreement: Spearman **59.7** with humans (mPLUG), vs CLIPScore **33.2**; human-human α 0.67 [T].
  - Weak spots: generators score worst on "counting, spatial relations, and composing multiple objects".
- **Davidsonian Scene Graph, DSG (Cho et al. 2024, ICLR).**
  - Fixes in the question generation: "atomic and unique questions organized in dependency graphs".
  - Dependency rule: "if the answer to a parent question is NO, all the answers to its child questions are counted as NO as well" (no colour question if the motorcycle is missing).
  - Question quality: precision 92.2% / recall 100% (manual); atomicity 96.5% vs TIFA 78.5%.
  - VQA vs humans: VQA answers match humans on entities at 82-84% but only **13.7-24.9%** on text rendering, about 67% on counting and <25% on style.
  - Overall: Spearman ρ **0.563** with human Likert [T].
  - **Lesson for us:** structure the passport as parent → child questions ("face visible?" → "chin visible?" → "scar present on chin crop?").
- **VQAScore (Lin et al. 2024, ECCV).**
  - Method: one question, P("Yes") to "Does this figure show '{text}'?".
  - Winoground group score **46.0** vs CLIPScore **7.8** [T].
  - GenAI-Bench: 1,600 prompts, >15,000 human ratings.
  - Drawback of decomposition it reports: question generators produce "nonsensical question-answer pairs", and VQA models say "Yes" too often (LLaVA 80%) [T].
  - **Lesson:** use token probability (P(yes)) where the API exposes it, and add negative or control questions.
- **Gecko (Wiles et al. 2024, ICLR 2025).**
  - Scale: >100K human annotations across 4 templates and 4 models.
  - Main finding: conclusions about which model is best change with the human annotation template and the metric [T].
  - **Lesson:** fix the human labelling template before comparing methods.

### 2.4 Video benchmarks (what to borrow)

- **VBench** (16 dimensions) [T].
  - "Subject consistency" is DINO cosine similarity of each frame against the first frame and the previous frame. Background consistency uses CLIP. Dynamic degree uses RAFT optical flow.
  - Human validation used pairwise A/B with "the video order within each pair is randomized".
  - These checks run in code, so they are cheap and cover identity drift inside a clip.
- **T2V-CompBench.** 1,400 prompts, 7 composition categories (attribute binding, spatial, motion, action, interactions, numeracy), with MLLM-, detection- and tracking-based metrics checked against humans [T]. Use detection or tracking for "is the prop still in the hand".
- **VideoScore.** Rates 5 aspects on a 1-4 scale (visual quality, temporal consistency, dynamic degree, text alignment, factual consistency) [V]. A fine-tuned scorer is far better than prompted frontier models on general video quality.
- **Video-Bench.** Chain-of-query plus few-shot scoring, both described above.

---

## 3. Objective metrics to pair with the judge

| Signal | Tool | What it tells you | Limits |
|---|---|---|---|
| **Face identity** | ArcFace-family embedding cosine (InsightFace `normed_embedding`). **License:** InsightFace pretrained models are "for non-commercial research only" [T]. **AuraFace-v1** (fal) is ArcFace-style, ResNet100, **Apache 2.0**, a drop-in for InsightFace's FaceAnalysis, LFW 0.9965 [T] | Same person or not, per still and per frame (median and 10th percentile across frames) | No universal threshold. Values depend on the backbone: PuLID reports ID cosine 0.733 / InstantID 0.725 / PhotoMaker 0.271 with CurricularFace [T]. **Calibrate the threshold on our own same/different pairs (UNVERIFIED that any fixed value transfers).** Robust by design to small marks, so it will **not** catch a missing scar |
| **Subject/costume/prop fidelity** | DINO ViT-S/16 cosine (DreamBooth); DreamSim | DINO is "not trained to ignore differences between subjects of the same class", unlike CLIP-I. Real-vs-real DINO is 0.774 [T] | Correlation with human preference is weak: DINO 0.32, CLIP-I 0.27 (DreamBooth user study) [T]. Use only as a gate or drift alarm |
| **In-clip identity drift** | VBench subject consistency (DINO frame to frame) | Morphing, flicker | Does not say *which* detail changed |
| **Prompt alignment** | VQAScore (CLIP-FlanT5) rather than CLIPScore | Composition | CLIPScore has a "bag of words" problem: it cannot tell "horse eating grass" from "grass eating horse" [T]. CLIP-blind pairs (MMVP) |
| **Facial action units** | py-feat `xgb_au` (AU1-AU43 incl. **AU6, AU12**; code MIT, but the fitted models carry training-dataset terms) [T]. OpenFace 3.0 (FG 2025): AU F1 **59%** DISFA / **59%** BP4D vs OpenFace 2.0 50% / 53%, "freely available for research purposes" [T] | AU12 (lip-corner pull) and AU6 (cheek raise) intensity over time; blinks (AU45); how much the face moves while speaking | **AU6+AU12 is not proof of a genuine smile.** Girard et al. (136 people, 751 smiles): "AU6 may just be an artifact of smile intensity". Controlling for AU12 cut the AU6-amusement link by 64% [T]. F1 around 0.6 means noisy per-frame labels. Trained on real faces, so accuracy on generated faces is unknown (**UNVERIFIED**) |
| **Voice pace** | WhisperX word timestamps (forced phoneme alignment) [T] → words per minute, pause lengths | Objective pace | Reference rates from 2,438 Switchboard phone conversations: average **196 WPM** (range 111-291); "net" rate without silences **236 WPM** (158-312) [V]. Acted lines differ, so set a target band per script, not from this corpus |
| **Lip sync** | SyncNet-based LSE-C / LSE-D (introduced with Wav2Lip) [T] | Mouth-audio offset | Thresholds for "good" are **UNVERIFIED** here. Calibrate on our own real footage |

---

## 4. Practitioner recipe (official and expert guides)

- **Hamel Husain, "LLM-as-a-Judge" (Critique Shadowing)** [V]
  - One principal domain expert gives **binary pass/fail with a written critique**. The critiques become few-shot examples.
  - "report the judge's True Positive Rate and True Negative Rate separately". "It took us only three iterations to achieve > 90% agreement".
  - "I hate off the shelf metrics … They tend to lead people astray."
- **Hamel Husain, Evals FAQ** [V]
  - "Binary evaluations force clearer thinking and more consistent labeling".
  - "Label 100 to 200 examples for each failure mode".
  - Split: train 10-20%, dev 40-45%, test 40-45%, with "30 to 50 Pass examples and 30 to 50 Fail examples in both the dev and test sets".
  - "building a separate judge for each type of failure".
  - Hamel's **judgy** library: corrected pass rate θ̂ = (p_obs + TNR − 1)/(TPR + TNR − 1), plus a bootstrap CI. It needs TPR + TNR > 1 [T].
- **Hamel Husain, "Your AI Product Needs Evals"** [T]. Three levels: unit tests → human and model eval → A/B. "track the correlation between model-based and human evaluation".
- **Eugene Yan, "Evaluating the Effectiveness of LLM-Evaluators"** [V]
  - Pairwise is "more reliable—for subjective evals". Direct scoring suits objective checks.
  - "where possible, I have my evaluators return binary outputs".
  - Use Cohen's κ.
- **Anthropic docs ("Define success criteria and build evaluations")** [V]
  - "choose the fastest, most reliable, most scalable method": code-based → LLM-based ("Test to ensure reliability first, then scale") → human ("Avoid if possible").
  - Tips: "Have detailed, clear rubrics"; "Be empirical or specific … output only 'correct' or 'incorrect'"; "Encourage reasoning: Use a grader model with thinking on".
  - "Generally best practice to evaluate with a different model from the one used to generate the evaluated output".
- **OpenAI evaluation best practices** [T]
  - Formats: pairwise, single-answer and reference-guided grading.
  - "Use pairwise comparison or pass/fail for more reliability".
  - "Control for response lengths".
  - "reasoning before scoring improves eval performance"; validate against human labels before scaling.
- **Google Vertex AI Gen AI evaluation** [T]
  - "Adaptive rubrics … Generates a unique set of pass or fail rubrics for each individual prompt", "like unit tests".
  - PairwiseMetric gives CANDIDATE / BASELINE / TIE plus a chain-of-thought explanation, and win rates.
  - **Our analogue:** generate pass/fail rubric items per character sheet and per shot.
- **Braintrust** [T]. Calibrate on human-labelled examples; "Randomizing order across runs and comparing results in both directions"; ongoing human spot checks.
- **Arize** [T]
  - "binary outputs tend to produce more stable and reliable evaluations".
  - "have the explanation produced before the final label".
  - Measure precision and recall for failure detection: "A perfect pass rate may reflect a strong application, an easy dataset, or an evaluator that misses failures."
- **Statistics: Miller 2024, "Adding Error Bars to Evals" (Anthropic)** [T]
  - Use cluster standard errors when items come in groups: "clustered standard errors can be over 3X larger than naive".
  - Analyse paired differences per item. Resample answers to cut variance. Run a power analysis.
- **Kappa reading (McHugh 2012)** [T]. "any kappa below 0.60 indicates inadequate agreement". Cohen's original bands: 0.61-0.80 "substantial", 0.81+ "almost perfect".
- **Temperature.** G-Eval sampled GPT-4 20 times at temperature 1 to estimate the score distribution. Stureborg et al. report poor agreement across samples. "Use temperature 0" is common advice, but **none of the official guides I opened states it (UNVERIFIED)**. Reasoning or "thinking" modes may not allow temperature control (**UNVERIFIED**). Safer rule: sample k = 3 times and take the majority, or use P(yes).

---

## 5. Ranking many takes

- **Bradley-Terry instead of online Elo.** Chatbot Arena moved to BT because "the BT coefficients are better for the purpose of statistical estimation" [T].
  - CIs: bootstrap or sandwich standard errors.
  - Active sampling picks pairs that shrink the CI most. Random sampling needed **54% more data** to reach 0.2 precision on the win matrix [T].
  - Ties: "tie" and "both are bad" buttons.
  - Crowd vs expert agreement: 72-83%.
- **Elo is fragile** (Boubdir et al. 2023) [T]. Ratings depend on the order of matches and on K. Run "Nperm≥100" random orderings. Ratings are unstable when win probability is about 0.5, which is exactly where near-equal takes sit.
- **How many comparisons** (PRP, Qin et al. 2023) [T].
  - All pairs costs O(N²). Sorting with a pairwise comparator costs O(N log N). A sliding window costs O(N) per pass and is good for top-K only.
  - Each pair is asked in both orders, and an inconsistent pair gives "0.5" to each.
- **PairS** (Liu et al. 2024, COLM) [T]. Pairwise preference plus an uncertainty-guided, merge-sort-like ranking beats direct scoring for alignment with humans.
- **Our arithmetic (not from a source).**
  - Round robin with both orders = N(N−1) calls per judge per criterion: N=4 → 12, N=6 → 30, N=8 → 56.
  - A sort-based tournament needs about N·log₂N pairs ×2 orders: N=16 → about 128 calls vs 240 for all pairs.
  - For 4-8 takes per cell, use a full round robin, then fit BT.
  - For more takes, use Swiss rounds or sorting, then BT, then extra comparisons near the top (active sampling).
- **Ties.** Allow an explicit "tie / both fail". A flip between the two orders = tie (0.5 each). Report the tie rate.

---

## 6. PROTOCOL for our task

### 6.0 What was wrong with test #1 (two blind VLMs, 1-10, one image per cell)

1. **A 1-10 holistic score** is the format with the worst agreement in the research (MLLM scoring Pearson 0.30-0.49; generation scoring 30%), and scores bunch on one value.
2. **One image per cell.** Seed variance is mixed up with method, so you cannot tell a good method from a lucky seed.
3. **Two judges** give no majority, and a disagreement cannot be resolved.
4. **No human calibration**, so we do not know the judges' TPR/TNR.
5. **A holistic score mixes criteria.** Hamel: one judge per failure mode.
6. **Small left/right details judged on a full frame** sit in the VLM's weakest zone (small objects, left/right).

### 6.1 Inputs and blinding (before any judging)

- **Reference sheet** per character:
  - front, 3/4 and profile face crops;
  - full-body costume;
  - prop shots;
  - a numbered **passport list**, where each item gives the detail, the side in *subject* terms, the location, the size and colour, plus a reference crop. Example: "P3: pale vertical scar about 1.5 cm, subject's LEFT side of chin (viewer's right when the subject faces camera)".
- **Shot card** per cell: shot size, beat note (intended emotion and intensity), script line, and the target WPM band.
- **Blinding:**
  1. Rename every take to a random ID.
  2. Strip EXIF/C2PA and filenames.
  3. Re-encode all takes to one format and resolution, and crop to the same aspect.
  4. No borders, captions or overlays.
  5. Never pass the generation prompt, model name, method name or seed.
  6. Keep the ID → method map outside the judging code.

### 6.2 Programmatic checks first (cheap, deterministic, they gate the VLM)

| ID | Check | Tool | Gate |
|---|---|---|---|
| G1 | Decodes; resolution, fps and duration as specified; no black or frozen frames | ffmpeg / ffprobe | fail = stop |
| G2 | Expected number of faces found; face box short side ≥ 256 px | face detector (InsightFace/AuraFace stack) | below threshold → identity and passport checks = `cannot_determine` (256 px is our choice, **UNVERIFIED**) |
| G3 | Identity cosine vs the reference set ≥ T_same. Video: median and 10th percentile over frames sampled at 2-4 fps | **AuraFace** (Apache 2.0) or a licensed ArcFace | T_same calibrated on our own same/different pairs (**UNVERIFIED** value) |
| G4 | Costume/prop similarity to the reference crops (DINO / DreamSim) | DINO ViT-S/16 | drift alarm only |
| G5 | **Passport crops**: from 2D face landmarks, cut a fixed region per passport item on the **named side** and the **mirror side**; upscale so the short side is ≥ 512 px. If the source region is under about 64 px, set `cannot_determine` (not enough pixels) | landmarks + fixed region map | side decided in code, never by the VLM |
| G6 | Subject consistency across frames (VBench style) | DINO | flag morphing |
| G7 | AU traces: AU12 and AU6 intensity, AU variance during speech, blink count (AU45) | py-feat / OpenFace 3.0 (check licences) | flags only: "frozen face", "pegged at max", "smile without AU6". These are **heuristics (UNVERIFIED)**, used only as evidence for the judge or a human |
| G8 | Transcript WER vs script; WPM per line and net WPM; pause lengths | WhisperX | WPM outside the shot-card band ±15% → fail VO-1 (band is our choice) |
| G9 | Lip sync LSE-C / LSE-D | SyncNet | thresholds calibrated on real footage (**UNVERIFIED**) |

### 6.3 Rubric (each item binary, or anchored 0-2 / 3-way; all items also allow `cannot_determine`)

**A. Identity and passport (reference-guided; one call per item)**

- **ID-1 No contradicting features (binary).**
  - FAIL if, compared with the reference crops, the candidate face shows any of these: a different eye colour; a different eyebrow shape; a different nose bridge or tip shape; a different hairline or parting; a different face shape (jaw or chin); an apparent age gap of about 10 years or more; or different skin tone under similar light.
  - PASS otherwise. List each contradicting feature.
  - This is a **supplement** to G3, not a replacement.
- **PD-k Passport item k (binary).**
  - Input: reference crop of item k, candidate crop S (named side) and candidate crop M (mirror side), labelled only "CROP 1" and "CROP 2" in random order.
  - Ask: "Is [the detail, described in visual words] visible in CROP 1? In CROP 2?"
  - Code maps the answers back to sides. PASS = present on S and absent on M.
  - "Mirrored" = present on M only. Count it as a fail, as its own category.
  - Example: P3 scar. FAIL if the scar is missing, on the wrong side, the wrong shape (horizontal), or there are two scars.
- **PR-k Prop item k (binary).** Colour, shape, markings and logo placement match the reference crop. "Which hand" is decided by a pose model (**UNVERIFIED** tool choice), not by the VLM.
- Use DSG-style dependency: if "face visible" = NO, every child item = `cannot_determine` (not FAIL).

**B. Film-likeness and AI-slop tells (binary, one call each; give the crop for B1)**

- **B1 Anatomy.** FAIL: wrong finger count, fused or bent fingers, extra teeth, malformed ears, an asymmetric pupil shape.
- **B2 Skin.** FAIL: waxy or plastic surface, no pores or texture at a distance where they should show, airbrushed uniform sheen.
- **B3 Light logic.** FAIL: shadows or catchlights point to different sources; the face is lit with no plausible source in the scene; the rim light does not match.
- **B4 Text and graphics.** FAIL: any garbled or invented lettering. N/A if there is no text.
- **B5 Background coherence.** FAIL: objects merging or melting, straight lines bending, impossible architecture, repeated clone patterns.
- **B6 "AI gloss".** FAIL: over-sharpening or halos, oversaturation beyond the reference grade, a fully symmetric stock-ad composition when the shot card says otherwise. Anchor with the reference grade, because VLMs have aesthetic biases.
- **B7 Film-likeness (0-2, anchored with 3 reference frames from real films):**
  - **0** looks like an AI ad, stock photo or CG;
  - **1** a plausible photo but not cinema (flat or even light, video look, no lens character);
  - **2** could pass as a frame from a film (motivated light, natural grain, lens character, believable depth of field).
  - For *ranking* B7, use pairwise, not the 0-2 score.
- **B8 (video) Temporal.** FAIL: face, clothing or prop morphs; objects pop in or out; limbs pass through objects; flicker.

**C. Acting (video when possible; send a frame strip at 4-8 fps or raise the model's fps; include the G7 AU trace as text evidence)**

- **C1 Intended emotion reads (binary).** PASS if a viewer would name the beat note's emotion, or a close neighbour, from face and body. Example: beat "suppressed anger" → PASS: jaw set, lips pressed, a stare. FAIL: neutral or smiling.
- **C2 Genuine vs posed (0-2):**
  - **0** posed: a stock-photo grin, eyes not matching the mouth, held like a mask, aimed at the lens with no cause in the scene;
  - **1** plausible but stiff;
  - **2** spontaneous: eyes and mouth agree, slight asymmetry, the expression has a visible cause (a look or reaction), natural onset and offset.
  - AU6 is supporting evidence only (Girard: AU6 tracks smile intensity).
- **C3 Intensity calibration (3-way: UNDER / RIGHT / OVER)**, relative to the beat note and shot size, since close-ups need less.
  - OVER: mugging, brows or mouth at extremes, exaggerated nods.
  - UNDER: a dead face on an emotional line, lips moving while the rest of the face is static, no blinks.
- **C4 Timing (video, binary).** FAIL: the reaction snaps on or off, the expression starts before its trigger, or there are no blinks for more than about 10 s (the blink figure is **UNVERIFIED**; use the G7 count).
- **VO-1 Pace in band** is code (G8). **VO-2 Pace fits the emotion (binary)** goes only to an audio-capable judge or a human, and must be calibrated first.

### 6.4 Judge prompt (one criterion per call)

```
SYSTEM
You are a strict visual inspector for film production. You check ONE criterion.
You do not know how these images were made, and it does not matter.
Judge only what is visible. If the evidence is not visible or too small, answer
"cannot_determine" — do not guess.

USER (content order is fixed: reference first, candidate second)
[REFERENCE SHEET — character "C1"]
  <image: ref_front.png> <image: ref_34.png> <image: ref_detail_P3.png>
  Passport item P3: pale vertical scar, ~1.5 cm, on the chin.
[CANDIDATE take_7f3a]
  <image: CROP 1> <image: CROP 2>

CRITERION PD-P3
Question A: Is the scar described in P3 visible in CROP 1?
Question B: Is it visible in CROP 2?
Definitions: "visible" = a line of lighter or raised skin of roughly the
reference shape and orientation. Shadows, stubble or compression noise do not count.
Examples (from calibration set): <image: pass_example> PASS because ...
                                 <image: fail_example> FAIL because ...

Steps: 1) Describe what you see in each crop in 1-2 sentences.
2) Compare with the reference crop. 3) Answer.
Return ONLY JSON:
{"criterion":"PD-P3",
 "observation_crop1":"...", "observation_crop2":"...",
 "comparison":"...",
 "answer_crop1":"yes|no|cannot_determine",
 "answer_crop2":"yes|no|cannot_determine",
 "confidence":"low|medium|high"}
```

- The pairwise variant (B7, C2, ranking) asks for `"preference":"A|B|tie|both_fail"` after observations of both takes. It is always run twice with A and B swapped.
- If you group several binary B items in one call for cost, **shuffle their order** in every call. Multi-attribute anchoring is a measured bias.
- Turn thinking on (Anthropic tip) or keep the observation step. Keep critiques short, because a longer critique is not a better one.
- Where the API exposes token probabilities, record P(yes), as VQAScore and G-Eval do.

### 6.5 Randomisation and swaps

- New random IDs per run.
- Random order of takes across calls.
- Random crop label (CROP 1/2) per call.
- Reference always first.
- Pairwise in both orders: consistent → win; inconsistent → tie (0.5 each).
- Report **swap consistency** per judge as a health metric (target ≥ 0.8; our choice).

### 6.6 Judges: how many and which

- **Three judges from three families** (for example Anthropic Claude, Google Gemini, OpenAI GPT), all vision-capable, with pinned model versions.
- **Exclude or flag same-family judging.** If the take came from a Google model (e.g. Nano Banana or Veo), the Gemini judge's verdicts on it are flagged. Check per-family self-preference by comparing each judge's pass rate on its own family's takes against the other judges' rates.
- **Aggregation:**
  - binary → majority of 3;
  - 0-2 → median;
  - 3-way → majority, else "disputed";
  - two or more `cannot_determine` → `cannot_determine`;
  - 1-1-1 splits → human queue.
- **Calibrate each juror separately.** Drop any juror below the bar on a criterion. Mixed pools can be worse than the best single judge (Liu & Zhang 2025).
- Sample each judge k=3 times on borderline items and take the majority (handles sampling inconsistency).

### 6.7 Calibration against humans

1. **Rubric-shaping round.** Two people label 20-30 takes and edit the definitions. Then freeze and version the rubric (handles criteria drift).
2. **Labelled set per criterion.** Minimum 60 items, growing to Hamel's 100-200. Split 10-20% train (few-shot examples), 40-45% dev, 40-45% test, with ≥30 pass and ≥30 fail where possible. Seed fails on purpose: mirror-flip the scar, remove the ring, add a sixth finger. This gives enough negatives.
3. **Human ceiling.** Two raters label the same 40 items, then compute human-human κ. Do not expect the judge to beat it (video-quality α was only 0.52).
4. **Judge metrics on dev, then once on test:**
   - TPR (catches real failures) and TNR (passes good takes), with "positive = defect" as in Hamel's FAQ;
   - Cohen's κ vs the human consensus; weighted κ or Spearman for 0-2;
   - swap consistency; `cannot_determine` rate.
5. **Bar** (our choice, guided by Hamel's >90% and McHugh's κ ≥ 0.6): TPR ≥ 0.85, TNR ≥ 0.85, κ ≥ 0.6. Criteria that miss the bar go to humans or code. Expect C2/C3 (acting) and B7 to miss at first.
6. **Re-calibrate** on any change to the judge model, prompt or rubric.

### 6.8 Aggregation and reporting

- **Unit = cell** (character × shot × method). Use **≥ 3-4 seeds per cell** so seed variance is not read as a method effect.
- **Per method and criterion:** raw pass rate, then the **corrected** pass rate θ̂ = (p_obs + TNR − 1)/(TPR + TNR − 1) (Rogan-Gladen, as in judgy).
- **95% cluster-bootstrap CI.** Resample characters or scenes, not single images (clustered SEs can be over 3× naive), with about 2,000 resamples (our choice).
- **Method A vs B:** paired per-cell differences with a bootstrap CI. For pairwise data, fit Bradley-Terry with bootstrap CIs.
- **Agreement table:** judge-human κ per criterion; inter-judge Fleiss κ or Krippendorff α; swap consistency; tie rate; `cannot_determine` rate (reported, never counted as pass).
- **Power, rough arithmetic (not from a source).** To tell a 50% from a 65% pass rate (unpaired, α=0.05, power 0.8) you need about 170 cells per arm. Pairing by cell reduces this. A 1-image-per-cell test cannot detect differences of that size.
- Keep each verdict's JSON so humans can audit disagreements.

### 6.9 What NOT to ask a VLM

1. **Tiny details on a full frame.** Always crop and upscale. Below about 64 px of source detail the answer is `cannot_determine` (Claude: images under 200 px are error-prone; small-object accuracy drops 7-24 pp).
2. **Left vs right.** Decide the side in code from landmarks. The VLM only says "present / absent" in an unlabelled crop. What'sUp: 56% vs 99% for humans.
3. **"Same person?"** Use the face embedding (G3). The VLM may only list contradicting features (ID-1). Claude's docs say it will not identify people.
4. **Counting** fingers, teeth or buttons on a full frame. Use a crop or keypoints (BlindTest 58%).
5. **One holistic 1-10 "quality" score**, or ranking many takes in one prompt. Bunching, anchoring and list-order effects are all measured. Use binary items and pairwise instead.
6. **Genuine vs posed from one still**, or acting judged at 1 fps. Send frames at a higher rate plus AU evidence, and calibrate. GPT-4V fails on micro-expressions.
7. **Voice pace "by ear".** Measure WPM (G8).
8. **Anything that reveals provenance** (model, method or prompt names, filenames, captions in the image). Provenance cues shift verdicts by up to 18-50 points, and the judge never admits it (CAR = 0).
9. **Judging takes made by the judge's own model family** without flagging it.
10. **Trusting "ignore brightness/filters" instructions.** Visual biases survive prompt mitigation. Normalise the inputs instead.

---

## Sources (all opened; URL, short quote, key number)

**Text LLM-judge biases**

1. Zheng et al. 2023, *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. https://arxiv.org/html/2306.05685v4 [V]
   - "call a judge twice by swapping the order of two answers and only declare a win when an answer is preferred in both orders. If the results are inconsistent after swapping, we can call it a tie."
   - Consistency GPT-4 65.0%, Claude-v1 23.8%, GPT-3.5 46.2%. Repetitive-list failure 91.3% / 91.3% / 8.7%. "GPT-4 favors itself with a 10% higher win rate; Claude-v1 favors itself with a 25% higher win rate." GPT-4 vs humans 85% vs human-human 81%. Reference-guided math failure 70% → 15%.
2. Wang et al. 2023, *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926 and https://arxiv.org/html/2305.17926v2 [T]
   - "Vicuna-13B could beat ChatGPT on 66 over 80 tested queries with ChatGPT as an evaluator."
   - Conflict rate GPT-4 46.3%, ChatGPT 82.5%. MEC+BPC GPT-4 52.7% → 62.5%. HITL (20% human) 73.8%.
3. Shi et al. 2024, *Judging the Judges: A Systematic Investigation of Position Bias*. https://arxiv.org/abs/2406.07791 [T]
   - "position bias is strongly affected by the quality gap between solutions."
   - 15 judges, >150,000 instances.
4. Panickssery et al. 2024, *LLM Evaluators Recognize and Favor Their Own Generations*. https://arxiv.org/abs/2404.13076 and https://arxiv.org/html/2404.13076v1 [T]
   - "GPT-4 is 73.5% accurate distinguishing itself from two other LLMs and humans"; "countermeasures such as authorship obfuscation should be incorporated into standard prompting practice."
   - Kendall τ 0.41.
5. Li et al. 2025, *Preference Leakage*. https://arxiv.org/abs/2502.01534 [T]
   - "harder to detect compared to previously identified biases."
   - 3 relatedness types (same model, inheritance, same family).
6. Liu et al. 2023, *G-Eval*. https://arxiv.org/abs/2303.16634 and https://arxiv.org/html/2303.16634v3 [T]
   - "One digit usually dominates the distribution of the scores, such as 3 for a 1-5 scale"; "always gives higher scores to GPT-3.5 summaries than human-written summaries."
   - Spearman 0.514. n=20, temperature 1.
7. Kim et al. 2023, *Prometheus*. https://arxiv.org/abs/2310.08491 [T]
   - "Pearson correlation of 0.897 with human evaluators when evaluating with 45 customized score rubrics."
   - GPT-4 0.882.
8. Verga et al. 2024, *Replacing Judges with Juries (PoLL)*. https://arxiv.org/abs/2404.18796 and https://arxiv.org/html/2404.18796v2 [T]
   - "exhibits less intra-model bias due to its composition of disjoint model families"; "GPT-4 is a relatively weak judge, exhibiting high variance with minor changes to the prompt."
   - κ NQ 0.763 vs 0.627. 7-8× cheaper.
9. Shankar et al. 2024, *Who Validates the Validators? (EvalGen)*. https://arxiv.org/abs/2404.12272 and https://arxiv.org/html/2404.12272v1 [T]
   - "users need criteria to grade outputs, but grading outputs helps users define criteria."
   - 9 practitioners.
10. Thakur et al. 2024, *Judging the Judges*. https://arxiv.org/abs/2406.12624 and https://arxiv.org/html/2406.12624v3 [T]
    - "judges with high percent agreement can still assign vastly different scores"; "a tendency toward leniency."
    - Scott's π 88 vs human 96.2. Up to 5 points off. 13 judges.
11. Stureborg et al. 2024, *LLMs are Inconsistent and Biased Evaluators*. https://arxiv.org/abs/2405.01724 [T]
    - "anchoring effects for multi-attribute judgments"; "skewed and biased distributions of ratings."
12. Li et al. 2025, *Evaluating Scoring Bias in LLM-as-a-Judge*. https://arxiv.org/html/2506.22316v3 [T]
    - "the higher the score of the reference answer, the better the scoring accuracy."
    - DeepSeek-V3 gave 5 to more than half of the pairs.
13. Ye et al. 2024, *Justice or Prejudice? (CALM)*. https://arxiv.org/abs/2410.02736 [T]
    - "we identify 12 key potential biases."
14. *The Silent Judge* 2025. https://arxiv.org/html/2509.26072v2 [T]
    - "the Cue Acknowledgment Rate (CAR) is exactly zero."
    - Expert cue +18%; Human vs LLM +16%; Gemini +22%.
15. *Quantifying Label-Induced Bias* 2025. https://arxiv.org/html/2508.21164v2 [T]
    - "Blind evaluation protocols where model identity is concealed should be standard practice."
    - Swings up to 50 pp.
16. Gu et al. 2024/2025, *A Survey on LLM-as-a-Judge*. https://arxiv.org/abs/2411.15594 [T]
    - "How can reliable LLM-as-a-Judge systems be built?"

**Multimodal judges and VLM failure modes**

17. Chen et al. 2024, *MLLM-as-a-Judge* (ICML). https://arxiv.org/html/2402.04788v3 [V]
    - "GPT-4V achieved around 70% human agreement across all settings, excelling in the Pair Comparison task with 79.3% agreement"; "average gains of 0.6 and 0.75 points"; "LLaVA replicates this sequence in 88.2% of responses."
    - Scoring Pearson GPT-4V 0.490, Gemini 0.304.
18. *Judge Anything* 2025. https://arxiv.org/abs/2503.17489 [T]
    - "averaging only 53.37% in Pair Comparison setting and 30.05% in Score Evaluation setting" (generation tasks).
19. *MM-JudgeBias* 2026. https://arxiv.org/abs/2604.18164 [T]
    - "systematic modality neglect and asymmetric evaluation tendencies."
    - 26 MLLMs, 9 bias types.
20. Lee et al. 2025, *Fooling the LVLM Judges*. https://arxiv.org/html/2505.15249v2 [V]
    - "all tested LVLM judges exhibit vulnerability across all domains … visual biases persist under prompt-based mitigation strategies."
    - Up to +109.6%.
21. *When Vision-Language Models Judge Without Seeing* 2026. https://arxiv.org/abs/2604.17768 [T]
    - "VLM-as-a-Judge often pays limited attention to the image."
    - Bias reduced by up to 17%.
22. MJ-Bench 2024. https://arxiv.org/abs/2407.04842 [T]
    - "more accurate and stable feedback in natural language (Likert-scale) than numerical scales."
23. Zhang et al. 2025, *MLLMs Know Where to Look* (ICLR). https://arxiv.org/abs/2502.17422 and https://arxiv.org/html/2502.17422v1 [T]
    - Small-object accuracy drop: GPT-4o −7 pp, BLIP-2 −24 pp. Human crop: LLaVA-1.5 39.38% → 69.95%.
24. Kamath et al. 2023, *What's "up" with vision-language models?* https://arxiv.org/abs/2310.19785 [T]
    - "achieves 56% accuracy on our benchmarks vs. humans at 99%."
    - 18 models.
25. Rahmanzadehgervi et al. 2024, *Vision language models are blind*. https://arxiv.org/abs/2407.06581 [V]
    - "four state-of-the-art VLMs are only 58.07% accurate on average. Claude 3.5 Sonnet performs the best at 77.84%."
26. Tong et al. 2024, *Eyes Wide Shut? (MMVP)*. https://arxiv.org/abs/2401.06209 [T]
    - "including GPT-4V, struggle with straightforward questions across nine basic visual patterns."
27. Li et al. 2023, *POPE*. https://arxiv.org/abs/2305.10355 [T]
    - "they tend to generate objects that are inconsistent with the target images."
28. Anthropic, Claude vision docs. https://platform.claude.com/docs/en/build-with-claude/vision [V]
    - "might hallucinate or make mistakes when interpreting low-quality, rotated, or very small images under 200 pixels"; counts "approximate".
    - 1,568 px / 2,576 px long edge.
29. Google, Gemini video understanding. https://aistudio.google.com/docs/video-understanding [T]
    - "fast action sequences might lose detail due to the 1 FPS sampling rate."
    - About 66 tokens per frame (low resolution).
30. Lian et al. 2023, *GPT-4V with Emotion*. https://arxiv.org/abs/2312.04293 [T]
    - "cannot recognize micro-expressions that require specialized knowledge."
    - 21 datasets.
31. FaceXBench 2025. https://arxiv.org/abs/2501.10360 [T]
    - GPT-4o and Gemini "show significant room for improvement."
    - 5,000 questions, 14 tasks.

**Video judges and benchmarks**

32. He et al. 2024, *VideoScore*. https://arxiv.org/abs/2406.15252 and https://arxiv.org/html/2406.15252v3 [V]
    - "these multimodal language models also achieve very low agreement with human raters."
    - GPT-4o 23.0, Gemini-1.5-Pro 16.9, VideoScore 77.1 Spearman.
33. Huang et al. 2023, *VBench*. https://arxiv.org/abs/2311.17982 and https://arxiv.org/html/2311.17982v1 [T]
    - "the video order within each pair is randomized."
    - 16 dimensions; DINO subject consistency.
34. Sun et al. 2024, *T2V-CompBench*. https://arxiv.org/abs/2407.14505 [T]
    - "consistent attribute binding, dynamic attribute binding, spatial relationships, motion binding, action binding, object interactions, and generative numeracy."
    - 1,400 prompts.
35. Han et al. 2025, *Video-Bench* (CVPR). https://arxiv.org/abs/2504.04907 and https://arxiv.org/html/2504.04907v1 [V]
    - "the model often assigns the same (typically average) score to all videos."
    - Few-shot +10.33%. α human-human 0.52, human-Video-Bench 0.50, human-GPT 0.41.
36. Liu & Zhang 2025, *Is Your Video Language Model a Reliable Judge?* (ICLR). https://arxiv.org/abs/2503.05977v1 [T]
    - "incorporating collective judgments from such a mixed pool does not necessarily improve the accuracy of the final evaluation."

**Question decomposition for text-to-image**

37. Hu et al. 2023, *TIFA*. https://arxiv.org/abs/2303.11897 and https://arxiv.org/html/2303.11897v3 [T]
    - "counting, spatial relations, and composing multiple objects."
    - Spearman 59.7 vs CLIPScore 33.2. 4K prompts, 25K questions.
38. Cho et al. 2024, *Davidsonian Scene Graph*. https://arxiv.org/abs/2310.18235 and https://arxiv.org/html/2310.18235v4 [T]
    - "if the answer to a parent question is NO, all the answers to its child questions are counted as NO as well."
    - ρ 0.563. Text rendering VQA match 13.7-24.9%.
39. Lin et al. 2024, *VQAScore*. https://arxiv.org/abs/2404.01291 and https://arxiv.org/html/2404.01291v1 [T]
    - "LLaVA-1.5 biases towards answering 'Yes' to 80% of the questions should be answered with 'No'."
    - Winoground group 46.0 vs 7.8.
40. Wiles et al. 2024, *Gecko*. https://arxiv.org/abs/2404.16820 [T]
    - ">100K annotations"; a "QA-based auto-eval metric that is better correlated with human ratings."

**Objective metrics**

41. Deng et al., *ArcFace*. https://arxiv.org/abs/1801.07698 [T]
    - "Additive Angular Margin Loss".
42. InsightFace python package. https://github.com/deepinsight/insightface/tree/master/python-package [T]
    - "The pretrained models provided with this library are for non-commercial research only."
43. fal, *AuraFace-v1*. https://huggingface.co/fal/AuraFace-v1 [T]
    - Apache 2.0, commercial use allowed. LFW 0.99650.
44. Guo et al. 2024, *PuLID*. https://arxiv.org/html/2404.16022v2 [T]
    - "ID embeddings extracted using CurricularFace".
    - PuLID 0.733, InstantID 0.725, PhotoMaker 0.271.
45. Ruiz et al. 2022, *DreamBooth*. https://arxiv.org/html/2208.12242v2 [T]
    - DINO "not trained to ignore differences between subjects of the same class".
    - Real images DINO 0.774. Human correlation DINO 0.32 vs CLIP-I 0.27.
46. Fu et al. 2023, *DreamSim*. https://arxiv.org/abs/2306.09344 [T]
    - "focuses heavily on foreground objects and semantic content while also being sensitive to color and layout."
47. py-feat `xgb_au` model card. https://huggingface.co/py-feat/xgb_au/blame/main/README.md [T]
    - Lists AU6 and AU12. MIT licence, with dataset terms on the fitted models.
48. OpenFace 3.0 (2025). https://arxiv.org/html/2506.02891v1 [T]
    - "freely available for research purposes".
    - AU F1 59% DISFA / 59% BP4D vs OpenFace 2.0 50% / 53%.
49. Girard et al., *Reconsidering the Duchenne Smile*. https://pmc.ncbi.nlm.nih.gov/articles/PMC7193529 [T]
    - "AU6 may just be an artifact of smile intensity rather than a reliable and unique indicator of genuine positive emotion."
    - 136 people, 751 smiles; 64% reduction.
50. Bain et al. 2023, *WhisperX*. https://arxiv.org/abs/2303.00747 [T]
    - "word-level timestamps", "forced phoneme alignment".
51. Yuan, Liberman & Cieri 2006, *Towards an Integrated Understanding of Speaking Rate in Conversation*. https://www.ldc.upenn.edu/sites/default/files/interspeech2006-towards-integrated-understanding.pdf [V]
    - "an overall average rate of 196 words per minute (WPM)".
    - Range 111-291; net 236 WPM.
52. Prajwal et al. 2020, *Wav2Lip*. https://arxiv.org/abs/2008.10010 [T]
    - "new, rigorous evaluation benchmarks and metrics to accurately measure lip synchronization."

**Practitioner guides and statistics**

53. Hamel Husain, *LLM-as-a-Judge*. https://hamel.dev/blog/posts/llm-judge/ [V]
    - "report the judge's True Positive Rate and True Negative Rate separately. It took us only three iterations to achieve > 90% agreement."
54. Hamel Husain, *Evals FAQ*. https://hamel.dev/blog/posts/evals-faq/ [V]
    - "Label 100 to 200 examples for each failure mode"; "30 to 50 Pass examples and 30 to 50 Fail examples in both the dev and test sets"; "building a separate judge for each type of failure."
55. Hamel Husain, *Your AI Product Needs Evals*. https://hamel.dev/blog/posts/evals/ [T]
    - "track the correlation between model-based and human evaluation."
56. judgy (Hamel's evals course). https://github.com/ai-evals-course/judgy [T]
    - "θ̂ = (p_obs + TNR - 1) / (TPR + TNR - 1)"; "assumes … TPR + TNR > 1."
57. Eugene Yan, *Evaluating the Effectiveness of LLM-Evaluators*. https://eugeneyan.com/writing/llm-evaluators/ [V]
    - Pairwise is "more reliable—for subjective evals"; "where possible, I have my evaluators return binary outputs."
58. Anthropic, *Define success criteria and build evaluations*. https://platform.claude.com/docs/en/test-and-evaluate/develop-tests [V]
    - "Have detailed, clear rubrics"; "Encourage reasoning: Use a grader model with thinking on"; "Generally best practice to evaluate with a different model from the one used to generate the evaluated output."
59. OpenAI, *Evaluation best practices*. https://developers.openai.com/api/docs/guides/evaluation-best-practices [T]
    - "Use pairwise comparison or pass/fail for more reliability"; "Control for response lengths."
60. Google Vertex AI, *Gen AI evaluation overview*. https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/evaluation-overview [T]
    - "Rubrics are dynamically generated for each prompt, like unit tests."
61. Google Vertex AI, *PairwiseMetric*. https://docs.cloud.google.com/python/docs/reference/vertexai/latest/vertexai.evaluation.PairwiseMetric [T]
    - "compares two generative models' responses side-by-side."
62. Braintrust, *What is LLM-as-a-judge*. https://www.braintrust.dev/articles/what-is-llm-as-a-judge [T]
    - "Randomizing order across runs and comparing results in both directions."
63. Arize, *LLM-as-a-Judge*. https://arize.com/llm-as-a-judge/ [T]
    - "A perfect pass rate may reflect a strong application, an easy dataset, or an evaluator that misses failures."
64. Miller 2024, *Adding Error Bars to Evals*. https://arxiv.org/abs/2411.00640 and https://arxiv.org/html/2411.00640v1 [T]
    - "clustered standard errors can be over 3X larger than naive standard errors."
65. McHugh 2012, *Interrater reliability: the kappa statistic*. https://pmc.ncbi.nlm.nih.gov/articles/PMC3900052/ [T]
    - "any kappa below 0.60 indicates inadequate agreement."

**Ranking**

66. Chiang et al. 2024, *Chatbot Arena*. https://arxiv.org/html/2403.04132v1 [T]
    - "the BT coefficients are better for the purpose of statistical estimation."
    - Random sampling needs 54% more data. Crowd-expert agreement 72-83%.
67. Boubdir et al. 2023, *Elo Uncovered*. https://arxiv.org/abs/2311.17295 and https://arxiv.org/html/2311.17295v1 [T]
    - "ideally with Nperm≥100".
68. Qin et al. 2023, *Pairwise Ranking Prompting*. https://arxiv.org/html/2306.17563v2 [T]
    - "for each pair of documents, we will inquire the LLM twice by swapping their order."
    - O(N²) / O(N log N) / O(N).
69. Liu et al. 2024, *PairS (Aligning with Human Judgement)*. https://arxiv.org/abs/2403.16950 [T]
    - "employs pairwise comparisons locally and efficiently ranks candidate texts globally."

### Unverified items in this guide

- Face-size gate of 256 px and the 64 px minimum detail size.
- Any fixed ArcFace or AuraFace "same person" threshold.
- SyncNet LSE thresholds.
- AU-based over/under-acting heuristics and the blink-rate rule.
- "Temperature 0" as official advice, and temperature control in thinking modes.
- How accurate AU detectors are on generated faces.
- Pose-model "which hand" checks.
- The aesthetic-penalty quote from the search summary.
- The arithmetic on comparisons and power, which is my own.
- Acceptance bars (0.85 / 0.85 / κ 0.6, swap consistency 0.8), which are our choices, informed by Hamel and McHugh.
