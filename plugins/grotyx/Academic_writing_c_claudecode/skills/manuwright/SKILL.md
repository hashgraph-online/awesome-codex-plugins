---
name: manuwright
description: Medical manuscript workflow with the ManuWright engine. Use when planning, drafting, revising or checking a paper in a folder that has project.json, drafts/draft_plan.md or knowledge/evidence.md, or when the user mentions ManuWright, draft plan, analysis plan, evidence.md, EVID citations, reviewer response or submission build.
---

# ManuWright workflow

1. Load the rules for the current step: `manuwright rules <keyword>` (for example `Citation Integrity`, `Draft Plan`, `Verification Gates`, `Phase 4`). Run `manuwright rules` once for the full workflow when the phase is unclear.
2. Phase order: setup and evidence, then analysis plan (approved), analysis, draft plan (approved), drafting (Methods, Results, Introduction, Discussion, Conclusion, Abstract, Title), style polish, QC (3+ rounds), finalize, revision.
3. Plan first. If `drafts/draft_plan.md` or `data/analysis_plan.md` is missing, incomplete or not approved by the author, stop and help complete it. Show the plan to the author. When they approve it explicitly in chat ("승인", "approve"), record it with `manuwright approve <plan> --kind analysis|draft --approved-by "<author>" --quote "<their exact words>"` (ticks the box, notes who/when/what, writes the hashed receipt). Never approve on your own judgement or from a general "continue".
4. Grounding. Cite only `[EVID:id]` keys in `knowledge/evidence.md` and use only numbers in `results/*.csv`. Register new sources in `evidence.md` (verified PMID/DOI) before citing them: `manuwright search "<query>"`.
5. Analysis code runs in the paper's own environment: `manuwright env` (once; uv-managed Python with the packages in `data/requirements.txt`), then `manuwright run data/py/<script>.py`. Do not install packages into, or debug, the system/Homebrew/pyenv Python; add packages to `data/requirements.txt` and rerun `manuwright env`. Cite the versions in `data/environment.lock.txt` in Methods.
6. Verify before saying a step is done (see the `manuwright-verify` skill).
7. Academic writing: before drafting or rewriting a section, run `manuwright style card <section>` and write to that card (moves, rules, phrasebank, register of the model paragraphs, the author's learned corpus style). Never reuse the model paragraphs' facts, numbers or citations. Fix the academic-prose findings reported after each edit; in `strict` mode a write with high-severity findings is blocked until rewritten. After a style rewrite of existing text, `manuwright style preserve <before> <after>` must print OK.
8. Evidence and revision safeguards: record `Claim Strength` for each evidence.md entry and run `manuwright claim-strength drafts`; `manuwright search audit` (metadata match, retractions) before submission; letter-blind re-review (`manuwright blind-review packet` / `check`) before recording response_alignment; `manuwright style edits` proposes rules from the author's edits, which only the author approves. When the author asks in chat, run the tool for them: "내 문체 배워줘" / "learn my style" -> `manuwright style learn <folder>` (3+ papers); "내가 고친 거 배워줘" -> `manuwright style edits --git <rev>` (or two files), show the proposals, and after they approve a rule in chat run `manuwright style edits --approve "<rule>" --approved-by "<author>" --quote "<their words>" --apply`; "과장 표현 검사해줘" -> `manuwright claim-strength drafts`; "참고문헌 다시 확인해줘" -> `manuwright search audit`; "블라인드 재검토" -> `manuwright blind-review packet ...`.
9. Guides live in the engine, not in the paper folder: read any `docs/<name>.md` the rules cite with `manuwright guide <name>` (several at once allowed; `manuwright guide` lists them). Every `manuwright rules` output ends with the guides it cites; read the ones for the current step in full before doing it.

## Journal fit and suggestions

"Does it fit Spine J?" / "which journal?": build a PubMed query from the population, intervention and outcome, then `manuwright journal fit "<NLM abbreviation>" --query "..."` or `manuwright journal suggest --query "..." [--review]`. With no journal profile, create one (`manuwright journal profile "<journal>" --url <official page>`), read the official Aims & Scope / Guide for Authors yourself and fill it; mark it verified only after the author confirms. Never state an impact factor, acceptance rate or policy that is not in the profile (docs/critical_review_protocol.md section 6).

## Personal library (reused across papers)

`manuwright library` shows where it is (`~/.manuwright/library/`, or `$MANUWRIGHT_HOME/library`). New papers get copies from it at `manuwright init`; Word styles are chosen per paper in `manuwright target`.

**"Register my writing style"** (the author added papers with `manuwright library writing add <pdf|md> --kind own|landmark|target_journal`):
1. Read the engine's `Style/style_guide.md` (folder next to `manuwright rules --path`) and follow its Extraction Framework and copyright policy: patterns, metrics and short phrases, never copied paragraphs.
2. For each source in `library/writing/PDF/<kind>/` without a matching `library/writing/<kind>/<same basename>.md`, write that markdown anchor.
3. Measure instead of guessing: run `manuwright style learn` (it reads the library PDFs, or pass files) so every section card carries the measured style and model paragraphs, and `manuwright style extract <text or md files>` for sentence length and citation density in the anchors.
4. Update `library/writing/terminology.md` (preferred and forbidden terms with context) and write `library/writing/style_spec.md` from the engine's `docs/style_spec_template.md` (`manuwright guide style_spec_template`), bound to the author's own papers.
5. Show the author a short summary of the voice you found and the files you wrote; do not change any paper folder.

**"Fill my team profile"** (from a CV, author list or earlier title page the author gives you): edit `library/profile/authors.md` (`manuwright library profile` creates it from the template). Copy names, degrees, affiliations, ORCID, emails and grant numbers exactly as given; leave `[...]` placeholders for anything not given; never guess an ORCID or grant number. Ask the author to check it. Papers created later copy it to `profile/authors.md`; an existing paper keeps its own copy.

**Keep what the author teaches across papers (memory).** When the author asks you to remember something ("기억해", "앞으로는 X 대신 Y", "공동저자 추가해줘", "소속이 바뀌었어", "remember", "from now on"), save it in the personal library, additions only, and say in one line what you saved where:
- a wording rule: `manuwright library term --prefer "X" --avoid "Y" [--context "..."]` (library and this paper; a CONFLICT means the library already prefers another word: ask);
- one author, affiliation, ORCID, email or grant: edit only that person's lines in `library/profile/authors.md` and in this paper's `profile/authors.md` if it exists; show the changed lines first; never delete other people or guess numbers;
- any other lesson (journal requirements, reviewer preferences, method choices): `manuwright library note "<one sentence>" --topic journal|reviewer|writing|method|other`; notes appear at every session start in paper folders.
"라이브러리 최신으로 받아줘" = `manuwright library sync --pull`; "이 논문 것을 라이브러리에 올려줘" = `manuwright library sync --push`; "차이 보여줘" = `manuwright library sync`. Sync only adds; a "differs" line (style spec, team profile) is merged by you on request, line by line, with the author's confirmation. Rules the author approves with `style edits --apply` go to the library automatically, and a session in a paper folder pulls the library's additions automatically (`manuwright config set library-sync auto|ask|off`).
