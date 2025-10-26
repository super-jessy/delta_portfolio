from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt
from .chart_canvas import ChartCanvas  
from .custom_dropdown import CustomDropdown
from .drawing_tools_panel import DrawingToolsPanel


class ChartsPage(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 8, 10, 10)
        main_layout.setSpacing(8)

        # ----- Верхняя панель инструментов -----
        toolbar = QFrame()
        toolbar.setObjectName("toolbar")
        toolbar.setStyleSheet("""
            QFrame#toolbar {
                background-color: #222222;
                border: none;
            }
            QLabel { color: #A2DD84; }
        """)
        toolbar.setFixedHeight(48)

        tl = QHBoxLayout(toolbar)
        tl.setContentsMargins(12, 6, 12, 6)
        tl.setSpacing(10)

        # Поле для ввода тикера
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("Enter ticker (e.g. AAPL)")
        self.symbol_input.setFixedWidth(220)
        self.symbol_input.setStyleSheet("""
            QLineEdit {
                background-color: #2A2A2A;
                color: white;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 4px 10px;
                selection-background-color: #A2DD84;
            }
            QLineEdit:focus { border: 1px solid #A2DD84; }
        """)
        self.symbol_input.returnPressed.connect(self._on_symbol_enter)
        tl.addWidget(self.symbol_input)

        # Кнопки таймфреймов
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
            btn.clicked.connect(lambda _, t=tf: self._on_timeframe_click(t))
            self.timeframe_buttons[tf] = btn
            tl.addWidget(btn)
        self.timeframe_buttons["M30"].setChecked(True)

        # Dropdown для выбора типа графика
        self.dd_chart_type = CustomDropdown("Chart Type", ["Candlestick", "Line"], "Candlestick", parent=toolbar)
        self.dd_chart_type.changed.connect(self._on_chart_type_change)
        tl.addWidget(self.dd_chart_type)

        # Dropdown для индикаторов
        self.dd_indicators = CustomDropdown("Indicators", ["None", "EMA 25", "EMA 100", "EMA 200"], "None", parent=toolbar)
        self.dd_indicators.changed.connect(self._on_indicator_change)
        tl.addWidget(self.dd_indicators)

        tl.addStretch()
        main_layout.addWidget(toolbar)

        # Разделительная линия
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #2b2b2b;")
        main_layout.addWidget(sep)

        # ----- Нижняя часть: панель инструментов + график -----
        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 0, 0, 0)
        bottom.setSpacing(6)

        # Левая панель инструментов рисования
        self.tools_panel = DrawingToolsPanel()
        self.tools_panel.setFixedWidth(60)
        bottom.addWidget(self.tools_panel)

        # Сам график
        self.chart = ChartCanvas()
        bottom.addWidget(self.chart, stretch=1)

        main_layout.addLayout(bottom)

        # 🔗 Подключаем панель инструментов к графику
        self.tools_panel.tool_selected.connect(self.chart.set_drawing_tool)
        self.chart.tool_finished.connect(self.tools_panel.deactivate_all)

        # ----- Значения по умолчанию -----
        self.chart.symbol = "AAPL"
        self.chart.timeframe = "M30"
        self.chart.update_data()

    # ----- Обработчики -----
    def _on_symbol_enter(self):
        sym = self.symbol_input.text().strip().upper()
        if not sym:
            return
        self.chart.symbol = sym
        self.chart.update_data()

    def _on_timeframe_click(self, tf: str):
        for t, b in self.timeframe_buttons.items():
            b.setChecked(t == tf)
        self.chart.timeframe = tf
        self.chart.update_data()

    def _on_chart_type_change(self, val: str):
        self.chart.chart_type = val
        self.chart.update()

    def _on_indicator_change(self, val: str):
        # ожидаем значения "None" / "EMA 25" / "EMA 100" / "EMA 200"
        self.chart.apply_indicator(val)
