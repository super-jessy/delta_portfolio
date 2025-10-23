from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel, QFrame, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QCursor


class DropdownPopup(QWidget):
    optionSelected = pyqtSignal(str)

    def __init__(self, options: list[str], parent=None):
        super().__init__(parent)
        # делаем настоящий popup-виджет поверх всех, который сам закрывается при клике вне
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        frame = QFrame(self)
        frame.setObjectName("popupFrame")
        frame.setStyleSheet("""
            QFrame#popupFrame {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 0px;
            }
            QLabel {
                color: #ddd;
                padding: 6px 12px;
                font-size: 13px;
                border: none;
                border-radius: 0px;
                background-color: #2a2a2a;
            }
            QLabel:hover {
                background-color: #3a3a3a;
                color: #A2DD84;
            }
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(2)

        for opt in options:
            lbl = QLabel(opt, frame)
            lbl.setCursor(Qt.CursorShape.PointingHandCursor)
            # замыкаем значение
            lbl.mousePressEvent = lambda e, t=opt: self._choose(t)
            layout.addWidget(lbl)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(frame)

    def _choose(self, text: str):
        self.optionSelected.emit(text)
        self.close()  # Qt.Popup сам закроется, но на всякий случай


class CustomDropdown(QWidget):
    """Кнопка + popup-меню. Не двигает layout, открывается поверх графика."""
    changed = pyqtSignal(str)   # отдаём выбранное значение наружу

    def __init__(self, label_text: str, options: list[str], default: str = None, parent=None):
        super().__init__(parent)
        self.label_text = label_text
        self.options = options
        self.selected = default or (options[0] if options else "")

        self.button = QPushButton(f"{self.label_text}: {self.selected}")
        self.button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 5px 12px;
                text-align: left;
            }
            QPushButton:hover {
                border-color: #A2DD84;
            }
        """)
        self.button.clicked.connect(self._toggle_popup)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.button)

        self.popup = None  # создаём на лету, чтобы позиционировать корректно

    def _toggle_popup(self):
        if self.popup and self.popup.isVisible():
            self.popup.close()
            return

        self.popup = DropdownPopup(self.options, self)
        self.popup.optionSelected.connect(self._select)
        # позиция — под кнопкой
        global_pos = self.mapToGlobal(self.button.geometry().bottomLeft())
        # небольшое смещение, чтобы не перекрывать бордер
        self.popup.move(QPoint(global_pos.x(), global_pos.y() + 4))
        self.popup.show()

    def _select(self, text: str):
        self.selected = text
        self.button.setText(f"{self.label_text}: {self.selected}")
        self.changed.emit(text)