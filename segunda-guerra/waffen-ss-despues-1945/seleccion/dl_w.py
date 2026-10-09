import json, os, sys, time, hashlib, urllib.parse, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
D = os.path.dirname(os.path.abspath(__file__)); MED = sys.argv[1]
UA = {'User-Agent': 'Mozilla/5.0 TinnDocBot/1.0 (santymoli02@gmail.com)'}
cands = json.load(open(f'{D}/cands.json')); plan = json.load(open(f'{D}/plan.json'))
def name(tag): k, i = tag.rsplit('__', 1); return cands[k][int(i)]
def url(n, w):
    n = n.replace(' ', '_'); h = hashlib.md5(n.encode()).hexdigest(); q = urllib.parse.quote(n); ext = n.rsplit('.', 1)[-1].lower()
    suf = '' if ext in ('jpg', 'jpeg', 'png') else '.jpg' if ext in ('tif', 'tiff') else '.png'
    return f'https://upload.wikimedia.org/wikipedia/commons/thumb/{h[0]}/{h[:2]}/{q}/{w}px-{q}{suf}'
def fetch(item):
    n, tag = item; out = f'{MED}/{n}.jpg'
    if os.path.exists(out) and os.path.getsize(out) > 5000: return n, 'ok'
    nm = name(tag)
    for a in range(10):
        for w in (1920, 1280, 960, 330):
            try:
                data = urllib.request.urlopen(urllib.request.Request(url(nm, w), headers=UA), timeout=60).read()
                open(out, 'wb').write(data); return n, 'ok'
            except urllib.error.HTTPError as e:
                if e.code == 429: time.sleep(15 * (a + 1)); break
            except Exception: time.sleep(3)
    return n, 'ERROR ' + nm
items = sorted((n, v[1]) for n, v in plan.items() if v[0] == 'commons')
with ThreadPoolExecutor(2) as ex:
    for n, r in ex.map(fetch, items):
        if r != 'ok': print(n, r, flush=True)
print('DLDONE', flush=True)
