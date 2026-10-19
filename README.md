# MLOps Project

## Project Goal

Predicting future BTC/USDT 1h volatility using VU-GARCH-LSTM architecture.

## Directory Structure

- `dags/` — Airflow DAGs for orchestration
- `data/` — raw and processed datasets (tracked with DVC)
- `src/` — pipeline code (data prep, training, serving)
- `models/` — trained model artifacts
- `monitoring/` — Evidently AI drift/quality reports
- `notebooks/` — exploratory analysis
- `.devcontainer/` — Codespaces environment config

## Running in GitHub Codespaces

1. Click "Code" -> "Codespaces" -> "Create codespace on main"
2. Wait for the container to build (dependencies install automatically via `uv sync`)
3. Start MLflow: `uv run mlflow server --host 0.0.0.0 --port 5000`
4. Start Airflow: `uv run airflow standalone`
5. Run DVC pull to fetch data: `dvc pull`
6. Serve the model: `uv run bentoml serve src.serving.service:svc --port 3000`

## Branching Strategy

This project follows GitHub Flow: create a feature branch (e.g. `feat/initial-eda`), commit work, open a PR into `main`, validate results, then merge.

## Run Apache Airflow

```bash
./scripts/run-airflow.sh
```

To run apache airflow dags, use bash script provider. It will use multiplex to run both airflow api server and standalone in parallel.

## Bronze Data Ingestion

### Data Source

The Bronze pipeline collects BTCUSDT hourly candlestick (kline) data from the Binance Spot Market Data API.

- Endpoint: `https://api.binance.com/api/v3/klines`
- Symbol: `BTCUSDT`
- Interval: `1h`
- Format: Parquet
- Storage: `data/bronze/BTCUSDT/1h/YYYY/MM.parquet`

### Run Ingestion Manually

```bash
uv run python src/ingest_data.py
```

The first run attempts to backfill the previous two years of data. Subsequent runs fetch new candles incrementally, skipping incomplete candles and deduplicating records by open time.

### Pipeline Responsibilities

- **Bronze:** Preserve raw Binance market data and ingestion metadata.
- **Silver:** Clean data, normalize timestamps and types, remove duplicates, and check for missing candles.
- **Gold:** Generate features such as log returns, VU, and realized volatility for model training.

Bronze ingestion is implemented in `src/ingest_data.py` and orchestrated by `dags/bronze_ingestion.py`. Silver and Gold transformations will be implemented separately.
