"""Extract candidate concerts without publishing unreviewed data."""
import datetime as dt
import json
import re
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from validate_nhk import AGENT, AREAS, ROOT, composer_ids, expand_program, match


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


def program_lines(detail):
    for heading in detail.find_all(["h2", "h3", "h4", "dt", "th"]):
        if heading.get_text(strip=True) not in {"曲目", "演奏曲目", "プログラム", "主な演目", "予定曲目"}:
            continue
        sibling = heading.find_next_sibling() or heading.parent.find_next_sibling()
        if sibling:
            lines = sibling.get_text("\n", strip=True).splitlines()
            if lines:
                return lines
    return []


def html_rows(url, item, date, title, venue, link, program, fixed_venue="", time_selector=""):
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
        time = re.search(r"\d{1,2}:\d{2}", value(node, time_selector) if time_selector else raw_date)
        songs = node.select(program) if program else []
        lines = [line.strip() for song in songs for line in song.get_text("\n", strip=True).splitlines() if line.strip()]
        if not lines and fixed_venue:
            try:
                lines = program_lines(BeautifulSoup(fetch(urljoin(url, anchor["href"])).text, "html.parser"))
            except (requests.RequestException, ValueError):
                pass
        yield {"title": name, "date": day, "time": time.group() if time else "",
               "venue": fixed_venue or value(node, venue),
               "sourceUrl": urljoin(url, anchor["href"]),
               "program": lines}


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


def detail_rows(kind):
    base = "https://www.kanaphil.or.jp/" if kind == "kanaphil" else "https://www.geigeki.jp/"
    soup = BeautifulSoup(fetch(base).text, "html.parser")
    selector = ".concert-list__item a[href]" if kind == "kanaphil" else 'a[href*="/performance/concert"]'
    links = {}
    for anchor in soup.select(selector):
        url = urljoin(base, anchor["href"])
        if urlparse(url).netloc == urlparse(base).netloc:
            links[url] = anchor
    for url, anchor in list(links.items())[:12]:
        try:
            detail = BeautifulSoup(fetch(url).text, "html.parser")
        except (requests.RequestException, ValueError):
            continue
        if kind == "kanaphil":
            title = value(anchor, ".concert-list__ttl")
            date = value(detail, ".concert__date")
            text = detail.get_text(" ", strip=True)
            timing = re.search(r"開演時間\s*(\d{1,2}:\d{2})", text)
            place = re.search(r"公演場所\s*(.+?)(?=\s*(?:指揮者|共演者|出演者|主な演目|チケットを購入|料金))", text)
            venue = place.group(1).strip() if place else ""
            songs = [n.get_text(" ", strip=True) for n in anchor.select(".concert-list__programs span")]
        else:
            title = value(detail, "title")
            fields = {n.get_text(" ", strip=True): n.find_next_sibling("dd").get_text(" ", strip=True)
                      for n in detail.select(".p-performance-titles__data dt") if n.find_next_sibling("dd")}
            date = fields.get("日程", "")
            if len(re.findall(r"20\d{2}\s*年", date)) != 1 or re.search(r"[～〜－]|全\d+回", date):
                continue
            timing = re.search(r"(\d{1,2}:\d{2})\s*開演", date)
            venue = "東京芸術劇場 " + fields["会場"] if fields.get("会場") else ""
            songs = program_lines(detail)
        found = re.search(r"(20\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", date)
        if not found or "中止" in title:
            continue
        try:
            day = dt.date(*map(int, found.groups())).isoformat()
        except ValueError:
            continue
        yield {"title": title, "date": day, "time": timing.group(1) if timing else "",
               "venue": venue, "sourceUrl": url, "program": songs}


def cityphil():
    base = "https://www.cityphil.jp/concert/"
    soup = BeautifulSoup(fetch(base).text, "html.parser")
    home = BeautifulSoup(fetch("https://www.cityphil.jp/").text, "html.parser")
    links = dict.fromkeys(urljoin(base, a["href"]).split("&")[0] for a in home.select('a[href*="detail.php?id="]') + soup.select('a[href*="detail.php?id="]')
                          if urlparse(urljoin(base, a["href"])).path == "/concert/detail.php"
                          and urlparse(urljoin(base, a["href"])).netloc == urlparse(base).netloc)
    for url in list(links)[:20]:
        try:
            detail = BeautifulSoup(fetch(url).text, "html.parser")
        except (requests.RequestException, ValueError):
            continue
        title = value(detail, "title").split("｜")[0]
        if "中止" in title:
            continue
        body = detail.get_text(" ", strip=True)
        date = re.search(r"(20\d{2})\s*/\s*(\d{1,2})\s*/\s*(\d{1,2})\s*[（(][^）)]*[）)]\s*(\d{1,2}:\d{2})\s*開演", body)
        venue = re.search(r"会場[：:]\s*(.+?)\s*(?=>?会場アクセス|>座席表)", body)
        if not date or not venue:
            continue
        try:
            day = dt.date(*map(int, date.groups()[:3])).isoformat()
        except ValueError:
            continue
        songs = program_lines(detail)
        yield {"title": title, "date": day, "time": date.group(4), "venue": venue.group(1).strip(),
               "sourceUrl": url, "program": songs}


