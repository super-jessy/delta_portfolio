from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem
from PyQt6.QtCore import Qt

class HeatmapTable(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self); lay.setSpacing(8)
        title = QLabel("Copy of Option Volume Heat Map"); title.setStyleSheet("font-weight:600;")
        lay.addWidget(title)

        cols = ["Ticker","Last","Chg","%Chg","TotDptVol","Avg20C","OTEG"]
        table = QTableWidget(5, len(cols))
        table.setHorizontalHeaderLabels(cols)
        table.verticalHeader().setVisible(False)

        data = [
            ("FLIR", "21.02", "-0.06", "-0.28%", "1067", "111", "952.6%"),
            ("CCE",  "30.95", "-0.09", "-0.31%", "22981", "290", "896.9%"),
            ("WY",   "26.85", "-0.09", "-0.31%", "22876", "2552", "896.6%"),
            ("TMC",  "6.25",  "+0.05", "+0.81%", "2591", "290", "839.6%"),
            ("ECL",  "63.92", "-0.20", "-0.31%", "1044", "125", "837.9%"),
        ]
        for r, row in enumerate(data):
            for c, val in enumerate(row):
                it = QTableWidgetItem(str(val))
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if c in (2,3):  # изменения
                    s = str(val)
                    if s.startswith("+"): it.setForeground(Qt.GlobalColor.green)
                    if s.startswith("-"): it.setForeground(Qt.GlobalColor.red)
                table.setItem(r, c, it)

        table.resizeColumnsToContents()
        lay.addWidget(table)
