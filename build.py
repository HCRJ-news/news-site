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
CASES = ROOT / "data" / "cases.json"
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


CASE_META = json.loads(CASES.read_text()) if CASES.exists() else {}


def load():
    items = json.loads(DATA.read_text())
    for it in items:
        it["_date"] = date.fromisoformat(it["date"])
        it["_inst_slug"] = slugify(it["institution"])
    items.sort(key=lambda i: (i["_date"], i.get("added", "")), reverse=True)
    return items


def jsonld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>"


ORG = {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL + "/",
       "description": TAGLINE}


def page(title, body, *, description=TAGLINE, path="/", extra_head="", full_title=None, og_type="website"):
    full_title = full_title or (f"{title} | {SITE_NAME}" if title != SITE_NAME else SITE_NAME)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{SITE_URL}{path}">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="/feed.xml">
<link rel="preload" href="/public-sans-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/style.css">
<script src="/src.js" defer></script>
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{SITE_URL}{path}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:image" content="{SITE_URL}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
{extra_head}
</head>
<body>
<a class="skip" href="#main">Skip to the list</a>
<header class="site-head">
  <a class="brand" href="/">{SITE_NAME}</a>
  <nav>
    <a href="/guides/">Get help</a>
    <a href="/cases/">Major cases</a>
    <a href="/institutions/">Institutions</a>
    <a href="/attorneys/">Attorneys</a>
    <a href="/about/">About &amp; standards</a>
    <a href="/report/">Report</a>
    <a href="/feed.xml">RSS</a>
  </nav>
</header>
<aside class="report-band" aria-label="Report anonymously">
  <p><strong>Experienced abuse at a company, school, church or agency?</strong>
  You can tell the Hollywood Council for Restorative Justice what happened, anonymously.</p>
  <a class="report-btn" href="/report/">Report anonymously</a>
</aside>
{body}
<footer class="site-foot">
  <p>Every entry links to the original reporting. Summaries are written by this site; allegations are
  described as allegations until a court or prosecutor says otherwise.</p>
  <p>If you need support, the <a href="https://rainn.org">RAINN National Sexual Assault Hotline</a>
  is available 24/7 at 800-656-4673.</p>
  <p><a href="/guides/sexual-assault/">Sexual assault</a> · <a href="/guides/rape/">What to do after a rape</a> ·
  <a href="/guides/sexual-harassment-lawyer/">Finding a sexual harassment lawyer</a> · <a href="/report/">Report anonymously</a></p>
  <p><a href="/about/#corrections">Request a correction or removal</a></p>
</footer>
</body>
</html>
"""


def entry_html(it, show_institution=True, show_case=True):
    cat = it["category"]
    status = it.get("status", "allegation")
    inst = ""
    if show_institution:
        inst = (f'<a class="inst" href="/institutions/{it["_inst_slug"]}/">'
                f'{esc(it["institution"])}</a>')
    loc = f'<span class="loc">{esc(it["location"])}</span>' if it.get("location") else ""
    case = ""
    if show_case and it.get("case") and it["case"] in CASE_META:
        case = f'<a class="case" href="/cases/{it["case"]}/">{esc(CASE_META[it["case"]]["title"])}</a>'

    search_blob = " ".join([it["title"], it["institution"], it["summary"],
                            it["source"], it.get("location", ""),
                            STATUSES.get(status, status), CATEGORIES.get(cat, ""),
                            CASE_META.get(it.get("case", ""), {}).get("title", "")]).lower()
    return f"""<li class="entry cat-{cat}" data-cat="{cat}" data-status="{status}" data-q="{esc(search_blob)}">
  <time datetime="{it['date']}">{fmt_date(it['_date'])}</time>
  <div class="body">
    <h3><a href="{esc(it['url'])}" rel="noopener nofollow" target="_blank">{esc(it['title'])}</a></h3>
    <p class="summary">{esc(it['summary'])}</p>
    <p class="meta"><span class="status s-{status}">{STATUSES.get(status, status.title())}</span>
      {inst}{case}{loc}<span class="src">Reported by {esc(it['source'])}</span></p>
  </div>
