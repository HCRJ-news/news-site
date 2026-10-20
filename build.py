#!/usr/bin/env python3
"""Builds the static site into ./public from data/articles.json.

No third-party dependencies, so Cloudflare Pages can run it with:
    build command:  python3 build.py
    output folder:  public
"""
import html
import json
import re
import shutil
from collections import defaultdict
from datetime import date, datetime, timezone
from email.utils import format_datetime
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "articles.json"
STATIC = ROOT / "static"
OUT = ROOT / "public"

SITE_NAME = "Sex Abuse Litigation"
SITE_URL = "https://www.sexabuselitigation.org"
TAGLINE = ("An index of news reporting on sexual abuse allegations, lawsuits, "
           "investigations and outcomes involving companies, schools, governments and religious organizations.")

CATEGORIES = {
    "company": "Companies",
    "school": "Schools",
    "government": "Governments",
    "religious": "Religious organizations",
}
STATUSES = {
    "allegation": "Allegation",
    "lawsuit": "Lawsuit filed",
    "investigation": "Investigation",
    "charges": "Criminal charges",
    "settlement": "Settlement",
    "verdict": "Verdict",
    "conviction": "Conviction",
    "legislation": "Legislation",
    "policy": "Policy change",
}

esc = html.escape


def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:80] or "unknown"


def fmt_date(d):
    return d.strftime("%b %-d, %Y")


def load():
    items = json.loads(DATA.read_text())
    for it in items:
        it["_date"] = date.fromisoformat(it["date"])
        it["_inst_slug"] = slugify(it["institution"])
    items.sort(key=lambda i: (i["_date"], i.get("added", "")), reverse=True)
    return items


def page(title, body, *, description=TAGLINE, path="/", extra_head=""):
    full_title = f"{title} | {SITE_NAME}" if title != SITE_NAME else SITE_NAME
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{SITE_URL}{path}">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Public+Sans:ital,wght@0,400;0,500;0,700;0,800;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
{extra_head}
</head>
<body>
<a class="skip" href="#main">Skip to the list</a>
<header class="site-head">
  <a class="brand" href="/">{SITE_NAME}</a>
  <nav>
    <a href="/institutions/">Institutions</a>
    <a href="/about/">About &amp; standards</a>
    <a href="/feed.xml">RSS</a>
  </nav>
</header>
{body}
<footer class="site-foot">
  <p>Every entry links to the original reporting. Summaries are written by this site; allegations are
  described as allegations until a court or prosecutor says otherwise.</p>
  <p>If you need support, the <a href="https://rainn.org">RAINN National Sexual Assault Hotline</a>
  is available 24/7 at 800-656-4673.</p>
  <p><a href="/about/#corrections">Request a correction or removal</a></p>
</footer>
</body>
</html>
"""


def entry_html(it, show_institution=True):
    cat = it["category"]
    status = it.get("status", "allegation")
    inst = ""
    if show_institution:
        inst = (f'<a class="inst" href="/institutions/{it["_inst_slug"]}/">'
                f'{esc(it["institution"])}</a>')
    loc = f'<span class="loc">{esc(it["location"])}</span>' if it.get("location") else ""
    search_blob = " ".join([it["title"], it["institution"], it["summary"],
                            it["source"], it.get("location", ""),
                            STATUSES.get(status, status), CATEGORIES.get(cat, "")]).lower()
    return f"""<li class="entry cat-{cat}" data-cat="{cat}" data-status="{status}" data-q="{esc(search_blob)}">
  <time datetime="{it['date']}">{fmt_date(it['_date'])}</time>
  <div class="body">
    <h3><a href="{esc(it['url'])}" rel="noopener nofollow" target="_blank">{esc(it['title'])}</a></h3>
    <p class="summary">{esc(it['summary'])}</p>
    <p class="meta"><span class="status s-{status}">{STATUSES.get(status, status.title())}</span>
      {inst}{loc}<span class="src">Reported by {esc(it['source'])}</span></p>
  </div>
</li>"""


def grouped_list(items, show_institution=True):
    out, current = [], None
    for it in items:
        month = it["_date"].strftime("%B %Y")
        if month != current:
            if current is not None:
                out.append("</ol></section>")
            out.append(f'<section class="month"><h2>{month}</h2><ol class="entries">')
            current = month
        out.append(entry_html(it, show_institution))
    if current is not None:
        out.append("</ol></section>")
    return "\n".join(out)


def build_index(items):
    counts = defaultdict(int)
    for it in items:
        counts[it["category"]] += 1
    chips = [f'<button type="button" class="chip" aria-pressed="true" data-filter="all">'
             f'All <span>{len(items)}</span></button>']
    for key, label in CATEGORIES.items():
        chips.append(f'<button type="button" class="chip" aria-pressed="false" data-filter="{key}">'
                     f'{label} <span>{counts[key]}</span></button>')
    status_opts = "".join(f'<option value="{k}">{v}</option>' for k, v in STATUSES.items())
    updated = fmt_date(items[0]["_date"]) if items else ""
    body = f"""<main id="main">
