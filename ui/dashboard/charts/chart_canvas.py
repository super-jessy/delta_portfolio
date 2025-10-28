from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath
from services.chart_service import fetch_candles
import numpy as np


class ChartCanvas(QWidget):
    tool_finished = pyqtSignal()  # сигнал завершения инструмента рисования

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(480)
        self.setMouseTracking(True)
        self.setStyleSheet("background-color: #222222; border-radius: 6px;")

        # --- данные графика ---
        self.data = []
        self.symbol = "AAPL"
        self.timeframe = "M30"
        self.chart_type = "Candlestick"
        self.visible_candles = 150
        self.scroll_offset = 0
        self.vertical_offset = 0
        self.last_mouse_y = None
        self.cursor_pos = None
        self.active_indicators = []

        # --- перетаскивание графика ---
        self.dragging = False
        self.last_mouse_x = None
        self.last_mouse_y = None

        # --- инструменты рисования ---
        self.active_tool = None
        self.drawing_start = None
        # ВАЖНО: храним X в НОРМАЛИЗОВАННОМ виде (0..1), цену — в реальном значении
        # Пример: [((0.73, 186.2), (0.82, 188.0)), ...]
        self.persistent_drawings = []
        self.selected_line = None
        self.dragging_line = None
        self.dragging_point = None  # 'start' | 'end' | 'mid'

        # --- отступы ---
        self.margin_left = 10
        self.margin_right = 60
        self.margin_top = 25
        self.margin_bottom = 25
        self.font = QFont("Helvetica Neue", 9)

        # --- автообновление каждые 15 мин ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(15 * 60 * 1000)
        self.update_data()

    # ---------- загрузка данных ----------
    def update_data(self):
        try:
            self.data = fetch_candles(self.symbol, self.timeframe)
        except Exception as e:
            print(f"[Chart] Error loading data: {e}")
            self.data = []
        self.scroll_offset = 0
        self.update()

    # ---------- масштабирование колесом ----------
    def wheelEvent(self, event):
        if not self.data:
            return
        delta = event.angleDelta().y() / 120
        zoom_speed = 20
        self.visible_candles -= int(delta * zoom_speed)
        self.visible_candles = max(100, min(500, self.visible_candles))
        self.update()

    # ---------- обработка мыши ----------
    def mousePressEvent(self, event):
        pos = event.position()

        # удаление линии (ПКМ)
        if not self.active_tool and event.button() == Qt.MouseButton.RightButton:
            clicked_line, _ = self._find_near_line(pos)
            if clicked_line:
                self.persistent_drawings.remove(clicked_line)
                if self.selected_line == clicked_line:
                    self.selected_line = None
                self.update()
                return

        # выбор/захват линии (ЛКМ)
        if not self.active_tool and event.button() == Qt.MouseButton.LeftButton:
            clicked_line, point = self._find_near_line(pos)
            if clicked_line:
                self.selected_line = clicked_line
                self.dragging_line = clicked_line
                self.dragging_point = point  # 'start' | 'end' | 'mid'
                # фиксируем референс для "mid"-перетаскивания
                self._drag_ref = {"pos": pos, "orig": clicked_line}
                self.setCursor(Qt.CursorShape.SizeAllCursor)
                self.update()
                return

        # начало/завершение рисования трендлайна
        if self.active_tool == "trendline" and event.button() == Qt.MouseButton.LeftButton:
            if self.drawing_start is None:
                idx, price = self._pixel_to_data(pos.x(), pos.y())
                self.drawing_start = (idx, price)  # временно абсолютный индекс
                self.update()
                return
            else:
                idx, price = self._pixel_to_data(pos.x(), pos.y())
                nx1 = self._normalize_x(self.drawing_start[0])
                nx2 = self._normalize_x(idx)
                self.persistent_drawings.append(((nx1, self.drawing_start[1]), (nx2, price)))
                # Завершение инструмента — СРАЗУ выходим, чтобы не стартовать drag графика
                self.drawing_start = None
                self.active_tool = None
                self.tool_finished.emit()
                self.update()
                return

        # перетаскивание графика (если не рисуем и не тащим линию)
        if event.button() == Qt.MouseButton.LeftButton:
           self.dragging = True
           self.setCursor(Qt.CursorShape.ClosedHandCursor)
           self.last_mouse_x = pos.x()
           self.last_mouse_y = pos.y()

        # клик мимо объектов — снять выделение
        if event.button() == Qt.MouseButton.LeftButton and not self.active_tool and not self.dragging_line:
            clicked_line, _ = self._find_near_line(pos)
            if not clicked_line:
                self.selected_line = None
                self.update()

    def mouseMoveEvent(self, event):
        if self.dragging_line:
            pos = event.position()
            ((x1, p1), (x2, p2)) = self.dragging_line  # здесь x1/x2 — НОРМАЛИЗОВАНЫ

            if self.dragging_point == "start":
                ix, pr = self._pixel_to_data(pos.x(), pos.y())
                new_line = ((self._normalize_x(ix), pr), (x2, p2))
            elif self.dragging_point == "end":
                ix, pr = self._pixel_to_data(pos.x(), pos.y())
                new_line = ((x1, p1), (self._normalize_x(ix), pr))
            else:  # mid — перенос всей линии
                # гарантируем, что есть референс начального состояния
                if not hasattr(self, "_drag_ref"):
                    self._drag_ref = {"pos": pos, "orig": self.dragging_line}

                dx = pos.x() - self._drag_ref["pos"].x()
                dy = pos.y() - self._drag_ref["pos"].y()

                (ox1, op1), (ox2, op2) = self._drag_ref["orig"]
                # в пиксели — только через ДЕнормализацию X
                sx1, sy1 = self._data_to_pixel(self._denormalize_x(ox1), op1)
                sx2, sy2 = self._data_to_pixel(self._denormalize_x(ox2), op2)

                new_x1, new_y1 = sx1 + dx, sy1 + dy
                new_x2, new_y2 = sx2 + dx, sy2 + dy

                ix1, pr1 = self._pixel_to_data(new_x1, new_y1)
                ix2, pr2 = self._pixel_to_data(new_x2, new_y2)
                new_line = ((self._normalize_x(ix1), pr1), (self._normalize_x(ix2), pr2))

            # зафиксировать изменения
            idx = self.persistent_drawings.index(self.dragging_line)
            self.persistent_drawings[idx] = new_line
            self.dragging_line = new_line
            self.selected_line = new_line
            self.update()
            return

        if self.dragging and self.last_mouse_x is not None:
           dx = int(event.position().x() - self.last_mouse_x)
           dy = int(event.position().y() - self.last_mouse_y)
           self.last_mouse_x = event.position().x()
           self.last_mouse_y = event.position().y()

           self.scroll_offset += int(dx * 0.5)
           max_offset = max(0, len(self.data) - self.visible_candles)
           self.scroll_offset = max(0, min(max_offset, self.scroll_offset))

           self.vertical_offset += dy
           self.update()
        else:
           self.cursor_pos = event.position()
           self.update()


    def mouseReleaseEvent(self, event):
        if hasattr(self, "_drag_ref"):
            del self._drag_ref
        if self.dragging_line:
            # закончить перенос/редактирование линии
            self.dragging_line = None
            self.dragging_point = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            return
        if event.button() == Qt.MouseButton.LeftButton:
           self.dragging = False
           self.setCursor(Qt.CursorShape.ArrowCursor)
           self.last_mouse_x = None
           self.last_mouse_y = None

    def leaveEvent(self, event):
        self.cursor_pos = None
        self.update()

    # ---------- отрисовка ----------
    def paintEvent(self, event):
        if not self.data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        painter.fillRect(rect, QColor("#222222"))

        left, top = self.margin_left, self.margin_top
        width = rect.width() - self.margin_left - self.margin_right
        height = rect.height() - self.margin_top - self.margin_bottom

        total = len(self.data)
        start_idx = max(0, total - self.visible_candles - self.scroll_offset)
        end_idx = min(total, total - self.scroll_offset)
        subset = self.data[start_idx:end_idx]
        if not subset:
            return

        if not hasattr(self, "_fixed_min_price") or not hasattr(self, "_fixed_max_price"):
           highs = [c[2] for c in subset]
           lows = [c[3] for c in subset]
           self._fixed_min_price, self._fixed_max_price = min(lows), max(highs)

        closes = [c[4] for c in subset]
        min_price, max_price = self._fixed_min_price, self._fixed_max_price
        price_range = max_price - min_price if max_price > min_price else 1
        candle_width = width / self.visible_candles

        # --- сетка ---
        pen = QPen(QColor("#333333"))
        pen.setStyle(Qt.PenStyle.DotLine)
        painter.setPen(pen)
        for i in range(5):
            y = int(top + i * (height / 4))
            painter.drawLine(int(left), int(y), int(left + width), int(y))

        # --- ось X ---
        painter.setFont(self.font)
        painter.setPen(QColor("#A2DD84"))
        step = max(1, len(subset) // 6)
        for i in range(0, len(subset), step):
            dt = subset[i][0]
            label = dt.strftime("%H:%M") if self.timeframe.startswith("M") else dt.strftime("%d %b")
            x = int(left + i * candle_width)
            painter.drawText(x - 15, int(top + height + 15), label)

        # --- свечи / линия ---
        if self.chart_type == "Candlestick":
            for i, (dt, o, h, l, c) in enumerate(subset):
                x = left + i * candle_width - 20
                y_open = top + height - ((o - min_price) / price_range) * height
                y_close = top + height - ((c - min_price) / price_range) * height
                y_high = top + height - ((h - min_price) / price_range) * height
                y_low = top + height - ((l - min_price) / price_range) * height
                y_open += self.vertical_offset
                y_close += self.vertical_offset
                y_high += self.vertical_offset
                y_low += self.vertical_offset

                color = QColor("#A2DD84") if c >= o else QColor("#FF4D4D")
                pen = QPen(color, 1)
                painter.setPen(pen)
                painter.drawLine(int(x + candle_width / 2), int(y_high), int(x + candle_width / 2), int(y_low))
                painter.fillRect(int(x), int(min(y_open, y_close)), int(candle_width - 1), int(abs(y_close - y_open)), color)
        else:
            path = QPainterPath()
            path.moveTo(left, top + height - ((closes[0] - min_price) / price_range) * height)
            for i, c in enumerate(closes):
                x = left + i * candle_width
                y = top + height - ((c - min_price) / price_range) * height
                path.lineTo(x, y)
            painter.setPen(QPen(QColor("#A2DD84"), 1.5))
            painter.drawPath(path)

        # --- индикаторы (EMA/SMA) ---
        for ind in self.active_indicators:
            self.draw_indicator(painter, ind, subset, rect, min_price, price_range, candle_width, start_idx)

        # --- ось Y справа ---
        painter.setPen(QColor("#A2DD84"))
        for i in range(5):
            price = max_price - i * (price_range / 4)
            y = int(top + i * (height / 4))
            painter.drawText(int(left + width + 5), y + 5, f"{price:.2f}")

        # --- текущая цена ---
        last_price = subset[-1][4]
        y_last = top + height - ((last_price - min_price) / price_range) * height
        painter.setBrush(QColor("#A2DD84"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(int(left + width + 2), int(y_last - 8), 45, 16, 4, 4)
        painter.setPen(QColor("#000000"))
        painter.setFont(QFont("Helvetica Neue", 9, QFont.Weight.Medium))
        painter.drawText(int(left + width + 8), int(y_last + 5), f"{last_price:.2f}")

        # --- crosshair ---
        if self.cursor_pos and not self.dragging:
            cx, cy = int(self.cursor_pos.x()), int(self.cursor_pos.y())
            if left < cx < left + width and top < cy < top + height:
                self.draw_crosshair(painter, cx, cy, subset, left, top, width, height, min_price, price_range, candle_width)

        # --- линии (используем ДЕ-нормализацию X при отрисовке) ---
        painter.setPen(QPen(QColor("#A2DD84"), 1.8))
        for line in self.persistent_drawings:
            ((x1, p1), (x2, p2)) = line
            sx1, sy1 = self._data_to_pixel(self._denormalize_x(x1), p1)
            sx2, sy2 = self._data_to_pixel(self._denormalize_x(x2), p2)
            sy1 += self.vertical_offset
            sy2 += self.vertical_offset

            painter.drawLine(int(sx1), int(sy1), int(sx2), int(sy2))
            if line == self.selected_line:
                painter.setBrush(QColor("#A2DD84"))
                painter.drawEllipse(int(sx1) - 3, int(sy1) - 3, 6, 6)
                painter.drawEllipse(int(sx2) - 3, int(sy2) - 3, 6, 6)

        # --- временная линия при рисовании ---
        if self.active_tool == "trendline" and self.drawing_start and self.cursor_pos:
            painter.setPen(QPen(QColor("#A2DD84"), 1.2, Qt.PenStyle.DashLine))
            start_x, start_y = self._data_to_pixel(*self.drawing_start)
            end_idx, end_price = self._pixel_to_data(self.cursor_pos.x(), self.cursor_pos.y())
            end_x, end_y = self._data_to_pixel(end_idx, end_price)
            painter.drawLine(int(start_x), int(start_y), int(end_x), int(end_y))

    # ---------- служебные функции ----------
    def _data_to_pixel(self, x_idx, price):
      if not self.data:
          return 0, 0
      rect = self.rect()
      left, top = self.margin_left, self.margin_top
      width = rect.width() - self.margin_left - self.margin_right
      height = rect.height() - self.margin_top - self.margin_bottom
      candle_width = width / self.visible_candles
      min_price, max_price = self._price_range()
      y = top + height - ((price - min_price) / (max_price - min_price)) * height + self.vertical_offset
      x = left + (x_idx - (len(self.data) - self.visible_candles - self.scroll_offset)) * candle_width + 20
      return x, y

    def _pixel_to_data(self, x, y):
      rect = self.rect()
      left, top = self.margin_left, self.margin_top
      width = rect.width() - self.margin_left - self.margin_right
      height = rect.height() - self.margin_top - self.margin_bottom
      candle_width = width / self.visible_candles
      min_price, max_price = self._price_range()
      price = max_price - ((y - top - self.vertical_offset) / height) * (max_price - min_price)
      idx = int((x - left - 20) / candle_width) + (len(self.data) - self.visible_candles - self.scroll_offset)
      return idx, price


    def _normalize_x(self, idx):
        total = len(self.data)
        if not total:
            return 0.0
        # clamp на всякий случай
        return max(0.0, min(1.0, idx / total))

    def _denormalize_x(self, norm_x):
        total = len(self.data)
        if not total:
            return 0
        # clamp и перевод обратно в индекс
        nx = max(0.0, min(1.0, float(norm_x)))
        return int(nx * (total - 1))

    def _price_range(self):
        if not self.data:
            return 0, 1
        highs = [c[2] for c in self.data]
        lows = [c[3] for c in self.data]
        return min(lows), max(highs)

    def _find_near_line(self, pos, tolerance=8):
        x, y = pos.x(), pos.y()
        for line in reversed(self.persistent_drawings):
            ((x1, p1), (x2, p2)) = line
            # ДЕ-нормализуем X для перевода в пиксели
            sx1, sy1 = self._data_to_pixel(self._denormalize_x(x1), p1)
            sx2, sy2 = self._data_to_pixel(self._denormalize_x(x2), p2)
            if abs(sx1 - x) < tolerance and abs(sy1 - y) < tolerance:
                return line, "start"
            if abs(sx2 - x) < tolerance and abs(sy2 - y) < tolerance:
                return line, "end"
            if self._distance_point_to_segment(x, y, sx1, sy1, sx2, sy2) < tolerance:
                return line, "mid"
        return None, None

    def _distance_point_to_segment(self, px, py, x1, y1, x2, y2):
        vx, vy = x2 - x1, y2 - y1
        wx, wy = px - x1, py - y1
        c1 = wx * vx + wy * vy
        if c1 <= 0:
            return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
        c2 = vx * vx + vy * vy
        if c2 <= c1:
            return ((px - x2) ** 2 + (py - y2) ** 2) ** 0.5
        b = c1 / c2 if c2 else 0
        bx, by = x1 + b * vx, y1 + b * vy
        return ((px - bx) ** 2 + (py - by) ** 2) ** 0.5

    # ---------- crosshair ----------
    def draw_crosshair(self, painter, cx, cy, data, left, top, width, height, min_price, price_range, candle_width):
        cy += self.vertical_offset
        painter.setPen(QPen(QColor("#A2DD84"), 1, Qt.PenStyle.DashLine))
        painter.drawLine(cx, top, cx, top + height)
        painter.drawLine(left, cy, left + width, cy)

        idx = int((cx - left) / candle_width)
        if 0 <= idx < len(data):
            dt = data[idx][0].strftime("%d %b %H:%M")
            price = min_price + (height - (cy - top)) / height * price_range
            painter.setBrush(QColor(30, 30, 30, 220))
            painter.setPen(QColor("#A2DD84"))
            painter.drawRoundedRect(cx - 45, top + height + 5, 90, 18, 3, 3)
            painter.drawText(cx - 40, top + height + 18, dt)
            painter.drawRoundedRect(left + width + 2, cy - 8, 50, 16, 3, 3)
            painter.drawText(left + width + 8, cy + 5, f"{price:.2f}")

    # ---------- индикаторы ----------
    def apply_indicator(self, indicator_name):
        if indicator_name == "None":
            self.active_indicators.clear()
            self.update()
            return
        self.active_indicators = [indicator_name]
        self.update()

    def draw_indicator(self, painter, indicator_name, subset, rect, min_price, price_range, candle_width, start_idx):
        if indicator_name.startswith("EMA"):
            period = int(indicator_name.split(" ")[1])
            self.draw_ema(painter, self.data, period, QColor("#00BFFF"), subset, rect, min_price, price_range, candle_width, start_idx)
        elif indicator_name.startswith("SMA"):
            period = int(indicator_name.split(" ")[1])
            self.draw_sma(painter, self.data, period, QColor("#FFB347"), subset, rect, min_price, price_range, candle_width, start_idx)

    def draw_ema(self, painter, all_data, period, color, subset, rect, min_price, price_range, candle_width, start_idx):
        if len(all_data) < period:
            return
        closes = [c[4] for c in all_data]
        ema_values = []
        k = 2 / (period + 1)
        ema = closes[0]
        ema_values.append(ema)
        for price in closes[1:]:
            ema = price * k + ema * (1 - k)
            ema_values.append(ema)

        ema_visible = ema_values[start_idx:start_idx + len(subset)]
        left, top = self.margin_left, self.margin_top
        height = rect.height() - self.margin_top - self.margin_bottom
        path = QPainterPath()
        for i, ema_val in enumerate(ema_visible):
            x = left + i * candle_width
            y = top + height - ((ema_val - min_price) / price_range) * height
            if i == 0:
                path.moveTo(QPointF(x, y))
            else:
                path.lineTo(QPointF(x, y))
        painter.setPen(QPen(color, 1.5))
        painter.drawPath(path)

    def draw_sma(self, painter, all_data, period, color, subset, rect, min_price, price_range, candle_width, start_idx):
        if len(all_data) < period:
            return
        closes = np.array([c[4] for c in all_data])
        sma = np.convolve(closes, np.ones(period) / period, mode="valid")
        left, top = self.margin_left, self.margin_top
        height = rect.height() - self.margin_top - self.margin_bottom
        path = QPainterPath()
        for i, val in enumerate(sma[start_idx:start_idx + len(subset)]):
            x = left + (i + period - 1) * candle_width
            y = top + height - ((val - min_price) / price_range) * height
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        painter.setPen(QPen(color, 1.5))
        painter.drawPath(path)

    # ---------- выбор инструмента ----------
    def set_drawing_tool(self, tool_name):
        if tool_name:
            self.active_tool = tool_name.lower()
        else:
            self.active_tool = None
        self.update()
