# Official Sources

Research cut-off: **2026-07-23**. Every URL below was consulted on that
date. Undated living documentation is labeled "living docs"; a date in
parentheses is the page/release date visible in the source.

## psutil

- [psutil 7.2.2 documentation](https://psutil.readthedocs.io/) — living docs.
  Used for logical versus physical CPU counts, the warning that system CPU
  count can differ from process-usable CPUs under affinity/cgroups/Windows
  processor groups, `Process.cpu_affinity()`, `virtual_memory()`,
  `swap_memory()`, and `disk_usage()`.
- [psutil 7.2.2 on PyPI](https://pypi.org/project/psutil/7.2.2/) — current
  stable package pin verified 2026-07-23.

## Python

- [Python `os` documentation](https://docs.python.org/3/library/os.html) —
  Python 3.14.6 living docs. Used for `os.cpu_count()`,
  `os.process_cpu_count()`, and `os.sched_getaffinity()`.
- [Python multiprocessing](https://docs.python.org/3/library/multiprocessing.html)
  — Python 3.14.6 living docs. Used for process-aware pool defaults and the
  Python 3.14 start-method change.
- [Python concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html)
  — Python 3.14.6 living docs. Used for `ProcessPoolExecutor` defaults,
  Windows' 61-worker maximum, and `ThreadPoolExecutor` defaults.

## Linux procfs and cgroup v2

- [Linux kernel `/proc` filesystem documentation](https://docs.kernel.org/filesystems/proc.html)
  — living kernel docs. Used for `Cpus_allowed` and
  `Cpus_allowed_list`.
- [Linux kernel cgroup v2 documentation](https://docs.kernel.org/admin-guide/cgroup-v2.html)
  — living kernel docs; page history begins 2014-07-15. Used for
  `cpu.max`, `cpuset.cpus.effective`, `memory.current`, `memory.high`,
  `memory.max`, hierarchy, reclaim, and cgroup OOM behavior.
- [Linux kernel cpuset documentation](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v1/cpusets.html)
  — living kernel docs. Used to cross-check the interaction between affinity
  masks and cpuset constraints.

## Containers and OCI

- [Docker resource constraints](https://docs.docker.com/engine/containers/resource_constraints/)
  — living docs. Used for Docker's default lack of constraints, `--cpus`,
  quota/period, cpusets, and memory controls.
- [OCI Runtime Specification: Linux resources](https://specs.opencontainers.org/runtime-spec/config-linux/?v=v1.3.0)
  — OCI Runtime Spec 1.3.0. Used for CPU, memory, cgroup, and device resource
  semantics.

## NVIDIA

- [NVIDIA System Management Interface manual](https://docs.nvidia.com/deploy/nvidia-smi/index.html)
  — living docs. Used for fixed `--query-gpu` fields and
  `--format=csv,noheader,nounits`; NVIDIA notes that index ordering is not
  stable, which is why snapshots do not claim a persistent identity.
- [NVIDIA Container Toolkit specialized configurations](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/docker-specialized.html)
  — living docs. Used for `NVIDIA_VISIBLE_DEVICES`, driver capabilities, and
  runtime constraints.
- [NVIDIA `CUDA_VISIBLE_DEVICES`](https://docs.nvidia.com/deploy/topics/topic_5_2_1.html)
  — official deployment documentation. Used for CUDA application visibility.
- [NVIDIA CUDA compatibility](https://docs.nvidia.com/deploy/cuda-compatibility/latest/why-cuda-compatibility.html)
  — living docs. Used to distinguish management visibility from compatible
  GPU, driver, CUDA runtime, and dynamically linked libraries.

## AMD ROCm

- [AMD SMI CLI tool](https://rocm.docs.amd.com/projects/amdsmi/en/docs-7.2.0/how-to/amdsmi-cli-tool.html)
  — AMD SMI 7.2.0 docs. Used for read-only `list`/`static` JSON output and the
  meaning of unavailable fields.
- [ROCm SMI Python/CLI usage](https://rocm.docs.amd.com/projects/rocm_smi_lib/en/latest/how-to/use-python.html)
  — living docs. Used for the legacy `rocm-smi` read-only fallback.
- [ROCm GPU isolation techniques](https://rocm.docs.amd.com/en/docs-7.2.4/conceptual/gpu-isolation.html)
  — ROCm 7.2.4 docs. Used for `ROCR_VISIBLE_DEVICES`,
  `HIP_VISIBLE_DEVICES`, `CUDA_VISIBLE_DEVICES`, Docker device isolation, and
  the warning that environment variables are not isolation for untrusted code.
- [ROCm environment variables](https://rocm.docs.amd.com/en/latest/reference/environment-variables/index.html)
  — living docs. Used for AMD's Linux/Windows visibility-variable
  recommendations.

## Apple

- [Apple: Determining system capabilities](https://developer.apple.com/documentation/kernel/1387446-sysctlbyname/determining_system_capabilities)
  — living Apple Developer docs. Used for `hw.logicalcpu`,
  `hw.physicalcpu`, `hw.memsize`, performance levels, and the distinction
  between logical and physical cores.
- [Apple `sysctl(3)` manual](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man3/sysctl.3.html)
  — archived official manual. Used to cross-check physical-memory fields.
- [Apple Developer Technical Support: system_profiler and integrated/SoC memory](https://developer.apple.com/forums/thread/688443)
  — Apple DTS response dated 2021-08-24. Used for parseable
  `system_profiler` output and the warning that DIMM-style details do not map
  cleanly to integrated or Apple silicon memory.
- The fixed `system_profiler SPDisplaysDataType -json` and named `sysctl -n`
  queries were smoke-checked locally on Darwin 25.5.0 on 2026-07-23. The
  script never requests the full system profile.

## Slurm

- [Slurm `sbatch`](https://slurm.schedmd.com/sbatch.html) — living SchedMD
  docs. Used for exact output environment-variable scopes:
  `SLURM_CPUS_ON_NODE`, `SLURM_CPUS_PER_TASK`,
  `SLURM_JOB_CPUS_PER_NODE`, `SLURM_MEM_PER_CPU`,
  `SLURM_MEM_PER_NODE`, `SLURM_NTASKS`, and GPU variables. Also used for
  the explicit warning that memory requests require configured enforcement.
- [Slurm CPU Management Guide](https://slurm.schedmd.com/cpu_management.html)
  — living SchedMD docs. Used for `task/affinity`, `task/cgroup`,
  `ConstrainCores`, binding, and logical CPU/core allocation examples.
- [Slurm `srun`](https://slurm.schedmd.com/srun.html) — updated
  2026-07-14. Used for task confinement and GPU binding behavior.
- [Slurm `scontrol`](https://slurm.schedmd.com/scontrol.html) — living docs.
  Used for the read-only `scontrol show job` interpretation workflow.
- [Slurm `sstat`](https://slurm.schedmd.com/sstat.html) — living docs. Used
  for post-launch job-step accounting semantics.

## Windows

- [Microsoft: Processor Groups](https://learn.microsoft.com/en-us/windows/win32/procthread/processor-groups)
  — living Microsoft docs. Used for the distinction between system logical
  processors, physical cores, and processor-group scheduling.
- [GetLogicalProcessorInformation](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getlogicalprocessorinformation)
  — living Microsoft docs. Used for logical/physical relationships and the
  current-group limitation on systems over 64 logical processors.
- [GetLogicalProcessorInformationEx](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getlogicalprocessorinformationex)
  — page dated 2023-03-06. Used for system-wide processor-group topology.
