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

**v1.3: Logging explícito por tool call en modo B.** Al ejecutar cada tool call bajo modo short-circuit, prefijar la línea de status con:
- `[SC]` cuando la información viene de session context (ej: `[SC] usando package.json ya leído en turno 3`).
- `[SC→FS]` cuando el context no alcanzó y se dispara fallback puntual (ej: `[SC→FS] no encontré git log en session context, ejecuté git log --oneline -20`).

Sin este logging, la ambigüedad entre "no scaneé porque tenía context" vs "no scaneé porque me olvidé" es invisible al user.

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
- Detectar version source of truth con la **cascada v1.3** (Step 2a).
- `git log --oneline -20` para commits recientes.

En modo short-circuit: skipear las partes que ya tenés en session context, pero SIEMPRE hacer Read del ROADMAP.md y del archivo elegido por la cascada de versión (esos dos son mandatorios).

### 2a. Version source of truth — cascada (v1.3)

Intentar en este orden, quedarse con el PRIMERO que resuelve una versión semver válida. Reportar cuál se usó en el WARNINGS del reporte final (para que el humano confirme que el skill eligió bien).

1. `package.json.version` (Node/npm)
2. `pyproject.toml` — `[project].version` o `[tool.poetry].version` (Python)
3. `Cargo.toml` — `[package].version` (Rust)
4. `SKILL.md` (root) — YAML frontmatter `version:` (Claude Code / Codex skill)
5. `bin/**/*.js` — const `TOOL_VERSION` / `VERSION` / `PACKAGE_VERSION` (CLI zero-dep)
6. `git describe --tags --abbrev=0` (último tag semver del repo)

Si NINGUNA resuelve, avisar al user en el turno 0 y pedir explícito:
```
No pude detectar un version source. ¿Cuál usás?
  - Ruta del archivo (ej: "config.json")
  - Campo (ej: "version" o "meta.version")
  - O escribí "skip" para omitir el check de prose stale en esta corrida.
```

### 2b. Detectar prose stale (v1.1, ampliado v1.3)

Comparar la versión detectada en Step 2a con menciones de versión en el ROADMAP.md:

- Regex sobre el ROADMAP: buscar `v\d+\.\d+\.\d+`, "Estado actual — v...", "current version", "release v..." y similares.
- Si alguna versión mencionada en el ROADMAP != versión detectada → **flag "prose stale"** con:
  - Línea (número) donde apareció
  - Versión encontrada vs versión actual
  - Texto de la sección afectada
  - Label sugerido (ver Step 5 para la convención)

Este flag alimenta el diff en Step 5 con una sub-sección `PROSE UPDATE`.

### 2c. Detectar managed block basura (v1.3)

Si el ROADMAP.md tiene un `<!-- rs:managed:start -->` ... `<!-- rs:managed:end -->` (residuo del generator legacy pre-v1.0), evaluar heurística de "boilerplate genérico":

Contar tasks del bloque que contengan alguna de estas frases (case-insensitive):
- `"Stabilize <X> baseline"` / `"project baseline"`
- `"Document measurable"` / `"north star metrics"`
- `"Add automated test harness for <Language>"` (Shell, JavaScript, Python, etc.)
- `"Document <X> public API"` / `"Add test coverage for <X>"` (sin nombre específico de módulo)

Si **>50%** de las tasks del bloque matchean, agregar WARNING al reporte:
```
MANAGED BLOCK STALE: el bloque <!-- rs:managed --> parece boilerplate legacy
del generator pre-v1.0. Considerá:
  (a) Borrar el bloque completo y dejar solo la parte human-authored, o
  (b) Correr `npx roadmapsmith@0.14 generate` con project-type override si
      querés regenerar (nota: el generator ya no se shippa en v1.0+).
No modifico el managed block automáticamente.
```

**Cero acción automática** — el skill nunca borra el bloque. Solo avisa. El invariante "nunca modificar sin diff visible + OK" se mantiene.

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

### 3b. Detectar features shippeadas sin task (v1.3)

Correr `git log --oneline --since="30 days ago"` (o el rango que el user prefiera). Para cada commit que empiece con `feat:`, `fix:`, `refactor:`, o similar patrón convencional:

1. Extraer el subject del commit (después del type).
2. Grep el ROADMAP.md por 2-3 keywords significativos del subject.
3. Si **cero matches**, el commit representa una feature/fix shippeado sin task correspondiente.

Agregar al `NEW` del reporte:
```
NEW (features en git log sin task):
  - <commit subject> (<sha short>) — sugerido agregar como [x] retroactivo
```

**Aclaración de invariante:** el invariante "no inventar tasks solo del chat" (Invariantes, línea inferior) **NO aplica acá**. Git log ES evidencia del repo (persistente, versionada). Chat es efímero; commits no.

El user decide en Step 6 si acepta los retroactivos (`ok`), los rechaza (`no`), o pide detalle por commit.

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
- **v1.3: Task genérica con implementación real detectada** → propose RENAME+FLIP (ver abajo)

**v1.1: Prose updates.** Si Step 2b flageó prose stale, agregar sub-sección al diff:

```
PROSE UPDATE propuesto:
  Línea NN — sección "Estado actual"
  BEFORE: "## 2. Estado actual — v0.9.39"
  AFTER:  "## 2. Estado actual — v<versión detectada> [FIXED]"
```

