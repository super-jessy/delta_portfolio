# services/chart_service.py
import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime, timedelta
from core.data_ingestion_ws import fetch_quote_history

load_dotenv()

PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_DB = os.getenv("PG_DB")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")

DB_URL = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
engine = create_engine(DB_URL)

# === Обновление каждые 15 минут, независимо от ТФ ===
REFRESH_PERIOD = timedelta(minutes=15)


def fetch_candles(symbol: str, timeframe: str):
    """Возвращает свечи (datetime, open, high, low, close, volume) с проверкой и автодогрузкой"""
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT datetime, open, high, low, close, volume
                FROM instrument_quotes
                WHERE ticker = :symbol AND timeframe = :tf
                ORDER BY datetime ASC
            """)
            df = pd.read_sql(query, conn, params={"symbol": symbol, "tf": timeframe})
    except Exception as e:
        print(f"[chart_service] Ошибка при чтении из БД: {e}")
        df = pd.DataFrame()

    now = datetime.utcnow()

    # === Если данных нет вообще — загружаем полную историю ===
    if df.empty:
        print(f"[chart_service] История отсутствует в БД для {symbol} ({timeframe}) → первичная загрузка...")
        df_new = fetch_quote_history(symbol, timeframe)  # загрузим полные 1000 баров
        if not df_new.empty:
            save_to_db(df_new)
            return _to_tuples(df_new)
        else:
            print(f"[chart_service] ❌ Не удалось получить историю для {symbol}")
            return []

    # === Проверяем, пора ли обновлять (каждые 15 минут) ===
    last_dt = df["datetime"].max()
    if now - last_dt >= REFRESH_PERIOD:
        print(f"[chart_service] Обновляем {symbol} ({timeframe}) с {last_dt}")
        df_new = fetch_quote_history(symbol, timeframe, since=last_dt)
        if not df_new.empty:
            save_to_db(df_new)
            df = pd.concat([df, df_new]).drop_duplicates(subset="datetime").sort_values("datetime")
        else:
            print(f"[chart_service] ⚠️ FXOpen не вернул новых баров для {symbol}")

    return _to_tuples(df)


def _to_tuples(df: pd.DataFrame):
    """Превращает DataFrame в список кортежей"""
    return [
        (row["datetime"], row["open"], row["high"], row["low"], row["close"])
        for _, row in df.iterrows()
    ]


def save_to_db(df: pd.DataFrame):
    """Сохраняет новые бары в instrument_quotes без дубликатов"""
    if df.empty:
        return

    with engine.begin() as conn:
        for ticker, tf in df[['ticker', 'timeframe']].drop_duplicates().itertuples(index=False):
            # 1️⃣ Получаем уже существующие даты для этого тикера и ТФ
            existing_dates = pd.read_sql(
                text("""
                    SELECT datetime FROM instrument_quotes
                    WHERE ticker = :ticker AND timeframe = :tf
                """),
                conn,
                params={"ticker": ticker, "tf": tf}
            )['datetime'].astype('datetime64[ns]')

            # 2️⃣ Фильтруем только новые строки
            df_filtered = df[
                (df['ticker'] == ticker) &
                (df['timeframe'] == tf) &
                (~df['datetime'].isin(existing_dates))
            ]

            # 3️⃣ Записываем только уникальные
            if not df_filtered.empty:
                df_filtered.to_sql("instrument_quotes", conn, if_exists="append", index=False)
                print(f"[chart_service] Добавлено {len(df_filtered)} новых баров для {ticker} ({tf})")
            else:
                print(f"[chart_service] Нет новых баров для {ticker} ({tf}) — пропускаем.")
