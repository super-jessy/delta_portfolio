import os
import sys
import pandas as pd
import psycopg2
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Настройки
load_dotenv()
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DB = os.getenv("PG_DB", "delta_portfolio")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "1234")

CSV_PATH = "data/US stocks.csv"


# Загрузка тикеров из CSV

def load_csv_tickers(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Файл {path} не найден")
    df = pd.read_csv(path, header=None, names=["symbols"])
    tickers = df["symbols"].dropna().astype(str).str.strip().unique().tolist()
    print(f"📄 Загружено {len(tickers)} тикеров из {path}")
    return tickers


# Загрузка тикеров из базы данных

def load_db_tickers():
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD
    )
    cur = conn.cursor()
    cur.execute("SELECT ticker FROM instruments;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    tickers = [r[0].strip() for r in rows if r[0]]
    print(f"🗄 Найдено {len(tickers)} тикеров в таблице instruments")
    return tickers


# Сравнение и отчёт

def compare_tickers(csv_tickers, db_tickers):
    csv_set = set(csv_tickers)
    db_set = set(db_tickers)

    missing = sorted(csv_set - db_set)
    extra = sorted(db_set - csv_set)

    print("\n📊 РЕЗУЛЬТАТ СРАВНЕНИЯ:")
    print(f"✅ В базе найдено: {len(db_set & csv_set)} тикеров, совпадающих с CSV")
    print(f"❌ Отсутствует в базе: {len(missing)}")
    print(f"⚠️ В базе лишних (не из CSV): {len(extra)}\n")

    if missing:
        print("❌ Отсутствующие тикеры:")
        print(", ".join(missing))
        os.makedirs("logs", exist_ok=True)
        with open("logs/missing_in_db.txt", "w") as f:
            for t in missing:
                f.write(t + "\n")
        print("\n📝 Список сохранён в logs/missing_in_db.txt")

    if extra:
        print("\n⚠️ Лишние тикеры (в базе, но не в CSV):")
        print(", ".join(extra))


# Точка входа

if __name__ == "__main__":
    csv_tickers = load_csv_tickers(CSV_PATH)
    db_tickers = load_db_tickers()
    compare_tickers(csv_tickers, db_tickers)
