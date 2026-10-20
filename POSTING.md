# How new entries are added (instructions for the scheduled run)

1. Read `data/articles.json` to know what is already indexed (dedupe is by URL, but also skip a story
   already covered by a different outlet unless there is a genuinely new development).
2. Search the web for reporting published since the newest `date` in the file (look back 3 days to catch
   late finds) on sexual abuse allegations, lawsuits, investigations, charges, settlements, verdicts,
   convictions, legislation or policy changes involving **institutions**: companies, schools/universities,
   governments/public agencies, religious organizations.
3. Open each article to confirm the URL, date and facts. Skip paywalled pages you cannot verify.
4. Write new entries to a temp JSON file, then run `python3 scripts/add_articles.py <file>`.
   Fields: title (own words, <=110 chars), source, url, date (YYYY-MM-DD, article date), category
   (company | school | government | religious), institution (one primary name, reuse the exact name
   already in the file if the institution exists), summary (1-2 neutral sentences, own words), status
   (allegation | lawsuit | investigation | charges | settlement | verdict | conviction | legislation | policy),
   location ("Country, State").
5. Run `python3 build.py` to make sure it builds, then commit and push to `main`.

## Editorial rules (non-negotiable)
- Never name or identify survivors, victims or plaintiffs who are private individuals.
- Never include details that could identify a minor.
- Unproven claims are allegations. Only say convicted / found liable when the reporting says so.
- Name accused individuals only if they are public figures or have been criminally charged.
- No graphic detail. No copying article text.
- Do not post individual crimes with no institutional angle (e.g. a stranger assault with no employer,
  school, agency or organization implicated).
