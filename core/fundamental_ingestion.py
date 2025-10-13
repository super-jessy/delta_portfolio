import os
import json
import pandas as pd
import requests
from datetime import datetime
from sqlalchemy import create_engine
from dotenv import load_dotenv

# ==============================
# 🔧 Загрузка переменных окружения
# ==============================
load_dotenv()

API_KEY = os.getenv("ALPHA_VANTAGE_KEY")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_DB = os.getenv("PG_DB")

# Подключение к PostgreSQL
DB_URL = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
engine = create_engine(DB_URL)

# ==============================
# 🧩 Безопасное преобразование чисел
# ==============================
def safe_float(x):
    try:
        if x in (None, "None", "null", "", "NaN"):
            return 0.0
        return float(x)
    except Exception:
        return 0.0


# ==============================
# 📥 Загрузка фундаментальных данных
# ==============================
def fetch_fundamentals(symbol: str) -> pd.DataFrame:
    """Загружает фундаментальные данные из Alpha Vantage."""
    print(f"⏳ Загружаем фундаментальные данные для {symbol}...")
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={API_KEY}"
    resp = requests.get(url)
    data = resp.json()

    if "Symbol" not in data:
        print(f"⚠️  Нет данных для {symbol} — возможно, превышен лимит API или тикер отсутствует.")
        return pd.DataFrame()

    record = {
        "symbol": symbol,
        "report_date": datetime.now(),
        "pe_ratio": safe_float(data.get("PERatio")),
        "pb_ratio": safe_float(data.get("PriceToBookRatio")),
        "ev_ebitda": safe_float(data.get("EVToEBITDA")),
        "fcf_yield": safe_float(data.get("FCFYieldTTM")),
        "dividend_yield": safe_float(data.get("DividendYield")),
        "eps": safe_float(data.get("EPS")),
        "roe": safe_float(data.get("ReturnOnEquityTTM")),
        "roa": safe_float(data.get("ReturnOnAssetsTTM")),
        "gross_margin": safe_float(data.get("GrossProfitMarginTTM")),
        "operating_margin": safe_float(data.get("OperatingMarginTTM")),
        "net_margin": safe_float(data.get("NetProfitMarginTTM")),
        "raw_json": json.dumps(data),
    }

    print(f"✅ Фундаментальные данные получены для {symbol}")
    return pd.DataFrame([record])


# ==============================
# 💾 Сохранение в базу данных
# ==============================
def save_to_db(df: pd.DataFrame):
    if df.empty:
        return

    table_name = "fundamental_data"
    with engine.begin() as conn:
        df.to_sql(table_name, conn, if_exists="append", index=False)
    print(f"📊 Сохранено {len(df)} строк для {df['symbol'].iloc[0]}")


# ==============================
# 🚀 Основной запуск
# ==============================
if __name__ == "__main__":
    symbols = ["AAPL", "AMZN", "TSLA"]

    for sym in symbols:
        df = fetch_fundamentals(sym)
        save_to_db(df)

    print("🎯 Загрузка фундаментальных данных завершена успешно.")
