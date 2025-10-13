from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel

class ChartPanel(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(6)

        title = QLabel("FLR US Equity")
        title.setStyleSheet("font-weight:600;")
        header.addWidget(title)

        for tf in ["1D", "3D", "1W", "1M", "6M", "1Y", "YTD", "Max"]:
            header.addWidget(QPushButton(tf))

        header.addStretch(1)
        root.addLayout(header)

        chart_placeholder = QLabel("📈 Chart placeholder (Candlestick + Indicators)")
        chart_placeholder.setStyleSheet("color:#aaaaaa;")
        chart_placeholder.setMinimumHeight(200)
        root.addWidget(chart_placeholder)
