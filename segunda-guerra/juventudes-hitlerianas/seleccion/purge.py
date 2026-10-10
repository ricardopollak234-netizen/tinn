# uso: purge.py topic i,j,k  -> conserva solo esos candidatos (reindexados en ese orden)
import json, os, sys
D = os.path.dirname(os.path.abspath(__file__)); k = sys.argv[1]; keep = [int(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 and sys.argv[2] else []
c = json.load(open(f'{D}/cands.json')); old = c[k]
tmp = {}
for new, i in enumerate(keep):
    p = f'{D}/thumbs/{k}__{i}.jpg'
    if os.path.exists(p): tmp[new] = open(p, 'rb').read()
for i in range(len(old)):
    p = f'{D}/thumbs/{k}__{i}.jpg'
    if os.path.exists(p): os.remove(p)
for new, data in tmp.items(): open(f'{D}/thumbs/{k}__{new}.jpg', 'wb').write(data)
c[k] = [old[i] for i in keep]
bl = set(json.load(open(f'{D}/bl.json'))) if os.path.exists(f'{D}/bl.json') else set()
bl |= {old[i] for i in range(len(old)) if i not in keep}; json.dump(sorted(bl), open(f'{D}/bl.json', 'w'), ensure_ascii=False)
json.dump(c, open(f'{D}/cands.json', 'w'), ensure_ascii=False, indent=0)
g = json.load(open(f'{D}/good.json')); g[k] = list(range(len(keep))); json.dump(g, open(f'{D}/good.json', 'w'))
print(k, c[k])
