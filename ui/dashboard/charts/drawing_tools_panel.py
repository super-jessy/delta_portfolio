from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt


class DrawingToolsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(120)
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 15, 10, 15)
        layout.setSpacing(10)

        title = QLabel("Tools")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #A2DD84; font-size: 13px; font-weight: 500;")
        layout.addWidget(title)

        # === Кнопки инструментов ===
        self.tools = {
            "Line": QPushButton("Line"),
            "Ray": QPushButton("Ray"),
            "Channel": QPushButton("Channel"),
            "Fibonacci": QPushButton("Fibonacci"),
            "Text": QPushButton("Text"),
            "Remove All": QPushButton("Remove All")
        }

        for name, btn in self.tools.items():
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(30)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2a2a2a;
                    color: #A2DD84;
                    border: 1px solid #333;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #333;
                    border: 1px solid #A2DD84;
                }
                QPushButton:pressed {
                    background-color: #3a3a3a;
                }
            """)
            layout.addWidget(btn)

        layout.addStretch()
        self.setLayout(layout)
