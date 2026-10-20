# sexabuselitigation.org

Static news index. Entries live in `data/articles.json`; `python3 build.py` renders the site into `public/`.

- Cloudflare Pages: build command `python3 build.py`, output directory `public`.
- Add entries: `python3 scripts/add_articles.py new.json` (dedupes by URL, validates fields).
- Editorial rules: see `about.html`.
