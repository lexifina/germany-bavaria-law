<!-- lawwatch: written from data/checks by the check trail; edit the records, not this page -->

# Monitoring: what is read and what came of it

[Deutsch](README.md)

How global-law monitors every country: [global-law monitoring/](https://github.com/lexifina/global-law/tree/main/monitoring). This page is the same for Bavaria only: every time an official source is read, when, and what came of it (acts added, changed and removed). The machine-readable form is [data/checks/](../data/checks/) (JSON Lines, schema `lexifina-check/1`), in `git log` as `Kind: check` commits, and month by month in [checks/](checks/).

**Last check:** 2026-11-26 07:17 UTC, BAYERN.RECHT (Bavarian State Chancellery): 32 addresses read; 0 added, 0 changed, 0 removed; no change; 0 not published, 0 of them with no reason.

## Sources

| Source | Folders | How often | Last successful check | Last result | State |
| --- | --- | --- | --- | --- | --- |
| [BAYERN.RECHT (Bavarian State Chancellery)](https://www.gesetze-bayern.de) | `<act>/` | daily | 2026-11-26 07:17 UTC | no change | watched |

## The last 30 days

| Started (UTC) | Source | Read | Added | Changed | Removed | Not published (no reason) | Result | Commits |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| [2026-11-26 07:16](checks/2026-11.md#de-bayern-recht-20261126t071607z) | bayern-recht | 32 | 0 | 0 | 0 | 0 (0) | no change | — |
| [2026-11-25 07:14](checks/2026-11.md#de-bayern-recht-20261125t071440z) | bayern-recht | 32 | 0 | 0 | 0 | 0 (0) | no change | — |
| [2026-11-24 07:23](checks/2026-11.md#de-bayern-recht-20261124t072300z) | bayern-recht | 32 | 0 | 0 | 0 | 0 (0) | no change | — |
| [2026-11-23 23:48](checks/2026-11.md#de-bayern-recht-20261123t234838z) | bayern-recht | 32 | 0 | 0 | 0 | 0 (0) | no change | — |
| [2026-11-23 20:51](checks/2026-11.md#de-bayern-recht-20261123t205124z) | bayern-recht | 94 | 0 | 0 | 0 | 0 (0) | changes found `audit-disagrees` | [17](https://github.com/lexifina/germany-bavaria-law/compare/f2e55bb4ce8f...703798ef7fee) |

## Check it yourself

```
python tools/checktrail.py                      # the latest check of every source
python tools/checktrail.py --day 2026-11-23     # every check of a day
python tools/checktrail.py --act <id>           # when an act was seen and published
git log --grep='^Kind: check' --format='%ci %s'  # the checks in the history
```

Only the official publication has legal force; the texts here are copies for reading and searching.
