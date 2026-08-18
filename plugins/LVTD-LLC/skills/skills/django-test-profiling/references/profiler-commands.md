# Profiler Commands

Use these commands as starting points and adapt them to the project's runner, package manager, and CI environment.

## Baseline Timing

| Goal | Command |
|------|---------|
| Full Django suite wall-clock time | `time python manage.py test` |
| Django DB setup/teardown timing | `python manage.py test --timing` |
| Full pytest suite wall-clock time | `time pytest` |
| Slowest pytest phases | `pytest --durations 20` |
| PowerShell timing | `Measure-Command { python manage.py test }` |

Repeat short runs several times. For long suites, a single CI baseline may be enough to prioritize first-pass work, but note that it is a noisy measurement.

## py-spy

Use `py-spy` for a low-overhead overview of where a running suite spends time.

```bash
python -m pip install py-spy
sudo py-spy record -o profile.svg --subprocesses -- python manage.py test
sudo py-spy record --format speedscope -o profile.speedscope --subprocesses -- python manage.py test
```

Use `--subprocesses` for Django parallel tests or tools that fork worker processes. Add `--idle` only when sleeping or idle time is itself part of the diagnosis.

## cProfile

Use `cProfile` when sampling is too coarse or you need exhaustive Python call accounting.

```bash
python -m cProfile -s cumtime manage.py test
python -m cProfile -m pytest
python -m cProfile -o profile.prof manage.py test
```

Read cumulative time first to find expensive call trees. Then inspect total time to find functions that are expensive by themselves rather than through their callees.

## Visualizing cProfile

```bash
python -m pip install pyprof2calltree
pyprof2calltree -i profile.prof -k
```

Use kcachegrind/qcachegrind when you need caller/callee navigation. For pytest users, `pytest-profiling` can store cProfile output without manually wrapping the runner.

## Interpretation Checklist

- Is the cost in suite startup, test discovery, database setup, fixture creation, repeated query work, file/cache/network I/O, or actual assertions?
- Does one test class/module dominate a parallel run?
- Do slow pytest entries show setup, call, or teardown time?
- Does the profile point to test code, application code, or framework/package initialization?
- Can the next fix be validated by rerunning the same timing command?
