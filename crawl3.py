import json, re, ssl, os, sys, urllib.request, urllib.parse, concurrent.futures as cf

ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36',
    'Accept':'text/html,application/xhtml+xml,application/pdf,*/*;q=0.8','Accept-Language':'zh-HK,zh;q=0.9,en;q=0.7'}
REPORT=re.compile(r'報告|report',re.I)
ANNUAL=re.compile(r'(學校報告|校務報告|周年報告|年度報告|全校報告|school[\s_-]*report|annual[\s_-]*report|yearly[\s_-]*report)',re.I)
DROP=re.compile(r'(progress|grant|esr|external[\s_-]*school|panel|科組|進度|津貼|標籤|問卷|問卷調查|活動報告|實習|study[\s_-]*tour|交流團|student[\s_-]*report|成績報告)',re.I)
YR=re.compile(r'(20(?:2[1-6]))\s*[-–_/至~]\s*((?:20)?2[2-7])')
YR2=re.compile(r'(20(?:2[1-6]))(20(?:2[2-7]))')

def norm_year(s):
    out=set()
    for m in YR.finditer(s):
        a=int(m.group(1)); b=m.group(2); b=int(b) if len(b)==4 else 2000+int(b)
        if 2021<=a<=2026 and a+1==b: out.add(f'{a}-{str(b)[2:]}')
    for m in YR2.finditer(s):
        a=int(m.group(1)); b=int(m.group(2))
        if 2021<=a<=2026 and a+1==b: out.add(f'{a}-{str(b)[2:]}')
    # single year as publication year -> school year y-1/y
    for m in re.finditer(r'(20(?:2[1-6]))', s):
        y=int(m.group(1))
        if not out and 2021<=y<=2026: out.add(f'{y-1}-{str(y)[2:]}')
    return {x for x in out if x[:4] in ('2021','2022','2023','2024','2025')}

def fetch(u,t=15,maxb=900000):
    cands=[u] if u.startswith('http') else ['https://'+u,'http://'+u]
    if '://www.' in cands[0]: cands.append(cands[0].replace('://www.','://',1))
    if '://' in cands[0] and '://www.' not in cands[0]:
        p=urllib.parse.urlparse(cands[0]); cands.append(f'{p.scheme}://www.{p.netloc}{p.path}')
    last=None
    for c in dict.fromkeys(cands):
        try:
            r=urllib.request.urlopen(urllib.request.Request(c,headers=UA),timeout=t,context=ctx)
            return r.read(maxb), r.geturl()
        except Exception as e: last=e
    raise last

def anchors(html,base):
    out=[]
    for m in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',html,re.S|re.I):
        out.append((urllib.parse.urljoin(base,m.group(1)), re.sub(r'\s+',' ',re.sub(r'<[^>]+>','',m.group(2))).strip()[:60]))
    for m in re.finditer(r'<(?:iframe|embed|object)\b[^>]*(?:src|data)=["\']([^"\']+)["\']',html,re.I):
        out.append((urllib.parse.urljoin(base,m.group(1)),''))
    return out

def crawl(row):
    rec={'id':row['id'],'name':row['zh'],'home':row['webpage'],'pdfs':[],'pages':[],'note':''}
    try:
        d,base=fetch(row['webpage']); html=d.decode('utf-8','ignore')
    except Exception:
        rec['note']='home_fail'; return rec
    links=anchors(html,base)
    pages=[]
    for u,t in links:
        if u.lower().endswith('.pdf'): continue
        if REPORT.search(t) or REPORT.search(u.split('?')[0][-40:]):
            if u not in pages: pages.append(u)
    found={}
    def consider(u,t=''):
        if DROP.search(u) or DROP.search(t): return
        blob=u+' '+t
        if not REPORT.search(blob): return
        if not (ANNUAL.search(blob) or norm_year(blob)): return
        found.setdefault(u,set()).update(norm_year(blob))
    for u,t in links:
        if u.lower().endswith('.pdf'): consider(u,t)
    for u in pages[:6]:
        try: d2,b2=fetch(u,12,900000); h2=d2.decode('utf-8','ignore')
        except Exception: continue
        rec['pages'].append(u)
        for u2,t2 in anchors(h2,b2):
            if u2.lower().endswith('.pdf'): consider(u2,t2)
            elif 'drive.google.com' in u2 or 'docs.google.com' in u2:
                if ANNUAL.search(u2+t2): found.setdefault(u2,set())
    rec['pdfs']=[{'u':u,'y':sorted(v)} for u,v in list(found.items())[:15]]
    if not rec['pdfs']: rec['note']='no_pdf'
    return rec

rows=json.load(open('data/schools.json'))
path='data/reports/crawl3.json'
out=json.load(open(path)) if os.path.exists(path) else {}
lo=int(sys.argv[1]) if len(sys.argv)>1 else 0
hi=int(sys.argv[2]) if len(sys.argv)>2 else len(rows)
todo=[r for r in rows[lo:hi] if r['id'] not in out]
print('todo',len(todo),flush=True)
def work(r):
    try: return crawl(r)
    except Exception:
        return {'id':r['id'],'name':r['zh'],'home':r.get('webpage',''),'pdfs':[],'pages':[],'note':'err'}
with cf.ThreadPoolExecutor(max_workers=12) as ex:
    for i,rec in enumerate(ex.map(work,todo)):
        out[rec['id']]=rec
        if i%25==0:
            json.dump(out,open(path,'w'),ensure_ascii=False); print(i,len(out),flush=True)
json.dump(out,open(path,'w'),ensure_ascii=False)
print('done',len(out))
