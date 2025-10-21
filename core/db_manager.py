# core/db_manager.py

import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# ────────────────────────────────────────────────
# Настройки из .env
# ────────────────────────────────────────────────
load_dotenv()
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DB = os.getenv("PG_DB", "delta_portfolio")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "1234")
PG_SCHEMA = os.getenv("PG_SCHEMA", "public")


# ────────────────────────────────────────────────
# Класс управления базой данных
# ────────────────────────────────────────────────
class DatabaseManager:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                host=PG_HOST,
                port=PG_PORT,
                dbname=PG_DB,
                user=PG_USER,
                password=PG_PASSWORD
            )
            self.conn.autocommit = False
            print("✅ Database connection established.")
        except Exception as e:
            print(f"❗ Database connection failed: {e}")
            self.conn = None

    def close(self):
        if self.conn:
            self.conn.close()
            print("🔒 Database connection closed.")

    # ────────────────────────────────────────────────
    # Создание таблицы instruments
    # ────────────────────────────────────────────────
    def create_table(self):
        if not self.conn:
            raise RuntimeError("No active database connection.")
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql.SQL(f"""
                    CREATE TABLE IF NOT EXISTS {PG_SCHEMA}.instruments (
                        id SERIAL PRIMARY KEY,
                        ticker VARCHAR(16) UNIQUE,
                        name TEXT,
                        market TEXT,
                        locale TEXT,
                        primary_exchange TEXT,
                        currency_name TEXT,
                        composite_figi TEXT,
                        share_class_figi TEXT,
                        market_cap DOUBLE PRECISION,
                        phone_number TEXT,
                        address1 TEXT,
                        city TEXT,
                        state TEXT,
                        postal_code TEXT,
                        description TEXT,
                        sic_description TEXT,
                        homepage_url TEXT,
                        total_employees BIGINT,
                        list_date DATE,
                        share_class_shares_outstanding BIGINT,
                        weighted_shares_outstanding BIGINT,
                        round_lot BIGINT,
                        logo_data BYTEA
                    );
                """))
                self.conn.commit()
                print("✅ Table 'instruments' is ready.")
        except Exception as e:
            self.conn.rollback()
            print(f"❗ Failed to create table: {e}")

    # ────────────────────────────────────────────────
    # Безопасная вставка (UPSERT)
    # ────────────────────────────────────────────────
    def insert_instrument(self, data: dict):
        if not self.conn:
            raise RuntimeError("No active database connection.")

        try:
            def safe(val):
                if val is None:
                    return None
                if isinstance(val, str):
                    return val.strip()[:1000]
                return val

            columns = [
                "ticker", "name", "market", "locale", "primary_exchange",
                "currency_name", "composite_figi", "share_class_figi",
                "market_cap", "phone_number", "address1", "city", "state",
                "postal_code", "description", "sic_description",
                "homepage_url", "total_employees", "list_date",
                "share_class_shares_outstanding", "weighted_shares_outstanding",
                "round_lot", "logo_data"
            ]

            values = [safe(data.get(col)) for col in columns]
            placeholders = ", ".join(["%s"] * len(columns))
            update_set = ", ".join([f"{col} = EXCLUDED.{col}" for col in columns if col != "ticker"])

            query = f"""
                INSERT INTO {PG_SCHEMA}.instruments ({", ".join(columns)})
                VALUES ({placeholders})
                ON CONFLICT (ticker) DO UPDATE
                SET {update_set};
            """

            with self.conn.cursor() as cur:
                cur.execute(query, values)
            self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            print(f"❗ DB insert error for {data.get('ticker')}: {e}")
