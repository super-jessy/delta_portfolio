import requests
import xml.etree.ElementTree as ET
from datetime import datetime

MYFXBOOK_CALENDAR_URL = "https://www.myfxbook.com/rss/forex-economic-calendar-events"


def fetch_economic_calendar():
    """Парсит RSS фид экономического календаря Myfxbook через requests"""
    try:
        response = requests.get(MYFXBOOK_CALENDAR_URL, timeout=10)
        response.raise_for_status()
        xml_data = response.text
    except Exception as e:
        print(f"[econ_calendar_service] Request error: {e}")
        return []

    try:
        root = ET.fromstring(xml_data)
        items = root.findall(".//item")
    except ET.ParseError as e:
        print(f"[econ_calendar_service] XML parse error: {e}")
        return []

    events = []

    for item in items:
        title = item.findtext("title", default="No Title")
        link = item.findtext("link", default="")
        pub_date = item.findtext("pubDate", default="")
        description = item.findtext("description", default="")

        # Приводим дату к читаемому виду
        try:
            parsed_date = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
            date_str = parsed_date.strftime("%d %b %Y %H:%M GMT")
        except Exception:
            date_str = pub_date

        events.append({
            "title": title,
            "summary": description,
            "link": link,
            "published": date_str,
        })

    return events
