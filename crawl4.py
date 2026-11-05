import json,re,ssl,os,sys,urllib.request,urllib.parse,concurrent.futures as cf
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36'}
KW=re.compile(r'(報告|report|年報|校務|週年|周年|annual|school[\s_-]*document|學校文件|計劃與報告|計劃及報告)',re.I)
PDFOK=re.compile(r'(報告|report)',re.I)
BAD=re.compile(r'(progress|grant|esr|external[\s_-]*school|panel|科組|津貼|標籤|問卷|活動報告|study[\s_-]*tour|交流|student[\s_-]*report|成績|national[\s_-]*security)',re.I)
def fetch(u,t=12,maxb=900000):
    cands=[u] if u.startswith('http') else ['https://'+u,'http://'+u]
    err=None
    for c in dict.fromkeys(cands):
        try:
            r=urllib.request.urlopen(urllib.request.Request(c,headers=UA),timeout=t,context=ctx)
            return r.read(maxb), r.geturl()
        except Exception as e: err=e
    raise err
def anchors(h,b):
    out=[]
    for m in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',h,re.S|re.I):
        out.append((urllib.parse.urljoin(b,m.group(1)), re.sub(r'\s+',' ',re.sub(r'<[^>]+>','',m.group(2))).strip()[:60]))
    return out
def crawl(row):
    rec={'id':row['id'],'name':row['zh'],'home':row['webpage'],'pdfs':[],'note':''}
    try:
        d,base=fetch(row['webpage']); html=d.decode('utf-8','ignore')
    except Exception:
        rec['note']='home_fail'; return rec
    host=urllib.parse.urlparse(base).netloc
    links=anchors(html,base)
    pages=[u for u,t in links if not u.lower().endswith('.pdf') and (KW.search(t) or KW.search(u))][:8]
    found={}
    def add(u,t=''):
        if u.lower().endswith('.pdf') and PDFOK.search(u+' '+t) and not BAD.search(u):
            found.setdefault(u,True)
    for u,t in links: add(u,t)
    for u in pages:
        try: d2,b2=fetch(u,10); h2=d2.decode('utf-8','ignore')
        except Exception: continue
        for u2,t2 in anchors(h2,b2): add(u2,t2)
    # sitemap fallback
    if not found:
        for sm in ('/sitemap.xml','/sitemap_index.xml','/wp-sitemap.xml'):
            try:
                d3,b3=fetch(base.rstrip('/')+sm,10)
                for u in re.findall(r'<loc>([^<]+)</loc>', d3.decode('utf-8','ignore')):
                    add(u)
            except Exception: pass
    rec['pdfs']=[{'u':u,'y':[]} for u in list(found)[:10]]
    if not rec['pdfs']: rec['note']=rec['note'] or 'no_pdf'
    return rec
rows=json.load(open('data/schools.json'))
have=set(k for k,v in json.load(open('data/reports/parsed2.json')).items() if v)
path='data/reports/crawl4.json'
out=json.load(open(path)) if os.path.exists(path) else {}
todo=[r for r in rows if r['id'] not in have and r['id'] not in out]
print('todo',len(todo),flush=True)
def w(r):
    try: return crawl(r)
    except Exception: return {'id':r['id'],'name':r['zh'],'home':r.get('webpage',''),'pdfs':[],'note':'err'}
with cf.ThreadPoolExecutor(max_workers=12) as ex:
    for i,rec in enumerate(ex.map(w,todo)):
        out[rec['id']]=rec
        if i%25==0: json.dump(out,open(path,'w'),ensure_ascii=False); print(i,flush=True)
json.dump(out,open(path,'w'),ensure_ascii=False)
print('done',len(out),'with pdf',sum(1 for v in out.values() if v['pdfs']))
