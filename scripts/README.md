# Daily scraping

Install: `python -m pip install -r scripts/requirements.txt`.
Run: `python scripts/scrape.py`.

Sources are deliberately empty until terms, robots.txt and actual HTML selectors are verified. Each source requires id, url, approved, item, title, date, link, venue and area. CSS selectors must be verified against the actual site. A failed source retains its previous future events. If every source fails, the current snapshot is preserved. No demo events are carried into a real snapshot. Schedule on a local machine using cron or Task Scheduler after verification.

## Extraction configuration

Set methods to an ordered list of jsonld, css, api, rss. JSON-LD reads Event/MusicEvent. CSS uses selectors.item and field selectors (string or {css,attr}). API uses itemsPath and fields mapping to dotted keys. RSS uses fields mapping to selectors; date must be an actual event date, not publication date. Each source must supply area and venue defaults if not extracted. Use the final URL without redirects. Only approve sources after checking actual extraction and access conditions. No browser automation or custom adapter is enabled yet.

Run tests: python -m unittest discover -s scripts -p 'test_*.py'.
