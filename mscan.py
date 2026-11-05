import json,re,ssl,os,sys,urllib.parse as up,urllib.request as ur,concurrent.futures as cf
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36','Accept-Language':'zh-HK,zh;q=0.9,en;q=0.8'}
def get(u):
    try:
        r=ur.urlopen(ur.Request(u,headers=UA),timeout=20,context=ctx)
        b=r.read(6*1024*1024)
        ct=r.headers.get('Content-Type','')
        try: return b.decode('utf-8',errors='ignore') if 'pdf' not in ct else ''
        except: return ''
    except Exception as e:
        return 'ERR:'+str(e)[:60]
SCH=json.load(open('data/reports/manual/shatin_1.json'))
KW=re.compile(r'(報告|report|校務|周年|年報|計劃|plan)',re.I)
PDF=re.compile(r'href=["\']([^"\']+\.pdf[^"\']*)["\']',re.I)
def scan(s):
    base=s['web'].rstrip('/')
    home=get(base+'/')
    if home.startswith('ERR'): return s['id'],{'err':home,'pdfs':[]}
    links=set()
    for m in re.finditer(r'href=["\']([^"\']+)["\'][^>]*>([^<]{0,60})',home):
        h,txt=m.group(1),m.group(2)
        if KW.search(h) or KW.search(txt):
            links.add(up.urljoin(base+'/',h))
    pdfs=set()
    for m in PDF.finditer(home): pdfs.add(up.urljoin(base+'/',m.group(1)))
    pages=list(links)[:14]
    for p in pages:
        if p.lower().endswith('.pdf'): pdfs.add(p); continue
        h2=get(p)
        if h2.startswith('ERR'): continue
        for m in PDF.finditer(h2): pdfs.add(up.urljoin(p,m.group(1)))
        for m in re.finditer(r'href=["\']([^"\']+)["\'][^>]*>([^<]{0,60})',h2):
            hh,tt=m.group(1),m.group(2)
            if (KW.search(hh) or KW.search(tt)) and len(pdfs)<60:
                q=up.urljoin(p,hh)
                if '.pdf' in q.lower(): pdfs.add(q)
    return s['id'],{'home_ok':True,'pdfs':sorted(pdfs)[:60],'pages':pages}
res={}
with cf.ThreadPoolExecutor(max_workers=8) as ex:
    for sid,r in ex.map(scan,SCH): res[sid]=r
json.dump(res,open('data/reports/manual/scan1.json','w'),ensure_ascii=False,indent=1)
for s in SCH:
    r=res[s['id']]
    print('==',s['id'],s['name'],len(r.get('pdfs',[])),r.get('err',''))
    for p in r.get('pdfs',[])[:25]: print('   ',p)
