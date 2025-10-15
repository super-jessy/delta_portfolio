import os
import hmac
import json
import base64
import time
import hashlib
import asyncio
import websockets
import datetime
from dotenv import load_dotenv

load_dotenv()

FXOPEN_API_ID     = os.getenv("FXOPEN_API_ID")
FXOPEN_API_KEY    = os.getenv("FXOPEN_API_KEY")
FXOPEN_API_SECRET = os.getenv("FXOPEN_API_SECRET")
FXOPEN_AUTH_TYPE  = os.getenv("FXOPEN_AUTH_TYPE", "HMAC")

WS_URL = "wss://marginalttlivewebapi.fxopen.net/feed"


def create_signature(timestamp: int, api_id: str, api_key: str, secret: str) -> str:
    raw = f"{timestamp}{api_id}{api_key}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


async def _fetch_candles(symbol: str, timeframe: str):
    results = []
    try:
        async with websockets.connect(WS_URL, ping_interval=None) as ws:
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
            if "Result" not in auth_resp:
                raise Exception(f"Auth failed: {auth_resp}")

            # 30 дней истории примерно
            start_ts = int((datetime.datetime.utcnow() - datetime.timedelta(days=30)).timestamp() * 1000)

            req = {
                "Id": f"HISTORY-{symbol}",
                "Request": "QuoteHistoryBars",
                "Params": {
                    "Symbol": symbol,
                    "Periodicity": timeframe,
                    "PriceType": "bid",
                    "Timestamp": start_ts,
                    "Count": 500
                }
            }

            await ws.send(json.dumps(req))
            resp = json.loads(await ws.recv())

            bars = resp.get("Result", {}).get("Bars", [])
            for bar in bars:
                dt = datetime.datetime.utcfromtimestamp(bar["Timestamp"] / 1000)
                results.append((dt, bar["Open"], bar["High"], bar["Low"], bar["Close"]))

    except Exception as e:
        print(f"[chart_service] error: {e}")

    return results


def fetch_candles(symbol: str, timeframe: str):
    """Синхронный вызов для UI"""
    return asyncio.run(_fetch_candles(symbol, timeframe))
