from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath
from PyQt6.QtCore import Qt, QTimer, QPointF
from services.indices_service import fetch_intraday_indices
import random


class ChartCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(230)
        self.setMaximumHeight(260)
        self.setStyleSheet("background-color: #222222; border-radius: 6px;")

        self.data = {}
        self.colors = {}
        self.margin_left = 15
        self.margin_right = 45  # увеличено под шкалу %
        self.margin_top = 25
        self.margin_bottom = 20

        self.font = QFont("Helvetica Neue", 9)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1800000)
        self.update_data()

    def update_data(self):
        try:
            self.data = fetch_intraday_indices()
        except Exception as e:
            print("[ChartCanvas] data fetch error:", e)
            self.data = {}
        self.update()

    def paintEvent(self, event):
        if not self.data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()

        painter.fillRect(rect, QColor("#222222"))
        pen = QPen(QColor("#333333"))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRect(rect.adjusted(0, 0, -1, -1))

        left = self.margin_left
        top = self.margin_top
        width = rect.width() - self.margin_left - self.margin_right
        height = rect.height() - self.margin_top - self.margin_bottom
        chart_rect = (left, top, width, height)

        self.draw_grid(painter, chart_rect)
        self.draw_axes(painter, chart_rect)
        self.draw_lines(painter, chart_rect)
        self.draw_percentage_labels(painter, chart_rect)

    def draw_grid(self, painter, rect):
        left, top, width, height = rect
        pen = QPen(QColor("#333333"))
        pen.setStyle(Qt.PenStyle.DotLine)
        painter.setPen(pen)

        for i in range(5):
            y = int(top + (i * height / 4))
            painter.drawLine(int(left), y, int(left + width), y)

        for i in range(6):
            x = int(left + (i * width / 5))
            painter.drawLine(x, int(top), x, int(top + height))

    def draw_axes(self, painter, rect):
        left, top, width, height = rect
        painter.setFont(self.font)
        painter.setPen(QColor("#A2DD84"))

        # ось X — подняли значения ближе к линии
        for i in range(6):
            x = int(left + (i * width / 5))
            painter.drawText(x - 12, int(top + height + 15), f"{i*4:02d}:00")


    def draw_lines(self, painter, rect):
        left, top, width, height = rect
        symbols = list(self.data.keys())
        if not symbols:
            return

        base_colors = [
            "#1E90FF", "#FF4D4D", "#A2DD84", "#FFD700",
            "#FF69B4", "#00CED1", "#FF8C00", "#C71585",
            "#ADFF2F", "#BA55D3"
        ]
        self.colors = {sym: QColor(base_colors[i % len(base_colors)]) for i, sym in enumerate(symbols)}

        # легенда (уменьшили интервал между тикерами)
        legend_x, legend_y = int(left), int(top - 12)
        for i, sym in enumerate(symbols):
            c = self.colors[sym]
            painter.setPen(QPen(c))
            painter.drawText(legend_x + i * 65, legend_y, f"{sym}")

        all_vals = [v for sym in symbols for _, v in self.data[sym]]
        if not all_vals:
            return
        vmin, vmax = min(all_vals), max(all_vals)
        vrange = max(vmax - vmin, 0.0001)

        self.last_values = {}
        self.last_positions = {}

        for sym, data in self.data.items():
            c = self.colors[sym]
            path = QPainterPath()
            for i, (_, val) in enumerate(data):
                x = left + (i / (len(data) - 1)) * width
                y = top + height - ((val - vmin) / vrange) * height
                if i == 0:
                    path.moveTo(QPointF(x, y))
                else:
                    path.lineTo(QPointF(x, y))

            # эффект свечения
            glow = QPen(QColor(c.red(), c.green(), c.blue(), 60), 5)
            painter.setPen(glow)
            painter.drawPath(path)

            # основная линия
            pen = QPen(c, 2)
            painter.setPen(pen)
            painter.drawPath(path)

            # сохраняем последнее значение
            if data:
                self.last_values[sym] = data[-1][1]
                self.last_positions[sym] = (x, y)

    def draw_percentage_labels(self, painter, rect):
        """Отображает справа % изменения, с итеративным устранением наложений"""
        if not hasattr(self, "last_values") or not self.last_values:
            return

        left, top, width, height = rect
        painter.setFont(QFont("Helvetica Neue", 9, QFont.Weight.Medium))

        # Собираем данные: (sym, val, y)
        data = [
            (sym, val, self.last_positions[sym][1])
            for sym, val in self.last_values.items()
            if sym in self.last_positions
        ]
        if not data:
            return

        # сортируем сверху вниз
        data.sort(key=lambda x: x[2])

        y_spacing = 14  # минимальный зазор
        adjusted = True

        # итеративное раздвижение
        while adjusted:
            adjusted = False
            for i in range(1, len(data)):
                _, _, y_prev = data[i - 1]
                sym, val, y = data[i]
                if abs(y - y_prev) < y_spacing:
                    # если близко — сдвигаем текущее вниз
                    y = y_prev + y_spacing
                    data[i] = (sym, val, y)
                    adjusted = True

        # Рисуем значения
        for sym, val, y in data:
            color = self.colors.get(sym, QColor("#FFFFFF"))
            x = int(left + width + 5)
            sign = "+" if val >= 0 else ""
            text = f"{sign}{val:.2f}%"

            # тень/свечение
            glow = QPen(QColor(color.red(), color.green(), color.blue(), 80), 4)
            painter.setPen(glow)
            painter.drawText(x, int(y + 4), text)

            painter.setPen(QPen(color))
            painter.drawText(x, int(y + 4), text)
            
class MarketMap(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        title = QLabel("Intraday Market Map")
        title.setStyleSheet("background: transparent; border: none; font-weight: bold; font-family: 'Helvetica Neue'; font-size: 12px;")
        layout.addWidget(title)

        self.canvas = ChartCanvas()
        layout.addWidget(self.canvas)
