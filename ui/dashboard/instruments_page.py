from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QTextEdit, QFrame, QLineEdit, QScrollArea
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

        # ─── Поиск ───
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

        # ─── Таблица ───
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(["Ticker", "Company Name"])
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_widget.cellClicked.connect(self.load_instrument_details)

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

        # ───── Правая часть (инфо + нижние окна) ─────
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # ─── Верх — окно информации ───
        self.info_frame = QFrame()
        self.info_frame.setStyleSheet("background-color: #222222; border: 1px solid #333; border-radius: 6px;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        scroll.setWidget(self.info_frame)

        self.info_layout = QVBoxLayout(self.info_frame)
        self.info_layout.setContentsMargins(15, 15, 15, 15)
        self.info_layout.setSpacing(8)

        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setFixedHeight(100)
        self.info_layout.addWidget(self.logo_label)

        # Текстовые поля
        self.labels = {}
        fields = [
            "Name", "Ticker", "Market", "Locale", "Exchange", "Currency",
            "Market Cap", "Employees", "Phone", "Address", "Postal Code",
            "SIC Description", "List Date", "Shares Outstanding", "Round Lot",
            "Composite FIGI", "Share Class FIGI", "Homepage"
        ]
        for f in fields:
            lbl = QLabel(f"{f}: -")
            lbl.setStyleSheet("color: white; font-size: 13px;")
            self.labels[f] = lbl
            self.info_layout.addWidget(lbl)

        # Описание
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
        self.info_layout.addWidget(self.description_box)

        right_layout.addWidget(scroll, stretch=2)

        # ─── Нижние два окна (статичные) ───
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

    # ──────────────────────────────
    # Загрузка тикеров
    # ──────────────────────────────
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
            self.all_tickers = rows
            self.display_tickers(rows)
        except Exception as e:
            print(f"Ошибка загрузки тикеров: {e}")

    # ──────────────────────────────
    # Отображение тикеров
    # ──────────────────────────────
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

    # ──────────────────────────────
    # Поиск тикеров
    # ──────────────────────────────
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

    # ──────────────────────────────
    # Загрузка деталей инструмента
    # ──────────────────────────────
    def load_instrument_details(self, row, column):
        ticker_item = self.table_widget.item(row, 0)
        if not ticker_item:
            return
        ticker = ticker_item.text()

        def fmt_num(n):
            try:
                return f"{float(n):,.0f}"
            except Exception:
                return "-"

        try:
            conn = psycopg2.connect(
                host=PG_HOST, port=PG_PORT, dbname=PG_DB,
                user=PG_USER, password=PG_PASSWORD
            )
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    name, ticker, market, locale, primary_exchange, currency_name,
                    market_cap, total_employees, phone_number,
                    address1, city, state, postal_code,
                    sic_description, list_date,
                    share_class_shares_outstanding, round_lot,
                    composite_figi, share_class_figi,
                    homepage_url, description, logo_data
                FROM instruments
                WHERE ticker = %s;
            """, (ticker,))
            data = cur.fetchone()
            conn.close()

            if not data:
                self.description_box.setPlainText("No data for this ticker.")
                return

            (name, ticker, market, locale, exch, currency,
             cap, employees, phone, address1, city, state, postal,
             sic_desc, list_date, shares, round_lot,
             composite_figi, share_class_figi, homepage, desc, logo_data) = data

            # Логотип
            if logo_data:
                pixmap = QPixmap()
                pixmap.loadFromData(logo_data)
                scaled = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio)
                self.logo_label.setPixmap(scaled)
            else:
                self.logo_label.clear()
                self.logo_label.setText("No logo")

            # Текстовые поля
            self.labels["Name"].setText(f"Name: {name or '-'}")
            self.labels["Ticker"].setText(f"Ticker: {ticker or '-'}")
            self.labels["Market"].setText(f"Market: {market or '-'}")
            self.labels["Locale"].setText(f"Locale: {locale or '-'}")
            self.labels["Exchange"].setText(f"Exchange: {exch or '-'}")
            self.labels["Currency"].setText(f"Currency: {currency or '-'}")
            self.labels["Market Cap"].setText(f"Market Cap: {fmt_num(cap)}")
            self.labels["Employees"].setText(f"Employees: {employees or '-'}")
            self.labels["Phone"].setText(f"Phone: {phone or '-'}")

            addr = ", ".join([p for p in [address1, city, state] if p])
            self.labels["Address"].setText(f"Address: {addr or '-'}")
            self.labels["Postal Code"].setText(f"Postal Code: {postal or '-'}")
            self.labels["SIC Description"].setText(f"SIC Description: {sic_desc or '-'}")
            self.labels["List Date"].setText(f"List Date: {list_date or '-'}")
            self.labels["Shares Outstanding"].setText(f"Shares Outstanding: {fmt_num(shares)}")
            self.labels["Round Lot"].setText(f"Round Lot: {round_lot or '-'}")
            self.labels["Composite FIGI"].setText(f"Composite FIGI: {composite_figi or '-'}")
            self.labels["Share Class FIGI"].setText(f"Share Class FIGI: {share_class_figi or '-'}")

            if homepage:
                self.labels["Homepage"].setText(f'<a href="{homepage}" style="color:#A2DD84;">{homepage}</a>')
                self.labels["Homepage"].setTextFormat(Qt.TextFormat.RichText)
                self.labels["Homepage"].setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
                self.labels["Homepage"].setOpenExternalLinks(True)
            else:
                self.labels["Homepage"].setText("Homepage: -")

            self.description_box.setPlainText(desc or "No description available.")

        except Exception as e:
            self.description_box.setPlainText(f"Ошибка загрузки данных: {e}")
