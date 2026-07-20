---
name: roadmap-init
description: Create a fresh ROADMAP.md by scanning the repo and asking the user 3 minimal questions. Groups tasks by phase and code area. Never overwrites an existing ROADMAP.md.
---

# roadmap-init

**Trigger:** user types `/roadmap-init` or dice "hazme un roadmap", "create a roadmap", equivalente.

Este skill es hermano de `roadmap-update`. Ambos comparten las mismas invariantes al final.

## Procedimiento

### 1. Pre-scan del repo

Read (best-effort, no bloquear en missing files):
- `README.md` (repo root) para contexto
- `package.json` / `pyproject.toml` / `Cargo.toml` para nombre, description, deps
- Glob code files: `**/*.{js,ts,jsx,tsx,py,go,rs,rb,java,kt}` excluyendo `node_modules .git dist build .next coverage`
- Grep de `TODO|FIXME|HACK` comments en el código

**v1.3: Signals de Claude Code / Codex skill/plugin project.** Chequear también:
- `SKILL.md` en root con YAML frontmatter (`name:` y `description:`)
- `.claude-plugin/plugin.json`
- `.codex-plugin/plugin.json`
- `commands/*.md` con frontmatter YAML
- `bin/*.js` como entrypoint (no vale `bin/*.sh` — esos suelen ser wrappers del install)
- `plugins/**/skills/**/SKILL.md` (bundle multi-skill)