<section class="intro">
  <h1>Who knew, who was sued, and what happened next.</h1>
  <p class="lede">{TAGLINE} Latest entry {updated}.</p>
  <form class="filters" role="search" onsubmit="return false">
    <label class="search"><span class="sr">Search</span>
      <input type="search" id="q" placeholder="Search by institution, place or keyword" autocomplete="off"></label>
    <div class="chips" role="group" aria-label="Institution type">{''.join(chips)}</div>
    <label class="status-filter">Stage
      <select id="status"><option value="">Any stage</option>{status_opts}</select></label>
  </form>
  <p class="count" id="count" aria-live="polite"></p>
</section>
<div class="ledger" id="ledger">
{grouped_list(items)}
</div>
<p class="empty" id="empty" hidden>No entries match. Clear the search or pick a different stage.</p>
</main>
<script src="/filter.js" defer></script>"""
    return page(SITE_NAME, body)


def build_institutions(items):
    by_inst = defaultdict(list)
    for it in items:
        by_inst[it["_inst_slug"]].append(it)
    # individual pages
    for slug, its in by_inst.items():
        name = its[0]["institution"]
        cat = CATEGORIES[its[0]["category"]].rstrip("s").lower() if its[0]["category"] in CATEGORIES else ""
        body = f"""<main id="main">
<section class="intro narrow">
  <p class="crumb"><a href="/institutions/">All institutions</a></p>
  <h1>{esc(name)}</h1>
  <p class="lede">{len(its)} {'report' if len(its) == 1 else 'reports'} indexed, newest first.</p>
</section>
<div class="ledger">{grouped_list(its, show_institution=False)}</div>
</main>"""
        d = OUT / "institutions" / slug
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(page(name, body, path=f"/institutions/{slug}/",
                                           description=f"News reporting on sexual abuse cases involving {name}."))
    # directory
    sections = []
    for key, label in CATEGORIES.items():
        rows = sorted(((s, i) for s, i in by_inst.items() if i[0]["category"] == key),
                      key=lambda x: x[1][0]["institution"].lower())
        if not rows:
            continue
        lis = "".join(f'<li><a href="/institutions/{s}/">{esc(i[0]["institution"])}</a>'
                      f'<span>{len(i)}</span></li>' for s, i in rows)
        sections.append(f'<section class="dir cat-{key}"><h2>{label}</h2><ul>{lis}</ul></section>')
    body = f"""<main id="main">
<section class="intro narrow"><h1>Institutions</h1>
<p class="lede">Every organization named in the index, with the number of reports about it.</p></section>
<div class="dirs">{''.join(sections)}</div>
</main>"""
    d = OUT / "institutions"
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(page("Institutions", body, path="/institutions/"))


def build_about():
    src = (ROOT / "about.html").read_text()
    d = OUT / "about"
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(page("About & standards", src, path="/about/"))


def build_feed(items):
    now = format_datetime(datetime.now(timezone.utc))
    entries = []
    for it in items[:50]:
        pub = format_datetime(datetime.combine(it["_date"], datetime.min.time(), timezone.utc))
        entries.append(f"""<item><title>{esc(it['title'])}</title><link>{esc(it['url'])}</link>
<guid isPermaLink="false">{esc(it['url'])}</guid><pubDate>{pub}</pubDate>
<description>{esc(it['summary'] + ' (' + it['source'] + ')')}</description>
<category>{CATEGORIES.get(it['category'], '')}</category></item>""")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>{SITE_NAME}</title><link>{SITE_URL}/</link>
<description>{esc(TAGLINE)}</description><lastBuildDate>{now}</lastBuildDate>
{''.join(entries)}
</channel></rss>"""
    (OUT / "feed.xml").write_text(xml)


def build_sitemap(items):
    urls = [f"{SITE_URL}/", f"{SITE_URL}/institutions/", f"{SITE_URL}/about/"]
    urls += sorted({f"{SITE_URL}/institutions/{it['_inst_slug']}/" for it in items})
    body = "".join(f"<url><loc>{u}</loc></url>" for u in urls)
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>')
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for f in STATIC.iterdir():
        shutil.copy(f, OUT / f.name)
    items = load()
    (OUT / "index.html").write_text(build_index(items))
    build_institutions(items)
    build_about()
    build_feed(items)
    build_sitemap(items)
    print(f"Built {len(items)} entries into {OUT}")


if __name__ == "__main__":
    main()
