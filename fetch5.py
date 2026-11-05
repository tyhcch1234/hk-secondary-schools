import json,re,os,ssl,glob,subprocess,tempfile,urllib.request,concurrent.futures as cf
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36'}
def dl(u):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=30,context=ctx)
        b=r.read(22*1024*1024)
        return b if b[:4]==b'%PDF' else None
    except Exception:
        return None
def txt(b):
    fd,p=tempfile.mkstemp(suffix='.pdf'); os.write(fd,b); os.close(fd)
    try:
        return subprocess.run(['pdftotext','-layout','-enc','UTF-8',p,'-'],capture_output=True,text=True,timeout=150).stdout
    except Exception: return ''
    finally:
        try: os.unlink(p)
        except: pass
def year(t,u):
    for a,b in re.findall(r'(20(?:2[1-6]))\s*[-–—/至]\s*((?:20)?2[2-7])', t[:2500]+' '+u):
        a=int(a); b=int(b) if len(b)==4 else 2000+int(b)
        if a+1==b and 2021<=a<=2025: return f'{a}-{str(b)[2:]}'
    return ''
crawl=json.load(open('data/reports/crawl4.json'))
todo=[(sid,v) for sid,v in crawl.items() if v['pdfs'] and not glob.glob(f'data/reports/txt/{sid}_*.txt')]
print('todo',len(todo),flush=True)
found={}
def work(item):
    sid,v=item; best={}
    for p in v['pdfs'][:8]:
        u=p['u']; b=dl(u)
        if not b: continue
        t=txt(b)
        if len(t)<800: continue
        if '關注事項' not in t and 'major concern' not in t.lower(): continue
        sc=sum(1 for s in ['關注事項','成效','檢討','辦學目標','成就'] if s in t)
        if sc<2: continue
        y=year(t,u)
        if not y: continue
        if y not in best or sc>best[y][0]: best[y]=(sc,t,u)
    for y,(sc,t,u) in best.items():
        open(f'data/reports/txt/{sid}_{y}.txt','w',encoding='utf-8').write(t)
    return sid,[(y,best[y][0]) for y in best]
with cf.ThreadPoolExecutor(max_workers=6) as ex:
    for sid,k in ex.map(work,todo):
        if k: found[sid]=k
        print(sid,k[:1],flush=True) if False else None
print('schools with new txt',len(found))
json.dump(found,open('data/reports/fetch5.json','w'),ensure_ascii=False)
