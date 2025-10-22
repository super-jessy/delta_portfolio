import os
import time
import json
import base64
import hmac
import hashlib
import pandas as pd
from uuid import uuid4
from datetime import datetime, timedelta
from dotenv import load_dotenv
from websocket import create_connection
from sqlalchemy import create_engine, text

# =======================================================
# ⚙️ Конфигурация
# =======================================================
load_dotenv()

FXOPEN_API_ID = os.getenv("FXOPEN_API_ID")
FXOPEN_API_KEY = os.getenv("FXOPEN_API_KEY")
FXOPEN_API_SECRET = os.getenv("FXOPEN_API_SECRET")

PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_DB = os.getenv("PG_DB")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")

DB_URL = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
engine = create_engine(DB_URL)

WS_URL = "wss://marginalttlivewebapi.fxopen.net/feed"
TIMEFRAME = "M30"  # по умолчанию, можно менять

# =======================================================
# 🔐 Подпись HMAC
# =======================================================
def create_signature(timestamp, api_id, api_key, secret):
    msg = f"{timestamp}{api_id}{api_key}"
    digest = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()

# =======================================================
# 🧩 Получение тикеров из instruments
# =======================================================
def get_tickers_from_db():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT ticker FROM instruments"))
        tickers = [row[0] for row in result]
    return tickers

# =======================================================
# 📈 Проверка последней даты по тикеру
# =======================================================
def get_last_datetime(ticker, timeframe):
    query = text("""
        SELECT MAX(datetime)
        FROM instrument_quotes
        WHERE ticker = :ticker AND timeframe = :tf
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"ticker": ticker, "tf": timeframe}).scalar()
    return result

# =======================================================
# 📡 Получение истории котировок
# =======================================================
def fetch_quote_history(symbol: str, timeframe: str = "D1", count: int = -2000, since: datetime | None = None):
    print(f"⏳ Подключаемся к WebSocket для {symbol} ({timeframe})...")

    ws = create_connection(WS_URL)
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
            "AppSessionId": "AUTO_UPDATE"
        }
    }

    ws.send(json.dumps(login_msg))
    response = json.loads(ws.recv())
    if response.get("Response") != "Login" or response.get("Result", {}).get("Info") != "ok":
        print("❌ Ошибка авторизации:", response)
        ws.close()
        return pd.DataFrame()

    req_id = str(uuid4())
    params = {
        "Symbol": symbol,
        "Periodicity": timeframe,
        "PriceType": "bid",
        "Timestamp": int(time.time() * 1000),
        "Count": count
    }
    if since:
        params["From"] = int(since.timestamp() * 1000)

    ws.send(json.dumps({"Id": req_id, "Request": "QuoteHistoryBars", "Params": params}))
    data = json.loads(ws.recv())
    ws.close()

    if "Result" not in data or "Bars" not in data["Result"]:
        print(f"⚠️ Нет данных для {symbol}: {data}")
        return pd.DataFrame()

    bars = data["Result"]["Bars"]
    df = pd.DataFrame(bars)
    df["datetime"] = pd.to_datetime(df["Timestamp"], unit="ms")
    df["ticker"] = symbol
    df["timeframe"] = timeframe
    df.rename(columns={
        "Open": "open", "High": "high", "Low": "low",
        "Close": "close", "Volume": "volume"
    }, inplace=True)
    df = df[["ticker", "timeframe", "datetime", "open", "high", "low", "close", "volume"]]
    print(f"✅ Получено {len(df)} баров для {symbol}")
    return df

# =======================================================
# 💾 Сохранение котировок в instrument_quotes
# =======================================================
def save_to_db(df: pd.DataFrame):
    if df.empty:
        print("⚠️ Пустой DataFrame, пропускаем.")
        return
    with engine.begin() as conn:
        df.to_sql("instrument_quotes", conn, if_exists="append", index=False)
    print(f"📊 Сохранено {len(df)} строк для {df['ticker'].iloc[0]} ({df['timeframe'].iloc[0]})")

# =======================================================
# 🔁 Проверка и обновление котировок
# =======================================================
def update_quotes_if_needed(ticker, timeframe):
    print(f"🔍 Проверка обновления для {ticker} ({timeframe})")
    last_dt = get_last_datetime(ticker, timeframe)
    now = datetime.utcnow()

    # Интервалы обновления по таймфрейму
    refresh_period = {
        "M1": timedelta(minutes=1),
        "M5": timedelta(minutes=5),
        "M15": timedelta(minutes=15),
        "M30": timedelta(minutes=30),
        "H1": timedelta(hours=1),
        "D1": timedelta(days=1)
    }.get(timeframe, timedelta(hours=1))

    # Проверяем, пора ли обновлять
    if last_dt is None or now - last_dt >= refresh_period:
        print(f"🕒 Обновляем данные для {ticker} с {last_dt}")
        df = fetch_quote_history(ticker, timeframe=timeframe, count=-500, since=last_dt)
        if not df.empty:
            save_to_db(df)
    else:
        print(f"✅ Актуальные данные для {ticker}, обновление не требуется.")

# =======================================================
# 🚀 Основной цикл автообновления
# =======================================================
def run_auto_update(timeframe="M30"):
    print("🚀 Запуск автообновления котировок...")
    while True:
        tickers = get_tickers_from_db()
        for ticker in tickers:
            try:
                update_quotes_if_needed(ticker, timeframe)
            except Exception as e:
                print(f"❌ Ошибка обновления для {ticker}: {e}")
        time.sleep(60)  # проверяем каждые 60 секунд

# =======================================================
# 🧪 Тестовый запуск
# =======================================================
if __name__ == "__main__":
    run_auto_update(timeframe="M30")
