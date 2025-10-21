from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QLabel,
    QTextEdit, QFrame, QSplitter, QSizePolicy
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import psycopg2
import os
from dotenv import load_dotenv
import io
import requests

# ────────────────────────────────────────────────
# Настройки подключения к БД
# ────────────────────────────────────────────────
load_dotenv()
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DB = os.getenv("PG_DB", "delta_portfolio")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "1234")


# ────────────────────────────────────────────────
# Основной класс страницы Instruments
# ────────────────────────────────────────────────
class InstrumentsPage(QWidget):
    def __init__(self):
        super().__init__()

        # Главный layout — горизонтальный (4 окна)
        main_layout = QHBoxLayout(self)

        # ───── 1. Список инструментов ─────
        self.list_widget = QListWidget()
        self.list_widget.setMinimumWidth(200)
        self.list_widget.itemClicked.connect(self.load_instrument_details)
        main_layout.addWidget(self.list_widget)

        # ───── 2. Окно информации ─────
        self.info_frame = QFrame()
        self.info_layout = QVBoxLayout(self.info_frame)

        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setFixedHeight(100)

        self.name_label = QLabel("Name: -")
        self.market_cap_label = QLabel("Market Cap: -")
        self.exchange_label = QLabel("Exchange: -")
        self.address_label = QLabel("Address: -")
        self.employees_label = QLabel("Employees: -")

        self.description_box = QTextEdit()
        self.description_box.setReadOnly(True)
        self.description_box.setMinimumHeight(150)
        self.description_box.setStyleSheet("background-color: #1E1E1E; color: #A2DD84;")

        for w in [
            self.logo_label, self.name_label, self.market_cap_label,
            self.exchange_label, self.address_label, self.employees_label,
            self.description_box
        ]:
            self.info_layout.addWidget(w)

        main_layout.addWidget(self.info_frame)

        # ───── 3 и 4 окна (пока пустые) ─────
        placeholder3 = QFrame()
        placeholder3.setStyleSheet("background-color: #121212; border: 1px solid #333;")
        placeholder4 = QFrame()
        placeholder4.setStyleSheet("background-color: #121212; border: 1px solid #333;")

        main_layout.addWidget(placeholder3)
        main_layout.addWidget(placeholder4)

        # Загрузка тикеров при старте
        self.load_tickers()

    # ────────────────────────────────────────────────
    # Загрузка списка тикеров
    # ────────────────────────────────────────────────
    def load_tickers(self):
        try:
            conn = psycopg2.connect(
                host=PG_HOST, port=PG_PORT, dbname=PG_DB,
                user=PG_USER, password=PG_PASSWORD
            )
            cur = conn.cursor()
            cur.execute("SELECT ticker, name FROM instruments ORDER BY ticker ASC;")
            rows = cur.fetchall()
            for ticker, name in rows:
                self.list_widget.addItem(f"{ticker} — {name}")
            conn.close()
        except Exception as e:
            self.list_widget.addItem(f"Ошибка загрузки: {e}")

    # ────────────────────────────────────────────────
    # Загрузка деталей выбранного инструмента
    # ────────────────────────────────────────────────
    def load_instrument_details(self, item):
        ticker = item.text().split(" — ")[0]
        try:
            conn = psycopg2.connect(
                host=PG_HOST, port=PG_PORT, dbname=PG_DB,
                user=PG_USER, password=PG_PASSWORD
            )
            cur = conn.cursor()
            cur.execute("""
                SELECT name, market_cap, primary_exchange, city, state,
                       total_employees, description, homepage_url, logo_data
                FROM instruments WHERE ticker = %s;
            """, (ticker,))
            row = cur.fetchone()
            conn.close()

            if row:
                name, cap, exch, city, state, employees, desc, url, logo_data = row
                self.name_label.setText(f"Name: {name or '-'}")
                self.market_cap_label.setText(f"Market Cap: {cap:,.0f}" if cap else "Market Cap: -")
                self.exchange_label.setText(f"Exchange: {exch or '-'}")
                self.address_label.setText(f"Address: {city or ''}, {state or ''}")
                self.employees_label.setText(f"Employees: {employees or '-'}")
                self.description_box.setPlainText(desc or "No description available.")

                # Покажем логотип (если он есть)
                if logo_data:
                    pixmap = QPixmap()
                    pixmap.loadFromData(logo_data)
                    scaled = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio)
                    self.logo_label.setPixmap(scaled)
                else:
                    self.logo_label.clear()
                    self.logo_label.setText("No logo")

        except Exception as e:
            self.description_box.setPlainText(f"Ошибка загрузки данных: {e}")
