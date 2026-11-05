import json, re, ssl, os, sys, subprocess, tempfile, urllib.request, concurrent.futures as cf

ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36'}
MAXB=22*1024*1024

def download(u):
    for _ in range(2):
        try:
            r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=25,context=ctx)
            b=r.read(MAXB)
            if b[:4]==b'%PDF': return b
            return None
        except Exception:
            pass
    return None

def pdftext(b):
    fd,p=tempfile.mkstemp(suffix='.pdf'); os.write(fd,b); os.close(fd)
    try:
        r=subprocess.run(['pdftotext','-layout','-enc','UTF-8',p,'-'],capture_output=True,text=True,timeout=120)
        return r.stdout
    except Exception:
        return ''
    finally:
        os.unlink(p)

SIG=['關注事項','學校報告','校務報告','辦學目標','成效','檢討','學生表現']
ANNUAL=re.compile(r'(學校報告|校務報告|周年報告|annual[\s_-]*school[\s_-]*report|school[\s_-]*report)',re.I)
BAD=re.compile(r'(national[\s_-]*security|國家安全|plan|計劃|grant|津貼|esr|external[\s_-]*school|progress|subject|panel|科組|標籤)',re.I)
def score(t,u=''):
    sc=sum(1 for s in SIG if s in t)
    blob=(u or '')+' '+t[:1500]
    if ANNUAL.search(blob): sc+=3
    if '成效' in t and '關注事項' in t: sc+=2
    if len(t)>40000: sc+=1
    tail=(u or '').split('/')[-1]
    if BAD.search(tail): sc-=4
    if '關注事項' not in t: sc-=5
    return sc

def year_of(t, url):
    head=t[:3000]
    cands=re.findall(r'(20(?:2[1-6]))\s*[-–—/至]\s*((?:20)?2[2-7])', head+' '+url)
    for a,b in cands:
        a=int(a); b=int(b) if len(b)==4 else 2000+int(b)
        if a+1==b and 2021<=a<=2025: return f'{a}-{str(b)[2:]}'
    return ''

def handle(item):
    sid,rec=item
    import glob as _g
    if _g.glob(f'data/reports/txt/{sid}_*.txt'): return sid, []
    out=[]
    for p in rec['pdfs']:
        u=p['u']
        b=download(u)
        if not b: continue
        t=pdftext(b)
        if len(t)<800: continue
        sc=score(t,u)
        if sc<2: continue
        y=year_of(t,u) or (p['y'][0] if p['y'] else '')
        out.append({'u':u,'y':y,'sc':sc,'len':len(t),'t':t})
    # keep best per year, prefer target years
    best={}
    for o in out:
        y=o['y']
        if y and (y not in best or o['sc']>best[y]['sc']): best[y]=o
    keep=[v for y,v in best.items() if y in ('2021-22','2022-23','2023-24','2024-25','2025-26')]
    keep=sorted(keep,key=lambda x:x['y'])[-3:]
    for o in keep:
        open(f"data/reports/txt/{sid}_{o['y']}.txt",'w',encoding='utf-8').write(o['t'])
    return sid,[{'y':o['y'],'u':o['u'],'sc':o['sc'],'chars':len(o['t'])} for o in keep]

rows=json.load(open('data/schools.json'))
crawl=json.load(open('data/reports/crawl4.json'))
items=[(r['id'],crawl[r['id']]) for r in rows if crawl.get(r['id'],{}).get('pdfs')]
lo=int(sys.argv[1]) if len(sys.argv)>1 else 0
hi=int(sys.argv[2]) if len(sys.argv)>2 else len(items)
items=items[lo:hi]
res={}
if os.path.exists('data/reports/pdf_index4.json'):
    res=json.load(open('data/reports/pdf_index4.json'))
with cf.ThreadPoolExecutor(max_workers=7) as ex:
    for i,(sid,kept) in enumerate(ex.map(handle,items)):
        res[sid]=kept
        if i%15==0:
            json.dump(res,open('data/reports/pdf_index4.json','w'),ensure_ascii=False); print(i,flush=True)
json.dump(res,open('data/reports/pdf_index4.json','w'),ensure_ascii=False)
print('done',len(res))
