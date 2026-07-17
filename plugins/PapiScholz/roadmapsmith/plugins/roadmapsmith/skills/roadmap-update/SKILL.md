---
name: roadmap-update
description: Update ROADMAP.md truthfully based on real code. Full-scan the repo, evaluate evidence per task, propose a diff for user approval. Never flips [x] without verifiable evidence in code.
---

# roadmap-update

**Trigger (manual):** user types `/roadmap-update`, or says "actualizá el roadmap", "update the roadmap", or equivalent.

**Trigger (proactivo, experimental):** al terminar una tarea en la sesión actual que parezca coincidir con una task de ROADMAP.md, proponer el update antes de responder al user. NOTA v1.1: este trigger depende de que el agente se acuerde — sin enforcement mecánico se cae. Está siendo evaluado, ver ROADMAP del proyecto para la task de PostToolUse hook.

Este skill es hermano de `roadmap-init`. Ambos comparten las mismas invariantes al final.

## Procedimiento

### 0. Preflight — modo de scan (v1.1)

**PREGUNTAR AL USER PRIMERO** (antes de cualquier otro paso):

```
¿Modo de scan?
  A. full-scan (default, determinístico, ~20-30 tool calls: Glob + Read package.json + git log + evidence eval por task)
  B. short-circuit (más rápido, uso el contexto de la sesión si tengo suficiente; fallback a full-scan si no)
```

Esperar respuesta. Comportamiento:
- `A` o `full` o silence → seguir con Step 1 completo.
- `B` o `short` o `fast` → seguir con Step 1, pero en Step 2 usar session context en lugar de re-scannear si hay evidence reciente en la conversación (files leídos, git log ya visto, etc.). Si el context no alcanza, hacer fallback a full-scan Y notificar al user "(short-circuit fallback: context insuficiente, ejecuté full-scan)".

En AMBOS modos, el report final debe incluir un campo `MODE:` explícito (full-scan / short-circuit / short-circuit-fallback).

### 1. Locate ROADMAP.md

Buscar en este orden:
1. `ROADMAP.md` (repo root)
2. `roadmap.md` (repo root)
3. `docs/roadmap.md`
4. `TODO.md` (último recurso)

Si ninguno existe, decirle al user: "no encuentro ROADMAP.md. Corré `/roadmap-init` primero" y parar.

### 2. Full scan del estado actual

- Read el ROADMAP.md completo. Extraer TODAS las líneas de task (`- [ ] ...` y `- [x] ...`), preservando `<!-- rs:task=... -->` markers si existen.
- Glob code files: `**/*.{js,ts,jsx,tsx,py,go,rs,rb,java,kt,swift,cs,php}` excluyendo `node_modules .git dist build .next coverage __pycache__ .venv .worktrees`.
- Read `package.json` / `pyproject.toml` / `Cargo.toml` para nombre, deps, scripts, **y versión** (necesaria para Step 2b).
- `git log --oneline -20` para commits recientes.

En modo short-circuit: skipear las partes que ya tenés en session context, pero SIEMPRE hacer Read del ROADMAP.md y del package.json (esos dos son mandatorios).

### 2b. Detectar prose stale (v1.1)

Comparar la versión del `package.json` (root, no `legacy/`) con menciones de versión en el ROADMAP.md:

- Regex sobre el ROADMAP: buscar `v\d+\.\d+\.\d+`, "Estado actual — v...", "current version", "release v..." y similares.
- Si alguna versión mencionada en el ROADMAP != `package.json.version` → **flag "prose stale"** con:
  - Línea (número) donde apareció
  - Versión encontrada vs versión actual
  - Texto de la sección afectada

Este flag alimenta el diff en Step 5 con una sub-sección `PROSE UPDATE`.

### 3. Evaluar evidence por task (multi-signal)

Para cada task, combinar estas señales:

- **Grep**: extraer 2-3 keywords significativos del texto (nombres propios, function names, paths). Buscar en los code files.
- **File/function match**: si la task menciona un archivo o función específica (ej: `src/auth.js`, `loginUser()`), verificar que exista.
- **Session context**: si en el chat actual ya leíste/escribiste files que matchean la task, contar como señal.
- **Git log**: si un commit reciente menciona la task, weight it.

Asignar un nivel de evidence a cada task:
- **strong**: múltiples señales convergen en files específicos
- **weak**: 1 sola señal, ambigua o genérica
- **none**: cero señal en el repo
- **ambiguous**: > 5 candidatos, no confident

### 4. Manejar ambigüedad