</li>"""


def grouped_list(items, show_institution=True, show_case=True, year_only=False):
    out, current = [], None
    for it in items:
        month = it["_date"].strftime("%Y" if year_only else "%B %Y")
        if month != current:
            if current is not None:
                out.append("</ol></section>")
            out.append(f'<section class="month"><h2>{month}</h2><ol class="entries">')
            current = month
        out.append(entry_html(it, show_institution, show_case))
    if current is not None:
        out.append("</ol></section>")
    return "\n".join(out)


def logo_wall(items):
    """Left menu: logos of institutions at the center of each major case, linking to the case timeline."""
    by_case = defaultdict(lambda: defaultdict(int))
    for it in items:
        if it.get("case") in CASE_META:
            by_case[it["case"]][it["institution"]] += 1
    inst_cat = {it["institution"]: it["category"] for it in items}
    rank = {"company": 0, "school": 1, "religious": 2, "government": 3}
    cands = []
    for case, insts in by_case.items():
        for inst, n in insts.items():
            cands.append((rank.get(inst_cat.get(inst), 4), -n, inst, case))
    seen, tiles = set(), []
    for _, _, inst, case in sorted(cands):
        slug = slugify(inst)
        if slug in seen or not (ROOT / "logos" / f"{slug}.png").exists():
            continue
        seen.add(slug)
        title = CASE_META[case]["title"]
        tiles.append(f'<a class="logo" href="/cases/{case}/" title="{esc(inst)}: {esc(title)}">'
                     f'<img src="/logos/{slug}.png" alt="{esc(inst)}" width="64" height="64" loading="lazy"></a>')
    return f"""<aside class="wall" aria-label="Major cases by institution">
  <h2>Major cases</h2>
  <p>Organizations at the center of the biggest sexual abuse cases. Select a logo for the full history.</p>
  <div class="tiles">{''.join(tiles)}</div>
  <a class="all" href="/cases/">All major cases</a>
</aside>"""


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
    featured = ""
    for slug, meta in CASE_META.items():
        if not meta.get("featured"):
            continue
        its = [i for i in items if i.get("case") == slug]
        if not its:
            continue
        latest = its[:3]
        lis = "".join(f'<li><time datetime="{i["date"]}">{fmt_date(i["_date"])}</time> '
                      f'<a href="{esc(i["url"])}" rel="noopener nofollow" target="_blank">{esc(i["title"])}</a></li>'
                      for i in latest)
        featured += (f'<section class="featured"><p class="flag">{esc(meta["featured"])}</p>'
                     f'<h2><a href="/cases/{slug}/">{esc(meta["title"])}</a></h2>'
                     f'<p>{esc(meta["summary"])}</p><ul>{lis}</ul>'
                     f'<a class="more" href="/cases/{slug}/">Full timeline, {len(its)} developments</a></section>')
    body = f"""<main id="main">
<section class="intro">
  <h1>Sexual Abuse Litigation and Resources for Victims</h1>
  <p class="lede">{TAGLINE}</p>
  <form class="filters" role="search" onsubmit="return false">
    <label class="search"><span class="sr">Search</span>
      <input type="search" id="q" placeholder="Search by institution, place or keyword" autocomplete="off"></label>
    <label class="status-filter">Stage
      <select id="status"><option value="">Any stage</option>{status_opts}</select></label>
  </form>
  <p class="count" id="count" aria-live="polite"></p>
</section>
{featured}
<div class="with-wall">
{logo_wall(items)}
<div class="ledger" id="ledger">
{grouped_list(items)}
<p class="empty" id="empty" hidden>No entries match. Clear the search or pick a different stage.</p>
</div>
</div>
</main>
<script src="/filter.js" defer></script>"""
    ld = jsonld({"@context": "https://schema.org", "@graph": [
        {"@type": "WebSite", "name": SITE_NAME, "url": SITE_URL + "/", "description": TAGLINE},
        ORG,
        {"@type": "CollectionPage", "name": "Sexual Abuse Litigation and Resources for Victims", "url": SITE_URL + "/",
         "about": ["Sexual assault", "Rape", "Sexual harassment", "Sexual abuse lawsuits"]}]})
    return page(SITE_NAME, body, extra_head=ld,
                full_title="Sexual Assault, Rape & Sexual Harassment Lawsuits and Help for Victims | " + SITE_NAME)


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


def build_cases(items):
    by_case = defaultdict(list)
    for it in items:
        if it.get("case") in CASE_META:
            by_case[it["case"]].append(it)
    rows = []
    for slug, meta in sorted(CASE_META.items(), key=lambda kv: kv[1]["title"].lower()):
        its = sorted(by_case.get(slug, []), key=lambda i: i["_date"])
        if not its:
            continue
        span = f"{its[0]['_date'].year}" + (f"–{its[-1]['_date'].year}" if its[-1]['_date'].year != its[0]['_date'].year else "")
        body = f"""<main id="main">
<section class="intro narrow">
  <p class="crumb"><a href="/cases/">All major cases</a></p>
  <h1>{esc(meta['title'])}</h1>
  <p class="lede">{esc(meta['summary'])}</p>
  <p class="count">{len(its)} developments, {span}, oldest first.</p>
