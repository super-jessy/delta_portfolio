from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from ui.dashboard.charts.chart_toolbar import ChartToolbar
from ui.dashboard.charts.chart_canvas import CandleChart
from ui.dashboard.charts.drawing_tools_panel import DrawingToolsPanel


class ChartsPage(QWidget):
    def __init__(self):
        super().__init__()

        # === ГЛАВНЫЙ вертикальный layout ===
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === ВЕРХНЯЯ панель (toolbar) ===
        self.toolbar = ChartToolbar(
            on_symbol_change=self.on_symbol_change,
            on_timeframe_change=self.on_timeframe_change,
            on_type_change=self.on_chart_type_change,
            on_indicator_change=self.on_indicator_change
        )
        main_layout.addWidget(self.toolbar)

        # === НИЖНЯЯ часть (левая панель + график) ===
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(10, 10, 10, 10)
        bottom_layout.setSpacing(6)

        # --- Левая панель инструментов ---
        self.drawing_panel = DrawingToolsPanel()
        bottom_layout.addWidget(self.drawing_panel)

        # --- Центральная часть (график) ---
        self.chart_canvas = CandleChart()
        bottom_layout.addWidget(self.chart_canvas)

        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

        # === Дефолтный запуск ===
        self.chart_canvas.symbol = "AAPL"
        self.chart_canvas.timeframe = "M30"
        self.chart_canvas.update_data()

    # ---------- Обработчики ----------
    def on_symbol_change(self, symbol):
        self.chart_canvas.symbol = symbol
        self.chart_canvas.update_data()

    def on_timeframe_change(self, timeframe):
        self.chart_canvas.timeframe = timeframe
        self.chart_canvas.update_data()

    def on_chart_type_change(self, chart_type):
        self.chart_canvas.chart_type = chart_type
        self.chart_canvas.update()

    def on_indicator_change(self, indicator_name):
        self.chart_canvas.apply_indicator(indicator_name)
