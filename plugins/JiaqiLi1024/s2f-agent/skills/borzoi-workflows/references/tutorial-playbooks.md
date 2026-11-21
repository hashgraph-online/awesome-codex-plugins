# Tutorial Playbooks

Use this file for grounded tutorial command sequences.

## Default guidance

- Prefer `tutorials/latest/*`.
- Keep `legacy` only for manuscript-style transform compatibility.
- Make clear that tutorials are minimal examples, not full paper benchmarking pipelines.
- For user requests focused on direct real inference rather than tutorial reproduction, use `references/real-inference-fastpath.md`.

## Data processing (`latest/make_data`)

Goal: Convert sample `.bigwig` tracks into `.w5`, merge replicates, run QC, and create TFRecords.

```bash
conda activate borzoi_py310
cd ~/borzoi/tutorials/latest/make_data
./download_dependencies.sh
./download_bw.sh
./process_w5.sh
make
```

Grounded internals:

- `bw_h5.py` creates `.w5`
- `w5_merge.py` merges replicates
- `w5_qc.py` computes QC
- Makefile generates multi-fold TFRecords

## Model training (`latest/train_model`)

Train tutorial models on sample processed data:

```bash
conda activate borzoi_py310
cd ~/borzoi/tutorials/latest/train_model
./train_mini.sh
```

Smaller/faster option:

```bash
./train_micro.sh
```

Grounded notes:

- Mini ensemble is about 40M parameters.
- Micro ensemble is about 5M parameters.
- Tutorial docs mention 24GB-class GPUs (for example Titan RTX or RTX 4090) for those example settings.

## Indel/SV/STR analysis (`latest/analyze_sv`)

Install extra plotting dependency and run examples:

```bash
pip install plotly
cd ~/borzoi/tutorials/latest/analyze_sv
bash download_dependencies_SV.sh
bash analyze_indel.sh
```

STR workflow:

```bash
bash download_dependencies_STR.sh
bash score_STRs.sh
```

Grounded caveats:

- SV visualization script handles one variant per run (`.vcf` should contain one variant).
- Outputs are interactive plots by tissue and cross-tissue summaries.
