from PyQt6.QtCore import QPointF, Qt, QRectF, QObject, pyqtSignal
from PyQt6.QtGui import QPen, QColor
from .base_tool import BaseTool


class TrendlineTool(BaseTool, QObject):

    finished = pyqtSignal(object) 

    def __init__(self, chart):
        BaseTool.__init__(self, chart)
        QObject.__init__(self)
        self.creating = False
        self.temp_start = None
        self.temp_end = None
        self.selected = None
        self.dragging = False
        self.dragging_point = None
        self.last_pos = None
        self.color = QColor("#A2DD84")
        self.sel_color = QColor("#FFFFFF")

    def mouse_press(self, event):
        pos = event.position()

        # --- Удаление правой кнопкой ---
        if event.button() == Qt.MouseButton.RightButton:
            if self.selected:
                self.objects = [obj for obj in self.objects if obj != self.selected]
                self.selected = None
                self.chart.update()
            return

        # --- Создание новой линии ---
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.creating:
                self.temp_start = pos
                self.temp_end = pos
                self.creating = True
            else:
                # фиксируем новую линию
                new_line = (self.temp_start, pos)
                self.objects.append(new_line)
                self.temp_start = None
                self.temp_end = None
                self.creating = False
                self.chart.update()
                self.finished.emit(new_line)

    def mouse_move(self, event):
        pos = event.position()

        # --- Создание новой линии ---
        if self.creating and self.temp_start:
            self.temp_end = pos
            self.chart.update()

    def mouse_release(self, event):
        self.dragging = False
        self.dragging_point = None
        self.last_pos = None

    def draw(self, painter):
        """Отрисовка всех линий"""
        base_pen = QPen(self.color, 1.6)
        painter.setPen(base_pen)

        # --- Постоянные линии ---
        for start, end in self.objects:
            painter.drawLine(start, end)

        # --- Временная линия при создании ---
        if self.creating and self.temp_start and self.temp_end:
            dash_pen = QPen(self.color, 1.2, Qt.PenStyle.DashLine)
            painter.setPen(dash_pen)
            painter.drawLine(self.temp_start, self.temp_end)
