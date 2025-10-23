from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt


class ChartToolbar(QWidget):
    def __init__(self, on_symbol_change, on_timeframe_change, on_type_change, on_indicator_change):
        super().__init__()
        self.on_symbol_change = on_symbol_change
        self.on_timeframe_change = on_timeframe_change
        self.on_type_change = on_type_change
        self.on_indicator_change = on_indicator_change

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)

        # === Поле ввода тикера ===
        symbol_label = QLabel("Symbol:")
        symbol_label.setStyleSheet("color: white; font-weight: 500;")
        layout.addWidget(symbol_label)

        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("Enter symbol (e.g. AAPL)")
        self.symbol_input.setStyleSheet("""
            QLineEdit {
                background-color: #1E1E1E;
                border: 1px solid #444;
                border-radius: 6px;
                color: white;
                padding: 4px 8px;
                min-width: 130px;
            }
            QLineEdit:focus {
                border: 1px solid #A2DD84;
            }
        """)
        self.symbol_input.returnPressed.connect(self._handle_symbol_enter)
        layout.addWidget(self.symbol_input)

        # === Таймфреймы как кнопки ===
        tflabel = QLabel("Timeframe:")
        tflabel.setStyleSheet("color: white; font-weight: 500; margin-left: 10px;")
        layout.addWidget(tflabel)

        self.timeframe_buttons = {}
        for tf in ["M1", "M5", "M15", "M30", "H1", "D1"]:
            btn = QPushButton(tf)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    background-color:#333;
                    color:white;
                    border-radius:5px;
                    padding:4px 10px;
                }
                QPushButton:checked {
                    background-color:#A2DD84;
                    color:black;
                }
            """)
            btn.clicked.connect(lambda _, t=tf: self._timeframe_clicked(t))
            self.timeframe_buttons[tf] = btn
            layout.addWidget(btn)

        self.timeframe_buttons["M30"].setChecked(True)

        # === Тип графика ===
        type_label = QLabel("Chart Type:")
        type_label.setStyleSheet("color: white; font-weight: 500; margin-left: 10px;")
        layout.addWidget(type_label)

        self.type_box = QComboBox()
        self.type_box.addItems(["Candlestick", "Line"])
        self.type_box.currentTextChanged.connect(self.on_type_change)
        self.type_box.setStyleSheet("""
            QComboBox {
                background-color: #1E1E1E;
                color: white;
                border-radius: 5px;
                padding: 3px 10px;
            }
            QComboBox:hover {
                border: 1px solid #A2DD84;
            }
        """)
        layout.addWidget(self.type_box)

        # === Индикаторы ===
        ind_label = QLabel("Indicators:")
        ind_label.setStyleSheet("color: white; font-weight: 500; margin-left: 10px;")
        layout.addWidget(ind_label)

        self.indicators_box = QComboBox()
        self.indicators_box.addItems(["None", "EMA 10", "EMA 50", "EMA 200", "SMA 50"])
        self.indicators_box.currentTextChanged.connect(self.on_indicator_change)
        self.indicators_box.setStyleSheet("""
            QComboBox {
                background-color: #1E1E1E;
                color: white;
                border-radius: 5px;
                padding: 3px 10px;
            }
            QComboBox:hover {
                border: 1px solid #A2DD84;
            }
        """)
        layout.addWidget(self.indicators_box)

        layout.addStretch()

        self.setStyleSheet("background-color: #1a1a1a; border-radius: 6px;")

    # === Обработчик нажатия Enter ===
    def _handle_symbol_enter(self):
        symbol = self.symbol_input.text().strip().upper()
        if symbol:
            self.on_symbol_change(symbol)

    # === Обработчик нажатия кнопки таймфрейма ===
    def _timeframe_clicked(self, tf):
        for b in self.timeframe_buttons.values():
            b.setChecked(False)
        self.timeframe_buttons[tf].setChecked(True)
        self.on_timeframe_change(tf)
