from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath
from services.chart_service import fetch_candles


class CandleChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(430)
        self.setMouseTracking(True)
        self.setStyleSheet("background-color: #222222; border-radius: 6px;")

        # --- параметры графика ---
        self.data = []
        self.symbol = "AAPL"
        self.timeframe = "M30"
        self.visible_candles = 100
        self.scroll_offset = 0
        self.cursor_pos = None

        # --- перетаскивание ---
        self.dragging = False
        self.last_mouse_x = None

        # --- отступы ---
        self.margin_left = 10
        self.margin_right = 60
        self.margin_top = 25
        self.margin_bottom = 25

        self.font = QFont("Helvetica Neue", 9)

        # --- автообновление каждые 30 мин ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1800000)
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

    # ---------- начало перетаскивания ----------
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.last_mouse_x = event.position().x()

    # ---------- движение мыши ----------
    def mouseMoveEvent(self, event):
        if self.dragging and self.last_mouse_x is not None:
            # вычисляем смещение
            dx = int(event.position().x() - self.last_mouse_x)
            self.last_mouse_x = event.position().x()

            # изменение scroll_offset
            scroll_speed = 0.5  # плавность
            self.scroll_offset += int(dx * scroll_speed)

            # ограничиваем диапазон
            max_offset = max(0, len(self.data) - self.visible_candles)
            self.scroll_offset = max(0, min(max_offset, self.scroll_offset))

            self.update()
        else:
            self.cursor_pos = event.position()
            self.update()

    # ---------- завершение перетаскивания ----------
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.last_mouse_x = None

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

        if len(subset) > self.visible_candles:
            subset = subset[-self.visible_candles:]

        if not subset:
            return

        closes = [c[4] for c in subset]
        highs = [c[2] for c in subset]
        lows = [c[3] for c in subset]

        min_price = min(lows)
        max_price = max(highs)
        price_range = max_price - min_price if max_price > min_price else 1
        candle_width = width / self.visible_candles

        # --- сетка ---
        pen = QPen(QColor("#333333"))
        pen.setStyle(Qt.PenStyle.DotLine)
        painter.setPen(pen)
        for i in range(5):
            y = int(top + i * (height / 4))
            painter.drawLine(int(left), y, int(left + width), y)

        # --- ось X ---
        painter.setFont(self.font)
        painter.setPen(QColor("#A2DD84"))
        step = max(1, len(subset) // 6)
        for i in range(0, len(subset), step):
            dt = subset[i][0]
            label = dt.strftime("%H:%M") if self.timeframe == "M30" else dt.strftime("%d %b")
            x = int(left + i * candle_width)
            painter.drawText(x - 15, int(top + height + 15), label)

        # --- свечи ---
        for i, (dt, o, h, l, c) in enumerate(subset):
            x = left + i * candle_width
            y_open = top + height - ((o - min_price) / price_range) * height
            y_close = top + height - ((c - min_price) / price_range) * height
            y_high = top + height - ((h - min_price) / price_range) * height
            y_low = top + height - ((l - min_price) / price_range) * height

            color = QColor("#A2DD84") if c >= o else QColor("#FF4D4D")
            pen = QPen(color, 1)
            painter.setPen(pen)
            painter.drawLine(int(x + candle_width / 2), int(y_high), int(x + candle_width / 2), int(y_low))
            painter.fillRect(int(x), int(min(y_open, y_close)),
                             int(candle_width - 1), int(abs(y_close - y_open)),
                             color)

        # --- EMA по всему графику (вперёд) ---
        self.draw_ema(painter, self.data, 25, QColor("#00BFFF"), subset, rect, min_price, price_range, candle_width, start_idx)
        self.draw_ema(painter, self.data, 100, QColor("#FFB347"), subset, rect, min_price, price_range, candle_width, start_idx)

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

    # ---------- crosshair ----------
    def draw_crosshair(self, painter, cx, cy, data, left, top, width, height, min_price, price_range, candle_width):
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

    # ---------- EMA вперёд по всем данным ----------
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


class ChartPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # верхняя панель
        top_bar = QHBoxLayout()
        self.symbol_box = QComboBox()
        self.symbol_box.addItems(["AAPL", "AMZN", "TSLA"])
        self.symbol_box.currentTextChanged.connect(self.on_symbol_change)

        self.timeframe_buttons = {}
        for tf in ["M30", "D1", "W1"]:
            btn = QPushButton(tf)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    background-color:#333;
                    color:white;
                    border-radius:5px;
                    padding:4px 10px;
                }
                QPushButton:checked {
                    background-color:#A2DD84;
                    color:black;
                }
            """)
            btn.clicked.connect(lambda _, t=tf: self.on_timeframe_change(t))
            self.timeframe_buttons[tf] = btn
            top_bar.addWidget(btn)

        self.timeframe_buttons["M30"].setChecked(True)
        top_bar.addSpacing(15)
        top_bar.addWidget(QLabel("Symbol:"))
        top_bar.addWidget(self.symbol_box)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        # график
        self.chart = CandleChart()
        layout.addWidget(self.chart)

    def on_symbol_change(self, symbol):
        self.chart.symbol = symbol
        self.chart.update_data()

    def on_timeframe_change(self, tf):
        for t, btn in self.timeframe_buttons.items():
            btn.setChecked(t == tf)
        self.chart.timeframe = tf
        self.chart.update_data()
