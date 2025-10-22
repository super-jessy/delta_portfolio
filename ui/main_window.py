from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedLayout
from ui.dashboard.dashboard import DashboardPage
from ui.dashboard.portfolios_page import PortfoliosPage
from ui.dashboard.instruments_page import InstrumentsPage
from ui.dashboard.charts.charts_page import ChartsPage
from ui.dashboard.analysis_page import AnalysisPage
from ui.dashboard.fundamentals_page import FundamentalsPage
from ui.dashboard.options_page import OptionsPage
from ui.dashboard.navbar import NavBar
from ui.styles import load_dark_theme


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DELTA Portfolio — Investment Terminal")
        self.setStyleSheet(load_dark_theme())

        # Центральный контейнер
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Навигация (верхнее меню)
        self.navbar = NavBar()
        layout.addWidget(self.navbar)

        # Стек для страниц
        self.stack = QStackedLayout()
        layout.addLayout(self.stack)

        # Страницы
        self.pages = {
            "Home": DashboardPage(),
            "Portfolios": PortfoliosPage(),
            "Instruments": InstrumentsPage(),
            "Charts": ChartsPage(),
            "Analysis": AnalysisPage(),
            "Fundamentals": FundamentalsPage(),
            "Options": OptionsPage()
        }

        for page in self.pages.values():
            self.stack.addWidget(page)

        # Подключаем сигнал
        self.navbar.page_selected.connect(self.show_page)

        # Стартовая страница
        self.show_page("Home")

    def show_page(self, page_name):
        widget = self.pages.get(page_name)
        if widget:
            self.stack.setCurrentWidget(widget)
