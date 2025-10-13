from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QSizePolicy

TABS = ["Home", "Portfolios", "Instruments", "Charts", "News", "Fundamentals", "Options"]

class NavBar(QWidget):
    def __init__(self):
        super().__init__()
        row = QHBoxLayout(self)
        row.setContentsMargins(6, 6, 6, 6)
        row.setSpacing(10)

        burger = QPushButton("≡")
        burger.setFixedWidth(40)
        title = QLabel("DELTA TERMINAL")
        title.setStyleSheet("background: transparent; border: none; font-weight:600; color:#A2DD84; font-size:15px;")
        title.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

        row.addWidget(burger)
        row.addWidget(title)

        for t in TABS:
            btn = QPushButton(t)
            btn.setCheckable(True)
            btn.setMinimumWidth(120)
            btn.setMinimumHeight(36)
            btn.setStyleSheet("font-size:13px; font-weight:500;")
            if t == "Home":
                btn.setChecked(True)
            row.addWidget(btn)

        row.addStretch(1)
