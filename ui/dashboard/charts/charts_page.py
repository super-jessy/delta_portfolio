# ui/dashboard/charts/charts_page.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from PyQt6.QtCore import Qt
from ..navbar import NavBar
from .chart_toolbar import ChartToolbar
from .chart_canvas import ChartCanvas
from .drawing_tools_panel import DrawingToolsPanel
from .indicator_panel import IndicatorPanel


class ChartsPage(QWidget):
    def __init__(self):
        super().__init__()

        # === Главный вертикальный layout (вся страница) ===
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)

        # === Верхняя панель (toolbar) ===
        self.toolbar = ChartToolbar()
        main_layout.addWidget(self.toolbar)

        # === Центральная область: левая панель + график + индикаторы ===
        center_layout = QHBoxLayout()
        center_layout.setSpacing(5)

        # Левая панель рисования
        self.drawing_panel = DrawingToolsPanel()
        center_layout.addWidget(self.drawing_panel)

        # Центральный график
        self.chart_canvas = ChartCanvas()
        center_layout.addWidget(self.chart_canvas, stretch=1)

        # Правая панель индикаторов
        self.indicator_panel = IndicatorPanel()
        center_layout.addWidget(self.indicator_panel)

        # Добавляем центральный блок в основной layout
        main_layout.addLayout(center_layout)
