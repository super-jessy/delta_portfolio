import os
import time
import json
import base64
import hmac
import hashlib
import pandas as pd
from uuid import uuid4
from dotenv import load_dotenv
from websocket import create_connection
from core.database import engine

# =======================================================
# 🧩 Конфигурация
# =======================================================
load_dotenv()

FXOPEN_API_ID = os.getenv("FXOPEN_API_ID")
FXOPEN_API_KEY = os.getenv("FXOPEN_API_KEY")
FXOPEN_API_SECRET = os.getenv("FXOPEN_API_SECRET")

WS_URL = "wss://marginalttlivewebapi.fxopen.net/feed"
SYMBOLS = ["AAPL", "AMZN", "TSLA"]
TIMEFRAME = "D1"
BARS_COUNT = -500  # отрицательное значение = назад

# =======================================================
# 🔐 Создание HMAC-подписи
# =======================================================
def create_signature(timestamp, api_id, api_key, secret):
    """
    Возвращает Base64(HMAC_SHA256(timestamp + id + key, secret))
    """
    msg = f"{timestamp}{api_id}{api_key}"
    digest = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()

# =======================================================
# 📡 Получение истории котировок
# =======================================================
def fetch_quote_history(symbol: str, timeframe: str = "D1", count: int = -500):
    print(f"⏳ Подключаемся к WebSocket для {symbol}...")

    ws = create_connection(WS_URL)

    # Генерируем параметры для логина
    timestamp = int(time.time() * 1000)
    signature = create_signature(timestamp, FXOPEN_API_ID, FXOPEN_API_KEY, FXOPEN_API_SECRET)

    login_msg = {
        "Id": str(uuid4()),
        "Request": "Login",
        "Params": {
            "AuthType": "HMAC",
            "WebApiId": FXOPEN_API_ID,
            "WebApiKey": FXOPEN_API_KEY,
            "Timestamp": timestamp,
            "Signature": signature,
            "DeviceId": "DELTA_PORTFOLIO_APP",
            "AppSessionId": "DEV_001"
        }
    }

    # Авторизация
    ws.send(json.dumps(login_msg))
    response = json.loads(ws.recv())
    if response.get("Response") != "Login" or response.get("Result", {}).get("Info") != "ok":
        print("❌ Ошибка авторизации:", response)
        ws.close()
        return pd.DataFrame()

    print("✅ Авторизация прошла успешно!")

    # Запрашиваем бары
    req_id = str(uuid4())
    history_msg = {
        "Id": req_id,
        "Request": "QuoteHistoryBars",
        "Params": {
            "Symbol": symbol,
            "Periodicity": timeframe,
            "PriceType": "bid",
            "Timestamp": int(time.time() * 1000),
            "Count": count
        }
    }

    ws.send(json.dumps(history_msg))
    data = json.loads(ws.recv())

    # Проверяем результат
    if "Result" not in data or "Bars" not in data["Result"]:
        print(f"⚠️ Нет данных для {symbol}: {data}")
        ws.close()
        return pd.DataFrame()

    bars = data["Result"]["Bars"]
    ws.close()

    # Конвертируем в DataFrame
    df = pd.DataFrame(bars)
    df["datetime"] = pd.to_datetime(df["Timestamp"], unit="ms")
    df["symbol"] = symbol
    df.rename(columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    }, inplace=True)
    df = df[["symbol", "datetime", "open", "high", "low", "close", "volume"]]

    print(f"✅ Получено {len(df)} баров для {symbol}")
    return df

# =======================================================
# 💾 Сохранение в PostgreSQL
# =======================================================
def save_to_db(df: pd.DataFrame, table_name: str = "market_ohlc"):
    if df.empty:
        print("⚠️ DataFrame пуст, пропускаем сохранение.")
        return
    with engine.begin() as conn:
        df.to_sql(table_name, conn, if_exists="append", index=False)
        print(f"📊 Сохранено {len(df)} строк для {df['symbol'].iloc[0]}")

# =======================================================
# 🧪 Тестовый запуск
# =======================================================
if __name__ == "__main__":
    all_data = []
    for sym in SYMBOLS:
        try:
            df = fetch_quote_history(sym, timeframe=TIMEFRAME, count=BARS_COUNT)
            if not df.empty:
                save_to_db(df)
                all_data.append(df)
        except Exception as e:
            print(f"❌ Ошибка для {sym}: {e}")

    if all_data:
        total_rows = sum(len(d) for d in all_data)
        print(f"🎯 Всего обработано {total_rows} строк.")
    else:
        print("⚠️ Не удалось получить данные ни по одному символу.")
