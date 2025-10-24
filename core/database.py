import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base


# Загрузка переменных окружения

load_dotenv()

PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_DB = os.getenv("PG_DB")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_SCHEMA = os.getenv("PG_SCHEMA", "public")


# Формирование URL подключения

DATABASE_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"


# Инициализация SQLAlchemy

engine = create_engine(DATABASE_URL, echo=False)

# Устанавливаем схему по умолчанию
metadata = MetaData(schema=PG_SCHEMA)
Base = declarative_base(metadata=metadata)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# Пример ORM моделей

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON

class MarketOHLC(Base):
    __tablename__ = "market_ohlc"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, index=True)
    datetime = Column(DateTime, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)


class FundamentalData(Base):
    __tablename__ = "fundamental_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, index=True)
    report_date = Column(DateTime, index=True)
    pe_ratio = Column(Float)
    pb_ratio = Column(Float)
    ev_ebitda = Column(Float)
    fcf_yield = Column(Float)
    dividend_yield = Column(Float)
    eps = Column(Float)
    roe = Column(Float)
    roa = Column(Float)
    gross_margin = Column(Float)
    operating_margin = Column(Float)
    net_margin = Column(Float)
    raw_json = Column(JSON)


class ExperimentRegistry(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String, unique=True)
    created_at = Column(DateTime)
    config = Column(JSON)
    metrics = Column(JSON)
    tag = Column(String, index=True)

# Функции и инициализация

def init_db():
    """Создаёт все таблицы в PostgreSQL, если их нет."""
    print("⏳ Initializing PostgreSQL database...")
    Base.metadata.create_all(bind=engine)
    print(f"✅ Database initialized successfully (schema: {PG_SCHEMA})")


def get_db():
    """Создаёт и возвращает сессию SQLAlchemy."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
