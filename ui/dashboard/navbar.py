from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QSizePolicy
from PyQt6.QtCore import pyqtSignal

TABS = ["Home", "Portfolios", "Instruments", "Charts", "Analysis", "Fundamentals", "Options"]

class NavBar(QWidget):
    page_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        row = QHBoxLayout(self)
        row.setContentsMargins(10, 12, 6, 4)
        row.setSpacing(10)

        burger = QPushButton("≡")
        burger.setFixedWidth(40)

        title = QLabel("DELTA TERMINAL")
        title.setStyleSheet("""
            background: transparent;
            border: none;
            font-weight: 600;
            color: #A2DD84;
            font-size: 15px;
        """)
        title.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

        row.addWidget(burger)
        row.addWidget(title)

        self.buttons = {}

        for t in TABS:
            btn = QPushButton(t)
            btn.setCheckable(True)
            btn.setMinimumWidth(120)
            btn.setMinimumHeight(36)
            btn.setStyleSheet("font-size:13px; font-weight:500;")
            if t == "Home":
                btn.setChecked(True)
            btn.clicked.connect(lambda _, name=t: self.select_tab(name))
            row.addWidget(btn)
            self.buttons[t] = btn

        row.addStretch(1)

    def select_tab(self, name):
        for t, btn in self.buttons.items():
            btn.setChecked(t == name)
        self.page_selected.emit(name)
