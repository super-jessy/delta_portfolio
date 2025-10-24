from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame
from .navbar import NavBar
from .portfolio_panel import PortfolioPanel
from .market_map import MarketMap
from .chart_panel import ChartPanel
from .news_panel import NewsPanel
from .econ_calendar import EconCalendar
from PyQt6.QtCore import Qt


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # Центральная зона: Portfolio (слева) | Chart (справа)
        middle = QHBoxLayout()
        middle.setSpacing(8)

        left = FrameWrap(PortfolioPanel(), stretch=4, margins=(8, 0, 8, 8))
        left.layout().setAlignment(Qt.AlignmentFlag.AlignTop)
        right = FrameWrap(ChartPanel(), stretch=8, margins=(8, 0, 0, 0))

        middle.addWidget(left, left.stretch)
        middle.addWidget(right, right.stretch)
        root.addLayout(middle, stretch=7)

        # Нижняя зона: News | Market Map | Economic Calendar
        bottom = QHBoxLayout()
        bottom.setSpacing(8)

        b_left = FrameWrap(NewsPanel(), stretch=4)
        b_center = FrameWrap(MarketMap(), stretch=4)
        b_right = FrameWrap(EconCalendar(), stretch=4)

        bottom.addWidget(b_left, b_left.stretch)
        bottom.addWidget(b_center, b_center.stretch)
        bottom.addWidget(b_right, b_right.stretch)
        root.addLayout(bottom, stretch=4)


class FrameWrap(QFrame):
    def __init__(self, content: QWidget, stretch: int = 1, margins=(8, 0, 8, 8)):
        super().__init__()
        self.stretch = stretch
        lay = QVBoxLayout(self)
        lay.setContentsMargins(*margins)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)  # ключевая строка!
        lay.addWidget(content)

