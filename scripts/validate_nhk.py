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
         "ミューザ川崎シンフォニーホール": "神奈川", "横浜みなとみらいホール": "神奈川", "パルテノン多摩": "東京",
         "市川市文化会館": "千葉", "所沢市民文化センター": "埼玉"}


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


ALIASES = {
    "グリーグ／ピアノ協奏曲 イ短調 作品16": "grieg-1",
    "シューベルト／交響曲 第7番 ロ短調 D. 759「未完成」": "schubert-1",
    "ストラヴィンスキー／バレエ音楽「春の祭典」": "stravinsky-1",
    "ストラヴィンスキー／組曲「プルチネッラ」": "stravinsky-6",
    "バッハ／マタイ受難曲 BWV 244": "bach-4",
    "ブラームス／ハイドンの主題による変奏曲 作品56a": "brahms-14",
    "ブラームス／大学祝典序曲 作品80": "brahms-12",
    "プロコフィエフ／古典交響曲 作品25": "prokofiev-2",
    "ベルリオーズ／幻想交響曲 作品14": "berlioz-1",
    "マーラー／リュッケルトによる5つの歌": "mahler-14",
    "メンデルスゾーン／ヴァイオリン協奏曲 ホ短調 作品64": "mendelssohn-1",
    "モーツァルト／歌劇「魔笛」序曲": "mozart-5",
    "ラヴェル／バレエ組曲「ダフニスとクロエ」第1番、第2番": "ravel-2",
    "ワーグナー／歌劇《タンホイザー》（全3幕／ドイツ語上演･日本語字幕付）": "wagner-1",
    "ワーグナー／歌劇「タンホイザー」─「おごそかなこの広間よ」◇": "wagner-1",
    "ワーグナー／楽劇「トリスタンとイゾルデ」─「愛の夜よ、とばりを降ろせ」◇◆": "wagner-2",
    "ワーグナー／歌劇「ローエングリン」─聖杯の物語「はるかな国に」◆": "wagner-5"
}


def match(song, composers, works):
    alias = ALIASES.get(song)
    if alias and any(w["id"] == alias for w in works):
        return alias
    parts = re.split(r"[／/：:]", song, maxsplit=1)
    if len(parts) != 2:
        return None
    author, title = map(key, parts)
    author_aliases = {"jsバッハ": "bach", "ヨハンセバスティアンバッハ": "bach",
                      "fメンデルスゾーン": "mendelssohn", "ドヴォルジャーク": "dvorak",
                      "ベルリオーズ": "berlioz", "jシュトラウスii世": "jstrauss",
                      "jシュトラウス2世": "jstrauss", "rシュトラウス": "rstrauss"}
    ids = {c["id"] for c in composers if key(c["name"]) == author}
    if author in author_aliases:
        ids.add(author_aliases[author])
    pool = [w for w in works if w["composerId"] in ids]
    exact = [w["id"] for w in pool if key(w["title"]) == title]
    if len(exact) == 1:
        return exact[0]
    # Remove only explicit trailing catalogue numbers and key signatures.
    simplified = re.sub(r"(?:作品|op|bwv|kv|k|wab|d)\d+[a-z]?$", "", title)
    simplified = re.sub(r"[イロハニホヘト](?:変|嬰)?[長短]調$", "", simplified)
    simplified = re.sub(r"(?:変|嬰)?[イロハニホヘト][長短]調$", "", simplified)
    exact = [w["id"] for w in pool if key(w["title"]) == simplified]
    if len(exact) == 1:
        return exact[0]
    numbered = re.match(r"(交響曲|ピアノ協奏曲|ヴァイオリン協奏曲|チェロ協奏曲|弦楽四重奏曲|ピアノソナタ)第(\d+)番", title)
    if numbered:
        prefix = numbered.group()
        candidates = [w["id"] for w in pool if key(w["title"]).startswith(prefix)]
        if len(candidates) == 1:
            return candidates[0]
    # Quoted distinctive titles can identify a parent work, but never guess
    # between multiple catalog entries.
    quoted = [key(q) for q in re.findall(r"[「『《](.*?)[」』》]", parts[1]) if len(key(q)) >= 3]
    candidates = [w["id"] for w in pool if any(q == key(w["title"]) or q in re.findall(r"[「『《](.*?)[」』》]", w["title"]) for q in quoted)]
    if len(candidates) == 1:
        return candidates[0]
    return None


def normalize(concerts, halls, composers, works, today):
    rows = {}
    unknown = set()
    unmatched = set()
    for event in concerts:
        if event.get("status") is not True:
            continue
        venue = clean(halls.get(str(event.get("hall_id")), {}).get("name"))
        area = next((area for name, area in AREAS.items() if venue == name or venue.startswith(name + " ")), None)
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
