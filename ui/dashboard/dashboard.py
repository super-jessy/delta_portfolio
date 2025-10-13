from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame
from .navbar import NavBar
from .portfolio_table import PortfolioTable
from .market_map import MarketMap
from .chart_panel import ChartPanel
from .news_panel import NewsPanel
from .heatmap_table import HeatmapTable
from .valuation_table import ValuationTable
from .econ_calendar import EconCalendar


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # Навигация
        root.addWidget(NavBar())

        # Центральная зона: Portfolio | Market Map | Chart
        middle = QHBoxLayout()
        middle.setSpacing(8)

        left = FrameWrap(PortfolioTable(), stretch=4)
        center = FrameWrap(MarketMap(), stretch=3)
        right = FrameWrap(ChartPanel(), stretch=5)

        middle.addWidget(left, left.stretch)
        middle.addWidget(center, center.stretch)
        middle.addWidget(right, right.stretch)
        root.addLayout(middle, stretch=6)

        # Нижняя зона: News | Heatmap | Valuation
        bottom = QHBoxLayout()
        bottom.setSpacing(8)

        b_left = FrameWrap(NewsPanel(), stretch=4)
        b_center = FrameWrap(HeatmapTable(), stretch=3)
        b_right = FrameWrap(ValuationTable(), stretch=5)

        bottom.addWidget(b_left, b_left.stretch)
        bottom.addWidget(b_center, b_center.stretch)
        bottom.addWidget(b_right, b_right.stretch)
        root.addLayout(bottom, stretch=5)

        # Экономический календарь
        root.addWidget(FrameWrap(EconCalendar()), stretch=2)


class FrameWrap(QFrame):
    def __init__(self, content: QWidget, stretch: int = 1):
        super().__init__()
        self.stretch = stretch
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.addWidget(content)
