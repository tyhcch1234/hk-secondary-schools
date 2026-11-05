import json,re,os,ssl,subprocess,tempfile,urllib.request,sys,concurrent.futures as cf
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
    'Accept':'application/pdf,text/html,*/*','Accept-Language':'zh-HK,zh;q=0.9,en;q=0.8','Referer':'https://www.google.com/'}
os.makedirs('data/reports/manual/txt',exist_ok=True)
def dl(u):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60,context=ctx)
        b=r.read(30*1024*1024)
        return b
    except Exception as e:
        return None
def pdftext(b):
    fd,p=tempfile.mkstemp(suffix='.pdf'); os.write(fd,b); os.close(fd)
    try:
        return subprocess.run(['pdftotext','-layout','-enc','UTF-8',p,'-'],capture_output=True,text=True,timeout=200).stdout
    except Exception: return ''
    finally:
        try: os.unlink(p)
        except Exception: pass
YRE=re.compile('20(2[1-6])[-–—~至/ ]*((?:20)?2[2-7])')
def findyear(t,u):
    s=(u or '')+' '+t[:4000]
    for a,b in YRE.findall(s):
        a=2000+int(a); b=int(b) if len(b)==4 else 2000+int(b)
        if a+1==b and 2021<=a<=2025: return f'{a}-{str(b)[2:]}'
    return ''
def one(u):
    b=dl(u)
    if not b or b[:4]!=b'%PDF': return u,None,0,'notpdf'
    t=pdftext(b)
    return u,t,len(t),''
if __name__=='__main__':
    jobs=json.load(open(sys.argv[1]))  # {id: [urls]}
    log={}
    for sid,urls in jobs.items():
        log[sid]=[]
        with cf.ThreadPoolExecutor(max_workers=5) as ex:
            for u,t,n,err in ex.map(one,urls):
                y=findyear(t or '',u) if t else ''
                info=(u,n,err,y)
                log[sid].append(info)
                print(sid,n,err,y,u[-70:],flush=True)
                if t and n>1500:
                    open(f'data/reports/manual/txt/{sid}_{y or "unk"}.txt','w',encoding='utf-8').write(t)
    json.dump(log,open('data/reports/s2_fetchlog.json','w'),ensure_ascii=False,indent=1)
