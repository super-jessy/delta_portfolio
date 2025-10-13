def load_dark_theme() -> str:
    return """
    QWidget {
        background-color: #1B1B1B;
        color: #EAEAEA;
        font-family: 'Century Gothic', 'Segoe UI', sans-serif;
        font-size: 12px;
    }
    QFrame {
        background-color: #222;
        border: 1px solid #2D2D2D;
        border-radius: 6px;
    }
    QLabel {
        color: #EAEAEA;
    }
    QTableWidget {
        background-color: #1F1F1F;
        gridline-color: #333;
        selection-background-color: #2E3B2E;
    }
    QHeaderView::section {
        background-color: #2A2A2A;
        color: #CCCCCC;
        padding: 6px;
        border: none;
    }
    QPushButton {
        background-color: #2A2A2A;
        border: 1px solid #3A3A3A;
        padding: 6px 10px;
        border-radius: 6px;
    }
    QPushButton:hover {
        background-color: #333;
    }
    QPushButton:checked {
        background-color: #314231;
        border-color: #4B6B4B;
    }
    """
