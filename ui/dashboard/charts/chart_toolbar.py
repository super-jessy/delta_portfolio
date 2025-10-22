# ui/dashboard/charts/chart_toolbar.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox
from PyQt6.QtGui import QFont


class ChartToolbar(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        font = QFont("Helvetica Neue", 11)

        # === Выбор инструмента ===
        self.symbol_label = QLabel("Symbol:")
        self.symbol_label.setFont(font)
        self.symbol_label.setStyleSheet("color: #A2DD84;")
        self.symbol_combo = QComboBox()
        self.symbol_combo.setStyleSheet("""
            QComboBox {
                background-color: #1E1E1E;
                color: white;
                border: 1px solid #333;
                padding: 3px 10px;
                border-radius: 4px;
                min-width: 100px;
            }
        """)

        # === Выбор таймфрейма ===
        self.timeframe_label = QLabel("Timeframe:")
        self.timeframe_label.setFont(font)
        self.timeframe_label.setStyleSheet("color: #A2DD84;")
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["M1", "M5", "M15", "M30", "H1", "D1"])
        self.timeframe_combo.setStyleSheet("""
            QComboBox {
                background-color: #1E1E1E;
                color: white;
                border: 1px solid #333;
                padding: 3px 10px;
                border-radius: 4px;
                min-width: 80px;
            }
        """)

        # === Тип графика ===
        self.charttype_label = QLabel("Chart Type:")
        self.charttype_label.setFont(font)
        self.charttype_label.setStyleSheet("color: #A2DD84;")
        self.charttype_combo = QComboBox()
        self.charttype_combo.addItems(["Candlestick", "Line", "OHLC"])
        self.charttype_combo.setStyleSheet("""
            QComboBox {
                background-color: #1E1E1E;
                color: white;
                border: 1px solid #333;
                padding: 3px 10px;
                border-radius: 4px;
                min-width: 100px;
            }
        """)

        # Добавляем элементы в layout
        layout.addWidget(self.symbol_label)
        layout.addWidget(self.symbol_combo)
        layout.addWidget(self.timeframe_label)
        layout.addWidget(self.timeframe_combo)
        layout.addWidget(self.charttype_label)
        layout.addWidget(self.charttype_combo)
        layout.addStretch()
