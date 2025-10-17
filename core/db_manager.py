# core/db_manager.py

import psycopg2
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("PG_HOST"),
    "port": os.getenv("PG_PORT"),
    "dbname": os.getenv("PG_DB"),
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD")
}


class DatabaseManager:
    def __init__(self):
        self.connection = psycopg2.connect(**DB_CONFIG)
        self.connection.autocommit = True
        self.cursor = self.connection.cursor()

    def create_table(self):
        """Создает таблицу instruments, если она еще не существует"""
        create_query = """
        CREATE TABLE IF NOT EXISTS instruments (
            id SERIAL PRIMARY KEY,
            ticker VARCHAR(10) UNIQUE,
            name TEXT,
            market VARCHAR(20),
            locale VARCHAR(10),
            primary_exchange VARCHAR(10),
            currency_name VARCHAR(10),
            composite_figi VARCHAR(20),
            share_class_figi VARCHAR(20),
            market_cap NUMERIC,
            phone_number VARCHAR(50),
            address1 TEXT,
            city TEXT,
            state TEXT,
            postal_code TEXT,
            description TEXT,
            sic_description TEXT,
            homepage_url TEXT,
            total_employees INT,
            list_date DATE,
            share_class_shares_outstanding BIGINT,
            weighted_shares_outstanding BIGINT,
            round_lot INT,
            logo_data BYTEA
        );
        """
        self.cursor.execute(create_query)
        print("✅ Table 'instruments' is ready.")

    def insert_instrument(self, data):
        """Вставляет данные по инструменту в таблицу"""
        insert_query = """
        INSERT INTO instruments (
            ticker, name, market, locale, primary_exchange, currency_name,
            composite_figi, share_class_figi, market_cap, phone_number,
            address1, city, state, postal_code, description,
            sic_description, homepage_url, total_employees, list_date,
            share_class_shares_outstanding, weighted_shares_outstanding,
            round_lot, logo_data
        ) VALUES (
            %(ticker)s, %(name)s, %(market)s, %(locale)s, %(primary_exchange)s, %(currency_name)s,
            %(composite_figi)s, %(share_class_figi)s, %(market_cap)s, %(phone_number)s,
            %(address1)s, %(city)s, %(state)s, %(postal_code)s, %(description)s,
            %(sic_description)s, %(homepage_url)s, %(total_employees)s, %(list_date)s,
            %(share_class_shares_outstanding)s, %(weighted_shares_outstanding)s,
            %(round_lot)s, %(logo_data)s
        )
        ON CONFLICT (ticker)
        DO UPDATE SET
            name = EXCLUDED.name,
            market = EXCLUDED.market,
            locale = EXCLUDED.locale,
            primary_exchange = EXCLUDED.primary_exchange,
            currency_name = EXCLUDED.currency_name,
            composite_figi = EXCLUDED.composite_figi,
            share_class_figi = EXCLUDED.share_class_figi,
            market_cap = EXCLUDED.market_cap,
            phone_number = EXCLUDED.phone_number,
            address1 = EXCLUDED.address1,
            city = EXCLUDED.city,
            state = EXCLUDED.state,
            postal_code = EXCLUDED.postal_code,
            description = EXCLUDED.description,
            sic_description = EXCLUDED.sic_description,
            homepage_url = EXCLUDED.homepage_url,
            total_employees = EXCLUDED.total_employees,
            list_date = EXCLUDED.list_date,
            share_class_shares_outstanding = EXCLUDED.share_class_shares_outstanding,
            weighted_shares_outstanding = EXCLUDED.weighted_shares_outstanding,
            round_lot = EXCLUDED.round_lot,
            logo_data = EXCLUDED.logo_data;
        """
        self.cursor.execute(insert_query, data)
        print(f"✅ Inserted/Updated: {data.get('ticker')}")

    def get_instrument(self, ticker):
        """Возвращает данные по тикеру"""
        self.cursor.execute("SELECT * FROM instruments WHERE ticker = %s;", (ticker,))
        return self.cursor.fetchone()

    def close(self):
        """Закрывает соединение"""
        self.cursor.close()
        self.connection.close()
