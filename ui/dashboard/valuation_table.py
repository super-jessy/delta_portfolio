from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem
from PyQt6.QtCore import Qt

class ValuationTable(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self); lay.setSpacing(8)
        title = QLabel("Comparable Valuation Analysis for Multiple Securities")
        title.setStyleSheet("font-weight:600;")
        lay.addWidget(title)

        cols = ["Ticker","Company","Report","P/E","EV/EBITDA","EPS","ROE"]
        table = QTableWidget(6, len(cols))
        table.setHorizontalHeaderLabels(cols)
        table.verticalHeader().setVisible(False)

        rows = [
            ("IBM","IBM US Equity","12/2023","18.2","9.8","9.40","45.2%"),
            ("HPQ","Hewlett-Packard","06/2023","13.4","6.5","3.12","39.5%"),
            ("DELL","DELL Inc.","01/2024","20.6","7.7","6.33","31.0%"),
            ("ORCL","Oracle Group","05/2024","33.7","13.9","5.55","65.8%"),
            ("MSFT","Microsoft Corp.","06/2023","35.7","20.3","9.68","49.1%"),
            ("ACN","Accenture PLC-A","08/2024","28.1","14.7","11.92","41.3%"),
        ]
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                it = QTableWidgetItem(str(val))
                align = Qt.AlignmentFlag.AlignCenter if c != 1 else Qt.AlignmentFlag.AlignLeft
                it.setTextAlignment(align | Qt.AlignmentFlag.AlignVCenter)
                table.setItem(r, c, it)

        table.resizeColumnsToContents()
        lay.addWidget(table)
