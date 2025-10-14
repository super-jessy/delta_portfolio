import os
import hmac
import json
import base64
import time
import hashlib
import asyncio
import websockets
import datetime
from typing import Dict, List, Tuple
from dotenv import load_dotenv

# --- загрузим .env ---
load_dotenv()

FXOPEN_API_ID     = os.getenv("FXOPEN_API_ID")
FXOPEN_API_KEY    = os.getenv("FXOPEN_API_KEY")
FXOPEN_API_SECRET = os.getenv("FXOPEN_API_SECRET")
FXOPEN_AUTH_TYPE  = os.getenv("FXOPEN_AUTH_TYPE", "HMAC")

WS_URL = "wss://marginalttlivewebapi.fxopen.net/feed"

INDEX_SYMBOLS = [
    "#UK100", "#J225", "#SPXm",
    "#ESX50", "#AUS200", "#HSI"
]

# Кэш для предотвращения лишних запросов
_cache = {}
_cache_time = 0


def create_signature(timestamp: int, api_id: str, api_key: str, secret: str) -> str:
    """Создаёт HMAC подпись (Base64 HMAC_SHA256)"""
    raw = f"{timestamp}{api_id}{api_key}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def utc_start_of_day() -> int:
    """Возвращает таймстамп начала дня UTC в мс"""
    now = datetime.datetime.utcnow()
    start = datetime.datetime(now.year, now.month, now.day, 0, 0, 0)
    return int(start.timestamp() * 1000)


async def _fetch_all_symbols() -> Dict[str, List[Tuple[str, float]]]:
    """Единое соединение: логин + запросы для всех тикеров"""
    results = {}

    try:
        async with websockets.connect(WS_URL, ping_interval=None) as ws:
            # 1️⃣ Авторизация один раз
            ts = int(time.time() * 1000)
            signature = create_signature(ts, FXOPEN_API_ID, FXOPEN_API_KEY, FXOPEN_API_SECRET)

            login_req = {
                "Id": "LOGIN",
                "Request": "Login",
                "Params": {
                    "AuthType": FXOPEN_AUTH_TYPE,
                    "WebApiId": FXOPEN_API_ID,
                    "WebApiKey": FXOPEN_API_KEY,
                    "Timestamp": ts,
                    "Signature": signature,
                    "DeviceId": "DELTA-TERMINAL",
                    "AppSessionId": "DELTA-PORTFOLIO"
                }
            }

            await ws.send(json.dumps(login_req))
            auth_resp = json.loads(await ws.recv())
            if "Result" not in auth_resp and "Error" in auth_resp:
                raise Exception(f"Auth failed: {auth_resp}")

            # 2️⃣ Цикл по символам
            start_ts = utc_start_of_day()
            for sym in INDEX_SYMBOLS:
                req = {
                    "Id": f"HISTORY-{sym}",
                    "Request": "QuoteHistoryBars",
                    "Params": {
                        "Symbol": sym,
                        "Periodicity": "M30",
                        "PriceType": "bid",
                        "Timestamp": start_ts,
                        "Count": 48
                    }
                }
                await ws.send(json.dumps(req))
                resp = json.loads(await ws.recv())

                bars = resp.get("Result", {}).get("Bars", [])
                if not bars:
                    print(f"[indices_service] No data for {sym}")
                    continue

                times, closes = [], []
                for bar in bars:
                    ts_ms = bar.get("Timestamp")
                    close = bar.get("Close")
                    dt = datetime.datetime.utcfromtimestamp(ts_ms / 1000.0)
                    times.append(dt.strftime("%H:%M"))
                    closes.append(close)

                results[sym] = list(zip(times, closes))
                print(f"[indices_service] Loaded {sym}: {len(closes)} bars")

    except Exception as e:
        print(f"[indices_service] WebSocket error: {e}")

    return results


def fetch_intraday_indices() -> Dict[str, List[Tuple[str, float]]]:
    """Основная синхронная функция для UI"""
    global _cache, _cache_time

    # Кэш 30 минут
    if time.time() - _cache_time < 1800 and _cache:
        return _cache

    try:
        data = asyncio.run(_fetch_all_symbols())

        normalized: Dict[str, List[Tuple[str, float]]] = {}
        for sym, values in data.items():
            if not values:
                continue
            base = values[0][1]
            arr = []
            for ts, close in values:
                change = ((close - base) / base) * 100
                arr.append((ts, change))
            normalized[sym] = arr

        _cache = normalized
        _cache_time = time.time()
        return normalized

    except Exception as e:
        print(f"[indices_service] fetch_intraday_indices error: {e}")
        return {}
