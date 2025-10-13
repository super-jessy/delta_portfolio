from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem

class NewsPanel(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setSpacing(8)
        title = QLabel("News")
        title.setStyleSheet("font-weight:600;")
        lay.addWidget(title)

        lst = QListWidget()
        for t in [
            "Stocks fall amid bond yield surge",
            "Fed signals cautious stance on rate cuts",
            "Tech sector leads rebound in late trading",
        ]:
            lst.addItem(QListWidgetItem(t))
        lay.addWidget(lst)
