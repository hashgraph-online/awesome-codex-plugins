# Reference: the ORE adapter

Risk Desk adds no XVA model. `risk_xva` (`src/riskdesk/server.py:207-214`)
and `riskdesk xva` (`src/riskdesk/cli.py:52-54, 74-75`) both call
`run_ore` (`src/riskdesk/ore.py:64-85`), which checks the project, runs
ORE in a separate Python process (`src/riskdesk/ore_worker.py`) and
translates its reports. Pinned backend: `open-source-risk-engine==1.8.16.0`,
the `xva` extra in `pyproject.toml`. The reproduction route and the pinned
regression figures are in `docs/ORE.md` of the repository; they are not
repeated here.

## Inputs

| argument | rule | code |
|---|---|---|
| `data_mode` | `synthetic`, `user-licensed` or `upstream-example`; the caller's declaration, checked first | `ore.py:61, 65-66` |
| `project` | a directory; resolved to an absolute path | `ore.py:11` |
| `config` | relative to `project`, must resolve to a file inside it, root tag `ORE` | `ore.py:12-19` |
| `output` | must not be inside `project`; created new, so an existing directory is refused | `ore.py:15-16, 49`, `tests/test_ore.py:19-24, 32-35` |

Checks on the configuration before anything runs (`ore.py:20-47`):

- `Analytics/Analytic[@type='simulation']` and `[@type='xva']` both have
  `active` set to `Y` or `TRUE`. Otherwise refused: an old cube is never
  reused (`tests/test_ore.py:27-29`).
- `Setup` has `inputPath` and `outputPath`; `inputPath` is a directory
  inside the project.
- Every input file parameter (`marketDataFile`, `fixingDataFile`,
  `curveConfigFile`, `conventionsFile`, `marketConfigFile`,
  `pricingEnginesFile`, `portfolioFile`, `calendarAdjustment`,
  `currencyConfiguration`, `simulationConfigFile`, `csaFile`) resolves to a
  file inside the project.
- Every output file parameter (`logFile`, `outputFileName`,
  `scenariodump`, `cubeFile`, `scenarioFile`,
  `aggregationScenarioDataFileName`, `rawCubeOutputFile`,
  `netCubeOutputFile`) is a bare file name.
- No symlink anywhere in the project.

Then (`ore.py:45-58`): the SHA-256 of every project file is recorded as
`input_hashes`; the output directory is created; `inputPath` and
`outputPath` are rewritten to absolute paths and `continueOnError` is
forced to `false` in a copy, `OUTPUT/effective-ore.xml`. The project's own
files are not modified (`tests/test_ore.py:19-23`).

## The run

`sys.executable -m riskdesk.ore_worker OUTPUT/effective-ore.xml`, working
directory the project, stdout and stderr to `OUTPUT/worker.log`, timeout
600 seconds (`ore.py:64, 68-71`). The worker imports `ORE`, or fails with
"Install riskdesk[xva] for the ORE backend" (`ore_worker.py:9-12`), then
runs `ORE.OREApp` (`ore_worker.py:13-16`).

Refusals after the run (`ore.py:72-78`), each a `RuntimeError` and no summary:

- worker exit code not zero: "ORE failed; inspect OUTPUT/worker.log". A
  missing backend arrives this way; its message is in `worker.log`.
- ORE reported any error: "ORE reported errors; inspect ore-result.json"
  (`tests/test_ore.py:38-45`). `riskdesk-xva.json` is not written.
- no rows in the `xva` report: "ORE produced no XVA rows".

The output directory exists from the start of the run, so a retry needs a
new `output`.

## What is kept

Only the report named `xva` and reports whose names start `exposure_`
(`ore_worker.py:19-21`). Each becomes `{"columns": [...], "rows": [...]}`
with ORE's header text as keys (`ore_worker.py:22-36`). Column types:
size and real as numbers, dates as ISO text, periods as text, and ORE's
`nullDouble()` sentinel as JSON null (`ore_worker.py:18, 25-35`). The
netting-set exposure report of netting set `ID` is
`exposure_nettingset_ID` (`scripts/ore_smoke.py:37`).

Result fields from the worker (`ore_worker.py:39-45`): `backend`,
`backend_version`, `backend_git_hash`, `currency` (the xva analytic's
`baseCurrency`), `as_of` (`Setup/asofDate`, as written in the
configuration), `requested_xva_flags` (whichever of `cva`, `dva`, `fva`,
`colva`, `collateralFloor`, `mva`, `kva` the xva analytic sets), `errors`
and `reports`. Added by the adapter (`ore.py:79-83`): `data_mode`,
`input_hashes`, `degraded` (false), `degraded_reason` (null),
`assumptions` and `artifact`, the path of `OUTPUT/riskdesk-xva.json`,
which holds the same result (`ore.py:84`).

Files left in `OUTPUT`: `effective-ore.xml`, `worker.log`,
`ore-result.json`, `riskdesk-xva.json`, and whatever ORE itself writes to
its `outputPath`.

## Reading the XVA report

- Netting-set and trade rows overlap (`docs/ORE.md`). For the upstream
  example, `scripts/ore_smoke.py:35-39` asserts two rows whose CVA agree
  to within 1e-8: adding them would double count.
- Null is unavailable, not zero. The same script asserts that `MVA` is
  null on the second row (`scripts/ore_smoke.py:36`).
- A column whose adjustment `requested_xva_flags` does not request is a
  disabled calculation; a zero there is not a result.
- The result is not a Risk Desk envelope: there is no `source` and no
  `input_sha256`. Cite the `artifact` path, `backend_version` and
  `input_hashes` instead.

## Into risk_exposure_profile

`risk_exposure_profile` (`src/riskdesk/counterparty.py:292-361`) takes the
rows of one `exposure_nettingset_...` report as ORE wrote them, plus
`as_of`, `currency`, `source` and `data_mode`. Its `data_mode` takes the same
three values as `risk_xva` (`OreDataMode` in `src/riskdesk/models.py`), so the
run's declaration passes through unchanged. The step by step
is `../risk-counterparty/workflows/exposure-profile.md`.

## Not established by a clean run

Forecast skill, calibration quality, wrong-way-risk treatment, SIMM
permissions, regulatory approval, or coverage of every ORE instrument
(`docs/ORE.md`, "What this does not establish"). The process boundary
keeps a normal run isolated; it does not make a hostile configuration
safe.
