# ui/dashboard/charts/indicator_panel.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class IndicatorPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel("📈 Indicators Panel (coming soon)")
        label.setFont(QFont("Helvetica Neue", 11))
        label.setStyleSheet("color: #A2DD84;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(label)
        layout.addStretch()
