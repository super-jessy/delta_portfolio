from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QTextEdit, QFrame, QLineEdit
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import psycopg2
import os
from dotenv import load_dotenv

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

        # ───── Главный горизонтальный layout ─────
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # ───── Левая часть (поиск + таблица инструментов) ─────
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        # ─── Строка поиска ───
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search instrument...")
        self.search_input.textChanged.connect(self.filter_tickers)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #222222;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #A2DD84;
                outline: none;
            }
        """)
        left_layout.addWidget(self.search_input)

        # ─── Таблица инструментов ───
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(["Ticker", "Company Name"])
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_widget.cellClicked.connect(self.load_instrument_details)

        # Стиль DELTA
        self.table_widget.setStyleSheet("""
            QHeaderView::section {
                background-color: #222222;
                color: #A2DD84;
                font-weight: bold;
                border: none;
                padding: 6px;
            }
            QTableWidget {
                background-color: #222222;
                color: white;
                gridline-color: #333;
                selection-background-color: #A2DD84;
                selection-color: black;
                font-size: 13px;
                outline: none;
            }
            QTableWidget::item:hover {
                background-color: #3B5530;
            }
        """)

        left_layout.addWidget(self.table_widget)
        main_layout.addWidget(left_frame, stretch=2)

        # ───── Правая часть ─────
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # ─── Верхнее окно — информация об инструменте ───
        self.info_frame = QFrame()
        self.info_layout = QVBoxLayout(self.info_frame)
        self.info_frame.setStyleSheet("background-color: #222222; border: 1px solid #333; border-radius: 6px;")
        self.info_layout.setContentsMargins(15, 15, 15, 15)
        self.info_layout.setSpacing(8)

        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setFixedHeight(100)

        self.name_label = QLabel("Name: -")
        self.market_cap_label = QLabel("Market Cap: -")
        self.exchange_label = QLabel("Exchange: -")
        self.address_label = QLabel("Address: -")
        self.employees_label = QLabel("Employees: -")

        for lbl in [self.name_label, self.market_cap_label, self.exchange_label, self.address_label, self.employees_label]:
            lbl.setStyleSheet("color: white; font-size: 13px;")

        self.description_box = QTextEdit()
        self.description_box.setReadOnly(True)
        self.description_box.setMinimumHeight(120)
        self.description_box.setStyleSheet("""
            background-color: #222222;
            color: #A2DD84;
            border: 1px solid #333;
            border-radius: 6px;
            padding: 6px;
        """)

        for w in [
            self.logo_label, self.name_label, self.market_cap_label,
            self.exchange_label, self.address_label, self.employees_label,
            self.description_box
        ]:
            self.info_layout.addWidget(w)

        right_layout.addWidget(self.info_frame, stretch=2)

        # ─── Нижняя часть — два статичных окна ───
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(10)

        placeholder3 = QFrame()
        placeholder3.setStyleSheet("background-color: #222222; border: 1px solid #333; border-radius: 6px;")
        placeholder4 = QFrame()
        placeholder4.setStyleSheet("background-color: #222222; border: 1px solid #333; border-radius: 6px;")

        bottom_layout.addWidget(placeholder3)
        bottom_layout.addWidget(placeholder4)

        bottom_wrapper = QFrame()
        bottom_wrapper.setLayout(bottom_layout)
        right_layout.addWidget(bottom_wrapper, stretch=1)

        main_layout.addWidget(right_frame, stretch=3)

        # Загрузка тикеров при старте
        self.all_tickers = []
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
            conn.close()

            self.all_tickers = rows  # сохраним для поиска
            self.display_tickers(rows)

        except Exception as e:
            print(f"Ошибка загрузки тикеров: {e}")

    # ────────────────────────────────────────────────
    # Отображение тикеров в таблице
    # ────────────────────────────────────────────────
    def display_tickers(self, rows):
        self.table_widget.setRowCount(len(rows))
        for i, (ticker, name) in enumerate(rows):
            ticker_item = QTableWidgetItem(ticker)
            name_item = QTableWidgetItem(name or "-")
            ticker_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.table_widget.setItem(i, 0, ticker_item)
            self.table_widget.setItem(i, 1, name_item)

        self.table_widget.setColumnWidth(0, 90)
        self.table_widget.horizontalHeader().setStretchLastSection(True)

    # ────────────────────────────────────────────────
    # Поиск и фильтрация тикеров
    # ────────────────────────────────────────────────
    def filter_tickers(self, text):
        text = text.strip().lower()
        if not text:
            self.display_tickers(self.all_tickers)
            return

        filtered = [
            (t, n) for (t, n) in self.all_tickers
            if text in t.lower() or text in (n or "").lower()
        ]
        self.display_tickers(filtered)

    # ────────────────────────────────────────────────
    # Загрузка деталей выбранного инструмента
    # ────────────────────────────────────────────────
    def load_instrument_details(self, row, column):
        ticker_item = self.table_widget.item(row, 0)
        if not ticker_item:
            return
        ticker = ticker_item.text()

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