</section>
<div class="ledger timeline">{grouped_list(its, show_case=False, year_only=True)}</div>
</main>"""
        d = OUT / "cases" / slug
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(page(meta["title"], body, path=f"/cases/{slug}/", description=meta["summary"]))
        rows.append(f'<li><a href="/cases/{slug}/">{esc(meta["title"])}</a>'
                    f'<p>{esc(meta["summary"])}</p><span>{len(its)} developments · {span}</span></li>')
    body = f"""<main id="main">
<section class="intro narrow"><h1>Major cases</h1>
<p class="lede">The full history of the largest scandals, from first reports through criminal cases, civil
litigation and reforms. Each development links to the reporting at the time.</p></section>
<ul class="cases">{''.join(rows)}</ul>
</main>"""
    d = OUT / "cases"
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(page("Major cases", body, path="/cases/"))


def build_report():
    src = (ROOT / "report.html").read_text()
    d = OUT / "report"
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(page("Report anonymously", src, path="/report/",
        description="Anonymously and confidentially report sexual abuse or misconduct to the Hollywood Council for Restorative Justice.",
        extra_head='<script src="/report.js" defer></script><script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>'))


GUIDES = json.loads((ROOT / "data" / "guides.json").read_text())


def build_guides(items):
    today = date.today().isoformat()
    cards = []
    for slug, g in GUIDES.items():
        body_html = (ROOT / "guides" / f"{slug}.html").read_text()
        faq_html = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in g["faqs"])
        others = "".join(f'<li><a href="/guides/{o}/">{esc(GUIDES[o]["h1"])}</a></li>' for o in GUIDES if o != slug)
        body = f"""<main id="main">
<article class="guide">
  <p class="crumb"><a href="/guides/">Help and resources</a></p>
  <h1>{esc(g['h1'])}</h1>
  <p class="updated">Updated <time datetime="{today}">{fmt_date(date.today())}</time></p>
  {body_html}
  <h2>Frequently asked questions</h2>
  <div class="faqs">{faq_html}</div>
  <h2>More help</h2>
  <ul>{others}<li><a href="/report/">Report anonymously to the Hollywood Council for Restorative Justice</a></li></ul>
</article>
</main>"""
        ld = jsonld({"@context": "https://schema.org", "@graph": [
            {"@type": "Article", "headline": g["title"], "description": g["description"],
             "dateModified": today, "url": f"{SITE_URL}/guides/{slug}/", "publisher": ORG, "author": ORG},
            {"@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in g["faqs"]]}]})
        d = OUT / "guides" / slug
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(page(g["h1"], body, path=f"/guides/{slug}/", description=g["description"],
                                           extra_head=ld, full_title=g["title"], og_type="article"))
        cards.append(f'<li><a href="/guides/{slug}/">{esc(g["h1"])}</a><p>{esc(g["description"])}</p></li>')
    body = f"""<main id="main">
<section class="intro narrow"><h1>Help and resources for survivors</h1>
<p class="lede">Plain-language guides for people who have experienced sexual assault, rape or sexual harassment, including
what to do, where to get support, and how legal action works. If you're in danger, call 911. For confidential support, call
RAINN at 800-656-4673.</p></section>
<ul class="cases">{''.join(cards)}<li><a href="/report/">Report anonymously</a><p>Tell the Hollywood Council for Restorative Justice what happened, without giving your name.</p></li></ul>
</main>"""
    d = OUT / "guides"
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(page("Help and resources", body, path="/guides/",
        description="Guides for survivors of sexual assault, rape and sexual harassment: what to do, support, reporting, and legal options."))


ATTORNEYS = json.loads((ROOT / "data" / "attorneys.json").read_text()) if (ROOT / "data" / "attorneys.json").exists() else []


def build_attorneys():
    if not ATTORNEYS:
        return
    profiles, toc = [], []
    for a in ATTORNEYS:
        slug = slugify(a["name"])
        toc.append(f'<li><a href="#{slug}">{esc(a["name"])}</a></li>')
        cases = " ".join(f'<a class="case" href="/cases/{c}/">{esc(CASE_META[c]["title"])}</a>'
                         for c in a.get("cases", []) if c in CASE_META)
        rows = "".join(
            f'<li><span class="yr">{esc(o["year"])}</span><div><strong>{esc(o["institution"])}</strong>: '
            f'{esc(o["result"])}.<br><span class="role">{esc(o["role"])}.</span> '
            f'<a href="{esc(o["url"])}" rel="noopener nofollow" target="_blank">Reported by {esc(o["source"])}</a></div></li>'
            for o in sorted(a["outcomes"], key=lambda o: o["year"]))
        profiles.append(f"""<section class="attorney" id="{slug}">
  <h2>{esc(a['name'])}</h2>
  <p class="firm">{esc(a['firm'])} · {esc(a['base'])}</p>
  <p>{esc(a['summary'])}</p>
  <h3>Documented outcomes</h3>
  <ol class="outcomes">{rows}</ol>
  <p class="meta">{cases}</p>
