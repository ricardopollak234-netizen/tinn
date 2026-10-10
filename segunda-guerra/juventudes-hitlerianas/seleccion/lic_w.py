import json,re,time,html,urllib.parse,urllib.request,urllib.error,os
UA={'User-Agent':'Mozilla/5.0 TinnDocBot/1.0 (santymoli02@gmail.com)'}
c=json.load(open('cands.json')); p=json.load(open('plan.json'))
names=sorted({c[v.rsplit('__',1)[0]][int(v.rsplit('__',1)[1])] for k,v in p.values() if k=='commons'})
extra=[]
out=json.load(open('lic.json')) if os.path.exists('lic.json') else {}
def strip(x): return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',x))).strip()
for n in names+extra:
    if n in out: continue
    url='https://commons.wikimedia.org/wiki/'+urllib.parse.quote('File:'+n.replace(' ','_'))
    for a in range(5):
        try: t=urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=40).read().decode('utf-8','replace'); break
        except urllib.error.HTTPError as e:
            t=None
            if e.code==404: break
            time.sleep(15*(a+1))
        except Exception: t=None; time.sleep(5)
    if not t: out[n]={'err':1}; continue
    lic=[strip(x) for x in re.findall(r'class="licensetpl(?:_|&#95;)short"[^>]*>(.*?)</span>',t,re.S)]
    m=re.search(r'id="fileinfotpl(?:_|&#95;)aut"[^>]*>.*?</td>\s*<td[^>]*>(.*?)</td>',t,re.S)
    aut=strip(m.group(1))[:160] if m else ''
    m=re.search(r'class="licensetpl(?:_|&#95;)attr"[^>]*>(.*?)</span>',t,re.S)
    attr=strip(m.group(1))[:200] if m else ''
    out[n]={'lic':sorted(set(lic)),'autor':aut,'attr':attr,'url':url}
    json.dump(out,open('lic.json','w'),ensure_ascii=False,indent=0)
    time.sleep(1.2)
print('LICDONE',len(out),sum(1 for v in out.values() if v.get('err')))
