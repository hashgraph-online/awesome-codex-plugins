---
name: smart-init
description: Conversational onboarding for A Team. Detects ROADMAP.md, extracts context, generates INIT.md without requiring technical knowledge. Invoked automatically by the orchestrator when INIT.md is missing.
---

# Smart Init — Conversational Onboarding

## Trigger

This skill is invoked by the orchestrator when `/orchestrate init` is called and no `INIT.md` exists.

## Detection Sequence

Check in this order:

1. `INIT.md` exists → stop, use current init flow unchanged
2. `ROADMAP.md` exists → Path A (extract from ROADMAP)
3. `ROADMAP_*.md` exists (e.g. `ROADMAP_icd10.md`) → Path A (extract from that file)
4. Neither exists → Path B (full 5-question interview)

---

## Path A — ROADMAP Exists

Read the ROADMAP file and extract:

| Look for in ROADMAP | Maps to INIT.md field |
|--------------------|-----------------------|
| Project name in H1 or title | Project name |
| Description paragraph | Project overview |
| Stack table or technology mentions | Languages & stack |
| "Princípios não-negociáveis" or "Non-negotiable" section | Immutable rules |
| "Próximo" / "Next" / "Roadmap" items | Active work context |
| Compliance mentions (GDPR, local-first, privacy, HIPAA) | Compliance scope |
| "Feito" / "Done" section | Existing coverage |

After extraction, ask **only one question** (the only thing a ROADMAP cannot tell you):

> "Que ferramentas de IA estás a usar para escrever código neste projecto?"
> → A) Claude Code
> → B) Codex CLI
> → C) Cursor
> → D) OpenCode
> → E) Várias — escolho mais do que uma

Then generate INIT.md (see Template section below) and show the review gate.

---

## Path B — No ROADMAP (Full Interview)

Ask these 5 questions, one at a time. Use plain language — assume the user is non-technical.

**Q1 (free text):**
> "O que queres construir? Descreve com as tuas palavras."

**Q2 (multiple choice):**
> "Já existe código ou começas do zero?"
> → A) Começo do zero
> → B) Já existe código
> → C) Não tenho a certeza

*If answer is B: run stack inference silently (see Stack Inference section).*

**Q3 (multiple choice):**
> "Que tipo de projecto é?"
> → A) App web (abre no browser)
> → B) App móvel (iPhone ou Android)
> → C) API ou serviço de backend
> → D) Análise de dados ou automação
> → E) Outro

**Q4 (multiple choice):**
> "Em que dispositivo ou plataforma deve correr?"
> → A) Browser (qualquer dispositivo)
> → B) iPhone / iPad
> → C) Android
> → D) Desktop (Windows / Mac / Linux)
> → E) Servidor / cloud

**Q5 (multiple choice):**
> "Que ferramentas de IA estás a usar para escrever código?"
> → A) Claude Code
> → B) Codex CLI
> → C) Cursor
> → D) OpenCode
> → E) Várias — escolho mais do que uma

After Q5: generate INIT.md, show review gate, then **offer to create ROADMAP.md**:
> "Queres que eu crie um ROADMAP.md para este projecto com base no que descreveste? É útil para futuras sessões."

---

## Stack Inference (Path B, answer B to Q2 only)

Run silently after the user answers B. Do NOT run for new projects (answer A or C).

```bash
git ls-files | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -10
```

Extension → stack mapping:
- `.kt` → Kotlin / Android (agents: kotlin-reviewer, compose-ui)
- `.swift` → Swift / iOS (agents: swift-reviewer)
- `.py` → Python (agents: python-reviewer)
- `.ts` or `.tsx` → TypeScript / React (agents: code-reviewer)
- `.go` → Go (agents: go-reviewer)
- `.rs` → Rust (agents: rust-reviewer)
- `.dart` → Flutter (agents: flutter-reviewer)
- `.java` → Java / Android (agents: kotlin-reviewer as fallback)

Confidence threshold: if one extension accounts for >40% of tracked files, pre-fill Q3/Q4 and confirm with user. If ambiguous, ask normally.

---

## Review Gate

After generating INIT.md, display ONLY the `## O que entendi` section and ask:

> "Está correcto? Falta alguma coisa?"

- User says "ok" / "sim" / "yes" → run `/orchestrate init` automatically
- User describes a correction → update the relevant INIT.md section, show `## O que entendi` again
- After 3 correction rounds without approval → ask user to edit INIT.md manually: "Não consegui perceber a correcção. Por favor edita o INIT.md directamente e diz 'ok' quando estiver pronto."

---

## Codex Warning

Show this **before** the final approval:

> "Última coisa: o Codex vai pedir para aprovares um script de segurança na próxima sessão. Clica em 'Trust' para continuar — é o script de estado da A Team."

---

## INIT.md Template

Generate this file at the project root. Fill each field from the interview answers or ROADMAP extraction.

```markdown
## O que entendi
[Plain language summary: what the project is, inferred stack, active AI platforms, agent count after init]

Se algo estiver errado, edita este ficheiro antes de continuar.

---

# INIT.md — [Project Name]

> Run `/orchestrate init` after reviewing this file.

## Project Overview

**Name:** [from Q1 or ROADMAP H1]
**Type:** [from Q3: web app / mobile app / API / data / other]
**Status:** [New project / Active development]
**Description:** [from Q1 free text or ROADMAP description]

## Languages & Stack

[Check all that apply — inferred from ROADMAP or stack scan]
- [ ] Kotlin
- [ ] Swift
- [ ] Python
- [ ] TypeScript / JavaScript
- [ ] Go
- [ ] Rust
- [ ] Flutter / Dart
- [ ] Other: ___

**Framework / UI:** [inferred or left blank]
**Database:** [inferred or left blank]
**Build system:** [inferred or left blank]

## Compliance Scope

[Extracted from ROADMAP compliance mentions, or left unchecked]
- [ ] GDPR
- [ ] Child privacy / COPPA
- [ ] Local-first / no external data
- [ ] HIPAA
- [ ] PCI-DSS

## Active AI Platforms

[From Q5 or Path A question]
- [ ] Claude Code
- [ ] Codex CLI
- [ ] Cursor
- [ ] OpenCode

## Non-Negotiable Rules

[Extracted from ROADMAP "princípios não-negociáveis" section, or left blank]

## Active Work / Next Steps

[Extracted from ROADMAP "Próximo" / "Next" section, or left blank]

## Agents to Prune

[Inferred from stack — list agents irrelevant to this project's languages/domain]
```