Cada cambio de prose se muestra explícitamente con before/after. El user aprueba o rechaza cada uno individualmente (o todos con `ok`, ninguno con `no`).

**v1.3: RENAME+FLIP para tasks genéricas.** Si una task tiene texto vago (ej: "Add automated test harness for Shell", "Document project baseline") Y existe un archivo real que la implementa (grep del keyword principal → hit en un file específico), proponer rename+flip en el mismo diff:

```
RENAME+FLIP propuesto:
  Línea NN
  BEFORE: - [ ] Add automated test harness for Shell
  AFTER:  - [x] Add self-test for bin/lib/diff-classify.js
    ✅ evidence: bin/lib/diff-classify.self-test.js
```

Regla estricta: solo proponer RENAME+FLIP si la task ORIGINAL era vaga (matchea el heurístico de Step 2c O contiene solo palabras genéricas: "Add", "Document", "Stabilize", "Improve" + nombre de lenguaje) Y la evidencia es `strong` (archivo específico existente). Si la task original era específica pero mal, es un rename normal (no flip).

**v1.3: Convención de labels canónicos para prose.** Al proponer cambios de prose (Step 2b) o warnings sobre secciones, usar estos labels standard para que el ROADMAP quede consistente a lo largo de corridas:

- `[HISTÓRICO]` — texto correcto para su versión original, se mantiene por trazabilidad. Ej: bloque "Estado actual — v0.9.39" queda con `[HISTÓRICO]` al lado si el user quiere preservarlo.
- `[STALE]` — texto que quedó viejo pero el user no decidió aún si reemplazar. Marcar hasta próxima corrida.
- `[FIXED]` — reemplazo aplicado en esta corrida. Se agrega al AFTER del PROSE UPDATE.
- `[INFERRED]` — inferencia del skill que necesita revisión humana (ej: retroactivos de git log).

Sin esta convención, cada corrida elige labels ad-hoc y en 6 meses el ROADMAP es un caos de anotaciones inconsistentes.

### 6. Presentar diff + esperar OK

Mostrar al user:
1. El reporte estructurado (template abajo).
2. El diff completo de cambios propuestos (checkboxes + PROSE UPDATE + RENAME+FLIP si aplica).
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
- **NUNCA** inventar tasks basadas solo en el chat de la sesión. Solo agregar tasks si hay señal fuerte en el REPO (TODO comments, features parciales visibles en código, **commits en git log**). **Este invariante es estricto: la conversación es efímera, el ROADMAP es persistente. Git log SÍ cuenta como evidencia del repo** (v1.3).
- **NUNCA** trabajar sin haber leído el ROADMAP.md actual primero.
- **NUNCA** modificar el managed block (`<!-- rs:managed:start -->` ... `<!-- rs:managed:end -->`) automáticamente, ni siquiera cuando el heurístico de "basura" lo flaggea. Solo avisar (v1.3).
- Si el ROADMAP existente es "plano" (sin markers ni metadata), respetarlo. No agregar HTML comments ni metadata rica sin permiso explícito del user.
- Trabajar con TODO el ROADMAP en cada corrida (full scan). Nunca incremental sin decirle al user.
- **v1.1: CUALQUIER cambio de prose (headers, versions, textos que no sean checkboxes ni evidence lines) DEBE aparecer en el diff visible ANTES del OK.** Cero cambios silentes ni "de paso" — el scope creep en un solo `ok` es una violación blanda de este invariante.
- **v1.1: Al inicio SIEMPRE preguntar el modo de scan (full-scan / short-circuit).** No asumir. El humano elige el trade-off token vs determinismo.
- **v1.3: En modo short-circuit, loggear explícito `[SC]` (usando context) o `[SC→FS]` (fallback puntual) por cada tool call.** Sin este loggeo, la diferencia entre "no scaneé porque tenía context" vs "no scaneé porque me olvidé" es invisible al user.

## Template del reporte estructurado

Emitir SIEMPRE al final del update, incluso cuando cero cambios. Secciones vacías se rellenan con "(ninguno)" — nunca omitir una sección.

```
═══ roadmap-update report ═══

MODE: full-scan | short-circuit | short-circuit-fallback
VERSION SOURCE (v1.3): <archivo elegido por Step 2a> (ej: package.json / SKILL.md YAML / git tag)

DONE (marcadas [x] esta corrida):
  - <task text>

PENDING (siguen [ ]):
  - <task text> (weak evidence: <file>)

PROSE CHANGES (v1.1):
  - Línea NN: "<before>" → "<after> [FIXED]" (motivo: version mismatch)

RENAME+FLIP (v1.3):
  - Línea NN: "<task vaga>" → "<task específica> [x]" (evidence: <file>)

WARNINGS:
  - Ambigüedad no resuelta: <task text> (esperando respuesta del user)
  - Task [x] sin evidence: <task text> (sugerido revertir a [ ])
  - Task obsoleta: <task text> (propuesta borrar)
  - Prose stale detectada: <sección> menciona v<X.Y.Z>, versión actual v<A.B.C> [STALE]
  - MANAGED BLOCK STALE (v1.3): bloque parece boilerplate legacy, ver Step 2c

NEW (propuestas para agregar):
  - <task text> (motivo: <TODO en src/foo.js:42>)
  - <task text> (motivo: git log <sha> feat: <subject>) [INFERRED]

═══ end report ═══
```
