# roadmapsmith

[![skills.sh](https://skills.sh/b/PapiScholz/roadmapsmith)](https://skills.sh/PapiScholz/roadmapsmith)

Una habilidad para agentes de IA (Claude Code, Codex, o cualquier host que soporte skills en formato SKILL.md) que mantiene tu `ROADMAP.md` al día automáticamente. El agente lo crea, y después lo actualiza solo cuando ve evidence real en el código. Sin CLIs, sin configs.

## Install

Standard skills.sh CLI (detecta el agente automáticamente y soporta 70+ hosts):

```bash
# Direct add
npx skills add PapiScholz/roadmapsmith

# List first (revisa qué skills declara el repo antes de instalar)
npx skills add PapiScholz/roadmapsmith --list

# Search por keyword (aparece cuando skills.sh indexa el repo, ~1h después del primer add)
npx skills find roadmap

# Web (aparece cuando skills.sh indexa el repo)
# https://skills.sh/
```

Legacy shim (equivalente, delega al comando de arriba):

```bash
npx github:PapiScholz/roadmapsmith
```

Para Codex nativo, el manifest `.codex-plugin/plugin.json` en la raíz también declara los skills — instalación vía Codex plugin marketplace funciona igual.

## Uso (dos slashcommands)

```
/roadmap-init      # una vez, al arrancar un repo
/roadmap-update    # cuando querés que el agente refleje los cambios
```

That's it.

- `/roadmap-init` te hace 3 preguntas mínimas (nombre del proyecto, problema, usuario), escanea el repo, y crea `ROADMAP.md` con tasks agrupadas por fase y área del código.
- `/roadmap-update` releva el código en busca de evidence, te propone un diff con los cambios (`[ ]→[x]`, warnings, tareas nuevas), y espera un "ok" antes de escribir. Nunca marca una task como completa sin evidence verificable.

Si el agente cree que completó una tarea mientras trabajás, también te va a proponer marcarla antes de terminar su respuesta.

## Release (mantainers)

Dos comandos y el resto es automático:

```bash
npm version patch          # o minor / major
git push --follow-tags
```

Bajo el capó: el hook `version` de npm corre `scripts/sync-skills.js --fix` y propaga la nueva version a los 4 manifests (`.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, `plugins/roadmapsmith/.codex-plugin/plugin.json`, `skills.json`) antes del commit. Al pushear el tag, `.github/workflows/release.yml` publica a npm y crea el GitHub release. `prepublishOnly` corre un `--check` final como safety net.

No editar la `version` de los manifests a mano — la fuente de verdad es `package.json`. CI (`mirror-check.yml`) falla si hay drift.

## Personal tool

Esto es una herramienta personal. Feedback bienvenido vía issues; no busco adopción activa. Si te sirve, genial. Si no, `TODO.md` cubre el 90% del valor con menos ceremonia.

<details>
<summary>Legacy — CLI v0.15, deprecated</summary>

La versión previa (v0.10 a v0.15) era un CLI en Node con validator, audit engine, drift detection, 312 tests. Todo eso vive en [`legacy/`](legacy/) sin desarrollo activo. Ver [`legacy/README.md`](legacy/README.md).

El pivote a v1.0.0 tiró la ceremonia (validator, tests, marketing) y dejó solo lo que el user original quería: **un skill, dos slashcommands, ROADMAP.md al día**.

</details>
