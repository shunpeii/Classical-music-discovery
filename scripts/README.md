# Daily scraping

Install: `python -m pip install -r scripts/requirements.txt`.
Run: `python scripts/scrape.py`.

Sources are deliberately empty until terms, robots.txt and actual HTML selectors are verified. Each source requires id, url, approved, item, title, date, link, venue and area. CSS selectors must be verified against the actual site. A failed source retains its previous future events. If every source fails, the current snapshot is preserved. No demo events are carried into a real snapshot. Schedule on a local machine using cron or Task Scheduler after verification.
