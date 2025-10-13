from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem
from PyQt6.QtCore import Qt

class PortfolioTable(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setSpacing(8)

        title = QLabel("Portfolio")
        title.setStyleSheet("font-weight:600;")
        lay.addWidget(title)

        cols = ["Ticker", "% Wgt", "Prt CTR", "Curr Px", "1D Chg", "1D %Chg", "%YTD Rtn"]
        table = QTableWidget(5, len(cols))
        table.setHorizontalHeaderLabels(cols)
        table.verticalHeader().setVisible(False)

        sample = [
            ("AAPL", "2.44", "13.61", "167.9", "+1.07", "+0.65%", "+29.5%"),
            ("AMZN", "2.56", "2.68", "189.7", "-0.22", "-0.11%", "+25.7%"),
            ("TSLA", "2.29", "2.14", "241.4", "+0.38", "+0.16%", "+12.3%"),
        ]
        for r, row in enumerate(sample):
            for c, val in enumerate(row):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if val.startswith("+"):
                    item.setForeground(Qt.GlobalColor.green)
                elif val.startswith("-"):
                    item.setForeground(Qt.GlobalColor.red)
                table.setItem(r, c, item)

        lay.addWidget(table)
