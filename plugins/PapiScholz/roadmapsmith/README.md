# roadmapsmith

[![skills.sh](https://skills.sh/b/PapiScholz/roadmapsmith)](https://skills.sh/PapiScholz/roadmapsmith)

Un skill para agentes de IA (Claude Code, Codex, y cualquier host que lea `SKILL.md`) que mantiene tu `ROADMAP.md` coherente con lo que hay en el código. Dos slashcommands: uno para crearlo, otro para actualizarlo — el agente escanea el repo, pide evidence real antes de marcar `[x]`, y te pasa un diff antes de escribir.

## El problema

- Los `ROADMAP.md` se pudren: alguien marca `[x]` una task que no está terminada, o deja `[ ]` algo que ya se shippeó, y a los dos meses el archivo miente.
- Chequear a mano cada task contra el código no escala: el agente puede leer todo el repo en segundos y proponerte el diff.
- Marcar completado sin evidence verificable es autoengaño — este skill nunca flipea `[ ] → [x]` sin encontrar el archivo/símbolo que respalda la task.

## Cómo funciona (dos slashcommands)

```
/roadmap-init      # una vez, al arrancar un repo
/roadmap-update    # cuando querés reflejar tu progreso
```

- **`/roadmap-init`** — Te hace 3 preguntas mínimas (nombre, problema, usuario), escanea el repo, y genera `ROADMAP.md` con tasks agrupadas por fase (P0/P1/P2) y área del código. Nunca sobreescribe un `ROADMAP.md` existente.
- **`/roadmap-update`** — Releva el código en busca de evidence, te propone un diff (tareas a marcar, warnings de checked-sin-evidence, tareas nuevas detectadas), y espera tu `ok` antes de escribir. Modo `full-scan` (determinístico) o `short-circuit` (usa el contexto de la sesión si alcanza).

Full spec de cada uno:
[`skills/roadmap-init/SKILL.md`](skills/roadmap-init/SKILL.md) · [`skills/roadmap-update/SKILL.md`](skills/roadmap-update/SKILL.md)

## Cómo se ve

Antes:

```markdown
## Phase 0 — Baseline
### auth
- [ ] [P0] Add login endpoint
- [ ] [P0] Hash passwords with bcrypt
- [ ] [P0] Session cookies
```

Después de `/roadmap-update` (ya implementaste dos):

```markdown
## Phase 0 — Baseline
### auth
- [x] [P0] Add login endpoint <!-- evidence: src/auth/login.ts:14 -->
- [x] [P0] Hash passwords with bcrypt <!-- evidence: src/auth/hash.ts:8 -->
- [ ] [P0] Session cookies
```

El diff se te muestra en el chat antes de escribir. Si el agente marcó algo sin evidence real, aparece como `⚠️ checked pero sin evidence` en la propuesta.

## Install

Un comando:

```bash
npx skills add PapiScholz/roadmapsmith
```

Detecta el agente (Claude Code, Codex, 70+ más) e instala los dos skills en el lugar correcto. Nada más.

<details>
<summary>Otras vías de instalación</summary>

```bash
# Ver qué skills declara el repo antes de instalar
npx skills add PapiScholz/roadmapsmith --list

# Buscar por keyword (una vez que skills.sh indexa el repo, ~1h después del primer add)
npx skills find roadmap
```

- **Web:** [`https://skills.sh/PapiScholz/roadmapsmith`](https://skills.sh/PapiScholz/roadmapsmith)
- **Shim legacy** (equivalente, delega al `skills add` de arriba): `npx github:PapiScholz/roadmapsmith`
- **Codex plugin nativo:** el manifest `.codex-plugin/plugin.json` en la raíz declara los mismos skills — instalación vía Codex plugin marketplace funciona sin pasos extra.

</details>

## Update

```bash
npx skills update
```

Actualiza todos los skills instalados. Para actualizar solo uno: `npx skills update roadmap-init` o `npx skills update roadmap-update` (nombres de los skills, no del repo).

> **Warning esperado** — vas a ver `the following skills appear to have been deleted upstream` listando ~19 nombres viejos (`roadmap-sync`, `audit`, `zero`, `road`, etc.) y una cascada de `No matching skills found`. Es ruido cosmético del catálogo público de skills.sh, que todavía cachea entries de pre-v1.3.0. Ya está reportado upstream — respondé `Yes` para limpiar, los `No matching skills found` que siguen son no-ops porque nunca los tuviste instalados.

### ¿Ya tenías el CLI viejo instalado global?

Pre-v1.0.0 el paquete era un CLI y se instalaba con `npm i -g roadmapsmith`. Si `roadmapsmith --version` te devuelve `0.14.x`, tenés ese binario colgado — la instalación de skills es una ruta paralela y no lo pisa. Podés dejarlo (no molesta) o limpiarlo:

```bash
npm uninstall -g roadmapsmith
```

Post-v1.0.0 la única "instalación" que necesitás es la de skills; ya no hay CLI global que actualizar.

## Estado

Herramienta personal, sin roadmap comercial. Feedback y bug reports bienvenidos vía [issues](https://github.com/PapiScholz/roadmapsmith/issues). MIT.

Mantenimiento y flujo de release: [`docs/RELEASING.md`](docs/RELEASING.md).

<details>
<summary>Legacy — CLI v0.15 (deprecated)</summary>

La versión previa (v0.10 a v0.15) era un CLI en Node con validator, audit engine, drift detection y 312 tests. Todo eso vive en [`legacy/`](legacy/) sin desarrollo activo — ver [`legacy/README.md`](legacy/README.md).

El pivote a v1.0.0 tiró la ceremonia (validator, tests, marketing) y dejó solo lo que el user original quería: un skill, dos slashcommands, `ROADMAP.md` al día.

</details>
