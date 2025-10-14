from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame
from PyQt6.QtCore import Qt, QTimer
from services.news_service import get_news

class NewsPanel(QWidget):
    def __init__(self):
        super().__init__()

        self._cache = []
        self._loading = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Заголовок
        self.title = QLabel("News")
        self.title.setStyleSheet("background: transparent; border: none; font-weight: bold; font-size: 12px;")
        layout.addWidget(self.title)

        # Скролл
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setSpacing(8)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

        # Первичная загрузка
        self.load_news(initial=True)

        # Автообновление (каждые 60 секунд)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.load_news)
        self.timer.start(60000)

    def render_news(self, news_list):
        # Очистка старого
        for i in reversed(range(self.container_layout.count())):
            widget = self.container_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if not news_list:
            no_news = QLabel("No news available.")
            no_news.setStyleSheet("color: #888;")
            self.container_layout.addWidget(no_news)
            self.container_layout.addStretch()
            return

        for n in news_list:
            title_html = (
                f"<a href='{n['url']}' style='color:#FFFFFF; text-decoration:none;'>"
                f"<b>{n['title']}</b></a>"
            )
            meta_html = f"<span style='color:#A2DD84;'>{n['time_published']}</span>"

            label = QLabel(f"{title_html}<br>{meta_html}")
            label.setWordWrap(True)
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setOpenExternalLinks(True)
            label.setStyleSheet("font-size: 11px; line-height: 1.4;")
            self.container_layout.addWidget(label)

        self.container_layout.addStretch()

    def load_news(self, initial=False):
        if self._loading:
            return
        self._loading = True

        news_items = get_news(limit=8)
        if news_items:
            self._cache = news_items
            self.render_news(news_items)
        elif initial and not self._cache:
            self.render_news([])

        self._loading = False
