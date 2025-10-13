from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem
from PyQt6.QtCore import Qt

class EconCalendar(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self); lay.setSpacing(8)
        title = QLabel("Economic Calendars"); title.setStyleSheet("font-weight:600;")
        lay.addWidget(title)

        cols = ["Date","Time","Ctry","Event","Period","Survey","Actual","Prior","Revis"]
        table = QTableWidget(4, len(cols))
        table.setHorizontalHeaderLabels(cols)
        table.verticalHeader().setVisible(False)

        rows = [
            ("12/09","15:30","US","Empire Manufacturing","Sep","-2.0","-10.41","1.1",""),
            ("12/09","15:30","US","Current Account Balance","2Q","-$125.0B","-$137.8B","-$151.0B",""),
            ("12/09","15:30","US","Total Net TIC Flows","Jul","$27.5B","—","$9.3B",""),
            ("12/09","15:30","US","Net Long-term TIC Flows","Jul","$27.5B","—","$9.3B",""),
        ]
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                it = QTableWidgetItem(str(val))
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(r, c, it)

        table.resizeColumnsToContents()
        lay.addWidget(table)
