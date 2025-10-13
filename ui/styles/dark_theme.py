def load_dark_theme() -> str:
    return """
    QWidget {
        background-color: #1B1B1B;
        color: #EAEAEA;
        font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
        font-size: 12px;
        letter-spacing: 0.2px;
    }

    QFrame {
        background-color: #222;
        border: 1px solid #2D2D2D;
        border-radius: 6px;
    }

    QLabel {
        color: #EAEAEA;
        font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
    }

    QTableWidget {
        background-color: #1F1F1F;
        gridline-color: #333;
        selection-background-color: #2E3B2E;
        font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
        font-size: 11px;
    }

    QHeaderView::section {
        background-color: #2A2A2A;
        color: #CCCCCC;
        padding: 6px;
        border: none;
        font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
        font-weight: 500;
        letter-spacing: 0.3px;
    }

    QPushButton {
        background-color: #2A2A2A;
        border: 1px solid #3A3A3A;
        padding: 6px 12px;
        border-radius: 8px;
        color: #EAEAEA;
        font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
        font-weight: 500;
    }

    QPushButton:hover {
        background-color: #333;
        border-color: #4B4B4B;
    }

    QPushButton:checked {
        background-color: #314231;
        border-color: #4B6B4B;
        color: #A2DD84;
    }

    QComboBox {
        background-color: #222;
        color: #EAEAEA;
        border: 1px solid #3A3A3A;
        border-radius: 6px;
        padding: 5px 10px;
        font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
    }

    QComboBox QAbstractItemView {
        background-color: #2A2A2A;
        selection-background-color: #314231;
        color: #FFFFFF;
    }

    QScrollBar:vertical {
        background: #1E1E1E;
        width: 10px;
        margin: 0px;
        border-radius: 5px;
    }

    QScrollBar::handle:vertical {
        background: #3A3A3A;
        border-radius: 5px;
        min-height: 20px;
    }

    QScrollBar::handle:vertical:hover {
        background: #555;
    }
    """
