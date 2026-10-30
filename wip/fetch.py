"""Fetch BAYERN.RECHT (www.gesetze-bayern.de) into .cache/: the list of Gesetze and each act's XML download (ZIP).

    python -X utf8 fetch.py list          # the result list for NORMTYP ges, every page
    python -X utf8 fetch.py zip BayVerf BayBO ...
    python -X utf8 fetch.py zip --all     # every act on the cached list
    python -X utf8 fetch.py list rv       # the Rechtsverordnungen list (.cache/list-rv/)
    python -X utf8 fetch.py zip --all-rv  # every Rechtsverordnung on that list

Private (never published). One process, one request at a time, at least 2.5 s apart (robots.txt: Allow /, no
Crawl-delay), curl with a browser User-Agent, cached by name; stops on 403/429 or a challenge page.
"""
import hashlib, json, re, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE / '.cache'
BASE = 'https://www.gesetze-bayern.de'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
JAR = CACHE / 'jar.txt'
_last = [0.0]


def get(url: str, out: Path, jar: bool = False) -> int:
    if out.exists() and out.stat().st_size:
        return 200
    wait = 2.5 - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + '.part')
    cmd = ['curl', '-s', '-L', '--compressed', '--max-time', '90', '-A', UA, '-o', str(tmp), '-w', '%{http_code}']
    if jar:
        cmd += ['-c', str(JAR), '-b', str(JAR)]
    p = subprocess.run(cmd + [url], capture_output=True, text=True)
    _last[0] = time.time()
    code = int(p.stdout.strip() or 0)
    body = tmp.read_bytes() if tmp.exists() else b''
    with open(CACHE / 'requests.jsonl', 'a', encoding='utf-8') as f:
        f.write(json.dumps({'t': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'url': url, 'code': code,
                            'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}) + '\n')
    if code in (403, 429) or b'Just a moment' in body[:5000] or b'captcha' in body[:5000].lower():
        tmp.unlink(missing_ok=True)
        raise SystemExit(f'stop: {code} on {url}')
    if code == 200 and body:
        tmp.replace(out)
    else:
        tmp.unlink(missing_ok=True)
    return code


def listing(normtyp: str = 'ges'):
    d = CACHE / ('list' if normtyp == 'ges' else f'list-{normtyp}')
    JAR.unlink(missing_ok=True)
    for f in d.glob('*.html'):
        f.unlink()
    get(f'{BASE}/Search/Filter/NORMTYP/{normtyp}', d / 'p001.html', jar=True)
    seen = set(re.findall(r'href="/Content/Document/([^"?/]+)\?hl=true"', (d / 'p001.html').read_text(encoding='utf-8')))
    n = 2
    while n < 200:
        out = d / f'p{n:03d}.html'
        get(f'{BASE}/Search/Page/{n}', out, jar=True)
        new = set(re.findall(r'href="/Content/Document/([^"?/]+)\?hl=true"', out.read_text(encoding='utf-8'))) - seen
        if not new:
            out.unlink()
            break
        seen |= new
        n += 1
    print(len(seen), 'documents on', n - 1, 'pages')
    (d / 'DONE').write_text(f'{len(seen)} {n - 1}' + chr(10))


def ids_from_list(sub: str = 'list') -> list[str]:
    ids = []
    for f in sorted((CACHE / sub).glob('p*.html')):
        for i in re.findall(r'href="/Content/Document/([^"?/]+)\?hl=true"', f.read_text(encoding='utf-8')):
            if i not in ids:
                ids.append(i)
    return ids


if __name__ == '__main__':
    if sys.argv[1] == 'list':
        listing(*sys.argv[2:3])
    elif sys.argv[1] == 'zip':
        ids = ids_from_list() if sys.argv[2:] == ['--all'] else (
            ids_from_list('list-rv') if sys.argv[2:] == ['--all-rv'] else sys.argv[2:])
        for i in ids:
            print(i, get(f'{BASE}/Content/Zip/{i}', CACHE / 'zip' / f'{i}.zip'), flush=True)
