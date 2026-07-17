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

Construir un mapa mental:
- Nombre inferido (de package.json o repo dir name)
- Stack detectado (de dependencies)
- Áreas del código (de la estructura de directorios: auth/, api/, ui/, etc.)
- Señales de pending work (TODOs, features parciales)

### 2. Preguntar al user (UN SOLO TURNO, 3+1 preguntas)

Preguntar TODO en un solo mensaje. NO hacer preguntas de a una:

```
Antes de generar el ROADMAP.md, tres cosas:

1. Nombre del proyecto (default: <name inferido>):
2. Qué problema resuelve (una frase):
3. Usuario primario (ej: "solo dev", "equipo interno", "usuarios finales"; default: "solo dev"):

Y una decisión de formato:

4. Metadata mode:
   - "rica" — cada task incluye owner + evidence + fecha inline en HTML comments
   - "lite" — solo `[ ] [P0] Task text`, sin metadata

Cuál preferís?
```

Esperar respuesta. NO PROCEDER hasta que el user responda.

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

**Task inference** (max 10-15 total, quality over quantity):
- De `TODO/FIXME/HACK` comments → tasks `Address <TYPE>: <text> (<file>:<line>)`
- De archivos sin test coverage adyacente → `Add tests for <module>`
- De partial features detectados (imports/references a stubs) → `Complete <feature>`
- De secciones del README que digan "TODO" o "Next" → `<text del README>`

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

NEXT:
  - Revisá las tasks, edit o borrá cualquiera que no aplique
  - Usá `/roadmap-update` cuando quieras que el agente refleje tu progreso en el código

═══ end report ═══
```

## Invariantes (jamás violar)

- **NUNCA** crear ROADMAP.md sin haber hecho las 3 preguntas al user primero.
- **NUNCA** sobreescribir un ROADMAP.md existente. Si existe, redirigir a `/roadmap-update`.
- **NUNCA** inventar tasks que no tengan base clara en el repo scan o en las respuestas del user.
- **NUNCA** exceder 15 tasks en la generación inicial. Menos es más — el user va a agregar más con `/roadmap-update` u otras interacciones.
- Si el user pidió modo "lite", NO agregar HTML comments ni metadata rica en las tasks generadas.
- Los slashcommands del skill hermano `/roadmap-update` NO son responsabilidad de este skill. Solo hacé init y salite.
