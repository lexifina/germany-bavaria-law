# Bavaria (germany-bavaria-law) - private

State 2026-10-30 16:55 UTC (gitlaw-scraper-dell, German Länder fork of the ordinances wave):
- Source BAYERN.RECHT (www.gesetze-bayern.de). robots re-read 15:45 UTC: `User-agent: *` `Allow: /` (unchanged); no challenge.
- Published main 3949485 (verified rebuild 2220854 -> 3949485 by autopush_dell, standing approval, lease, old tip archived): Verfassung + 241 Gesetze + 486 Rechtsverordnungen = 727 acts, 727 versions (current text only, dated by "Text gilt ab").
- Verordnungen: result list NORMTYP rv (`fetch.py list rv`, 49 pages, .cache/list-rv/), one XML zip each (`fetch.py zip --all-rv`, run-rv.sh); parts corpus.d/40-verordnungen-01..10 (50 each, last 36). .cache/rv-done marks the list fully fetched.
- Parse rules for the Verordnungen parts only (Gesetze parts byte-identical): an amending-act key gvbl-YYYY-PPPP gets -YYYYMMDD unless the published parts hold that key for the same date (two acts can start on one GVBl page); a new key is labelled "Verordnung vom ..." when the act the portal names is a V/ÄndV/...verordnung, else "Gesetz vom ..."; the first act in list order that names a key sets its label.
- Verification: check_letters.py 486 acts, 0 differences; scratch build of all parts: check.py 727/727, 0 mismatches/trailer errors/merges/backwards/future-dated/missing in-force (world-law/de_ord_verify.py; result ordverify.json).
- Not yet: Verwaltungsvorschriften (1,478), Verträge (208).