**Regla de clasificación auto:** si 2+ signals de la lista de arriba matchean, marcar el mapa mental como `type: skill-plugin`. Esto evita el bug clásico del generator pre-v1.0 (v0.14) que ve `install.sh/ps1` y clasifica como "Shell" — sin mirar bin/*.js ni SKILL.md.

Construir un mapa mental:
- Nombre inferido (de package.json o repo dir name)
- Stack detectado (de dependencies)
- **Type detectado (v1.3):** `skill-plugin` / `cli` / `web` / `electron` / `monorepo` / `python-package` / `unknown`
- Áreas del código (de la estructura de directorios: auth/, api/, ui/, etc.)
- Señales de pending work (TODOs, features parciales)

### 2. Preguntar al user (UN SOLO TURNO, 3+2 preguntas)

Preguntar TODO en un solo mensaje. NO hacer preguntas de a una:

```
Antes de generar el ROADMAP.md, tres cosas:

1. Nombre del proyecto (default: <name inferido>):
2. Qué problema resuelve (una frase):
3. Usuario primario (ej: "solo dev", "equipo interno", "usuarios finales"; default: "solo dev"):

Y dos decisiones de formato:

4. Metadata mode:
   - "rica" — cada task incluye owner + evidence + fecha inline en HTML comments
   - "lite" — solo `[ ] [P0] Task text`, sin metadata

5. (v1.3, opcional) Project type — el auto-detect infirió "<type detectado>". Si es incorrecto, forzá el tipo:
   - "cli"           — Node.js / Python / Rust CLI tool
   - "skill-plugin"  — Claude Code / Codex skill o plugin (SKILL.md + plugin.json)
   - "web"           — Next.js / Vite / React / Vue frontend
   - "electron"      — Electron desktop app
   - "monorepo"      — pnpm / npm workspaces
   - "auto"          — dejar que el skill infiera (default)

Cuál preferís? (respondé con los 4-5 valores separados por líneas)
```

Esperar respuesta. NO PROCEDER hasta que el user responda.

Si el user responde algo distinto a "auto" en la pregunta 5, usar ese type en Step 4. El override humano gana sobre el auto-detect.

### 3. Decidir ubicación del ROADMAP.md

Default: `./ROADMAP.md` (repo root).

Si ya existe algún roadmap-like file (`docs/roadmap.md`, `TODO.md`), PREGUNTAR:
"Detecté `<archivo existente>`. ¿Escribo un ROADMAP.md nuevo en el root, o rescribo `<archivo existente>`?"

Si el user tenía un `ROADMAP.md` ya (contradice el trigger), redirigir a `/roadmap-update` y parar.

### 4. Generar contenido

Estructura (hybrid grouping: fases + áreas):

```
# <project name>

<problem statement>

**Primary user:** <user>
**Project type (v1.3):** <type auto-detectado o forzado por user>

## Phase 0 — Baseline

### <área 1 detectada>
- [ ] [P0] <task inferida>

### <área 2>
- [ ] [P0] <task inferida>

## Phase 1 — Growth

### <área>
- [ ] [P1] <task>

## Phase 2 — Polish

- [ ] [P2] <task>
```

**Task inference según type (v1.3, max 10-15 total, quality over quantity):**

- **Común a todos los types:**
  - De `TODO/FIXME/HACK` comments → tasks `Address <TYPE>: <text> (<file>:<line>)`
  - De archivos sin test coverage adyacente → `Add tests for <module>`
  - De partial features detectados (imports/references a stubs) → `Complete <feature>`
  - De secciones del README que digan "TODO" o "Next" → `<text del README>`

- **type=`skill-plugin` (v1.3):** priorizar tasks específicas al ecosistema:
  - Por cada SKILL.md sin `description:` compacta → `Compact description in <skill-name>/SKILL.md (currently >200 chars)`
  - Por cada `commands/*.md` sin frontmatter → `Add frontmatter to commands/<name>.md`
  - Si falta `.claude-plugin/plugin.json` → `Add .claude-plugin/plugin.json manifest`
  - Si el bin/ no tiene tests → `Add smoke test for bin/<entrypoint>.js`
  - **NO generar** genéricos tipo "Add automated test harness for Shell" o "Document north star metrics for Shell" — esos son el bug clásico del generator legacy.

- **type=`cli`:** tasks tipo `Add --help output for <subcommand>`, `Add exit-code contract tests`, `Document argv parsing edge cases`.

- **type=`web`:** tasks tipo `Add loading states for <page>`, `Wire up form validation for <form>`, `Add a11y audit for <route>`.

- **type=`electron`:** tasks tipo `Wire up auto-updater`, `Add crash reporter`, `Sign installer for macOS/Windows`.

- **type=`monorepo`:** tasks tipo `Enforce shared tsconfig`, `Add cross-package test in CI`.

**Task anatomy según metadata mode elegido:**
- **rica**: `- [ ] [P0] Add login <!-- owner: pending, evidence: (none yet), added: YYYY-MM-DD -->`
- **lite**: `- [ ] [P0] Add login`

**Priorizar**:
- P0: baseline, blockers, tests missing, TODOs marcados como urgente
- P1: growth, features parciales, docs importantes
- P2: polish, nice-to-have

### 5. Escribir y reportar

Write ROADMAP.md via Write tool.

Emitir reporte estructurado:

```
═══ roadmap-init report ═══

CREATED: <path>

STATS:
  - Áreas detectadas: <n>
  - Tasks generadas: <n> total (P0: <n>, P1: <n>, P2: <n>)
  - Metadata mode: <rich | lite>
  - Project type (v1.3): <type> (auto-detected | user-forced)

NEXT:
  - Revisá las tasks, edit o borrá cualquiera que no aplique
  - Usá `/roadmap-update` cuando quieras que el agente refleje tu progreso en el código

═══ end report ═══
```

## Invariantes (jamás violar)

- **NUNCA** crear ROADMAP.md sin haber hecho las 3+2 preguntas al user primero.
- **NUNCA** sobreescribir un ROADMAP.md existente. Si existe, redirigir a `/roadmap-update`.
- **NUNCA** inventar tasks que no tengan base clara en el repo scan o en las respuestas del user.
- **NUNCA** exceder 15 tasks en la generación inicial. Menos es más — el user va a agregar más con `/roadmap-update` u otras interacciones.
- **NUNCA** generar tasks genéricas por lenguaje ("Add automated test harness for Shell", "Document north star for JavaScript") — ese es el bug clásico del generator pre-v1.0. Si no hay signal específico del repo, no generar la task.
- Si el user pidió modo "lite", NO agregar HTML comments ni metadata rica en las tasks generadas.
- Los slashcommands del skill hermano `/roadmap-update` NO son responsabilidad de este skill. Solo hacé init y salite.