</section>""")
    body = f"""<main id="main">
<section class="intro narrow">
  <h1>Survivors' attorneys behind major outcomes</h1>
  <p class="lede">Profiles of {len(ATTORNEYS)} lawyers who represented survivors in the largest institutional sexual abuse
  cases in this index, with the settlements and verdicts that news reporting credits to them.</p>
</section>
<div class="prose attorneys">
  <p class="note"><strong>How this list works.</strong> Lawyers are listed alphabetically, not ranked. Each outcome
  is included only when published reporting names the lawyer or their firm as counsel for survivors, and each links to
  that reporting. Most large settlements were negotiated by several firms together and shared among many survivors, so
  a dollar figure is the total for the case, not what one lawyer won or was paid. Past results do not predict future
  outcomes. No one paid to be included. This site is not a law firm, does not give legal advice and does not endorse or
  refer to any lawyer. To find an attorney, contact your state bar's lawyer referral service, or read our guide to
  <a href="/guides/sexual-harassment-lawyer/">finding a lawyer</a>.</p>
  <ul class="toc">{''.join(toc)}</ul>
  {''.join(profiles)}
  <p class="note">See something wrong or missing? Email
  <a href="mailto:corrections@sexabuselitigation.org">corrections@sexabuselitigation.org</a>.</p>
</div>
</main>"""
    d = OUT / "attorneys"
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(page("Survivors' attorneys", body, path="/attorneys/",
        description="Lawyers who represented survivors in major institutional sexual abuse cases, with the settlements and verdicts reporting credits to them.",
        full_title="Sexual Abuse Lawyers Behind Major Settlements and Verdicts | " + SITE_NAME))


def build_llms(items):
    cases = "\n".join(f"- [{m['title']}]({SITE_URL}/cases/{s}/): {m['summary']}" for s, m in CASE_META.items())
    guides = "\n".join(f"- [{g['h1']}]({SITE_URL}/guides/{s}/): {g['description']}" for s, g in GUIDES.items())
    txt = f"""# {SITE_NAME}

> {TAGLINE} {len(items)} entries, each summarizing and linking to original news reporting. Updated several times a day.

Editorial standards: allegations are described as allegations; survivors who are private individuals are never named.
This site is not a law firm and does not give legal advice. Confidential support: RAINN 800-656-4673.

## Guides for survivors
{guides}
- [Report anonymously]({SITE_URL}/report/): send a confidential report to the Hollywood Council for Restorative Justice.

## Major cases (full timelines)
{cases}

## Other
- [All institutions]({SITE_URL}/institutions/)
- [Survivors' attorneys behind major outcomes]({SITE_URL}/attorneys/)
- [About and editorial standards]({SITE_URL}/about/)
- [RSS feed]({SITE_URL}/feed.xml)
"""
    (OUT / "llms.txt").write_text(txt)


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
    urls = [f"{SITE_URL}/", f"{SITE_URL}/guides/", f"{SITE_URL}/report/", f"{SITE_URL}/institutions/", f"{SITE_URL}/cases/", f"{SITE_URL}/attorneys/", f"{SITE_URL}/about/"]
    urls += [f"{SITE_URL}/guides/{g}/" for g in GUIDES]
    urls += sorted({f"{SITE_URL}/institutions/{it['_inst_slug']}/" for it in items})
    urls += sorted({f"{SITE_URL}/cases/{it['case']}/" for it in items if it.get("case") in CASE_META})
    lm = date.today().isoformat()
    body = "".join(f"<url><loc>{u}</loc><lastmod>{lm}</lastmod></url>" for u in urls)
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>')
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for f in STATIC.iterdir():
        shutil.copy(f, OUT / f.name)
    if (ROOT / "logos").exists():
        shutil.copytree(ROOT / "logos", OUT / "logos")
    items = load()
    (OUT / "index.html").write_text(build_index(items))
    build_institutions(items)
    build_cases(items)
    build_about()
    build_attorneys()
    build_guides(items)
    build_llms(items)
    build_report()
    build_feed(items)
    build_sitemap(items)
    print(f"Built {len(items)} entries into {OUT}")


if __name__ == "__main__":
    main()
