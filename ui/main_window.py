from PyQt6.QtWidgets import QMainWindow
from ui.dashboard.dashboard import DashboardPage
from ui.styles import load_dark_theme

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DELTA Portfolio — Investment Terminal")
        self.setStyleSheet(load_dark_theme())
        self.setCentralWidget(DashboardPage())
