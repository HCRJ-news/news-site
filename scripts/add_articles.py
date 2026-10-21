#!/usr/bin/env python3
"""Merge new entries into data/articles.json, skipping duplicates and invalid rows.

Usage: python3 scripts/add_articles.py new1.json [new2.json ...]
Each input file is a JSON array of entries. Prints how many were added.
"""
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

DATA = Path(__file__).resolve().parent.parent / "data" / "articles.json"
REQUIRED = ["title", "source", "url", "date", "category", "institution", "summary", "status"]
CATEGORIES = {"company", "school", "government", "religious"}
STATUSES = {"allegation", "lawsuit", "investigation", "charges", "settlement",
            "verdict", "conviction", "legislation", "policy"}


def norm_url(u):
    p = urlsplit(u.strip())
    return (p.netloc.lower().removeprefix("www.") + p.path.rstrip("/")).lower()


def valid(e):
    if any(not str(e.get(k, "")).strip() for k in REQUIRED):
        return "missing field"
    if e["category"] not in CATEGORIES:
        return f"bad category {e['category']}"
    if e["status"] not in STATUSES:
        return f"bad status {e['status']}"
    if not e["url"].startswith(("http://", "https://")):
        return "bad url"
    try:
        d = date.fromisoformat(e["date"])
    except ValueError:
        return "bad date"
    if d > date.today():
        return "future date"
    return None


def main(paths):
    existing = json.loads(DATA.read_text()) if DATA.exists() else []
    seen = {norm_url(e["url"]) for e in existing}
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    added = 0
    for p in paths:
        for e in json.loads(Path(p).read_text()):
            problem = valid(e)
            key = norm_url(e.get("url", ""))
            if problem:
                print(f"skip ({problem}): {e.get('title', '')[:70]}")
                continue
            if key in seen:
                continue
            seen.add(key)
            keep = {k: str(e[k]).strip() for k in REQUIRED}
            keep["location"] = str(e.get("location", "")).strip()
            if e.get("case"):
                keep["case"] = str(e["case"]).strip()
            keep["added"] = stamp
            existing.append(keep)
            added += 1
    existing.sort(key=lambda e: (e["date"], e.get("added", "")), reverse=True)
    DATA.write_text(json.dumps(existing, indent=1, ensure_ascii=False) + "\n")
    print(f"added {added}; total {len(existing)}")


if __name__ == "__main__":
    main(sys.argv[1:])
