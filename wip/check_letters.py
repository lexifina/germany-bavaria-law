"""Independent letters-and-digits check: each act's units against the raw XML in .cache/zip (regex, no XML parser).

    python -X utf8 check_letters.py [part.json ...]

Private. For each act: the XML text of <rumpf> (footnotes, sentence numbers, the citation line and the amendment list
removed) reduced to letters and digits must equal the act's provision files (all but 000-titel) reduced the same way,
taken in document order, and every provision must be found at its place.
"""
import json, re, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def ld(s: str) -> str:
    return ''.join(ch for ch in s if ch.isalnum())


def source_text(raw: bytes) -> str:
    s = raw.decode('utf-8-sig')
    s = s[s.index('<rumpf>'):]
    s = re.sub(r'(?s)<aenderungsverlauf>.*?</aenderungsverlauf>|<normzitat>.*?</normzitat>', '', s)
    s = re.sub(r'(?<=</annex\.nummer>)<annex\.nummer[^>]*>[^<]*</annex\.nummer>', '', s)  # a repeated number
    s = re.sub(r'(?s)<fn\.call[^>]*>.*?</fn\.call>|<satz\.nr[^>]*>.*?</satz\.nr>|<img[^>]*/?>', '', s)
    s = re.sub(r'<[^>]+>', ' ', s)
    return s.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('­', '')


def main(paths):
    bad = total = 0
    for p in paths:
        c = json.load(open(p, encoding='utf-8'))
        for a in c['acts']:
            dokid = a['url'].rsplit('/', 1)[1]
            z = zipfile.ZipFile(HERE / '.cache' / 'zip' / f'{dokid}.zip')
            raw = z.read([n for n in z.namelist() if n.endswith('.xml') and not n.startswith('META')][0])
            src = ld(source_text(raw))
            units = a['versions'][-1]['units']
            pos, ok = 0, True
            # Document order is the order in which the provisions' text occurs in the source.
            rest = {k: ld(re.sub(r'(?m)^#+ ', '', u['text'])) for k, u in units.items() if k != '000-titel'}
            got = ''
            while rest:
                hit = None
                for k, t in rest.items():
                    if src.startswith(t, pos):
                        if hit is None or len(t) > len(rest[hit]):
                            hit = k
                if hit is None:
                    ok = False
                    break
                pos += len(rest.pop(hit))
            total += 1
            if not ok or pos != len(src):
                bad += 1
                print(f'MISMATCH {a["slug"]}: matched {pos}/{len(src)} chars; next source: {src[pos:pos + 80]!r}; '
                      f'unplaced: {list(rest)[:5]}')
    print(f'{total} acts checked, {bad} mismatches')
    return bad


if __name__ == '__main__':
    sys.exit(1 if main(sys.argv[1:] or sorted(str(p) for p in (HERE / 'corpus.d').glob('*.json'))) else 0)
