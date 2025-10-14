from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QHeaderView
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor, QBrush
from services.econ_calendar_service import fetch_economic_calendar


class EconomicCalendarPanel(QWidget):
    """
    Панель экономического календаря (Myfxbook RSS)
    """
    def __init__(self):
        super().__init__()

        # --- Основной layout ---
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(8)

        title = QLabel("Economic Calendar")
        title.setStyleSheet("""
            color: #FFFFFF;
            font-size: 12px;
            font-weight: 600;
            background: transparent; 
            border: none;
        """)
        self.layout.addWidget(title)

        # --- Таблица календаря ---
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Date", "Time", "Event"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QHeaderView::section {
                background-color: #1E1E1E;
                color: #A2DD84;
                font-weight: 600;
                border: none;
                height: 25px;
            }
            QTableWidget {
                background-color: #121212;
                color: #FFFFFF;
                gridline-color: #2E2E2E;
                font-size: 12px;
            }
            QTableWidget::item:selected {
                background-color: #2E4C2F;
            }
        """)

        self.layout.addWidget(self.table)

        # --- Первичная загрузка данных ---
        self.load_calendar_data()

        # --- Автообновление каждые 30 минут ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.load_calendar_data)
        self.timer.start(1800000)

    def load_calendar_data(self):
        """Загружает и отображает данные из Myfxbook RSS"""
        events = fetch_economic_calendar()
        self.table.setRowCount(len(events))

        if not events:
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QTableWidgetItem("No data"))
            return

        for i, e in enumerate(events):
            date_str = e.get("published", "")
            event_title = e.get("title", "")

            # Определяем цвет события
            brush = QBrush(QColor("#A2DD84"))
            if "CPI" in event_title or "Inflation" in event_title:
                brush = QBrush(QColor("#FFB347"))
            elif "Unemployment" in event_title or "Job" in event_title:
                brush = QBrush(QColor("#FF5C5C"))

            date_part, time_part = self.split_datetime(date_str)
            self.table.setItem(i, 0, QTableWidgetItem(date_part))
            self.table.setItem(i, 1, QTableWidgetItem(time_part))
            event_item = QTableWidgetItem(event_title)
            event_item.setForeground(brush)
            self.table.setItem(i, 2, event_item)
    
            header = self.table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Date
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Time
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # Event

    def split_datetime(self, dt):
        """Разделяет дату и время из строки"""
        # Пример входа: "Tue, 14 Oct 2025 10:18 GMT"
        try:
            parts = dt.split(" ")
            if len(parts) >= 5:
                date_part = f"{parts[0]} {parts[1]} {parts[2]}"
                time_part = parts[4]
                return date_part, time_part
        except Exception:
            pass
        return dt, ""


# ✅ Чтобы импорт в dashboard.py не ломался:
EconCalendar = EconomicCalendarPanel
