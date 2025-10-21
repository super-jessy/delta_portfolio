# services/stock_info3.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import aiohttp
import async_timeout
from datetime import datetime
from typing import Any, Dict, Optional, List
from dotenv import load_dotenv

from core.db_manager import DatabaseManager


# ────────────────────────────────────────────────
# Настройки
# ────────────────────────────────────────────────
load_dotenv()
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
LOGS_DIR = "logs"
FAILED_FILE = os.path.join(LOGS_DIR, "failed_tickers3.txt")

# 👇 Минимальная конкуренция + пауза между запросами
CONCURRENCY = 1
REQUEST_TIMEOUT = 20
MAX_RETRIES = 5
RETRY_BACKOFF = 1.6
DELAY_BETWEEN = 5  # секунд между запросами

POLY_TICKER_URL = "https://api.polygon.io/v3/reference/tickers/{ticker}?apiKey={api_key}"

# ────────────────────────────────────────────────
# Последние «упрямые» тикеры
# ────────────────────────────────────────────────
RETRY_TICKERS = [
  "GLD"
]

# ────────────────────────────────────────────────
# Утилиты
# ────────────────────────────────────────────────
def ensure_logs_dir():
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)

def save_failed_tickers(failed: List[str]):
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


# ────────────────────────────────────────────────
# Сетевые функции
# ────────────────────────────────────────────────
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


# ────────────────────────────────────────────────
# Маппинг Polygon → БД
# ────────────────────────────────────────────────
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


# ────────────────────────────────────────────────
# Обработка тикера
# ────────────────────────────────────────────────
async def process_ticker(session: aiohttp.ClientSession, ticker: str) -> Optional[Dict[str, Any]]:
    url = POLY_TICKER_URL.format(ticker=ticker, api_key=POLYGON_API_KEY)
    print(f"🔎 Fetching {ticker}...")
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


# ────────────────────────────────────────────────
# Основная функция
# ────────────────────────────────────────────────
async def run_loader(tickers: List[str]):
    db = DatabaseManager()
    failed = []
    try:
        db.create_table()

        timeout = aiohttp.ClientTimeout(total=None, connect=REQUEST_TIMEOUT, sock_read=REQUEST_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for i, ticker in enumerate(tickers, start=1):
                res = await process_ticker(session, ticker)
                if res:
                    try:
                        db.insert_instrument(res)
                        print(f"✅ {ticker} inserted ({i}/{len(tickers)})")
                    except Exception as e:
                        print(f"❗ DB insert error for {ticker}: {e}")
                        failed.append(ticker)
                else:
                    failed.append(ticker)

                # пауза между запросами
                await asyncio.sleep(DELAY_BETWEEN)

        if failed:
            save_failed_tickers(failed)
            print(f"⚠️ Failed tickers saved to {FAILED_FILE}")
        print(f"✅ Done. Inserted/Updated: {len(tickers) - len(failed)} | Failed: {len(failed)}")

    finally:
        db.close()


# ────────────────────────────────────────────────
# Точка входа
# ────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"📄 Retrying {len(RETRY_TICKERS)} tickers (slow mode)...")
    asyncio.run(run_loader(RETRY_TICKERS))