Si una task tiene evidence `ambiguous` (>5 candidatos posibles), NO DECIDIR autónomo. En el diff proposal, listar los top 3 candidatos y preguntar al user:

"'<task text>' — ¿se refiere a alguno de estos? [1: <fileA>] [2: <fileB>] [3: <fileC>] [ninguna]"

Esperar respuesta antes de decidir el diff para esa task.

### 5. Construir el diff proposal (NO APLICAR AÚN)

Reglas de transición por task:
- `[ ]` + `strong` → propose flip a `[x]`
- `[x]` + `none` → propose flip a `[ ]` con WARNING "marcada sin evidence"
- `[ ]` + `weak` → mantener `[ ]`, notar "weak evidence, considerá agregar Evidence: line"
- `[x]` + `weak` → mantener `[x]`, notar "weak backing, agregá Evidence: line para consolidar"
- Task obsoleta (files/features que ya no existen) → propose BORRAR con confirmación explícita
- TODOs / partial features detectados en el repo que no están en el ROADMAP → propose AGREGAR nueva task

**v1.1: Prose updates.** Si Step 2b flageó prose stale, agregar sub-sección al diff:

```
PROSE UPDATE propuesto:
  Línea NN — sección "Estado actual"
  BEFORE: "## 2. Estado actual — v0.9.39"
  AFTER:  "## 2. Estado actual — v<package.json.version>"
```

Cada cambio de prose se muestra explícitamente con before/after. El user aprueba o rechaza cada uno individualmente (o todos con `ok`, ninguno con `no`).

### 6. Presentar diff + esperar OK

Mostrar al user:
1. El reporte estructurado (template abajo).
2. El diff completo de cambios propuestos (checkboxes + PROSE UPDATE si aplica).
3. Pregunta explícita: "aplico estos cambios? (ok / no / detalle)".

Comportamiento por respuesta:
- `ok` → paso 7.
- `no` → descartar todo, no escribir.
- `detalle <n>` o rechazo específico → iterar el diff aplicando solo lo aceptado.

### 7. Escribir y confirmar

Aplicar los cambios aprobados a ROADMAP.md via Edit tool. Preservar formatting, indentation, y markers exactos.

Emitir el reporte final estructurado confirmando lo que se escribió.

## Invariantes (jamás violar)

- **NUNCA** flipear `[x]` sin evidence verificable (nivel `strong`).
- **NUNCA** modificar ROADMAP.md sin mostrar el diff completo y esperar OK del user.
- **NUNCA** borrar una task sin confirmación explícita del user.
- **NUNCA** inventar tasks basadas solo en el chat de la sesión. Solo agregar tasks si hay señal fuerte en el REPO (TODO comments, features parciales visibles en código). **Este invariante es estricto: la conversación es efímera, el ROADMAP es persistente.**
- **NUNCA** trabajar sin haber leído el ROADMAP.md actual primero.
- Si el ROADMAP existente es "plano" (sin markers ni metadata), respetarlo. No agregar HTML comments ni metadata rica sin permiso explícito del user.
- Trabajar con TODO el ROADMAP en cada corrida (full scan). Nunca incremental sin decirle al user.
- **v1.1: CUALQUIER cambio de prose (headers, versions, textos que no sean checkboxes ni evidence lines) DEBE aparecer en el diff visible ANTES del OK.** Cero cambios silentes ni "de paso" — el scope creep en un solo `ok` es una violación blanda de este invariante.
- **v1.1: Al inicio SIEMPRE preguntar el modo de scan (full-scan / short-circuit).** No asumir. El humano elige el trade-off token vs determinismo.

## Template del reporte estructurado

Emitir SIEMPRE al final del update, incluso cuando cero cambios. Secciones vacías se rellenan con "(ninguno)" — nunca omitir una sección.

```
═══ roadmap-update report ═══

MODE: full-scan | short-circuit | short-circuit-fallback

DONE (marcadas [x] esta corrida):
  - <task text>

PENDING (siguen [ ]):
  - <task text> (weak evidence: <file>)

PROSE CHANGES (v1.1):
  - Línea NN: "<before>" → "<after>" (motivo: version mismatch)

WARNINGS:
  - Ambigüedad no resuelta: <task text> (esperando respuesta del user)
  - Task [x] sin evidence: <task text> (sugerido revertir a [ ])
  - Task obsoleta: <task text> (propuesta borrar)
  - Prose stale detectada: <sección> menciona v<X.Y.Z>, package.json dice v<A.B.C>

NEW (propuestas para agregar):
  - <task text> (motivo: <TODO en src/foo.js:42>)

═══ end report ═══
```
