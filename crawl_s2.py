import json,re,os,ssl,subprocess,tempfile,urllib.request,urllib.parse,concurrent.futures as cf,sys

ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
    'Accept':'text/html,application/xhtml+xml,application/pdf,*/*','Accept-Language':'zh-HK,zh;q=0.9,en;q=0.8'}
KW=re.compile(r'報告|报告|report|校務|校务|annual|計劃書|plan',re.I)

def get(u,limit=3_000_000):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40,context=ctx)
        return r.read(limit), r.geturl()
    except Exception as e:
        return None,None

def decode(b,ctype=''):
    m=re.search(r'charset=([\w-]+)',ctype or '',re.I)
    for enc in ([m.group(1)] if m else [])+['utf-8','big5','gb18030']:
        try: return b.decode(enc,errors='strict')
        except Exception: pass
    return b.decode('utf-8',errors='ignore')

def pdftext(b):
    fd,p=tempfile.mkstemp(suffix='.pdf'); os.write(fd,b); os.close(fd)
    try:
        return subprocess.run(['pdftotext','-layout','-enc','UTF-8',p,'-'],capture_output=True,text=True,timeout=180).stdout
    except Exception: return ''
    finally:
        try: os.unlink(p)
        except Exception: pass

YRE=[re.compile(r'20(2[1-6])\s*[-–—~至/]\s*((?:20)?2[2-7])'),re.compile(r'20(2[1-6])\s*[-–—~至/]\s*(\d\d)\s*年度')]
def findyear(t,u):
    s=(u or '')+' '+t[:3000]
    for rex in YRE:
        for a,b in rex.findall(s):
            a=2000+int(a); b=int(b) if len(b)==4 else 2000+int(b)
            if a+1==b and 2021<=a<=2025: return f'{a}-{str(b)[2:]}'
    return ''

def links(html,base):
    out=[]
    for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',html,re.I|re.S):
        href=m.group(1).strip(); txt=re.sub(r'<[^>]+>',' ',m.group(2))
        txt=re.sub(r'\s+',' ',txt)
        out.append((urllib.parse.urljoin(base,href),txt))
    return out

def crawl(sid,name,home,maxpages=14,maxpdf=40):
    seen=set(); pdfs=[]; queue=[(home,0)]; pages=0; tried=[]
    host=urllib.parse.urlparse(home).netloc.replace('www.','')
    while queue and pages<maxpages:
        u,d=queue.pop(0)
        if u in seen: continue
        seen.add(u)
        b,fin=get(u)
        if not b: continue
        if b[:4]==b'%PDF':
            pdfs.append(fin or u); continue
        pages+=1
        txt=decode(b)
        for url,at in links(txt,fin or u):
            if url in seen: continue
            low=url.lower()
            if low.endswith('.pdf'):
                if url not in pdfs: pdfs.append(url)
            elif KW.search(at+' '+urllib.parse.unquote(low)) and d<2:
                nh=urllib.parse.urlparse(url).netloc.replace('www.','')
                if nh==host and not any(low.endswith(x) for x in ('.jpg','.png','.doc','.xls','.zip','.mp4')):
                    queue.append((url,d+1))
    return pdfs[:maxpdf],pages,seen

def work(item):
    sid,name,home=item
    res={'id':sid,'name':name,'pdfs':[],'pages':0,'notes':[]}
    try:
        pdfs,pages,seen=crawl(sid,name,home)
    except Exception as e:
        res['notes'].append('crawlerr '+str(e)); return res
    res['pages']=pages
    res['pdfs']=pdfs
    return res

if __name__=='__main__':
    schools=json.load(open('data/reports/manual/shatin_2.json'))
    out={}
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        for r in ex.map(work,[(s['id'],s['name'],s['web']) for s in schools]):
            out[r['id']]=r
            print(r['id'],r['name'],'pages',r['pages'],'pdfs',len(r['pdfs']),flush=True)
    json.dump(out,open('data/reports/s2_crawl.json','w'),ensure_ascii=False,indent=1)
    for k,v in out.items():
        print('\n==',k,v['name'])
        for p in v['pdfs'][:15]: print('  ',p)
