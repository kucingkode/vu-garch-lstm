from datetime import UTC, datetime, timedelta
from pathlib import Path

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import dag

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dag(
    dag_id="btc_bronze_ingestion",
    description="Incrementally ingest closed BTCUSDT 1h klines",
    schedule="* * * * *",
    start_date=datetime(2026, 1, 1, tzinfo=UTC),
    catchup=False,
    max_active_runs=1,
    default_args={
        "retries": 3,
        "retry_delay": timedelta(minutes=2),
    },
    tags=["bronze", "binance", "btc"],
)
def bronze_ingestion():
    BashOperator(
        task_id="ingest_btcusdt_1h",
        bash_command=(
            f"cd '{PROJECT_ROOT}' && "
            "uv run python src/vu_garch_lstm/data/ingest_data.py"
        ),
    )


bronze_ingestion()
