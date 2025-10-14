import requests
import xml.etree.ElementTree as ET
from datetime import datetime

RSS_URL = "https://www.myfxbook.com/rss/latest-forex-news"

def get_news(limit=10):
    """
    Получает последние новости с Myfxbook RSS.
    Возвращает список словарей с ключами:
    title, link, pubDate, source.
    """
    try:
        response = requests.get(RSS_URL, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)

        items = []
        for item in root.findall(".//item")[:limit]:
            title = item.find("title").text if item.find("title") is not None else ""
            link = item.find("link").text if item.find("link") is not None else ""
            pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
            source = "Myfxbook"

            # преобразуем время в читаемый формат
            try:
                parsed = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
                pub_date = parsed.strftime("%H:%M · %b %d, %Y")
            except Exception:
                pass

            items.append({
                "title": title.strip(),
                "url": link.strip(),
                "source": source,
                "time_published": pub_date,
            })
        return items

    except Exception as e:
        print(f"[ERROR] Failed to fetch RSS: {e}")
        return []
