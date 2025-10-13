from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QSizePolicy

TABS = ["Global Mkt", "Global ETF", "My Stocks", "News", "Analysis", "Credits",
        "Charts", "Analyst Pg", "Worksheet", "Activity", "Equity", "FX", "Options"]

class NavBar(QWidget):
    def __init__(self):
        super().__init__()
        row = QHBoxLayout(self)
        row.setContentsMargins(6, 6, 6, 6)
        row.setSpacing(6)

        burger = QPushButton("≡")
        burger.setFixedWidth(36)
        title = QLabel("DELTA Portfolio")
        title.setStyleSheet("font-weight:600; color:#A2DD84;")
        title.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

        row.addWidget(burger)
        row.addWidget(title)

        for t in TABS:
            btn = QPushButton(t)
            btn.setCheckable(True)
            if t == "Equity":
                btn.setChecked(True)
            row.addWidget(btn)

        row.addStretch(1)
