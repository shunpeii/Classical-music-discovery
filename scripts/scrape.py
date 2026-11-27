"""Build a daily static snapshot from explicit, approved source configurations."""
import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public/data/concerts"
AGENT = "OpusConcertDiscovery/0.1"

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def write(path, value):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)

def scrape(source):
    url = source["url"]
    if not source.get("approved"):
        raise ValueError("Source has not been approved")
    robot = RobotFileParser(urljoin(url, "/robots.txt"))
    robot.read()
    if not robot.can_fetch(AGENT, url):
        raise ValueError("robots.txt disallows fetching")
    response = requests.get(url, headers={"User-Agent": AGENT}, timeout=25)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    rows = []
    for node in soup.select(source["item"]):
        def field(key):
            el = node.select_one(source[key])
            return el.get_text(" ", strip=True) if el else ""
        title = field("title")
        date = field("date")
        match = re.search(r"(\d{4})[年./-](\d{1,2})[月./-](\d{1,2})", date)
        if not title or not match:
            continue
        day = dt.date(*map(int, match.groups())).isoformat()
        if day < dt.date.today().isoformat():
            continue
        link = node.select_one(source["link"])
        href = urljoin(url, link.get("href", "")) if link else url
        if urlparse(href).scheme not in ("http", "https"):
            continue
        venue = source["venue"]
        key = hashlib.sha256(f"{source['id']}|{day}|{title}|{href}".encode()).hexdigest()[:24]
        rows.append(dict(id=key,title=title,date=day,venue=venue,area=source["area"],price=None,workIds=[],mood="",sourceId=source["id"],sourceUrl=href))
    if not rows:
        raise ValueError("No valid future events; verify selectors")
    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT/"scripts/sources.json")
    args = parser.parse_args()
    sources = read(args.config)
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
            combined.extend(row for row in previous if row.get("sourceId")==source["id"] and row["date"]>=dt.date.today().isoformat())
    if not successes:
        raise SystemExit("No successful sources; existing snapshot preserved")
    unique = {row["id"]: row for row in combined}
    rows = sorted(unique.values(), key=lambda r:(r["date"],r["title"]))
    filename = dt.date.today().isoformat()+".json"
    write(OUT/filename, rows)
    write(OUT/"latest.json", dict(file=filename,sample=False,concertCount=len(rows),updatedAt=dt.datetime.now(dt.timezone.utc).isoformat()))
if __name__ == "__main__":
    main()
