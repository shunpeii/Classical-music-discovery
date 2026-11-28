"""Extract candidate concerts without publishing unreviewed data."""
import datetime as dt
import json
import re
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from validate_nhk import AGENT, AREAS, ROOT, match


def fetch(url):
    robots = requests.get(urljoin(url, "/robots.txt"), timeout=20)
    if robots.status_code != 404:
        robots.raise_for_status()
        parser = RobotFileParser()
        parser.parse(robots.text.splitlines())
        if not parser.can_fetch(AGENT, url):
            raise ValueError("robots disallows URL")
    response = requests.get(url, headers={"User-Agent": AGENT}, timeout=25, allow_redirects=False)
    if response.status_code != 200:
        raise ValueError(f"HTTP {response.status_code}")
    if response.encoding in (None, "ISO-8859-1"):
        response.encoding = response.apparent_encoding or "utf-8"
    return response


def value(node, selector):
    child = node.select_one(selector)
    return child.get_text(" ", strip=True) if child else ""


def html_rows(url, item, date, title, venue, link, program, fixed_venue=""):
    soup = BeautifulSoup(fetch(url).text, "html.parser")
    for node in soup.select(item):
        anchor = node.select_one(link)
        if not anchor or not anchor.get("href"):
            continue
        raw_date = value(node, date)
        found = re.search(r"(20\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", raw_date)
        if not found:
            continue
        try:
            day = dt.date(*map(int, found.groups())).isoformat()
        except ValueError:
            continue
        name = value(node, title)
        if fixed_venue and not re.search(r"クラシック|オーケストラ|交響楽|オルガン|管弦楽|ピアノ|室内楽|弦楽", name):
            continue
        time = re.search(r"\d{1,2}:\d{2}", raw_date)
        songs = node.select(program) if program else []
        yield {"title": name, "date": day, "time": time.group() if time else "",
               "venue": fixed_venue or value(node, venue),
               "sourceUrl": urljoin(url, anchor["href"]),
               "program": [line.strip() for song in songs for line in song.get_text("\n", strip=True).splitlines() if line.strip()]}


def yokohama():
    url = "https://yokohama-minatomiraihall.jp/cal.json"
    data = fetch(url).json()
    for day, entry in data["cal"].items():
        for event in entry.get("concerts", []):
            ja = event.get("ja", {})
            songs = [f"{s.get('author', '')}／{s.get('title', '')}" for s in ja.get("program", []) if s.get("author") and s.get("title")]
            if not songs:
                continue
            yield {"title": ja.get("title", ""), "date": day, "time": event.get("start_time", ""),
                   "venue": "横浜みなとみらいホール", "venueCode": event.get("venue"),
                   "sourceUrl": urljoin(url, ja["url"]) if ja.get("url") else "",
                   "program": songs, "sourceEventId": event.get("id")}


def main():
    master = ROOT / "public/data/master"
    composers = json.loads((master / "composers.json").read_text(encoding="utf-8"))
    works = json.loads((master / "works.json").read_text(encoding="utf-8"))
    today = dt.datetime.now(ZoneInfo("Asia/Tokyo")).date()
    sources = {
        "tmso": lambda: html_rows("https://www.tmso.or.jp/j/concert/", ".entry-content", ".entry-date", ".entry-title", ".entry-hall", ".entry-link", ".notes"),
        "triphony": lambda: html_rows("https://www.triphony.com/", ".boxPickUp", ".eventDate", ".ttlPickUp", "", ".txtMore a", "", "すみだトリフォニーホール"),
        "yokohama": yokohama,
    }
    reports = {}
    for source, extract in sources.items():
        rows = {}
        incomplete = 0
        try:
            for row in extract():
                try:
                    day = dt.date.fromisoformat(row["date"])
                except (TypeError, ValueError):
                    continue
                if day < today:
                    continue
                venue = row["venue"]
                area = next((a for name, a in AREAS.items() if venue.startswith(name)), None)
                if not area or not row["title"] or not row["time"] or urlparse(row["sourceUrl"]).scheme not in ("http", "https"):
                    incomplete += 1
                    continue
                row["area"] = area
                row["workIds"] = sorted({w for song in row["program"] if (w := match(song, composers, works))})
                rows[(row["date"], row["time"], row["title"], venue)] = row
            reports[source] = {"normalizedCount": len(rows), "incompleteCount": incomplete,
                               "matchedConcertCount": sum(bool(row["workIds"]) for row in rows.values()),
                               "rows": list(rows.values())}
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            reports[source] = {"error": str(exc), "normalizedCount": 0}
    path = ROOT / "scripts/diagnostics/sites-validation.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    print({source: report["normalizedCount"] for source, report in reports.items()})


if __name__ == "__main__":
    main()
