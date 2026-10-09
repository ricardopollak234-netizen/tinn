import json, sys, os
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
from topics import R
S = {x['n']: x['t'] for x in json.load(open(f'{D}/scenes.json'))}
cands = json.load(open(f'{D}/cands.json')); good = json.load(open(f'{D}/good.json')); clips = json.load(open(f'{D}/clips.json'))
GRAF = {24,25,37,38,42,106,109,149,206,225,230,245,334,349,350,351,352,353}
TOPIC_OVR = {26: 'berlin_1945', 335: 'recap'}
ia = {f[:3] for f in os.listdir(f'{D}/ia') if f.endswith('.png')}
topic = {}
for a, b, k in R:
    for n in range(a, b + 1): topic[n] = k
topic.update(TOPIC_OVR)
OVR = json.load(open(f'{D}/scene_override.json')) if os.path.exists(f'{D}/scene_override.json') else {}
def name(tag): k, i = tag.rsplit('__', 1); return cands[k][int(i)]
pools = {k: [x if isinstance(x, str) else f'{k}__{x}' for x in v] for k, v in good.items()}
plan, used, missing = {}, set(), []
for t in (json.load(open(f'{D}/scene_override.json')) if os.path.exists(f'{D}/scene_override.json') else {}).values(): used.add(name(t))
for n in range(1, len(S) + 1):
    s = f'{n:03d}'
    if s in clips: plan[s] = ['clip', clips[s][:2]]; continue
    if n in GRAF: plan[s] = ['graf', None]; continue
    if s in ia: plan[s] = ['ia', None]; continue
    if s in OVR: used.add(name(OVR[s])); plan[s] = ['commons', OVR[s]]; continue
    k = topic[n]; got = None
    for tag in pools.get(k, []):
        try: nm = name(tag)
        except (KeyError, IndexError): continue
        if nm not in used: got = tag; break
    if got: used.add(name(got)); pools[k].remove(got); plan[s] = ['commons', got]
    else: plan[s] = ['ia', None]; missing.append((s, k))
json.dump(plan, open(f'{D}/plan.json', 'w'), indent=0)
from collections import Counter
print(Counter(v[0] for v in plan.values()))
print('IA nuevas:', len(missing)); print(missing)
