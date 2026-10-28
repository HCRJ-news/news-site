"""Statute of limitations guide: /guides/statute-of-limitations/ plus one page per state.
Data: data/sol.json = {"verified": "YYYY-MM-DD", "states": [{state, code, adult_civil, child_civil, window,
criminal_adult, criminal_child, recent_change, confidence, notes, sources}]}"""
import json
import re
from datetime import date
from html import escape as esc

HUB = "statute-of-limitations"
TITLE = "Sexual Abuse Statute of Limitations by State (2026): Deadlines to Sue or Press Charges"
H1 = "Sexual abuse statutes of limitations, state by state"
DESC = ("The deadlines to file a lawsuit or criminal charges for sexual assault, rape and childhood sexual abuse in all 50 "
        "states and DC, including lookback windows that revive older claims. Updated for 2026.")

DISCLAIMER = """<p class="disclaimer"><strong>This is general information, not legal advice.</strong> Deadlines depend on the
facts: when the abuse happened, the survivor's age, when the harm was discovered, and who is being sued. Laws also change
often. Sex Abuse Litigation is not a law firm. Talk to a licensed attorney in your state before relying on any deadline here,
and act quickly, because some deadlines are short.</p>"""


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def load(root):
    p = root / "data" / "sol.json"
    if not p.exists():
        return None
    return json.loads(p.read_text())


def _sources(st):
    out = []
    for u in st.get("sources", [])[:4]:
        host = re.sub(r"^www\.", "", u.split("/")[2]) if "//" in u else u
        out.append(f'<li><a href="{esc(u)}" rel="nofollow noopener">{esc(host)}</a></li>')
    return "".join(out)


def _faqs(st):
    n = st["state"]
    return [
        (f"What is the statute of limitations for childhood sexual abuse in {n}?", st["child_civil"]),
        (f"How long do adult survivors of sexual assault have to sue in {n}?", st["adult_civil"]),
        (f"Does {n} have a lookback window for expired sexual abuse claims?", st["window"]),
        (f"Is there a time limit to press criminal charges for rape in {n}?", st["criminal_adult"]),
    ]


