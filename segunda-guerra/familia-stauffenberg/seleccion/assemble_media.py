"""Asigna una foto/clip distinto a cada escena y lo deja en medios/NNN.ext.
Uso: python3 assemble_media.py CARPETA_VIDEO
"""
import urllib.error, json, os, re, sys, time, html, hashlib, urllib.parse, urllib.request, subprocess, csv
from concurrent.futures import ThreadPoolExecutor
S = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, S)
from mapping import MAP
from assets import A
V = sys.argv[1]; MED = os.path.join(V, 'medios'); os.makedirs(MED, exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 TinnDocBot/1.0 (santymoli02@gmail.com)'}
cands = json.load(open(f'{S}/cands/cands.json'))
picks = json.load(open(f'{S}/picks.json'))
clips = json.load(open(f'{S}/clips.json'))
over = json.load(open(f'{S}/scene_override.json')) if os.path.exists(f'{S}/scene_override.json') else {}

def cand_name(tag):
    k, i = tag.rsplit('__', 1)
    return cands[k][int(i)]

plan = {}; used = set(); problems = []
pool = {k: list(v) for k, v in picks.items()}
from collections import Counter as _C
_oc = _C(cand_name(t) for n_, t in over.items() if n_ not in clips)
assert not [x for x, c in _oc.items() if c > 1], [x for x, c in _oc.items() if c > 1]
used |= set(_oc)
for n0, m in enumerate(MAP, 1):
    n = f'{n0:03d}'; key = m.split('|')[0]; tipo = A[key][0]
    if n in clips:
        plan[n] = ('clip', clips[n]); continue
    if n in over:
        tag = over[n]; plan[n] = ('commons', tag); used.add(cand_name(tag)); continue
    if tipo in ('GRAF', 'MAPA'):
        plan[n] = ('graf', None); continue
    if tipo == 'GLABS':
        plan[n] = ('glabs', key); continue
    got = None
    for tag in pool.get(key, []):
        if cand_name(tag) not in used:
            got = tag; break
    if got is None:
        problems.append((n, key)); plan[n] = ('missing', key); continue
    pool[key].remove(got); used.add(cand_name(got)); plan[n] = ('commons', got)

if problems:
    print('SIN FOTO ASIGNADA:', problems)
    if '--check' in sys.argv: sys.exit(1)
if '--check' in sys.argv:
    print('ok, todas asignadas'); sys.exit(0)

def url_full(name, w=1920):
    n = name.replace(' ', '_'); h = hashlib.md5(n.encode()).hexdigest(); q = urllib.parse.quote(n)
    ext = n.rsplit('.', 1)[-1].lower()
    suf = '' if ext in ('jpg', 'jpeg', 'png') else '.jpg' if ext in ('tif', 'tiff') else '.png'
    return f'https://upload.wikimedia.org/wikipedia/commons/thumb/{h[0]}/{h[:2]}/{q}/{w}px-{q}{suf}'
def url_orig(name):
    n = name.replace(' ', '_'); h = hashlib.md5(n.encode()).hexdigest()
    return f'https://upload.wikimedia.org/wikipedia/commons/{h[0]}/{h[:2]}/{urllib.parse.quote(n)}'
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()

def fetch(item):
    n, (kind, val) = item
    if kind != 'commons': return n, None
    name = cand_name(val); out = os.path.join(MED, f'{n}.jpg')
    if os.path.exists(out) and os.path.getsize(out) > 5000: return n, name
    for attempt in range(6):
        for u in (url_full(name, 1920), url_full(name, 1280)):
            try:
                data = get(u); open(out, 'wb').write(data); return n, name
            except urllib.error.HTTPError as e:
                if e.code == 429: time.sleep(10 * (attempt + 1)); break
            except Exception:
                time.sleep(2)
    return n, 'ERROR:' + name

with ThreadPoolExecutor(3) as ex:
    res = list(ex.map(fetch, sorted(plan.items())))
errs = [r for r in res if r[1] and r[1].startswith('ERROR')]
print('descargas con error:', errs)

# clips
CL = os.path.join(S, 'clips_dl')
rows = list(csv.reader(open(os.path.join(V, 'tiempos_escenas.csv'), encoding='utf-8-sig'), delimiter=';'))[1:]
dur = {r[0]: float(r[3]) for r in rows}
for n, (kind, val) in plan.items():
    if kind != 'clip': continue
    f, start, crop, _ = val
    out = os.path.join(MED, f'{n}.mp4')
    if os.path.exists(out) and n != '053': continue
    vf = 'crop=ih*4/3:ih,' if crop == 'pillar' else ''
    vf += 'scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(start), '-i', os.path.join(CL, f), '-t', f'{dur[n] + 0.6:.2f}',
                    '-vf', vf, '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', out], check=True)

json.dump({n: [k, v] for n, (k, v) in plan.items()}, open(os.path.join(S, 'plan_final.json'), 'w'), ensure_ascii=False, indent=0)
from collections import Counter
print(Counter(k for k, v in plan.values()))
