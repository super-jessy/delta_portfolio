from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class MarketMap(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setSpacing(8)
        title = QLabel("Intraday Market Map")
        title.setStyleSheet("font-weight:600; font-size:14px;")
        lay.addWidget(title)
        placeholder = QLabel("🟢 Asia Pacific +0.10%\n🔴 Hong Kong -0.05%\n⚪ Japan 0.00%")
        placeholder.setStyleSheet("color:#aaaaaa; font-size:12px;")
        lay.addWidget(placeholder)
        lay.addStretch(1)
