"""Validate NHK normalization and conservative catalog matching without publishing."""
import datetime as dt
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://www.nhkso.or.jp/"
AGENT = "OpusConcertDiscovery/0.1"
AREAS = {"NHKホール": "東京", "サントリーホール": "東京", "東京芸術劇場": "東京",
         "すみだトリフォニーホール": "東京", "東京文化会館": "東京",
         "ミューザ川崎シンフォニーホール": "神奈川", "横浜みなとみらいホール": "神奈川"}


def fetch(path):
    url = urljoin(BASE, path)
    robots = requests.get(urljoin(BASE, "robots.txt"), timeout=20)
    if robots.status_code != 404:
        robots.raise_for_status()
        parser = RobotFileParser()
        parser.parse(robots.text.splitlines())
        if not parser.can_fetch(AGENT, url):
            raise ValueError("robots.txt disallows " + url)
    response = requests.get(url, headers={"User-Agent": AGENT}, timeout=25, allow_redirects=False)
    if response.status_code != 200:
        raise ValueError(f"HTTP {response.status_code}: {url}")
    return response.json()


def clean(value):
    return BeautifulSoup(str(value or ""), "html.parser").get_text(" ", strip=True)


def key(value):
    return re.sub(r"[^\w]|_", "", unicodedata.normalize("NFKC", value).casefold())


def match(song, composers, works):
    parts = re.split(r"[／/：:]", song, maxsplit=1)
    if len(parts) != 2:
        return None
    author, title = map(key, parts)
    ids = {c["id"] for c in composers if key(c["name"]) == author}
    candidates = [w["id"] for w in works if w["composerId"] in ids and key(w["title"]) == title]
    return candidates[0] if len(candidates) == 1 else None


def normalize(concerts, halls, composers, works, today):
    rows = {}
    unknown = set()
    unmatched = set()
    for event in concerts:
        if event.get("status") is not True:
            continue
        venue = clean(halls.get(str(event.get("hall_id")), {}).get("name"))
        area = AREAS.get(venue)
        songs = [clean(s.get("name")) for s in event.get("songs", [])]
        for detail in event.get("details", []):
            try:
                day = dt.date.fromisoformat(detail["date"])
            except (KeyError, ValueError, TypeError):
                continue
            if day < today:
                continue
            if not area:
                unknown.add(venue or str(event.get("hall_id")))
                continue
            url = urljoin(BASE, event.get("details_url") or "")
            title = clean(event.get("title"))
            if not title or not event.get("details_url"):
                continue
            matched = [match(song, composers, works) for song in songs]
            unmatched.update(song for song, work in zip(songs, matched, strict=True) if song and not work)
            time = clean(detail.get("start_time"))
            identity = (url, day.isoformat(), time, venue)
            rows[identity] = {"title": title, "date": day.isoformat(), "time": time,
                              "venue": venue, "area": area, "sourceUrl": url,
                              "ticketUrl": detail.get("ticket_url"), "program": songs,
                              "workIds": sorted({w for w in matched if w})}
    return list(rows.values()), sorted(unknown), sorted(unmatched)


def main():
    master = ROOT / "public/data/master"
    composers = json.loads((master / "composers.json").read_text(encoding="utf-8"))
    works = json.loads((master / "works.json").read_text(encoding="utf-8"))
    concerts = fetch("concert/json/archive_concert_2026.json")["concerts"]
    halls = fetch("concert/hall/json/hall_all.json")["hall_info"]
    rows, unknown, unmatched = normalize(concerts, halls, composers, works, dt.datetime.now(ZoneInfo("Asia/Tokyo")).date())
    report = {"rawCount": len(concerts), "normalizedCount": len(rows),
              "matchedConcertCount": sum(bool(r["workIds"]) for r in rows),
              "unknownOrOutsideAreaVenues": unknown, "unmatchedSongs": unmatched, "rows": rows}
    destination = ROOT / "scripts/diagnostics/nhk-validation.json"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Normalized:", len(rows), "Matched:", report["matchedConcertCount"])


if __name__ == "__main__":
    main()
