# {{DATA_PRODUCT_NAME}}

dbt data product `{{DATA_PRODUCT_ID}}`. Published to [Entropy Data](https://entropy-data.com).

## Install

```bash
uv venv
source .venv/bin/activate
uv pip install dbt-core {{DBT_ADAPTER}} openlineage-dbt datacontract-cli entropy-data
```

## Configure

Copy `profiles.yml.example` to `~/.dbt/profiles.yml` (or merge it in) and fill in your credentials.

Set the Entropy Data API key for OpenLineage transport:

```bash
export OPENLINEAGE__TRANSPORT__AUTH__APIKEY=<your-entropy-data-api-key>
```

## Run

```bash
source .venv/bin/activate
dbt-ol run
dbt test
```

## Layout

```
models/
├── input_ports/      # external sources you read from
├── staging/          # 1:1 cleaned views over input ports
├── intermediate/     # joined / shaped views
└── output_ports/v1/  # published tables — one per output port
```

Output ports are versioned (`v1`, `v2`, ...). Each version directory contains the SQL models plus the ODCS data contract that governs the schema (`<contract-id>.odcs.yaml`). Cached input-port contracts live in `models/input_ports/` next to their `.source.yaml`.

## Publishing

CI in `.github/workflows/data-product.yml` runs `dbt run`, `dbt test`, publishes the data product spec and contract to Entropy Data, and runs the data contract test.
