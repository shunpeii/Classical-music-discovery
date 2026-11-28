"""Inspect candidate sources without publishing data."""
import io
import json
import re
from contextlib import redirect_stdout
from pathlib import Path
from urllib.parse import urljoin, urlparse
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
    if source.get("format") == "json":
        payload = response.json()
        print("JSON root type:", type(payload).__name__)
        if isinstance(payload, dict):
            print("JSON keys:", list(payload))
            for key, value in payload.items():
                print("Field:", key, type(value).__name__, str(value)[:2500])
        elif isinstance(payload, list):
            print("JSON count:", len(payload))
            print("JSON sample:", json.dumps(payload[:2], ensure_ascii=False)[:5000])
        return
    soup = BeautifulSoup(response.text, "html.parser")
    print("JSON-LD events:", len(list(jsonld(response.text))))
    print("Content-Type:", response.headers.get("Content-Type"))
    print("Response bytes:", len(response.content))
    print("Title:", soup.title.get_text(strip=True) if soup.title else "")
    print("Body preview:", soup.get_text(" ", strip=True)[:1500])
    print("Script sources:", [s.get("src") for s in soup.select("script[src]")][:30])
    print("Inline script types:", [s.get("type") for s in soup.select("script:not([src])")][:20])
    # Inspect only same-origin, robots-permitted public scripts.
    for script in soup.select("script[src]"):
        script_url = urljoin(url, script["src"])
        if urlparse(script_url).netloc != urlparse(url).netloc:
            continue
        if "/lib/" in script_url or robots.status_code != 404 and not parser.can_fetch(AGENT, script_url):
            continue
        try:
            js = requests.get(script_url, headers={"User-Agent": AGENT}, timeout=20, allow_redirects=False)
            if js.status_code != 200:
                continue
            for match in list(re.finditer(r"fetch\s*\(|ajax\s*\(|getJSON\s*\(|\.json\b|/api/|\.php\b", js.text, re.IGNORECASE))[:35]:
                print("JS candidate:", script_url, js.text[max(0, match.start()-100):match.end()+150])
        except requests.RequestException as exc:
            print("Script probe failed:", exc)
    for script in soup.select("script:not([src]):not([type])"):
        print("Inline JS:", script.get_text()[:2500])
    for link in soup.select("main a[href], #main a[href]")[:60]:
        print("Main link:", link.get_text(" ", strip=True)[:120], link.get("href"))
    for link in soup.select("a[href]")[:60]:
        print("Link:", link.get_text(" ", strip=True)[:100], link.get("href"))
    # Capture nearby event markup so selectors can be derived in one pass.
    seen = set()
    for node in soup.find_all(string=re.compile(r"20\d{2}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日")):
        if node.parent.name in ("script", "style"):
            continue
        for parent in list(node.parents)[1:6]:
            if parent.name in ("body", "html"):
                break
            if not parent.select_one("a[href]"):
                continue
            markup = str(parent)
            if len(markup) > 18000:
                break
            if markup not in seen:
                seen.add(markup)
                print("Event markup:", markup[:6500])
            break
        if len(seen) >= 8:
            break
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
