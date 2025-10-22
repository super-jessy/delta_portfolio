# ui/dashboard/charts/drawing_tools_panel.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt6.QtGui import QFont

class DrawingToolsPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        font = QFont("Helvetica Neue", 10)

        tools = ["Line", "Ray", "Channel", "Fibonacci", "Text", "Remove All"]
        for tool in tools:
            btn = QPushButton(tool)
            btn.setFont(font)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1E1E1E;
                    color: #A2DD84;
                    border: 1px solid #333;
                    border-radius: 6px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #2C2C2C;
                }
            """)
            layout.addWidget(btn)
        layout.addStretch()
