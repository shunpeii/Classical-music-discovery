"""Build a daily static snapshot from explicit, approved source configurations."""
import argparse
import datetime as dt
import hashlib
import json
import re
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import requests
from extractors import jsonld, css, api_json, rss, price

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public/data/concerts"
AGENT = "OpusConcertDiscovery/0.1"

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def write(path, value):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)

def normalize(raw, source):
    title = str(raw.get("title") or "").strip()
    match = re.search(r"(\d{4})[年./-](\d{1,2})[月./-](\d{1,2})", str(raw.get("date") or ""))
    if not title or not match or "EventCancelled" in str(raw.get("status", "")):
        return None
    try:
        day = dt.date(*map(int, match.groups())).isoformat()
    except ValueError:
        return None
    if day < dt.datetime.now(ZoneInfo("Asia/Tokyo")).date().isoformat():
        return None
    href = urljoin(source["url"], str(raw.get("link") or source["url"]))
    if urlparse(href).scheme not in ("http", "https"):
        return None
    venue = raw.get("venue") or source.get("venue")
    area = raw.get("area") or source.get("area")
    if not venue or not area:
        return None
    key = hashlib.sha256(f"{source['id']}|{day}|{title}|{href}".encode()).hexdigest()[:24]
    return dict(id=key, title=title, date=day, venue=venue, area=area,
                price=price(raw.get("price")), workIds=[], mood="", sourceId=source["id"],
                sourceUrl=href, program=str(raw.get("program") or ""))


def scrape(source):
    url = source["url"]
    if not source.get("approved"):
        raise ValueError("Source has not been approved")
    robot = RobotFileParser(urljoin(url, "/robots.txt"))
    robot.read()
    if not robot.can_fetch(AGENT, url):
        raise ValueError("robots.txt disallows fetching")
    response = requests.get(url, headers={"User-Agent": AGENT}, timeout=25, allow_redirects=False)
    if response.is_redirect:
        raise ValueError("Configure final URL and verify robots.txt")
    response.raise_for_status()
    if response.encoding in (None, 'ISO-8859-1'):
        response.encoding = response.apparent_encoding or 'utf-8'
    methods = source.get("methods", ["jsonld", "css"])
    for method in methods:
        if method == "jsonld":
            raw = jsonld(response.text)
        elif method == "css":
            if not source.get("selectors") and not source.get("item"):
                continue
            raw = css(response.text, source)
        elif method == "api":
            raw = api_json(response.text, source)
        elif method == "rss":
            raw = rss(response.text, source)
        else:
            raise ValueError(f"Unknown extraction method: {method}")
        rows = [row for item in raw if (row := normalize(item, source))]
        if rows:
            return rows
    raise ValueError("No valid future events; verify configuration")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT/"scripts/sources.json")
    args = parser.parse_args()
    sources = [s for s in read(args.config) if s.get('approved')]
    if not sources:
        raise SystemExit('No approved sources configured; snapshot preserved')
    pointer = read(OUT/"latest.json")
    previous = [] if pointer.get("sample") else read(OUT/pointer["file"])
    combined = []
    successes = 0
    for source in sources:
        try:
            combined.extend(scrape(source))
            successes += 1
        except Exception as exc:
            print(f"{source['id']}: {exc}")
            combined.extend(row for row in previous if row.get("sourceId")==source["id"] and row["date"]>=dt.datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat())
    if not successes:
        raise SystemExit("No successful sources; existing snapshot preserved")
    unique = {row["id"]: row for row in combined}
    rows = sorted(unique.values(), key=lambda r:(r["date"],r["title"]))
    filename = dt.datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()+".json"
    write(OUT/filename, rows)
    write(OUT/"latest.json", dict(file=filename,sample=False,concertCount=len(rows),updatedAt=dt.datetime.now(dt.timezone.utc).isoformat()))
if __name__ == "__main__":
    main()
