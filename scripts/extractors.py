"""Extract raw events without site-specific network logic."""
import json
import re
from bs4 import BeautifulSoup


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def jsonld(html):
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.get_text())
        except ValueError:
            continue
        for obj in walk(data):
            types = obj.get("@type", [])
            if isinstance(types, str):
                types = [types]
            if not any(t in ("MusicEvent", "Event") for t in types):
                continue
            location = obj.get("location") or {}
            if isinstance(location, list):
                location = location[0] if location else {}
            offers = obj.get("offers") or []
            if isinstance(offers, dict):
                offers = [offers]
            yield dict(title=obj.get("name"), date=obj.get("startDate"),
                       venue=location.get("name") if isinstance(location, dict) else location,
                       link=obj.get("url"), price=next((o.get("price", o.get("lowPrice")) for o in offers if isinstance(o, dict)), None),
                       program="", status=obj.get("eventStatus", ""))


def css(html, source):
    soup = BeautifulSoup(html, "html.parser")
    selectors = source.get("selectors", source)
    for node in soup.select(selectors["item"]):
        row = {}
        for key in ("title", "date", "venue", "area", "link", "price", "program"):
            selector = selectors.get(key)
            if not selector:
                continue
            if isinstance(selector, str):
                selector = {"css": selector}
            el = node.select_one(selector["css"])
            if el:
                attr = selector.get("attr", "href" if key == "link" else None)
                row[key] = el.get(attr, "") if attr else el.get_text(" ", strip=True)
        yield row


def api_json(body, source):
    data = json.loads(body)
    for key in source.get("itemsPath", "").split("."):
        if key:
            data = data[key]
    if not isinstance(data, list):
        raise ValueError("API items must be an array")
    for item in data:
        row = {}
        for field, path in source["fields"].items():
            value = item
            for key in path.split("."):
                value = value.get(key) if isinstance(value, dict) else None
            row[field] = value
        yield row


def rss(body, source):
    soup = BeautifulSoup(body, "html.parser")
    for item in soup.select("item, entry"):
        row = {}
        for field, selector in source["fields"].items():
            el = item.select_one(selector)
            if el:
                row[field] = el.get("href") or el.get_text(" ", strip=True)
        yield row


def price(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value) if value >= 0 else None
    match = re.fullmatch(r"\s*[¥￥]?\s*([\d,]+)\s*円?\s*", str(value))
    return int(match[1].replace(",", "")) if match else None
