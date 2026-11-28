"""Inspect candidate sources without publishing data."""
import json
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
    soup = BeautifulSoup(response.text, "html.parser")
    print("JSON-LD events:", len(list(jsonld(response.text))))
    for heading in soup.select("h2,h3")[:20]:
        print("Heading:", heading.get_text(" ", strip=True)[:100])
        for parent in list(heading.parents)[:4]:
            print(" ", parent.name, parent.get("class", []))
    for node in soup.find_all(string=lambda s: s and "年" in s and "月" in s and "日" in s)[:12]:
        print("Date:", node.strip()[:100], node.parent.name, node.parent.get("class", []))


def main():
    sources = json.loads(Path(__file__).with_name("candidates.json").read_text())
    for source in sources:
        print("\nSource:", source["id"], source["url"])
        try:
            probe(source)
        except (requests.RequestException, ValueError) as exc:
            print("Probe failed:", exc)


if __name__ == "__main__":
    main()
