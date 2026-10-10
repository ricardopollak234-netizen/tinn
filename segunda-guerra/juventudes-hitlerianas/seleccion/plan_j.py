import json, sys, os
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
from topics import R
S = {x['n']: x['t'] for x in json.load(open(f'{D}/scenes.json'))}
cands = json.load(open(f'{D}/cands.json')); good = json.load(open(f'{D}/good.json')); clips = json.load(open(f'{D}/clips.json'))
GRAF = {25, 43, 56, 89, 131, 334, 335, 348, 349, 350, 351, 352}
FORCE_IA = {'332', '266', '271'}
TOPIC_OVR = {15: 'hj_general', 24: 'hj_general', 41: 'hj_general', 42: 'hj_general', 49: 'hj_general', 50: 'hj_general', 26: 'hj_general', 277: 'flakhelfer', 278: 'pow_camp', 261: 'recap', 262: 'hj_general', 263: 'hj_general', 264: 'nuremberg', 265: 'nuremberg',
             267: 'witnesses', 268: 'witnesses', 269: 'witnesses', 270: 'witnesses', 286: 'hj_camps', 320: 'school_1945', 321: 'hj_camps', 322: 'pow_camp', 323: 'hj_general', 324: 'hj_general', 325: 'hj_general', 287: 'hj_camps', 288: 'volkssturm'}
# si el tema se queda sin fotos, se prueba con temas afines de la misma época (archivo antes que IA)
FALLBACK = {
 'hj_1945': ['volkssturm', 'flakhelfer', 'berlin_1945'], 'czech_1945': ['hj_1945', 'volkssturm', 'reichskanzlei'],
 'reichskanzlei': ['bunker', 'berlin_1945'], 'silesia_1945': ['wolfskinder', 'ruins_1945'], 'hitler_1945': ['bunker', 'hitler_1933'],
 'hj_general': ['hj_camps', 'bdm', 'recap'], 'hj_camps': ['hj_general'], 'bdm': ['hj_general'], 'klv': ['hj_general', 'bdm'],
 'flakhelfer': ['volkssturm', 'hj_division'], 'hj_division': ['flakhelfer', 'volkssturm'], 'volkssturm': ['flakhelfer', 'berlin_1945'],
 'berlin_1945': ['ruins_1945', 'volkssturm'], 'bunker': ['reichskanzlei', 'berlin_1945'], 'axmann': ['recap', 'hj_general'],
 'bormann': ['berlin_1945', 'bunker'], 'pow_camp': ['ruins_1945', 'hj_division', 'flakhelfer', 'volkssturm'], 'ruins_1945': ['truemmerfrauen', 'berlin_1945'],
 'truemmerfrauen': ['ruins_1945'], 'wolfskinder': ['silesia_1945', 'ruins_1945'], 'werwolf': ['volkssturm', 'aachen'],
 'aachen': ['ruins_1945'], 'gardelegen': ['pow_camp', 'ruins_1945', 'berlin_1945'], 'nkvd_camps': ['pow_camp', 'ruins_1945'], 'nuremberg': ['spandau', 'schirach'],
 'spandau': ['nuremberg'], 'ferdinand': ['schirach', 'spandau'], 'school_1945': ['schulspeisung', 'gya'], 'schulspeisung': ['school_1945', 'gya'],
 'gya': ['school_1945', 'schulspeisung'], 'fdj': ['school_1945'], 'skeptical': ['bonn_1950s', 'west_1960'], 'bonn_1950s': ['skeptical', 'west_1960'],
 'heck': ['witnesses', 'skeptical'], 'ratzinger': ['flakhelfer'], 'kohl': ['bonn_1950s'], 'writers': ['skeptical'], 'edelweiss': ['white_rose'],
 'white_rose': ['edelweiss'], 'students_1968': ['skeptical'], 'witnesses': ['skeptical'], 'recap': ['hj_general', 'schirach'],
 'west_1960': ['bonn_1950s', 'skeptical'], 'schirach': ['recap', 'nuremberg'], 'norkus': ['hitler_1933'], 'hitler_1933': ['hj_general'],
}
ia = {f[:3] for f in os.listdir(f'{D}/ia') if f.endswith('.png')}
topic = {}
for a, b, k in R:
    for n in range(a, b + 1): topic[n] = k
topic.update(TOPIC_OVR)
OVR = json.load(open(f'{D}/scene_override.json')) if os.path.exists(f'{D}/scene_override.json') else {}
def name(tag): k, i = tag.rsplit('__', 1); return cands[k][int(i)]
pools = {k: [f'{k}__{x}' for x in v] for k, v in good.items()}
plan, used, missing = {}, set(), []
for t in OVR.values(): used.add(name(t))
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
            if nm not in used: got = tag; break
        if got: pools[kk].remove(got); break
    if got: used.add(name(got)); plan[s] = ['commons', got]
    else: plan[s] = ['ia', None]; missing.append((s, k))
json.dump(plan, open(f'{D}/plan.json', 'w'), indent=0)
from collections import Counter
print(Counter(v[0] for v in plan.values()))
print('IA nuevas:', len(missing)); print(missing)
