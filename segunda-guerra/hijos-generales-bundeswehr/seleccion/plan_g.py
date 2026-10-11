import json, sys, os
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
from topics import R
S = {x['n']: x['t'] for x in json.load(open(f'{D}/scenes.json'))}
cands = json.load(open(f'{D}/cands.json')); good = json.load(open(f'{D}/good.json')); clips = json.load(open(f'{D}/clips.json'))
GRAF = {23, 44, 87, 129, 281, 289, 290, 299, 335, 350, 352, 354}
FORCE_IA = set()
TOPIC_OVR = {}
FALLBACK = {
 'ruhr_1945': ['ruins_1945', 'pow_1945'], 'model': ['recap'], 'vossenack': ['ruins_1945'], 'bw_1956': ['bw_generals', 'bw_1960s'],
 'bw_generals': ['bw_1956', 'speidel_heusinger'], 'recap': ['wehrmacht_honor', 'model', 'guderian'], 'ruins_1945': ['ruhr_1945', 'pow_1945'],
 'potsdam': ['control_council', 'ruins_1945'], 'control_council': ['potsdam', 'ruins_1945'], 'pow_1945': ['ruhr_1945', 'heimkehrer'],
 'young_soldiers': ['pow_1945', 'ruhr_1945'], 'ohne_mich': ['ruins_1945', 'young_soldiers', 'bundestag'], 'korea': ['eisenhower'],
 'adenauer': ['bundestag', 'bw_1956'], 'himmerod': ['speidel_heusinger'], 'speidel_heusinger': ['bw_generals'], 'senger_father': ['senger'],
 'wehrmacht_honor': ['recap', 'waffen_ss'], 'eisenhower': ['speidel_heusinger', 'adenauer'], 'bundestag': ['adenauer'],
 'nato_1955': ['adenauer', 'bw_1956'], 'scharnhorst': ['bw_founding'], 'bw_founding': ['bw_1956', 'speidel_heusinger'],
 'pga': ['bw_generals', 'stauffenberg'], 'waffen_ss': ['wehrmacht_honor'], 'heimkehrer': ['pow_1945'], 'erdmannsdorff': ['bagration', 'pow_1945'],
 'bagration': ['erdmannsdorff', 'recap'], 'foertsch': ['heimkehrer', 'bw_generals'], 'bw_1960s': ['bw_1956', 'senger_son'],
 'soviet_withdrawal': ['bw_1980s', 'nva'], 'ciliax': ['friedeburg'], 'senger': ['senger_father', 'recap'], 'senger_son': ['bw_1960s', 'bw_1980s'],
 'guderian': ['recap'], 'guderian_son': ['guderian', 'bw_1960s'], 'oster': ['fellgiebel', 'stauffenberg'], 'spiegel': ['bundestag', 'adenauer'],
 'stauffenberg': ['oster', 'fellgiebel'], 'rommel': ['tradition', 'recap'], 'friedeburg': ['ciliax', 'keitel'], 'keitel': ['recap'],
 'fellgiebel': ['stauffenberg', 'oster'], 'innere_fuehrung': ['bw_1956', 'bw_1960s', 'recap', 'wehrmacht_honor'], 'rudel': ['bw_1960s', 'tradition'],
 'tradition': ['rommel', 'bw_1980s'], 'manstein_schoerner': ['recap'], 'exhibition': ['tradition', 'recap'], 'nva': ['soviet_withdrawal'],
 'bw_1980s': ['bw_1960s', 'de_maiziere'], 'speidel_son': ['speidel_heusinger', 'bw_1980s'], 'de_maiziere': ['bw_1980s', 'bw_generals'],
}
ia = {f[:3] for f in os.listdir(f'{D}/ia') if f.endswith('.png')}
topic = {}
for a, b, k in R:
    for n in range(a, b + 1): topic[n] = k
topic.update(TOPIC_OVR)
for n in range(1, len(S) + 1):
    if n not in topic: topic[n] = topic.get(n - 1, 'recap')
OVR = json.load(open(f'{D}/scene_override.json')) if os.path.exists(f'{D}/scene_override.json') else {}
def name(tag): k, i = tag.rsplit('__', 1); return cands[k][int(i)]
from PIL import Image
def dh(p):
    try: im = Image.open(p).convert('L').resize((17, 16))
    except Exception: return None
    px = list(im.getdata())
    return sum(1 << i for i in range(256) if px[(i // 16) * 17 + i % 16] > px[(i // 16) * 17 + i % 16 + 1])
HASH = {}
def h(tag):
    if tag not in HASH: HASH[tag] = dh(f'{D}/thumbs/{tag}.jpg')
    return HASH[tag]
used_h = []
def similar(tag):
    x = h(tag)
    return x is not None and any(bin(x ^ y).count('1') < 60 for y in used_h)
def mark(tag):
    if h(tag) is not None: used_h.append(h(tag))
pools = {k: [f'{k}__{x}' for x in v] for k, v in good.items()}
plan, used, missing = {}, set(), []
for t in OVR.values(): used.add(name(t)); mark(t)
for n in range(1, len(S) + 1):
    s = f'{n:03d}'
    if s in clips: plan[s] = ['clip', clips[s][:2]]; continue
    if n in GRAF: plan[s] = ['graf', None]; continue
    if s in OVR: plan[s] = ['commons', OVR[s]]; continue
    if s in FORCE_IA: plan[s] = ['ia', None]; missing.append((s, 'forzada')); continue
    if s in ia: plan[s] = ['ia', None]; continue
    k = topic[n]; got = None
    for kk in [k] + FALLBACK.get(k, []):
        for tag in pools.get(kk, []):
            try: nm = name(tag)
            except (KeyError, IndexError): continue
            if nm not in used and not similar(tag): got = tag; break
        if got: pools[kk].remove(got); break
    if got: used.add(name(got)); mark(got); plan[s] = ['commons', got]
    else: plan[s] = ['ia', None]; missing.append((s, k))
json.dump(plan, open(f'{D}/plan.json', 'w'), indent=0)
from collections import Counter
print(Counter(v[0] for v in plan.values()))
print('IA nuevas:', len(missing)); print(missing)
