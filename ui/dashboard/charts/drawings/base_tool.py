from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPainter

class BaseTool:
    """Базовый класс для всех инструментов рисования"""
    def __init__(self, chart):
        self.chart = chart
        self.is_active = False  # выбран ли этот инструмент
        self.objects = []       # список нарисованных элементов (например, линий)

    def mouse_press(self, event):
        pass

    def mouse_move(self, event):
        pass

    def mouse_release(self, event):
        pass

    def draw(self, painter: QPainter):
        pass

    def select_object(self, pos: QPointF):
        """Проверка, кликнули ли по объекту"""
        return None
