import sys, os, re, json, time, html, hashlib, urllib.parse, urllib.request, urllib.error
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from topics import R, Q
D = os.path.dirname(os.path.abspath(__file__))
UA = {'User-Agent': 'Mozilla/5.0 TinnDocBot/1.0 (santymoli02@gmail.com)'}
need = Counter()
for a, b, k in R:
    if k in Q: need[k] += b - a + 1
def get(url, binary=False):
    for i in range(5):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read()
            return r if binary else r.decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            if e.code in (400, 404): raise
            time.sleep(8 * (i + 1))
        except Exception:
            time.sleep(4)
    raise RuntimeError('fail ' + url)
def thumb(name, w=330):
    n = name.replace(' ', '_'); h = hashlib.md5(n.encode()).hexdigest(); ext = n.rsplit('.', 1)[-1].lower(); q = urllib.parse.quote(n)
    suf = '' if ext in ('jpg', 'jpeg', 'png') else '.jpg' if ext in ('tif', 'tiff') else '.png'
    return f'https://upload.wikimedia.org/wikipedia/commons/thumb/{h[0]}/{h[:2]}/{q}/{w}px-{q}{suf}'
cf = f'{D}/cands.json'
res = json.load(open(cf)) if os.path.exists(cf) else {}
done = set(json.load(open(f'{D}/done.json'))) if os.path.exists(f'{D}/done.json') else set()
BOOST = set(sys.argv[1:])
BL = set(json.load(open(f'{D}/bl.json'))) if os.path.exists(f'{D}/bl.json') else set()
for k, qs in Q.items():
    if BOOST and k not in BOOST: continue
    target = need[k] + 5 + (12 if BOOST else 0)
    for kind, q in qs:
        tag = f'{k}|{kind}|{q}'
        if tag in done and not BOOST: continue
        have = res.setdefault(k, [])
        if len(have) >= target: done.add(tag); continue
        if kind == 'cat':
            url = 'https://commons.wikimedia.org/wiki/' + urllib.parse.quote('Category:' + q.replace(' ', '_'))
        else:
            url = 'https://commons.wikimedia.org/w/index.php?' + urllib.parse.urlencode({'search': q, 'title': 'Special:Search', 'ns6': 1, 'fulltext': 1, 'limit': 40})
        try: t = get(url)
        except Exception as e: print('ERR', tag, e, flush=True); continue
        names = []
        for m in re.finditer(r'(?:title|href)="(?:/wiki/)?(File:[^"#?]+?\.(?:jpe?g|png|tiff?))"', t, re.I):
            n = urllib.parse.unquote(html.unescape(m.group(1)))[5:].replace('_', ' ')
            if n not in names: names.append(n)
        jobs = []
        for n in names:
            if len(have) >= target: break
            if n in have or n in BL: continue
            i = len(have); have.append(n); jobs.append((n, f'{D}/thumbs/{k}__{i}.jpg'))
        def dl(job):
            n, p = job
            try: open(p, 'wb').write(get(thumb(n), True))
            except Exception as e: print('THUMBERR', k, n[:50], e, flush=True)
        with ThreadPoolExecutor(2) as ex: list(ex.map(dl, jobs))
        done.add(tag)
        json.dump(res, open(cf, 'w'), ensure_ascii=False, indent=0); json.dump(sorted(done), open(f'{D}/done.json', 'w'))
        print(tag, '+', len(jobs), f'({len(have)}/{target})', flush=True); time.sleep(1)
print('FETCHDONE', flush=True)
