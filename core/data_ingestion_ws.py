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
def fetch_quote_history(symbol: str, timeframe: str = "D1", since: datetime | None = None):
    """
    Загружает бары из FXOpen.
    - Если since=None → загружает последние 1000 баров (исторические, Count=-1000)
    - Если since задан → догружает новые бары вперёд по 1000 за итерацию (Count=1000)
    """
    print(f"⏳ Подключаемся к WebSocket для {symbol} ({timeframe})...")

    all_data = []
    total_bars = 0
    iteration = 0
    next_from = since
    last_max_dt = None

    while True:
        iteration += 1
        ws = create_connection(WS_URL)
        timestamp = int(time.time() * 1000)
        signature = create_signature(timestamp, FXOPEN_API_ID, FXOPEN_API_KEY, FXOPEN_API_SECRET)

        # --- Авторизация ---
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
            break

        # --- Формирование запроса ---
        req_id = str(uuid4())
        params = {
            "Symbol": symbol,
            "Periodicity": timeframe,
            "PriceType": "bid",
        }

        if next_from is None:
            # Первичная загрузка — 1000 баров назад
            params["Count"] = -1000
            params["Timestamp"] = int(time.time() * 1000)
        else:
            # Догрузка — по 1000 баров вперёд
            params["Count"] = 1000
            params["From"] = int(next_from.timestamp() * 1000)

        ws.send(json.dumps({"Id": req_id, "Request": "QuoteHistoryBars", "Params": params}))
        data = json.loads(ws.recv())
        ws.close()

        bars = data.get("Result", {}).get("Bars", [])
        if not bars:
            print(f"⚙️ FXOpen не вернул данных для {symbol}")
            break

        # --- Преобразуем в DataFrame ---
        df_part = pd.DataFrame(bars)
        df_part["datetime"] = pd.to_datetime(df_part["Timestamp"], unit="ms")

        # --- защита от зацикливания ---
        current_max_dt = df_part["datetime"].max()
        if last_max_dt and current_max_dt <= last_max_dt:
            print(f"⚠️ FXOpen вернул те же бары ({current_max_dt}), прерываем.")
            break
        last_max_dt = current_max_dt

        df_part["ticker"] = symbol
        df_part["timeframe"] = timeframe
        df_part.rename(columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume"
        }, inplace=True)
        df_part = df_part[["ticker", "timeframe", "datetime", "open", "high", "low", "close", "volume"]]
        all_data.append(df_part)

        total_bars += len(df_part)
        print(f"✅ [{iteration}] Получено {len(df_part)} баров ({df_part['datetime'].min()} → {df_part['datetime'].max()})")

        # --- Если это первичная загрузка (-1000), достаточно 1 итерации ---
        if since is None:
            print(f"🧩 Первичная загрузка завершена ({len(df_part)} баров).")
            break

        # --- Если меньше 1000, значит достигнут конец истории ---
        if len(df_part) < 1000:
            print(f"ℹ️ Последняя порция <1000 баров, загрузка завершена.")
            break

        # --- Следующее окно ---
        next_from = df_part["datetime"].max() + timedelta(milliseconds=1)
        time.sleep(0.5)

    if not all_data:
        print(f"⚠️ Нет данных для {symbol}")
        return pd.DataFrame()

    df = pd.concat(all_data).drop_duplicates(subset="datetime").sort_values("datetime")
    print(f"🎯 Загружено всего {total_bars} баров ({iteration} запросов) для {symbol} ({timeframe})")
    return df

# =======================================================
# 💾 Сохранение котировок в instrument_quotes (без дублей)
# =======================================================
def save_to_db(df: pd.DataFrame):
    if df.empty:
        print("⚠️ Пустой DataFrame, пропускаем.")
        return

    ticker = df["ticker"].iloc[0]
    timeframe = df["timeframe"].iloc[0]

    with engine.begin() as conn:
        existing_dates = pd.read_sql(
            text("""
                SELECT datetime FROM instrument_quotes
                WHERE ticker = :ticker AND timeframe = :tf
            """),
            conn,
            params={"ticker": ticker, "tf": timeframe}
        )['datetime'].astype('datetime64[ns]')

        df_filtered = df[~df["datetime"].isin(existing_dates)]

        if not df_filtered.empty:
            df_filtered.to_sql("instrument_quotes", conn, if_exists="append", index=False)
            print(f"📊 Добавлено {len(df_filtered)} новых баров для {ticker} ({timeframe})")
        else:
            print(f"✅ Нет новых баров для {ticker} ({timeframe}) — пропускаем.")

# =======================================================
# 🔁 Проверка и обновление котировок
# =======================================================
def update_quotes_if_needed(ticker, timeframe):
    print(f"🔍 Проверка обновления для {ticker} ({timeframe})")
    last_dt = get_last_datetime(ticker, timeframe)
    now = datetime.utcnow()

    refresh_period = {
        "M1": timedelta(minutes=1),
        "M5": timedelta(minutes=5),
        "M15": timedelta(minutes=15),
        "M30": timedelta(minutes=30),
        "H1": timedelta(hours=1),
        "D1": timedelta(days=1)
    }.get(timeframe, timedelta(hours=1))

    if last_dt is None:
        print(f"🆕 История отсутствует в БД → первичная загрузка {ticker} ({timeframe})")
        df = fetch_quote_history(ticker, timeframe=timeframe, since=None)
        if not df.empty:
            save_to_db(df)
    elif now - last_dt >= refresh_period:
        print(f"🕒 Обновляем данные для {ticker} с {last_dt}")
        df = fetch_quote_history(ticker, timeframe=timeframe, since=last_dt)
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
        time.sleep(60)

# =======================================================
# 🧪 Тестовый запуск
# =======================================================
if __name__ == "__main__":
    run_auto_update(timeframe="M30")
