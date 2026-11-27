<!-- lawwatch: written from data/checks by the check trail; edit the records, not this page -->

# Beobachtung: was gelesen wird und was daraus folgte

[English](README.en.md)

Wie global-law jedes Land beobachtet: [global-law monitoring/](https://github.com/lexifina/global-law/tree/main/monitoring). Diese Seite zeigt dasselbe nur für Bayern: jedes Lesen einer amtlichen Quelle, wann, und was daraus folgte (Vorschriften hinzugefügt, geändert und entfernt). Maschinenlesbar in [data/checks/](../data/checks/) (JSON Lines, Schema `lexifina-check/1`), in `git log` als Commits mit `Kind: check` und Monat für Monat in [checks/](checks/).

**Letzte Prüfung:** 2026-11-27 07:16 UTC, BAYERN.RECHT (Bayerische Staatskanzlei): 32 Adressen gelesen; 0 hinzugefügt, 0 geändert, 0 entfernt; keine Änderung; 0 nicht veröffentlicht, davon 0 ohne Grund.

## Quellen

| Quelle | Ordner | Wie oft | Letzte erfolgreiche Prüfung | Letztes Ergebnis | Stand |
| --- | --- | --- | --- | --- | --- |
| [BAYERN.RECHT (Bayerische Staatskanzlei)](https://www.gesetze-bayern.de) | `<act>/` | täglich | 2026-11-27 07:16 UTC | keine Änderung | beobachtet |

## Die letzten 30 Tage

| Beginn (UTC) | Quelle | Gelesen | Hinzugefügt | Geändert | Entfernt | Nicht veröffentlicht (ohne Grund) | Ergebnis | Commits |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| [2026-11-27 07:15](checks/2026-11.md#de-bayern-recht-20261127t071528z) | bayern-recht | 32 | 0 | 0 | 0 | 0 (0) | keine Änderung | — |
| [2026-11-26 07:16](checks/2026-11.md#de-bayern-recht-20261126t071607z) | bayern-recht | 32 | 0 | 0 | 0 | 0 (0) | keine Änderung | — |
| [2026-11-25 07:14](checks/2026-11.md#de-bayern-recht-20261125t071440z) | bayern-recht | 32 | 0 | 0 | 0 | 0 (0) | keine Änderung | — |
| [2026-11-24 07:23](checks/2026-11.md#de-bayern-recht-20261124t072300z) | bayern-recht | 32 | 0 | 0 | 0 | 0 (0) | keine Änderung | — |
| [2026-11-23 23:48](checks/2026-11.md#de-bayern-recht-20261123t234838z) | bayern-recht | 32 | 0 | 0 | 0 | 0 (0) | keine Änderung | — |
| [2026-11-23 20:51](checks/2026-11.md#de-bayern-recht-20261123t205124z) | bayern-recht | 94 | 0 | 0 | 0 | 0 (0) | Änderungen gefunden `audit-disagrees` | [17](https://github.com/lexifina/germany-bavaria-law/compare/f2e55bb4ce8f...703798ef7fee) |

## Selbst prüfen

```
python tools/checktrail.py                      # die letzte Prüfung jeder Quelle
python tools/checktrail.py --day 2026-11-23     # jede Prüfung eines Tages
python tools/checktrail.py --act <id>           # wann eine Vorschrift gesehen und veröffentlicht wurde
git log --grep='^Kind: check' --format='%ci %s'  # die Prüfungen in der Historie
```

Rechtskraft hat nur die amtliche Verkündung; die Texte hier sind Kopien zum Lesen und Suchen.
