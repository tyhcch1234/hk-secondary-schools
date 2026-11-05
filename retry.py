import json, re, os, ssl, subprocess, tempfile, urllib.request, concurrent.futures as cf
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36',
    'Referer':'https://www.google.com/'}
def drive_id(u):
    m=re.search(r'/d/([A-Za-z0-9_-]{20,})',u) or re.search(r'[?&]id=([A-Za-z0-9_-]{20,})',u)
    return m.group(1) if m else None
def dl(u):
    if 'drive.google.com' in u or 'docs.google.com' in u:
        i=drive_id(u)
        if not i: return None
        u=f'https://drive.google.com/uc?export=download&id={i}'
    for _ in range(2):
        try:
            r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=30,context=ctx)
            b=r.read(22*1024*1024)
            if b[:4]==b'%PDF': return b
            if b[:2]==b'PK' or b'%PDF' in b[:2000]: 
                k=b.find(b'%PDF'); return b[k:]
            return None
        except Exception: pass
    return None
def txt(b):
    fd,p=tempfile.mkstemp(suffix='.pdf'); os.write(fd,b); os.close(fd)
    try: return subprocess.run(['pdftotext','-layout','-enc','UTF-8',p,'-'],capture_output=True,text=True,timeout=150).stdout
    except Exception: return ''
    finally: os.unlink(p)
def yr(t,u):
    for a,b in re.findall(r'(20(?:2[1-6]))\s*[-–—/至]\s*((?:20)?2[2-7])', (t[:2000]+' '+u)):
        a=int(a); b=int(b) if len(b)==4 else 2000+int(b)
        if a+1==b and 2021<=a<=2025: return f'{a}-{str(b)[2:]}'
    return ''
idx=json.load(open('data/reports/pdf_index.json'))
crawl=json.load(open('data/reports/crawl3.json'))
targets=[sid for sid,v in idx.items() if not v]
print('retry schools',len(targets),flush=True)
def work(sid):
    out=[]
    for p in crawl.get(sid,{}).get('pdfs',[]):
        u=p['u']; b=dl(u)
        if not b: continue
        t=txt(b)
        if len(t)<800: continue
        if '關注事項' not in t and 'major concern' not in t.lower(): continue
        sc=sum(1 for s in ['關注事項','成效','檢討','辦學目標'] if s in t)
        y=yr(t,u)
        if not y: continue
        out.append({'u':u,'y':y,'sc':sc,'chars':len(t),'t':t})
    best={}
    for o in out:
        if o['y'] not in best or o['sc']>best[o['y']]['sc']: best[o['y']]=o
    keep=[{'y':v['y'],'u':v['u'],'sc':v['sc'],'chars':v['chars']} for v in best.values()]
    keep=sorted(keep,key=lambda x:x['y'])[-3:]
    for o in best.values():
        if any(k['y']==o['y'] for k in keep):
            open(f"data/reports/txt/{sid}_{o['y']}.txt",'w',encoding='utf-8').write(o['t'])
    return sid,keep
with cf.ThreadPoolExecutor(max_workers=10) as ex:
    for i,(sid,keep) in enumerate(ex.map(work,targets)):
        if keep: idx[sid]=keep
        if i%15==0:
            json.dump(idx,open('data/reports/pdf_index.json','w'),ensure_ascii=False); print(i,flush=True)
json.dump(idx,open('data/reports/pdf_index.json','w'),ensure_ascii=False)
print('schools with data now',sum(1 for v in idx.values() if v))
