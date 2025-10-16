# ui/dashboard/analysis_page.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from .navbar import NavBar

class AnalysisPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title = QLabel("Analysis Page — Coming Soon")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Helvetica Neue", 16, QFont.Weight.Medium))
        title.setStyleSheet("color: #A2DD84;")

        layout.addWidget(title)
        layout.addStretch()
