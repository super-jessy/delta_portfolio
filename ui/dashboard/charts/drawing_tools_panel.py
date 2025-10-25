from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QSize

class DrawingToolsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Узкая, тёмная панель
        self.setFixedWidth(60)
        self.setStyleSheet("background-color: #1E1E1E; border: none;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        # Все инструменты (PNG)
        tools = [
            ("Trendline", "assets/icons/chart_page/trendline.png"),
            ("Horisontal Line", "assets/icons/chart_page/horisontal_line.png"),
            ("Rectangle", "assets/icons/chart_page/rectangle.png"),
            ("Vertical Line", "assets/icons/chart_page/vertical_line.png"),
            ("Chart Arrow", "assets/icons/chart_page/chart_arrow.png"),
            ("Arrow Projection", "assets/icons/chart_page/arrow_projection.png"),
            ("Fibonacci", "assets/icons/chart_page/fibonacci.png"),
            ("Circle", "assets/icons/chart_page/circle.png"),
            ("Ellipse", "assets/icons/chart_page/ellipse.png"),
            ("Price Range", "assets/icons/chart_page/price_range.png"),
            ("Date Range", "assets/icons/chart_page/date_range.png"),
            ("Brush", "assets/icons/chart_page/brush.png"),
            ("Text", "assets/icons/chart_page/text.png"),
            ("Arrow Up", "assets/icons/chart_page/arrow_up.png"),
            ("Arrow Down", "assets/icons/chart_page/arrow_down.png"),
        ]

        self.buttons = []
        for name, icon_path in tools:
            btn = QPushButton()
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(32, 32))
            btn.setFixedSize(47, 47)
            btn.setToolTip(name)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            # Стилизация: hover + active (selected)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: rgba(162, 221, 132, 0.18);
                }
                QPushButton:checked {
                    background-color: none;
                    border: 1px solid #A2DD84;
                    border-radius: 8px;
                }
            """)

            btn.clicked.connect(lambda checked, b=btn: self.on_tool_selected(b))
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)
            self.buttons.append(btn)

        layout.addStretch()

    def on_tool_selected(self, selected_button):
        """Активирует выбранный инструмент и деактивирует остальные"""
        for btn in self.buttons:
            if btn is not selected_button:
                btn.setChecked(False)
