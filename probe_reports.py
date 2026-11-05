import json, re, ssl, random, urllib.request, urllib.parse, concurrent.futures as cf
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36'}
def get(u,t=12,limit=600000):
    for cand in ([u] if u.startswith('http') else ['http://'+u,'https://'+u]):
        try:
            r=urllib.request.urlopen(urllib.request.Request(cand,headers=UA),timeout=t,context=ctx)
            return r.read(limit).decode('utf-8','ignore'), r.geturl()
        except Exception as e:
            last=e
    raise last

def links(html, base):
    out=[]
    for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.S|re.I):
        href, txt = m.group(1), re.sub(r'<[^>]+>','',m.group(2))
        txt=txt.strip()[:40]
        out.append((urllib.parse.urljoin(base,href), txt))
    return out

def probe(row):
    res={'n':row['zh'],'home':0,'rep_page':0,'pdf':0}
    try:
        h,base=get(row['webpage'])
        res['home']=1
    except Exception as e:
        return res
    cand=[(u,t) for u,t in links(h,base) if re.search(r'報告|report', u+t, re.I) and re.search(r'報告|report|計劃|plan', u+t, re.I)]
    # prefer pages over pdfs at this stage
    for u,t in cand[:6]:
        if u.lower().endswith('.pdf'): 
            res['pdf']+=1; continue
        try:
            h2,b2=get(u,10)
            res['rep_page']=1
            pdfs=[x for x,y in links(h2,b2) if x.lower().endswith('.pdf')]
            res['pdf']+=len([p for p in pdfs if re.search(r'報告|report', p, re.I)][:5])
            if res['pdf']: return res
        except Exception:
            continue
    return res

rows=json.load(open('data/schools.json'))
random.seed(11); samp=random.sample(rows,14)
with cf.ThreadPoolExecutor(max_workers=7) as ex:
    for r in ex.map(probe,samp):
        print(r['n'],'| home',r['home'],'rep_page',r['rep_page'],'pdf',r['pdf'])
print('---done')
