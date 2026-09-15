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