def yomikyo():
    base = "https://yomikyo.or.jp/concert/"
    pending = [base]
    seen = set()
    for page in pending:
        if len(seen) >= 24:
            break
        if page in seen:
            continue
        seen.add(page)
        try:
            soup = BeautifulSoup(fetch(page).text, "html.parser")
        except (requests.RequestException, ValueError):
            continue
        for anchor in soup.select("a[href]"):
            url = urljoin(base, anchor["href"]).split("#")[0]
            if urlparse(url).netloc == urlparse(base).netloc and re.fullmatch(r"/concert/20\d{2}/\d{2}/[^/]+\.php", urlparse(url).path) and url not in pending:
                pending.append(url)
        title = value(soup, "title").split(" | ")[0]
        if page == base or "中止" in title:
            continue
        body = soup.get_text(" ", strip=True)
        event = re.search(r"Concert\s+" + re.escape(title) + r"\s+(20\d{2})\s+(\d{1,2})\.(\d{1,2})\s*[〈＜][^〉＞]+[〉＞]\s*(\d{1,2}:\d{2})\s+(.+?)(?=\s+(?:指揮|出演|ピアノ|ヴァイオリン|チェロ)[＝=:：])", body)
        if not event:
            continue
        try:
            day = dt.date(*map(int, event.groups()[:3])).isoformat()
        except ValueError:
            continue
        program = body[event.end():].split("【発売日】")[0]
        songs = [line for n in soup.find_all(["p", "li"])
                 if n.get_text(" ", strip=True) in program
                 for line in n.get_text("\n", strip=True).splitlines() if "：" in line or ":" in line]
        yield {"title": title, "date": day, "time": event.group(4), "venue": event.group(5).strip(),
               "sourceUrl": page, "program": songs}


def main():
    master = ROOT / "public/data/master"
    composers = json.loads((master / "composers.json").read_text(encoding="utf-8"))
    works = json.loads((master / "works.json").read_text(encoding="utf-8"))
    today = dt.datetime.now(ZoneInfo("Asia/Tokyo")).date()
    AREAS.update({"日生劇場": "東京", "ドイツ文化会館OAGホール": "東京", "S＆D秋川キララホール": "東京"})
    AREAS.update({"綾瀬市オーエンス文化会館": "神奈川", "横浜美術館": "神奈川", "神奈川県民ホール": "神奈川", "神奈川県立音楽堂": "神奈川"})
    AREAS.update({"東京オペラシティ": "東京", "豊洲シビックセンター": "東京", "ミューザ川崎": "神奈川", "ティアラこうとう": "東京"})
    sources = {
        "yomikyo": yomikyo,
        "tokyosymphony": lambda: html_rows("https://tokyosymphony.jp/concert/", ".concertslist__box", ".concertslist__contents-date", ".concertslist__contents-title", ".concertslist__contents-location", "a.concertslist__box-link", ".concertslist__program-items", time_selector=".concertslist__contents-time"),
        "cityphil": cityphil,
        "kanaphil": lambda: detail_rows("kanaphil"),
        "geigeki": lambda: detail_rows("geigeki"),
        "njp": lambda: html_rows("https://www.njp.or.jp/concerts/", "div:has(> .--title):has(> .--date)", ".--date", ".--title", ".--place", "a.--detail", ".program__list"),
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
                row["program"] = expand_program(row["program"], composers)
                row["workIds"] = sorted({w for song in row["program"] if (w := match(song, composers, works))})
                row["composerIds"] = composer_ids(row["program"], composers, works, row["workIds"])
                rows[(row["date"], row["time"], row["title"], venue)] = row
            reports[source] = {"normalizedCount": len(rows), "incompleteCount": incomplete,
                               "missingProgramCount": sum(not row["program"] for row in rows.values()),
                               "unmatchedSongs": sorted({song for row in rows.values() for song in row["program"] if not match(song, composers, works)}),
                               "matchedConcertCount": sum(bool(row["workIds"]) for row in rows.values()),
                               "composerMatchedConcertCount": sum(bool(row["composerIds"]) for row in rows.values()),
                               "rows": list(rows.values())}
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            reports[source] = {"error": str(exc), "normalizedCount": 0}
    path = ROOT / "scripts/diagnostics/sites-validation.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    print({source: report["normalizedCount"] for source, report in reports.items()})


if __name__ == "__main__":
    main()
