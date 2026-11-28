"""Publish fresh adapter results, retaining previous rows for failed sources."""
import hashlib
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public/data/concerts"
DIAG = ROOT / "scripts/diagnostics"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def key(value):
    return re.sub(r"[^\w]", "", unicodedata.normalize("NFKC", value).casefold())


def identity(row):
    return tuple(key(str(row.get(field) or "")) for field in ("date", "time", "venue", "title"))


def merge(rows):
    result = {}
    for row in rows:
        k = identity(row)
        if k not in result:
            result[k] = dict(row)
            continue
        old = result[k]
        for field in ("workIds", "composerIds", "program"):
            old[field] = list(dict.fromkeys(old.get(field, []) + row.get(field, [])))
    return sorted(result.values(), key=lambda r: (r["date"], r.get("time") or "", r["title"]))


def main():
    today = datetime.now(ZoneInfo("Asia/Tokyo")).date().isoformat()
    previous = read(PUBLIC / read(PUBLIC / "latest.json")["file"])
    reports = read(DIAG / "sites-validation.json")
    reports["nhk"] = read(DIAG / "nhk-validation.json")
    rows = []
    successful = 0
    old_ids = {identity(r): r["id"] for r in previous}
    for source, report in reports.items():
        old = [r for r in previous if r.get("sourceId") == source and r["date"] >= today]
        fresh = report.get("rows", [])
        if report.get("error") or not fresh or len(fresh) < len(old) / 2:
            print(f"Warning: retaining {len(old)} previous rows for {source}")
            rows.extend(old)
            continue
        successful += 1
        for row in fresh:
            if row["date"] < today or re.search(r"公演中止|開催中止|中止のお知らせ", row["title"]):
                continue
            k = identity(row)
            row.update(sourceId=source, id=old_ids.get(k) or "concert-" + hashlib.sha256("|".join(k).encode()).hexdigest()[:20],
                       price=None, mood="")
            rows.append(row)
    if not successful:
        raise RuntimeError("No healthy sources; public snapshot unchanged")
    data = merge(rows)
    if not data:
        raise RuntimeError("Empty snapshot; public snapshot unchanged")
    filename = today + "-monthly.json"
    (PUBLIC / filename).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (PUBLIC / "latest.json").write_text(json.dumps({"file": filename, "sample": False, "concertCount": len(data),
        "updatedAt": today, "method": "monthly official-source extraction"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Published {len(data)} concerts from {successful} healthy sources")


if __name__ == "__main__":
    main()
