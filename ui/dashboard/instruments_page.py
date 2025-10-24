from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QTextEdit, QFrame, QLineEdit, QScrollArea, QGridLayout
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

        # ───── Главный layout ─────
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # ───── Левая часть (поиск + таблица) ─────
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        # Поиск
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search instrument...")
        self.search_input.textChanged.connect(self.filter_tickers)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #222;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #A2DD84;
            }
        """)
        left_layout.addWidget(self.search_input)

        # Таблица инструментов
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(["Ticker", "Company Name"])
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_widget.cellClicked.connect(self.load_instrument_details)
        self.table_widget.setStyleSheet("""
            QHeaderView::section {
                background-color: #222;
                color: #A2DD84;
                font-weight: bold;
                border: none;
                padding: 6px;
            }
            QTableWidget {
                background-color: #222;
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

        # ───── Правая часть (инфо) ─────
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        self.info_frame = QFrame()
        self.info_frame.setStyleSheet("""
            QFrame {
                background-color: #1B1B1B;
                border: none;
            }
        """)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        scroll.setWidget(self.info_frame)

        self.info_layout = QVBoxLayout(self.info_frame)
        self.info_layout.setContentsMargins(20, 20, 20, 20)
        self.info_layout.setSpacing(24)

        # ───────────── HEADER ─────────────
        self.header_frame = QFrame()
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(15)

        # Квадратный фон под логотипом
        self.logo_bg = QFrame()
        self.logo_bg.setFixedSize(80, 80)
        self.logo_bg.setStyleSheet("""
            background-color: #A2DD84;
            border-radius: 10%;
        """)

        # Логотип
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(60, 60)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setStyleSheet("background: transparent; border: none;")

        logo_layout = QVBoxLayout(self.logo_bg)
        logo_layout.setContentsMargins(10, 10, 10, 10)
        logo_layout.addWidget(self.logo_label)

        # Название и тикер
        text_block = QVBoxLayout()
        text_block.setSpacing(4)

        self.company_name = QLabel("Select a company")
        self.company_name.setStyleSheet("""
            font-size: 20px;
            font-weight: 600;
            color: white;
            background: transparent;
            border: none;
        """)

        self.ticker_exchange = QLabel("")
        self.ticker_exchange.setStyleSheet("""
            font-size: 13px;
            color: #A2DD84;
            background: transparent;
            border: none;
        """)

        text_block.addWidget(self.company_name)
        text_block.addWidget(self.ticker_exchange)

        header_layout.addWidget(self.logo_bg)
        header_layout.addLayout(text_block)
        header_layout.addStretch()

        self.info_layout.addWidget(self.header_frame)
        self.add_divider(self.info_layout)

        self.sections = {}

        def create_section(title):
            section_frame = QFrame()
            section_frame.setStyleSheet("background: transparent; border: none;")
            
            section_layout = QVBoxLayout(section_frame)
            section_layout.setContentsMargins(0, 0, 0, 0)
            section_layout.setSpacing(6)

            title_label = QLabel(title)
            title_label.setStyleSheet("""
                color: #A2DD84;
                font-weight: 600;
                font-size: 14px;
                background: transparent;
                border: none;
            """)
            section_layout.addWidget(title_label)

            grid = QGridLayout()
            grid.setHorizontalSpacing(10)
            grid.setVerticalSpacing(2)
            section_layout.setSpacing(8)
            section_layout.addLayout(grid)

            self.info_layout.addWidget(section_frame)
            self.add_divider(self.info_layout)
            return grid

        self.sections["Instrument Specifications"] = create_section("Instrument Specifications")
        self.sections["Company Specifications"] = create_section("Company Specifications")
        self.sections["Company Contacts"] = create_section("Company Contacts")

        desc_label = QLabel("Description")
        desc_label.setStyleSheet("color: #A2DD84; font-weight: 600; font-size: 14px; margin-top: 8px; background: transparent; border: none;")
        self.info_layout.addWidget(desc_label)

        self.description_box = QTextEdit()
        self.description_box.setReadOnly(True)
        self.description_box.setMinimumHeight(120)
        self.description_box.setStyleSheet("""
            background: transparent;
            color: #A2DD84;
            border: none;
            padding: 6px;
            font-size: 13px;
        """)
        self.info_layout.addWidget(self.description_box)

        right_layout.addWidget(scroll, stretch=2)
        main_layout.addWidget(right_frame, stretch=3)

        self.all_tickers = []
        self.load_tickers()
        
        for row_idx, (ticker, name) in enumerate(self.all_tickers):
          if ticker == "AAPL":
             self.table_widget.selectRow(row_idx)        
             self.load_instrument_details(row_idx, 0)       
             break

    def add_divider(self, layout):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("""
            QFrame {
                background-color: #333;
                max-height: 1px;
                margin-left: 20px;
                margin-right: 20px;
            }
        """)
        layout.addWidget(line)

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

    def filter_tickers(self, text):
        text = text.strip().lower()
        if not text:
            self.display_tickers(self.all_tickers)
            return
        filtered = [(t, n) for (t, n) in self.all_tickers if text in t.lower() or text in (n or "").lower()]
        self.display_tickers(filtered)


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

            # HEADER
            self.company_name.setText(name or "-")
            self.ticker_exchange.setText(f"{ticker} • {exch}" if exch else ticker)

            # Логотип
            if logo_data:
                pixmap = QPixmap()
                pixmap.loadFromData(logo_data)
                scaled = pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.logo_label.setPixmap(scaled)
            else:
                self.logo_label.clear()

            # Очистка старых данных
            for grid in self.sections.values():
                while grid.count():
                    item = grid.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()

            # ─ Instrument Specifications ─
            instr = self.sections["Instrument Specifications"]
            self.add_info_pair(instr, 0, "Locale", locale)
            self.add_info_pair(instr, 0, "Currency", currency, col=1)
            self.add_info_pair(instr, 1, "Round Lot", round_lot)
            self.add_info_pair(instr, 1, "Market", market, col=1)

            # ─ Company Specifications ─
            comp = self.sections["Company Specifications"]
            self.add_info_pair(comp, 0, "Market Cap", fmt_num(cap))
            self.add_info_pair(comp, 0, "Employees", employees, col=1)
            self.add_info_pair(comp, 1, "SIC Description", sic_desc)
            self.add_info_pair(comp, 1, "List Date", list_date, col=1)
            self.add_info_pair(comp, 2, "Shares Outstanding", fmt_num(shares))
            self.add_info_pair(comp, 2, "Composite FIGI", composite_figi, col=1)
            self.add_info_pair(comp, 3, "Share Class FIGI", share_class_figi)

            # ─ Company Contacts ─
            cont = self.sections["Company Contacts"]
            addr = ", ".join([p for p in [address1, city, state] if p])
            self.add_info_pair(cont, 0, "Address", addr)
            self.add_info_pair(cont, 1, "Postal Code", postal)
            self.add_info_pair(cont, 2, "Phone", phone)
            if homepage:
                label = QLabel(f'<a href="{homepage}" style="color:#A2DD84; background: transparent; border: none;">{homepage}</a>')
                label.setTextFormat(Qt.TextFormat.RichText)
                label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
                label.setOpenExternalLinks(True)
                cont.addWidget(label, 3, 0, 1, 2)
            else:
                self.add_info_pair(cont, 3, "Homepage", "-")

            # Описание
            self.description_box.setPlainText(desc or "No description available.")

        except Exception as e:
            self.description_box.setPlainText(f"Ошибка загрузки данных: {e}")

    # ──────────────────────────────
    def add_info_pair(self, grid, row, key, value, col=0):
     container = QHBoxLayout()
     container.setContentsMargins(0, 0, 0, 0)
     container.setSpacing(6)  # ← регулирует расстояние между "Locale:" и "us"

     key_label = QLabel(f"{key}:")
     key_label.setStyleSheet("color: #CCCCCC; font-size: 13px; background: transparent; border: none;")
     val_label = QLabel(str(value or "-"))
     val_label.setStyleSheet("color: white; font-size: 13px; background: transparent; border: none;")

     container.addWidget(key_label)
     container.addWidget(val_label)
     container.addStretch()

     frame = QFrame()
     frame.setLayout(container)
     frame.setStyleSheet("background: transparent; border: none;")

     grid.addWidget(frame, row, col)
