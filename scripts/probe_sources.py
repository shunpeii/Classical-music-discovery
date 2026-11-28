"""Inspect candidate sources without publishing data."""
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from extractors import jsonld

AGENT = "OpusConcertDiscovery/0.1"


def probe(source):
    url = source["url"]
    robots = requests.get(urljoin(url, "/robots.txt"), timeout=20)
    if robots.status_code != 404:
        robots.raise_for_status()
        parser = RobotFileParser()
        parser.parse(robots.text.splitlines())
        if not parser.can_fetch(AGENT, url):
            print("Blocked by robots.txt")
            return
    response = requests.get(url, headers={"User-Agent": AGENT}, timeout=25, allow_redirects=False)
    print("HTTP", response.status_code)
    if response.status_code != 200:
        return
    if response.encoding in (None, "ISO-8859-1"):
        response.encoding = response.apparent_encoding or "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")
    print("JSON-LD events:", len(list(jsonld(response.text))))
    print("Content-Type:", response.headers.get("Content-Type"))
    print("Response bytes:", len(response.content))
    print("Title:", soup.title.get_text(strip=True) if soup.title else "")
    print("Body preview:", soup.get_text(" ", strip=True)[:1500])
    print("Script sources:", [s.get("src") for s in soup.select("script[src]")][:30])
    print("Inline script types:", [s.get("type") for s in soup.select("script:not([src])")][:20])
    for link in soup.select("a[href]")[:60]:
        print("Link:", link.get_text(" ", strip=True)[:100], link.get("href"))
    for node in soup.select("time, [datetime], [data-date]")[:20]:
        print("Date element:", str(node)[:300])
    for heading in soup.select("h2,h3")[:20]:
        print("Heading:", heading.get_text(" ", strip=True)[:100])
        for parent in list(heading.parents)[:4]:
            print(" ", parent.name, parent.get("class", []))
    for node in soup.find_all(string=lambda s: s and "年" in s and "月" in s and "日" in s)[:12]:
        print("Date:", node.strip()[:100], node.parent.name, node.parent.get("class", []))


def main():
    sources = json.loads(Path(__file__).with_name("candidates.json").read_text())
    results = []
    for source in sources:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            try:
                probe(source)
            except (requests.RequestException, ValueError) as exc:
                print("Probe failed:", exc)
        output = buffer.getvalue()
        print(source["id"], output)
        results.append({"id": source["id"], "url": source["url"], "diagnostics": output})
    destination = Path(__file__).with_name("diagnostics") / "latest.json"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
