"""Bavarian law from BAYERN.RECHT's XML downloads (.cache/zip/<dokid>.zip) into corpus.d/ parts.

    python -X utf8 parse.py

Reads only the cache; the same cache gives the same bytes. Parts:
  10-verfassung.json   the Verfassung des Freistaates Bayern
  20-gesetze-NN.json   the other Gesetze, in the portal's list order, about 50 acts a part
  40-verordnungen-NN.json   the Rechtsverordnungen (NORMTYP rv), in the portal's list order, about 50 acts a part
A part is written only when every act it holds is in the cache, so a published part never changes when more arrive.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE / '.cache'
BASE = 'https://www.gesetze-bayern.de'
RETRIEVED = '2026-10-30'
PART_SIZE = 50
SKIP_INLINE = {'fn.call', 'satz.nr', 'fn.def', 'fn.text'}
BLOCK = {'p', 'ul', 'ol', 'li', 'table', 'tr', 'dl', 'dt', 'dd', 'div', 'absatz.text', 'jurAbsatz', 'tbody', 'thead',
         'tgroup', 'row', 'entry', 'td', 'th', 'img', 'pre'}

COUNTRY = {
    'code': 'DE-BY', 'name': 'Bavaria', 'slug': 'germany-bavaria', 'lang': 'de', 'tz': 'Europe/Berlin',
    'future_branch': 'zukunft',
    'publisher': {'name': 'Bayerische Staatskanzlei (Bürgerservice BAYERN.RECHT)',
                  'email': 'bayern-recht@gesetze-bayern.de.invalid'},
    'default_in_force_rule': {
        'text': 'Verfassung des Freistaates Bayern Art. 76 Abs. 2: "Jedes Gesetz muß den Tag bestimmen, an dem es in '
                'Kraft tritt." Each version here is dated by the day BAYERN.RECHT says its consolidated text applies '
                'from ("Text gilt ab", the "inkraft" date of the XML).',
        'source': 'https://www.gesetze-bayern.de/Content/Document/BayVerf-82'},
    'licence_note': 'Texts: Bürgerservice BAYERN.RECHT (Bayerische Staatskanzlei; consolidation by Verlag C.H.Beck on '
                    'behalf of the Free State of Bavaria), www.gesetze-bayern.de. Its terms allow the texts of the '
                    'Vorschriften to be used, reproduced and distributed without restriction, commercially or not; '
                    'Gesetze and Verordnungen are not protected by copyright (§ 5 Abs. 1 UrhG). Non-official text: '
                    'only the Gesetz- und Verordnungsblatt is authoritative.',
}


def norm(s: str) -> str:
    s = s.replace(' ', ' ').replace(' ', ' ').replace(' ', ' ').replace('­', '')
    return re.sub(r'[ \t\r\n]+', ' ', s).strip()


def inline(el: ET.Element, br: str = ' ') -> str:
    """Text of el and its inline descendants; footnotes and sentence numbers left out."""
    out = [el.text or '']
    for ch in el:
        if ch.tag in SKIP_INLINE:
            pass
        elif ch.tag == 'br':
            out.append(br)
        else:
            out.append(inline(ch, br))
        out.append(ch.tail or '')
    return ''.join(out)


def has_block(el: ET.Element) -> bool:
    return any(ch.tag in BLOCK for ch in el.iter() if ch is not el)


def lines(el: ET.Element) -> list[str]:
    """One line per paragraph, list item or table row."""
    t = el.tag
    if t in SKIP_INLINE:
        return []
    if t == 'p':
        if has_block(el):
            return mixed(el)
        return [x for x in (norm(s) for s in inline(el, '\n').split('\n')) if x]
    if t == 'li':
        sym = ''
        rest = []
        for ch in el:
            if ch.tag == 'symbol':
                sym = norm(inline(ch))
            else:
                rest.append(ch)
        body: list[str] = []
        lead = norm(el.text or '')
        if lead:
            body.append(lead)
        for ch in rest:
            body += lines(ch) if ch.tag in BLOCK else [x for x in [norm(inline(ch))] if x]
            tail = norm(ch.tail or '')
            if tail:
                body.append(tail)
        if sym:
            body = [f'{sym} {body[0]}' if body else sym] + body[1:]
        return body
    if t in ('tr', 'row'):
        cells = [norm(' '.join(lines(c)) if has_block(c) else inline(c)) for c in el if c.tag in ('td', 'th', 'entry')]
        return [' | '.join(cells)] if any(cells) else []
    if t == 'img':
        return []
    return mixed(el)


def mixed(el: ET.Element) -> list[str]:
    """A container: block children give lines; loose text and inline children in between gather into one line."""
    out: list[str] = []
    buf = [el.text or '']

    def flush():
        for s in ''.join(buf).split('\n'):
            s = norm(s)
            if s:
                out.append(s)
        buf.clear()
    for ch in el:
        if ch.tag in BLOCK:
            flush()
            out += lines(ch)
        elif ch.tag == 'br':
            buf.append('\n')
        elif ch.tag not in SKIP_INLINE:
            buf.append(inline(ch))
        buf.append(ch.tail or '')
    flush()
    return out


def unit_key(nr: str, seen: set[str], pad: int) -> tuple[str, str]:
    m = re.match(r'^(Art\.|Artikel|§§?)\s*(\d+)\s*([a-z]?)\b(?:\s*(?:bis|-|–|und)\s*(\d+)\s*([a-z]?))?', nr)
    if m:
        pre = 'art' if m.group(1).startswith('Art') else 'par'
        k = f'{pre}-{int(m.group(2)):0{pad}d}{m.group(3)}'
        if m.group(4):
            k += f'-{int(m.group(4)):0{pad}d}{m.group(5)}'
        kind = pre
    else:
        m = re.match(r'^(Anlage|Anhang|Anl\.|Tabelle|Muster|Formblatt|Verzeichnis)\s*(\d*)\s*([a-z]?)', nr)
        if m:
            k = 'z-' + re.sub(r'[^a-z0-9]+', '-', m.group(1).lower().replace('.', '')).strip('-')
            k += f'-{int(m.group(2)):02d}{m.group(3)}' if m.group(2) else ''
            kind = 'annex'
        else:
            k = 'y-' + (re.sub(r'[^a-z0-9]+', '-', nr.lower().translate(str.maketrans('äöüß', 'aous')))
                        .strip('-')[:40] or 'teil')
            kind = 'other'
    base, i = k, 2
    while k in seen:
        k = f'{base}-{i}'
        i += 1
    seen.add(k)
    return k, kind


def parse_xml(raw: bytes, dokid: str) -> dict:
    root = ET.fromstring(raw)
    kopf = root.find('kopf')
    va = kopf.find('angaben.versabh')
    vu = kopf.find('angaben.versunabh')
    inkraft = (va.findtext('inkraft') or '').strip()
    ausf = (vu.findtext('ausfertigung/ausfertigungsdatum') or '').strip()
    title_el = va.find('titelangaben')
    title_lines = [x for x in (norm(s) for s in inline(title_el, '\n').split('\n')) if x] if title_el is not None else [dokid]
    abk = norm(va.findtext('amtlicheAbk') or '') or norm(va.findtext('kurzbezeichnung') or '') or dokid
    rumpf = root.find('rumpf')
    nums = [int(n) for n in re.findall(r'(?:Art\.|§)\s*(\d+)', ' '.join(norm(inline(e)) for e in rumpf.iter('para.nr')))]
    pad = 4 if nums and max(nums) > 999 else 3
    units: dict[str, dict] = {}
    seen: set[str] = set()
    head = [f'# {t}' if i == 0 else t for i, t in enumerate(title_lines)]
    zitat = norm(inline(rumpf.find('normzitat'))) if rumpf.find('normzitat') is not None else ''
    if zitat:
        head.append(zitat)
    amend: list[str] = []
    av = rumpf.find('aenderungsverlauf')
    if av is not None:
        for x in av:
            if x.tag == 'p':
                head += lines(x)
        for li in av.iter('li'):
            sym = norm(inline(li.find('symbol'))) if li.find('symbol') is not None else ''
            txt = norm(' '.join(inline(c) for c in li if c.tag != 'symbol'))
            if txt or sym:
                head.append(f'{sym} {txt}'.strip())
                amend.append(txt)
    units['000-titel'] = {'label': 'Titel', 'kind': 'title', 'text': '\n'.join(head) + '\n'}
    seen.add('000-titel')
    pending: list[str] = []
    order = ['000-titel']

    def annex(ch: ET.Element):
        nr_el, ti_el = ch.find('.//annex.nummer'), ch.find('.//annex.titel')
        nr = norm(' '.join(lines(nr_el)) or inline(nr_el)) if nr_el is not None else ''
        ti = norm(' '.join(lines(ti_el)) or inline(ti_el)) if ti_el is not None else ''
        key, kind = unit_key(nr or 'Anlage', seen, pad)
        body: list[str] = []
        for koerper in ch:
            for x in koerper:
                if x.tag not in ('annex.nummer', 'annex.titel'):
                    body += lines(x) if x.tag in BLOCK or len(x) else [y for y in [norm(inline(x))] if y]
        heading = '# ' + ' '.join(x for x in (nr, ti) if x)
        units[key] = {'label': nr or 'Anlage', 'kind': 'annex', 'text': '\n'.join(pending + [heading] + body) + '\n'}
        pending.clear()
        order.append(key)

    def walk(el: ET.Element, depth: int):
        for ch in el:
            if ch.tag in ('normzitat', 'aenderungsverlauf', 'gliederung.titel'):
                continue
            if ch.tag == 'gliederung':
                t = ch.find('gliederung.titel')
                if t is not None:
                    txt = ' '.join(lines(t)) or norm(inline(t))
                    if txt:
                        pending.append('#' * min(depth + 1, 6) + ' ' + txt)
                walk(ch, depth + 1)
            elif ch.tag == 'einzelnorm':
                nr_el = ch.find('para.nr')
                nr = norm(inline(nr_el)) if nr_el is not None else ''
                ti_el = ch.find('para.titel')
                ti = norm(' '.join(lines(ti_el)) or inline(ti_el)) if ti_el is not None else ''
                if nr:
                    key, kind = unit_key(nr, seen, pad)
                    label = nr
                elif re.search(r'(?i)pr(ä|ae)ambel|vorspruch', ti):
                    key, kind, label = '001-praeambel', 'preamble', ti.strip('[]') or 'Präambel'
                    seen.add(key)
                else:
                    key, kind = unit_key(ti or 'eingang', seen, pad)
                    label = ti or 'Eingang'
                body: list[str] = []
                for ab in ch:
                    if ab.tag != 'jurAbsatz':
                        continue
                    n = norm(inline(ab.find('absatz.nr'))) if ab.find('absatz.nr') is not None else ''
                    tx = ab.find('absatz.text')
                    ls = lines(tx) if tx is not None else []
                    if n:
                        ls = [f'{n} {ls[0]}' if ls else n] + ls[1:]
                    body += ls
                heading = '# ' + ' '.join(x for x in (nr, ti) if x)
                text = '\n'.join(pending + [heading] + body) + '\n'
                pending.clear()
                units[key] = {'label': label, 'kind': kind, 'text': text}
                order.append(key)
            elif ch.tag == 'annex':
                annex(ch)
            elif ch.tag in ('jurAbsatz', 'p', 'ul', 'table'):  # loose text outside any Einzelnorm
                key, kind = unit_key('text', seen, pad)
                units[key] = {'label': 'Text', 'kind': 'other', 'text': '\n'.join(pending + lines(ch)) + '\n'}
                pending.clear()
                order.append(key)
            else:
                walk(ch, depth)
    walk(rumpf, 1)
    for ch in root.findall('annex'):
        annex(ch)
    if pending and order:
        units[order[-1]]['text'] += '\n'.join(pending) + '\n'
    return {'dokid': dokid, 'inkraft': inkraft, 'ausfertigung': ausf, 'title': title_lines[0], 'title_lines': title_lines,
            'abk': abk, 'units': units, 'order': order, 'amend': amend,
            'bayrs': norm(va.findtext('gliederungsNr.BayRS') or '')}


def read_zip(path: Path) -> tuple[bytes, str]:
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if n.endswith('.xml') and not n.startswith('META-INF')]
        return z.read(names[0]), names[0]


def amending_laws(amend: list[str]) -> dict:
    """The amending acts the portal lists, as law records keyed by their place in the GVBl (year and first page)."""
    laws = {}
    for t in amend:
        m = re.search(r'vom (\d{1,2})\.(\d{1,2})\.(\d{4})\s*\(GVBl\.?\s*(\d{4})?\s*S\.\s*(\d+)', t)
        if not m:
            continue
        d, mo, y, gy, page = m.groups()
        gy = gy or y
        key = f'gvbl-{gy}-{int(page):04d}'
        laws[key] = {'label': f'Gesetz vom {int(d)}.{int(mo)}.{y} (GVBl. {gy} S. {int(page)})',
                     'title': norm(re.sub(r'^(?:Art\.|§§?)\s*[\d\w]+(?:\s*(?:Abs\.|Nr\.|Satz)\s*\d+\w*)*\s*', '', t[:m.start()])) or None, 'kind': 'law', 'enacted': f'{y}-{int(mo):02d}-{int(d):02d}', 'published': None,
                     'url': None, 'temporary_until': None, 'restores': None,
                     'note': 'Listed by BAYERN.RECHT among the acts that amended this act; its text is not in this record.'}
    return laws


def published_labels() -> dict:
    """Law key -> label in the parts already written (the Verfassung and Gesetze): a key keeps its label."""
    out = {}
    for f in sorted((HERE / 'corpus.d').glob('*.json')):
        if not f.name.startswith('40-'):
            for k, lw in json.loads(f.read_text(encoding='utf-8')).get('laws', {}).items():
                out.setdefault(k, lw['label'])
    return out


def vo_labels(laws: dict, known: dict) -> dict:
    """In the Verordnungen parts, a new key is labelled by the kind of act its title names (an amending
    Verordnung "V", "ÄndV", ... or an amending Gesetz "G", "ÄndG", ...); a key the earlier parts hold keeps their
    label."""
    for k, lw in laws.items():
        if k in known:
            lw['label'] = known[k]
            continue
        t = lw.get('title') or ''
        mv = re.search(r'(?<![\w])(V|VO|VOen|\w*V|\w*[Vv]erordnung\w*)(?![\w])', t)
        mg = re.search(r'(?<![\w])(G|\w*G|\w*[Gg]esetz\w*)(?![\w])', t)
        if mv and (not mg or mv.start() < mg.start()):
            lw['label'] = 'Verordnung' + lw['label'][len('Gesetz'):]
    return laws


def act_of(dokid: str) -> tuple[dict, dict]:
    path = CACHE / 'zip' / f'{dokid}.zip'
    raw, _ = read_zip(path)
    p = parse_xml(raw, dokid)
    day = p['inkraft'] or p['ausfertigung']
    slug = re.sub(r'[^a-z0-9]+', '-', dokid.lower()).strip('-')
    act = {
        'slug': slug, 'short': p['abk'], 'title': p['title'], 'url': f'{BASE}/Content/Document/{dokid}',
        'first_law': None, 'earlier_laws': sorted(amending_laws(p['amend'])),
        'versions': [{
            'from': day, 'source_url': f'{BASE}/Content/Document/{dokid}',
            'sha256': hashlib.sha256(raw).hexdigest(),
            'units': p['units'], 'credits': {},
            'note': f'Consolidated text as published by BAYERN.RECHT on {RETRIEVED} (in force from {day}'
                    + (f'; {p["bayrs"]}' if p['bayrs'] else '') + ').'}],
    }
    return act, p


def part(name: str, ids: list[str], country: bool) -> None:
    acts, decisions, laws = [], [], {}
    for i in ids:
        a, p = act_of(i)
        if not a['versions'][0]['from']:
            print('no date, left out:', i, file=sys.stderr)
            continue
        acts.append(a)
        laws.update(vo_labels(amending_laws(p['amend']), KNOWN) if name.startswith('40-') else amending_laws(p['amend']))
    out = {'acts': acts, 'laws': dict(sorted(laws.items())), 'applies': [],
           'sources': [{'name': 'Bürgerservice BAYERN.RECHT (Bayerische Staatskanzlei), XML download of each act',
                        'url': BASE, 'retrieved': RETRIEVED,
                        'licence': 'BAYERN.RECHT "Rechtliche Hinweise und Nutzungsbedingungen": the Vorschriften may '
                                   'be used and reused without restriction of place, time or content, and expressly '
                                   'reproduced, distributed, made public and processed commercially and non-commercially '
                                   '(simple right of use; database right under §§ 87a ff. UrhG unaffected). § 5 Abs. 1 '
                                   'UrhG: Gesetze, Verordnungen and amtliche Erlasse enjoy no copyright protection.',
                        'notes': f'{len(acts)} acts in this part, each the current consolidated version '
                                 '(XML "byrecht-norm", one file per act).'}],
           'decisions': [
               'Current text only: BAYERN.RECHT publishes only the consolidated version in force, so each act is one '
               'version ("oldest version available"), credited to the publisher, not to an amending law.',
               'Each version is dated by the day BAYERN.RECHT says the consolidated text applies from ("Text gilt ab"; '
               'the inkraft date of the XML); if it is missing, by the Ausfertigung date. For some acts that day is earlier '
               'than the date of the last amending act the portal lists; the date the portal gives is kept, not guessed '
               'over. Days after the retrieval day go on the zukunft branch.',
               'One file per Artikel or Paragraph (einzelnorm); headings of the Teile and Abschnitte stand above the first '
               'provision under them; "000-titel" holds the title lines, the citation line and the list of amending acts '
               'the portal prints.',
               'Left out as editorial: footnotes (fn.call) and sentence numbers (satz.nr). Tables are one line per row, '
               'cells separated by " | "; images are left out.'] + decisions,
           'ai_use': ['Claude Code (claude-opus-5-5) wrote Lexifina\'s code and chose the sources. No model output is '
                      'used as legal text or dates: every word comes from the BAYERN.RECHT XML.']}
    if country:
        out['country'] = COUNTRY
    d = HERE / 'corpus.d'
    d.mkdir(exist_ok=True)
    tmp = d / (name + '.json.tmp')
    tmp.write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    tmp.replace(d / (name + '.json'))
    print(name, len(acts), 'acts', sum(len(a['versions'][0]['units']) for a in acts), 'units')


KNOWN: dict = {}


def list_ids(sub: str = 'list') -> list[str]:
    ids = []
    for f in sorted((CACHE / sub).glob('p*.html')):
        for i in re.findall(r'href="/Content/Document/([^"?/]+)\?hl=true"', f.read_text(encoding='utf-8')):
            if i not in ids:
                ids.append(i)
    return ids


if __name__ == '__main__':
    part('10-verfassung', ['BayVerf'], country=True)
    ids = [i for i in list_ids() if i != 'BayVerf']
    complete = (CACHE / 'list' / 'DONE').exists()
    for n in range(0, len(ids), PART_SIZE):
        chunk = ids[n:n + PART_SIZE]
        if len(chunk) < PART_SIZE and not complete:
            break
        if all((CACHE / 'zip' / f'{i}.zip').exists() for i in chunk):
            part(f'20-gesetze-{n // PART_SIZE + 1:02d}', chunk, country=False)
    # the Rechtsverordnungen (ordinances wave, 2026-10-30): NORMTYP rv, list order, about 50 acts a part; the last,
    # short part only once the whole list is fetched (.cache/rv-done)
    KNOWN.update(published_labels())
    ids = list_ids('list-rv')
    for n in range(0, len(ids), PART_SIZE):
        chunk = ids[n:n + PART_SIZE]
        if len(chunk) < PART_SIZE and not (CACHE / 'rv-done').exists():
            break
        if all((CACHE / 'zip' / f'{i}.zip').exists() for i in chunk):
            part(f'40-verordnungen-{n // PART_SIZE + 1:02d}', chunk, country=False)
        else:
            break