def build(root, out, page, jsonld, org, site_url, fmt_date, guides):
    data = load(root)
    if not data:
        return []
    verified = date.fromisoformat(data["verified"])
    states = sorted(data["states"], key=lambda s: s["state"])
    for s in states:
        s["slug"] = slugify(s["state"])
    urls = [f"{site_url}/guides/{HUB}/"]
    more = "".join(f'<li><a href="/guides/{g}/">{esc(v["h1"])}</a></li>' for g, v in guides.items())

    # ---- state pages
    for i, s in enumerate(states):
        n = s["state"]
        path = f"/guides/{HUB}/{s['slug']}/"
        faqs = _faqs(s)
        prev_s, next_s = states[i - 1], states[(i + 1) % len(states)]
        rows = [("Childhood sexual abuse (civil lawsuit)", s["child_civil"]),
                ("Adult sexual assault (civil lawsuit)", s["adult_civil"]),
                ("Lookback or revival window", s["window"]),
                ("Criminal charges: rape or sexual assault of an adult", s["criminal_adult"]),
                ("Criminal charges: sex crimes against children", s["criminal_child"])]
        table = "".join(f"<tr><th scope=\"row\">{esc(k)}</th><td>{esc(v)}</td></tr>" for k, v in rows)
        change = f"<p><strong>Recent change:</strong> {esc(s['recent_change'])}</p>" if s.get("recent_change") else ""
        caveat = ""
        if s.get("confidence") != "high" and s.get("notes"):
            caveat = f'<p class="caveat"><strong>Note:</strong> {esc(s["notes"])}</p>'
        elif s.get("notes"):
            caveat = f'<p class="caveat">{esc(s["notes"])}</p>'
        faq_html = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in faqs)
        body = f"""<main id="main">
<article class="guide sol">
  <p class="crumb"><a href="/guides/">Help and resources</a> › <a href="/guides/{HUB}/">Statutes of limitations</a></p>
  <h1>{esc(n)} sexual abuse statute of limitations</h1>
  <p class="updated">Last checked <time datetime="{verified.isoformat()}">{fmt_date(verified)}</time></p>
  <p class="answer"><strong>Childhood abuse:</strong> {esc(s['child_civil'])}<br><strong>Adult survivors:</strong> {esc(s['adult_civil'])}</p>
  <table class="sol-table"><tbody>{table}</tbody></table>
  {change}
  {caveat}
  {DISCLAIMER}
  <h2>Claims against institutions</h2>
  <p>Many lawsuits are brought not only against the abuser but against the school, church, employer, youth program or
  agency that allowed the abuse or covered it up. In some states the deadline or the damages differ for claims against an
  institution or a public entity, and claims against government agencies often require a formal notice within months.
  Federal claims, such as Title IX claims against schools, have their own deadlines.</p>
  <h2>Frequently asked questions</h2>
  <div class="faqs">{faq_html}</div>
  <h2>Sources</h2>
  <ul class="sources">{_sources(s)}</ul>
  <h2>Get help</h2>
  <ul>
    <li>Free, confidential support 24/7: RAINN at <a href="tel:18006564673">800-656-4673</a></li>
    <li>Find an attorney through the {esc(n)} state bar's lawyer referral service, or read our guide to <a href="/guides/sexual-harassment-lawyer/">finding a lawyer</a></li>
    <li><a href="/report/">Report anonymously</a> to the Hollywood Council for Restorative Justice</li>
  </ul>
  <p class="pager"><a href="/guides/{HUB}/{prev_s['slug']}/">← {esc(prev_s['state'])}</a>
  <a href="/guides/{HUB}/">All states</a>
  <a href="/guides/{HUB}/{next_s['slug']}/">{esc(next_s['state'])} →</a></p>
</article>
</main>"""
        ld = jsonld({"@context": "https://schema.org", "@graph": [
            {"@type": "Article", "headline": f"{n} Sexual Abuse Statute of Limitations",
             "dateModified": verified.isoformat(), "url": site_url + path, "publisher": org, "author": org,
             "about": {"@type": "State", "name": n}},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Help and resources", "item": f"{site_url}/guides/"},
                {"@type": "ListItem", "position": 2, "name": "Statutes of limitations", "item": f"{site_url}/guides/{HUB}/"},
                {"@type": "ListItem", "position": 3, "name": n, "item": site_url + path}]},
            {"@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}]})
        d = out / "guides" / HUB / s["slug"]
        d.mkdir(parents=True, exist_ok=True)
        desc = f"{n}: {s['child_civil']} Adult survivors: {s['adult_civil']}"
        (d / "index.html").write_text(page(f"{n} sexual abuse statute of limitations", body, path=path,
            description=desc[:300], extra_head=ld, og_type="article",
            full_title=f"{n} Sexual Abuse & Assault Statute of Limitations (2026) | Sex Abuse Litigation"))
        urls.append(site_url + path)

    # ---- hub
    rows = "".join(
        f'<tr data-q="{esc(s["state"].lower())} {s["code"].lower()}"><th scope="row"><a href="/guides/{HUB}/{s["slug"]}/">{esc(s["state"])}</a></th>'
        f'<td>{esc(s["child_civil"])}</td><td>{esc(s["adult_civil"])}</td><td>{esc(s["window"])}</td></tr>' for s in states)
    open_windows = [s for s in states if re.search(r"\bopen\b|\bcurrently\b|\bthrough 20(2[6-9]|3)", s["window"], re.I)
                    and not re.search(r"closed|expired|struck", s["window"], re.I)]
    ow = ""
    if open_windows:
        ow = ("<h2>Lookback windows that may be open now</h2><p>These states have a window that, as of our last check, "
              "may allow survivors to file claims that were previously too old. Windows close on fixed dates.</p><ul>" +
              "".join(f'<li><a href="/guides/{HUB}/{s["slug"]}/">{esc(s["state"])}</a>: {esc(s["window"])}</li>' for s in open_windows) +
              "</ul>")
    hub_faqs = [
        ("What is a statute of limitations for sexual abuse?",
         "It is the legal deadline to file a lawsuit or bring criminal charges. After it passes, a claim is usually barred, unless the law extends it, pauses it, or a lookback window revives it."),
        ("Is there a time limit to sue for childhood sexual abuse?",
         "It depends on the state. Many states now allow claims until the survivor reaches age 40, 50 or 55, or measure the deadline from when the survivor discovered the harm, and several have eliminated the limit entirely."),
        ("What is a lookback window?",
         "A lookback or revival window is a temporary period, set by a state legislature, during which survivors can file civil claims that had already expired. New York, California, New Jersey and Maryland are among states that opened them."),
        ("Is there a federal statute of limitations for child sexual abuse lawsuits?",
         "Federal law (18 U.S.C. § 2255) lets survivors of certain federal child sex crimes sue the perpetrator, and since 2022 those claims have no time limit. Federal claims have narrow requirements, so talk to a lawyer."),
        ("Is it too late to report a rape to police?",
         "Often not. Many states have no criminal time limit for rape, and others extend it when DNA evidence identifies a suspect. Support is available no matter how long ago it happened."),
    ]
    faq_html = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in hub_faqs)
    body = f"""<main id="main">
<article class="guide sol wide">
  <p class="crumb"><a href="/guides/">Help and resources</a></p>
  <h1>{esc(H1)}</h1>
  <p class="updated">Last checked <time datetime="{verified.isoformat()}">{fmt_date(verified)}</time></p>
  <p class="answer"><strong>A statute of limitations is the deadline to sue or to bring criminal charges.</strong> For
  sexual abuse, these deadlines vary widely by state, and many have been extended or eliminated since 2019, especially for
  abuse that happened in childhood. Some states have also opened temporary lookback windows that revive claims that had
  already expired. Find your state below.</p>
  {DISCLAIMER}
  <h2>Deadlines in every state</h2>
  <label class="sol-find" for="sol-q">Find your state</label>
  <input id="sol-q" type="search" placeholder="Type a state name" autocomplete="off">
  <div class="table-wrap"><table class="sol-table hub" id="sol-list">
  <thead><tr><th scope="col">State</th><th scope="col">Childhood sexual abuse (civil)</th><th scope="col">Adult survivors (civil)</th><th scope="col">Lookback window</th></tr></thead>
  <tbody>{rows}</tbody></table></div>
  <p class="hint">Select a state for criminal time limits, recent changes and sources.</p>
  {ow}
  <h2>How these deadlines work</h2>
  <ul>
    <li><strong>Civil vs. criminal.</strong> A civil lawsuit seeks money damages and can be brought by the survivor. A criminal case is brought by prosecutors. They have separate deadlines.</li>
    <li><strong>Age-based deadlines.</strong> For childhood abuse, many states let survivors sue until a certain age, such as 28, 40 or 55, rather than a fixed number of years after the abuse.</li>
    <li><strong>The discovery rule.</strong> Some states start the clock when the survivor realized, or reasonably should have realized, that the abuse caused their injuries. This matters because many survivors don't connect the two until years later.</li>
    <li><strong>Revival windows.</strong> Some legislatures have opened a fixed period during which expired claims can be filed. Courts in a few states have struck these down, so check the current status.</li>
    <li><strong>Institutions and government.</strong> Claims against schools, churches, employers and youth organizations often follow the same deadline, but claims against public schools and government agencies may require a formal notice of claim within months.</li>
    <li><strong>The law that applies.</strong> Usually it's the law in force where the abuse happened, but older abuse can be governed by the deadline that applied at the time, so an attorney's review is important.</li>
  </ul>
  <h2>Frequently asked questions</h2>
  <div class="faqs">{faq_html}</div>
  <h2>Sources and methodology</h2>
  <p>Each state's entry was compiled from the state's statutes and from trackers kept by
  <a href="https://childusa.org/sol/" rel="noopener">CHILD USA</a> and <a href="https://rainn.org" rel="noopener">RAINN</a>,
  cross-checked where possible, and is linked on that state's page. If you spot an error or a change in the law, email
  <a href="mailto:corrections@sexabuselitigation.org">corrections@sexabuselitigation.org</a>.</p>
  <h2>More help</h2>
  <ul>{more}<li><a href="/report/">Report anonymously to the Hollywood Council for Restorative Justice</a></li></ul>
</article>
</main>
<script>
(function(){{var q=document.getElementById('sol-q');var rows=[].slice.call(document.querySelectorAll('#sol-list tbody tr'));
q.addEventListener('input',function(){{var t=q.value.toLowerCase().trim();rows.forEach(function(r){{r.hidden=t&&r.dataset.q.indexOf(t)===-1;}});}});}})();
</script>"""
    ld = jsonld({"@context": "https://schema.org", "@graph": [
        {"@type": "Article", "headline": TITLE, "description": DESC, "dateModified": verified.isoformat(),
         "url": f"{site_url}/guides/{HUB}/", "publisher": org, "author": org},
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in hub_faqs]}]})
    d = out / "guides" / HUB
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(page(H1, body, path=f"/guides/{HUB}/", description=DESC, extra_head=ld,
                                       full_title=TITLE, og_type="article"))
    return urls
