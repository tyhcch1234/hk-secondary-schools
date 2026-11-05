import json, re, ssl, os, sys, time, urllib.request, urllib.parse, concurrent.futures as cf

ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36'}
MAXB=30*1024*1024

def fetch(u,t=12,maxb=800000):
    for cand in ([u] if u.startswith('http') else ['https://'+u,'http://'+u]):
        try:
            r=urllib.request.urlopen(urllib.request.Request(cand,headers=UA),timeout=t,context=ctx)
            data=r.read(maxb)
            return data, r.geturl(), r.headers.get('Content-Type','')
        except Exception as e:
            err=e
    raise err

def anchors(html, base):
    out=[]
    for m in re.finditer(r'<(a|iframe|embed|object)[^>]+(?:href|src)=["\']([^"\']+)["\'][^>]*>(.*?)</\1>', html, re.S|re.I):
        href=m.group(2); txt=re.sub(r'<[^>]+>','',m.group(3))[:60]
        out.append((urllib.parse.urljoin(base,href), txt))
    # standalone hrefs (void tags)
    for m in re.finditer(r'<(?:a|iframe|embed|object)\b[^>]*(?:href|src)=["\']([^"\']+)["\']', html, re.I):
        out.append((urllib.parse.urljoin(base,m.group(1)), ''))
    return out

REPORT_WORD=re.compile(r'報告|report', re.I)
PLAN_WORD=re.compile(r'計劃|计划|plan|報告|report', re.I)
YEAR=re.compile(r'(20(2[2-6]))\s*[-–_/至~]\s*(20)?(2[3-7])')

def detect_years(s):
    out=set()
    for m in YEAR.finditer(s):
        a=int(m.group(1)); b=int(m.group(4))
        out.add(f'{a}-{str(b) if b>20 else a+1}')
    for m in re.finditer(r'(20(2[2-6]))(20(2[3-7]))', s):
        out.add(f'{m.group(1)}-{m.group(4)}')
    return out

def safe(name):
    return re.sub(r'[^\w\-.]','_',name)

def crawl(row):
    sid=row['id']; rec={'id':sid,'name':row['zh'],'home':row['webpage'],'pages':[],'pdfs':[],'note':''}
    try:
        data,base,ct=fetch(row['webpage'],12,600000)
        html=data.decode('utf-8','ignore')
    except Exception as e:
        rec['note']='home_fail'; return rec
    links=anchors(html,base)
    cand=[(u,t) for u,t in links if REPORT_WORD.search(u+' '+t) and PLAN_WORD.search(u+' '+t)]
    # prefer report-ish and same-site
    host=urllib.parse.urlparse(base).netloc
    def score(x):
        u,t=x
        s=0
        if '報告' in t or '報告' in u: s-=3
        if '計劃' in t and '報告' not in t: s+=2
        if u.lower().endswith('.pdf'): s-=2
        if urllib.parse.urlparse(u).netloc!=host: s+=3
        return s
    cand=sorted(cand,key=score)
    pdfs=[]
    pages=0
    for u,t in cand:
        if len(pdfs)>=8 or pages>=4: break
        if u.lower().endswith('.pdf'):
            pdfs.append(u); continue
        if not u.startswith('http'): continue
        try:
            d,b2,_=fetch(u,10,800000); h2=d.decode('utf-8','ignore'); pages+=1
            rec['pages'].append(u)
            for u2,t2 in anchors(h2,b2):
                if u2.lower().endswith('.pdf') and REPORT_WORD.search(u2+' '+t2):
                    if u2 not in pdfs: pdfs.append(u2)
        except Exception:
            continue
    rec['pdfs']=pdfs[:8]
    if not pdfs: rec['note']='no_pdf'
    return rec

rows=json.load(open('data/schools.json'))
start=int(sys.argv[1]) if len(sys.argv)>1 else 0
end=int(sys.argv[2]) if len(sys.argv)>2 else len(rows)
out={}
path='data/reports/crawl.json'
if os.path.exists(path):
    out=json.load(open(path))
todo=[r for r in rows[start:end] if r['id'] not in out]
print('todo',len(todo),flush=True)
def work(r):
    try: return crawl(r)
    except Exception as e:
        return {'id':r['id'],'name':r['zh'],'home':r['webpage'],'pages':[],'pdfs':[],'note':'err:'+type(e).__name__}
with cf.ThreadPoolExecutor(max_workers=10) as ex:
    for i,rec in enumerate(ex.map(work,todo)):
        out[rec['id']]=rec
        if i%20==0:
            json.dump(out,open(path,'w'),ensure_ascii=False)
            print(i,len(out),flush=True)
json.dump(out,open(path,'w'),ensure_ascii=False)
print('done',len(out))
