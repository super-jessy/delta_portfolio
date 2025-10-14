from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QHBoxLayout, QFrame
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QPainterPath
from PyQt6.QtCore import Qt, QSize
import random


class MiniChart(QWidget):
    """Плавный мини-график"""
    def __init__(self, data=None, positive=True):
        super().__init__()
        self.data = data or [random.uniform(0.95, 1.05) for _ in range(28)]
        self.positive = positive
        self.setFixedSize(QSize(110, 30))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor("#A2DD84") if self.positive else QColor("#FF4E4E")
        painter.setPen(QPen(color, 2))

        w, h = self.width(), self.height()
        mx, mn = max(self.data), min(self.data)
        rng = mx - mn if mx != mn else 1
        scale = h / rng
        pts = [(i * (w / (len(self.data) - 1)), h - (v - mn) * scale) for i, v in enumerate(self.data)]

        path = QPainterPath()
        path.moveTo(*pts[0])
        for i in range(1, len(pts) - 2):
            xc = (pts[i][0] + pts[i + 1][0]) / 2
            yc = (pts[i][1] + pts[i + 1][1]) / 2
            path.quadTo(pts[i][0], pts[i][1], xc, yc)
        path.lineTo(*pts[-1])
        painter.drawPath(path)


class AssetCard(QFrame):
    """Актив — компактная карточка без рамок у текста"""
    def __init__(self, ticker, price, day_change, total_change):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #1E1E1E;
                border-radius: 10px;
                padding: 4px;
            }
            QLabel {
                color: #EAEAEA;
                background: transparent;
                border: none;
                font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(20)

        positive = day_change >= 0
        chart = MiniChart(positive=positive)

        ticker_lbl = QLabel(ticker)
        ticker_lbl.setFont(QFont("Helvetica Neue", 13, QFont.Weight.Bold))

        price_lbl = QLabel(f"{price:.2f}")
        price_lbl.setFont(QFont("Helvetica Neue", 12))

        day_lbl = QLabel(f"{day_change:+.2f}%")
        day_lbl.setFont(QFont("Helvetica Neue", 12))
        day_lbl.setStyleSheet(f"color: {'#A2DD84' if positive else '#FF4E4E'};")

        total_lbl = QLabel(f"{total_change:+.2f}%")
        total_lbl.setFont(QFont("Helvetica Neue", 12))
        total_lbl.setStyleSheet(f"color: {'#A2DD84' if total_change >= 0 else '#FF4E4E'};")

        align = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        layout.addWidget(ticker_lbl, 0, align)
        layout.addWidget(price_lbl, 0, align)
        layout.addWidget(chart, 0, align)
        layout.addWidget(day_lbl, 0, align)
        layout.addWidget(total_lbl, 0, align)
        layout.addStretch(1)

        self.setFixedHeight(56)


class PortfolioPanel(QWidget):
    """Панель портфеля — поднятая шапка и увеличенные карточки"""
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 12, 8, 8)
        main_layout.setSpacing(12)

        # Шапка
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 2)

        title = QLabel("Portfolio Overview")
        title.setFont(QFont("Helvetica Neue", 14, QFont.Weight.Medium))
        title.setStyleSheet("background: transparent; border: none; font-weight: bold; padding-top: 0px; font-size: 12px;")

        combo = QComboBox()
        combo.addItems(["Main Portfolio", "Tech Stocks", "Dividend Fund"])
        combo.setStyleSheet("""
            QComboBox {
                background-color: #222;
                color: #EAEAEA;
                padding: 5px 10px;
                border: 1px solid #333;
                border-radius: 6px;
                font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
            }
            QComboBox QAbstractItemView {
                background-color: #2A2A2A;
                selection-background-color: #314231;
                color: #FFFFFF;
            }
        """)

        header_layout.addWidget(title)
        header_layout.addStretch(1)
        header_layout.addWidget(combo)
        main_layout.addLayout(header_layout)

        # Список активов
        assets_data = [
            ("AAPL", 167.87, +0.65, +12.30),
            ("AMZN", 189.74, -0.11, +25.70),
            ("TSLA", 241.42, +0.16, +8.90),
            ("MSFT", 395.10, +0.38, +15.40),
        ]

        for t, p, d, tot in assets_data:
            main_layout.addWidget(AssetCard(t, p, d, tot))
