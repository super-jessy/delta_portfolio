# ui/dashboard/charts/chart_canvas.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class ChartCanvas(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        placeholder = QLabel("📊 Chart Canvas (Graph Area)")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setFont(QFont("Helvetica Neue", 14, QFont.Weight.Medium))
        placeholder.setStyleSheet("color: #A2DD84;")

        layout.addWidget(placeholder)
