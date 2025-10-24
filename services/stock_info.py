import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import aiohttp
import async_timeout
import pandas as pd
from datetime import datetime
from typing import Any, Dict, Optional, List
from dotenv import load_dotenv

from core.db_manager import DatabaseManager


# ────────────────────────────────────────────────
# Настройки
# ────────────────────────────────────────────────
load_dotenv()
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
CSV_PATH = "data/US stocks.csv"
LOGS_DIR = "logs"
FAILED_FILE = os.path.join(LOGS_DIR, "failed_tickers.txt")

CONCURRENCY = 1
REQUEST_TIMEOUT = 20
MAX_RETRIES = 5
RETRY_BACKOFF = 1.6

POLY_TICKER_URL = "https://api.polygon.io/v3/reference/tickers/{ticker}?apiKey={api_key}"



# Вспомогательные функции

def ensure_logs_dir():
    """Создаёт папку logs/, если её нет."""
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)

def save_failed_tickers(failed: List[str]):
    """Сохраняет список неудачных тикеров в файл."""
    ensure_logs_dir()
    with open(FAILED_FILE, "w") as f:
        for t in failed:
            f.write(t + "\n")

def _none_if_empty(val: Any) -> Optional[Any]:
    if val is None:
        return None
    if isinstance(val, str) and val.strip() == "":
        return None
    return val

def _safe_get(d: Dict, path: List[str], default=None):
    cur = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur

def _parse_date(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s).date().isoformat()
    except Exception:
        try:
            return datetime.strptime(s, "%Y-%m-%d").date().isoformat()
        except Exception:
            return None



# Сетевые функции

async def fetch_json(session: aiohttp.ClientSession, url: str) -> Optional[Dict]:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with async_timeout.timeout(REQUEST_TIMEOUT):
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    if resp.status in (429, 500, 502, 503, 504):
                        await asyncio.sleep(RETRY_BACKOFF ** (attempt - 1))
                        continue
                    return None
        except (asyncio.TimeoutError, aiohttp.ClientError):
            await asyncio.sleep(RETRY_BACKOFF ** (attempt - 1))
    return None


async def fetch_bytes(session: aiohttp.ClientSession, url: str) -> Optional[bytes]:
    if not url:
        return None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with async_timeout.timeout(REQUEST_TIMEOUT):
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return await resp.read()
                    if resp.status in (429, 500, 502, 503, 504):
                        await asyncio.sleep(RETRY_BACKOFF ** (attempt - 1))
                        continue
                    return None
        except (asyncio.TimeoutError, aiohttp.ClientError):
            await asyncio.sleep(RETRY_BACKOFF ** (attempt - 1))
    return None



# Маппинг Polygon → БД

def map_polygon_to_db(record: Dict, logo_bytes: Optional[bytes]) -> Dict[str, Any]:
    r = record.get("results", {}) if record else {}
    address = _safe_get(r, ["address"], {}) or {}

    return {
        "ticker": _none_if_empty(r.get("ticker")),
        "name": _none_if_empty(r.get("name")),
        "market": _none_if_empty(r.get("market")),
        "locale": _none_if_empty(r.get("locale")),
        "primary_exchange": _none_if_empty(r.get("primary_exchange")),
        "currency_name": _none_if_empty(r.get("currency_name")),
        "composite_figi": _none_if_empty(r.get("composite_figi")),
        "share_class_figi": _none_if_empty(r.get("share_class_figi")),
        "market_cap": _none_if_empty(r.get("market_cap")),
        "phone_number": _none_if_empty(r.get("phone_number")),
        "address1": _none_if_empty(address.get("address1")),
        "city": _none_if_empty(address.get("city")),
        "state": _none_if_empty(address.get("state")),
        "postal_code": _none_if_empty(address.get("postal_code")),
        "description": _none_if_empty(r.get("description")),
        "sic_description": _none_if_empty(r.get("sic_description")),
        "homepage_url": _none_if_empty(r.get("homepage_url")),
        "total_employees": _none_if_empty(r.get("total_employees")),
        "list_date": _parse_date(_none_if_empty(r.get("list_date"))),
        "share_class_shares_outstanding": _none_if_empty(r.get("share_class_shares_outstanding")),
        "weighted_shares_outstanding": _none_if_empty(r.get("weighted_shares_outstanding")),
        "round_lot": _none_if_empty(r.get("round_lot")),
        "logo_data": logo_bytes,
    }



# Обработка одного тикера

async def process_ticker(semaphore: asyncio.Semaphore,
                         session: aiohttp.ClientSession,
                         ticker: str) -> Optional[Dict[str, Any]]:
    url = POLY_TICKER_URL.format(ticker=ticker, api_key=POLYGON_API_KEY)
    async with semaphore:
        meta = await fetch_json(session, url)
        if not meta or meta.get("status") != "OK":
            print(f"⚠️ Skip {ticker}")
            return None

        def add_key(u):
            if not u:
                return None
            sep = "&" if "?" in u else "?"
            return f"{u}{sep}apiKey={POLYGON_API_KEY}"

        logo_url = add_key(_safe_get(meta, ["results", "branding", "logo_url"]))
        icon_url = add_key(_safe_get(meta, ["results", "branding", "icon_url"]))

        logo_bytes = await fetch_bytes(session, logo_url)
        if not logo_bytes and icon_url:
            logo_bytes = await fetch_bytes(session, icon_url)

        return map_polygon_to_db(meta, logo_bytes)



# Основная загрузка

async def run_loader(tickers: List[str]):
    if not POLYGON_API_KEY:
        raise RuntimeError("POLYGON_API_KEY не найден в .env")

    db = DatabaseManager()
    failed_tickers = []
    try:
        db.create_table()

        timeout = aiohttp.ClientTimeout(total=None, connect=REQUEST_TIMEOUT, sock_read=REQUEST_TIMEOUT)
        connector = aiohttp.TCPConnector(limit=None)
        semaphore = asyncio.Semaphore(CONCURRENCY)

        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            tasks = [process_ticker(semaphore, session, t.strip()) for t in tickers if t.strip()]
            total = len(tasks)
            completed = 0
            results: List[Optional[Dict[str, Any]]] = []

            for coro in asyncio.as_completed(tasks):
                res = await coro
                results.append(res)
                completed += 1
                percent = (completed / total) * 100
                print(f"⏳ Progress: {completed}/{total} ({percent:.1f}%)")

                if completed % 3 == 0:
                    await asyncio.sleep(2)

        inserted = 0
        for item, ticker in zip(results, tickers):
            if not item:
                failed_tickers.append(ticker)
                continue
            try:
                db.insert_instrument(item)
                inserted += 1
            except Exception as e:
                failed_tickers.append(ticker)
                print(f"❗ DB insert error for {ticker}: {e}")

        skipped = len(failed_tickers)
        print(f"✅ Done. Inserted/Updated: {inserted} | Skipped: {skipped} | Total: {len(tickers)}")

        if failed_tickers:
            save_failed_tickers(failed_tickers)
            print(f"⚠️ Failed tickers saved to {FAILED_FILE}")

    finally:
        db.close()



# CSV загрузка

def load_tickers_from_csv(path: str) -> List[str]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"CSV not found: {path}")
    df = pd.read_csv(path, header=None, names=["symbols"])
    return df["symbols"].dropna().astype(str).tolist()



# Точка входа

if __name__ == "__main__":
    try:
        tickers = load_tickers_from_csv(CSV_PATH)
        print(f"📄 Loaded {len(tickers)} tickers from {CSV_PATH}")
        asyncio.run(run_loader(tickers))
    except Exception as e:
        print(f"❗ Loader failed: {e}")
