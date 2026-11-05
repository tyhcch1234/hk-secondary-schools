import json, re, ssl, os, sys, urllib.request, urllib.parse, concurrent.futures as cf

ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36',
    'Accept-Language':'zh-HK,zh;q=0.9,en;q=0.8'}
KEEP=re.compile(r'(學校報告|校務報告|周年報告|年度報告|school[\s_-]*report|annual[\s_-]*report|yearly[\s_-]*report|報告及計劃|計劃及報告)',re.I)
DROP=re.compile(r'(progress|grant|esr|external[\s_-]*school|subject|panel|科組|進度|津貼|標籤|問卷|課程|活動報告|實習|study[\s_-]*tour)',re.I)
YEARRE=re.compile(r'(20(2[2-6]))\s*[-–_/至~]\s*((?:20)?2[3-7])')

def fetch(u,t=10,maxb=900000):
    errs=[]
    cands=[u] if u.startswith('http') else ['https://'+u,'http://'+u]
    if u.startswith('http') and '://www.' in u:
        cands.append(u.replace('://www.','://',1))
    for c in cands:
        try:
            r=urllib.request.urlopen(urllib.request.Request(c,headers=UA),timeout=t,context=ctx)
            return r.read(maxb), r.geturl()
        except Exception as e:
            errs.append(e)
    raise errs[-1]

def anchors(html,base):
    out=[]
    for m in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',html,re.S|re.I):
        out.append((urllib.parse.urljoin(base,m.group(1)), re.sub(r'\s+',' ',re.sub(r'<[^>]+>','',m.group(2))).strip()[:60]))
    for m in re.finditer(r'<(?:iframe|embed|object)\b[^>]*(?:src|data)=["\']([^"\']+)["\']',html,re.I):
        out.append((urllib.parse.urljoin(base,m.group(1)),''))
    return out

def years_of(s):
    out=set()
    for m in YEARRE.finditer(s):
        a=int(m.group(1)); b=m.group(2); b=int(b) if len(b)==4 else 2000+int(b)
        out.add(f'{a}-{str(b)[2:]}')
    for m in re.finditer(r'(20(2[2-6]))(20(2[3-7]))',s):
        out.add(f"{m.group(1)}-{m.group(4)[2:]}")
    return out

def crawl(row):
    rec={'id':row['id'],'name':row['zh'],'home':row['webpage'],'pdfs':[],'note':''}
    try:
        d,base=fetch(row['webpage'],10,700000); html=d.decode('utf-8','ignore')
    except Exception as e:
        rec['note']='home_fail'; return rec
    host=urllib.parse.urlparse(base).netloc
    links=anchors(html,base)
    # candidate report pages
    pages=[]
    for u,t in links:
        if u.lower().endswith('.pdf'): continue
        if KEEP.search(t) or KEEP.search(u):
            if u not in pages: pages.append(u)
    pdf={}
    def add(u):
        if DROP.search(u): return
        if not KEEP.search(u): return
        ys=years_of(u)
        pdf[u]=ys
    for u,t in links:
        if u.lower().endswith('.pdf'): add(u)
    for u in pages[:5]:
        if not u.startswith('http'): continue
        try:
            d2,b2=fetch(u,10,900000); h2=d2.decode('utf-8','ignore')
        except Exception: continue
        for u2,t2 in anchors(h2,b2):
            if u2.lower().endswith('.pdf'):
                if KEEP.search(u2) or KEEP.search(t2): add(u2)
                elif REPORT_YEAR_HINT(u2): pdf[u2]=years_of(u2)
    rec['pdfs']=[{'u':u,'y':sorted(v)} for u,v in list(pdf.items())[:12]]
    if not rec['pdfs']: rec['note']='no_pdf'
    return rec

def REPORT_YEAR_HINT(u):
    return bool(re.search(r'(?i)report',u)) and bool(years_of(u)) and not DROP.search(u)

rows=json.load(open('data/schools.json'))
path='data/reports/crawl2.json'
out=json.load(open(path)) if os.path.exists(path) else {}
todo=[r for r in rows if r['id'] not in out]
print('todo',len(todo),flush=True)
def work(r):
    try: return crawl(r)
    except Exception as e:
        return {'id':r['id'],'name':r['zh'],'home':row_safe(r),'pdfs':[],'note':'err'}
def row_safe(r): return r.get('webpage','')
with cf.ThreadPoolExecutor(max_workers=12) as ex:
    for i,rec in enumerate(ex.map(work,todo)):
        out[rec['id']]=rec
        if i%25==0:
            json.dump(out,open(path,'w'),ensure_ascii=False); print(i,flush=True)
json.dump(out,open(path,'w'),ensure_ascii=False)
print('done',len(out))
