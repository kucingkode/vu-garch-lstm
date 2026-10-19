import logging
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data" / "bronze"

BASE_URL = "https://api.binance.com/api/v3/klines"
SYMBOL = "BTCUSDT"
INTERVAL = "1h"
INTERVAL_MS = 60 * 60 * 1000
LIMIT = 1000

COLUMNS = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_asset_volume",
    "number_of_trades",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
    "ignore",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def fetch_klines(start_time: int, end_time: int) -> list:
    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "startTime": start_time,
        "endTime": end_time,
        "limit": LIMIT,
    }

    for attempt in range(6):
        try:
            response = requests.get(BASE_URL, params=params, timeout=30)

            if response.status_code in (418, 429, 500, 502, 503, 504):
                response.raise_for_status()

            response.raise_for_status()
            result = response.json()

            if not isinstance(result, list):
                raise ValueError("Unexpected Binance API response")  # noqa: TRY004

            return result

        except (requests.RequestException, ValueError):
            if attempt == 5:
                raise

            delay = min(2**attempt, 60)
            logger.warning("Request failed; retrying in %s seconds", delay)
            time.sleep(delay)

    return []


def get_latest_open_time() -> int | None:
    latest = None

    for path in DATA_DIR.glob(f"{SYMBOL}/{INTERVAL}/*/*.parquet"):
        month = pd.read_parquet(path, columns=["open_time"])
        if not month.empty:
            value = int(month["open_time"].max())
            latest = value if latest is None else max(latest, value)

    return latest


def save_monthly(df: pd.DataFrame) -> None:
    df["month"] = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.strftime(
        "%Y/%m"
    )

    for month, batch in df.groupby("month"):
        year, month_num = month.split("/")
        directory = DATA_DIR / SYMBOL / INTERVAL / year
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{month_num}.parquet"

        batch = batch.drop(columns=["month"])

        if path.exists():
            old = pd.read_parquet(path)
            batch = pd.concat([old, batch], ignore_index=True)

        batch = (
            batch.drop_duplicates(subset=["open_time"], keep="last")
            .sort_values("open_time")
            .reset_index(drop=True)
        )

        batch.to_parquet(path, index=False, engine="pyarrow")
        logger.info("Saved %s rows to %s", len(batch), path)


def ingest() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    latest = get_latest_open_time()

    if latest is None:
        start_time = int((datetime.now(UTC) - timedelta(days=730)).timestamp() * 1000)
    else:
        start_time = latest + INTERVAL_MS

    now_ms = int(datetime.now(UTC).timestamp() * 1000)
    end_time = (now_ms // INTERVAL_MS) * INTERVAL_MS - 1

    if start_time > end_time:
        logger.info("No new closed candles to ingest.")
        return

    batch_id = str(uuid.uuid4())
    frames = []

    while start_time <= end_time:
        rows = fetch_klines(start_time, end_time)

        if not rows:
            break

        batch = pd.DataFrame(rows, columns=COLUMNS)

        batch = batch[batch["close_time"] < now_ms]
        if not batch.empty:
            batch["source"] = "binance_spot_api"
            batch["ingested_at"] = datetime.now(UTC).isoformat()
            batch["batch_id"] = batch_id
            frames.append(batch)

        next_start = int(rows[-1][0]) + INTERVAL_MS
        if next_start <= start_time:
            raise RuntimeError("Pagination did not advance")
        start_time = next_start

        if len(rows) < LIMIT:
            break

        if frames:
            result = pd.concat(frames, ignore_index=True)
            save_monthly(result)
            logger.info("Ingestion complete: %s rows", len(result))
        else:
            logger.info("No new closed candles returned")


if __name__ == "__main__":
    ingest()
