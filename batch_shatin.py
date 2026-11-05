import json,re,ssl,os,subprocess,tempfile,urllib.request,urllib.parse,concurrent.futures as cf
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36','Referer':'https://www.google.com/'}
def get(u,t=15,maxb=900000):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=t,context=ctx)
        b=r.read(maxb); 
        return b, r.geturl(), r.headers.get('Content-Type','')
    except Exception: return None,None,''
SCHOOLS={225:'cmos.edu.hk',352:'lamhonkwong.edu.hk',263:'stgss.edu.hk',336:'ktscss.edu.hk',207:'mosttss.edu.hk',161:'blmcss.edu.hk',96:'bwwtc.edu.hk',240:'cymcac.edu.hk',142:'christcollege.edu.hk',375:'hkbuas.edu.hk',390:'fyk.edu.hk',258:'tic.edu.hk',265:'kccshatin.edu.hk',185:'lstyoungkhl.edu.hk',356:'nyss.edu.hk',20:'plkcwc.edu.hk',236:'puikiu.edu.hk',296:'skhtst.edu.hk',382:'spkc.edu.hk',51:'tsss.edu.hk',62:'twghfwfts.edu.hk',64:'twghwflc.edu.hk',252:'ychtcy.edu.hk'}
PATHS=['/','/school-report','/report','/about/report','/school-document','/school-documents','/tc/report','/en/report']
def probe(item):
    sid,dom=item
    out={'sid':sid,'home':None,'pdfs':[],'note':''}
    home=None
    for u in [f'https://{dom}',f'https://www.{dom}',f'http://{dom}']+[f'https://{dom}{p}' for p in PATHS[1:4]]:
        b,fu,ct=get(u,12)
        if b and 'html' in ct:
            home=(b.decode('utf-8','ignore'),fu); out['home']=fu; break
    if not home: out['note']='home_fail'; return out
    html,base=home
    links=re.findall(r'href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',html,re.S|re.I)
    cand=[]
    for href,txt in links:
        t2=re.sub(r'<[^>]+>','',txt); t2=re.sub(r'\s+',' ',t2).strip()
        u=urllib.parse.urljoin(base,href)
        if re.search(r'(報告|report|校務|年報)',t2+u,re.I): cand.append(u)
    cand=list(dict.fromkeys(cand))[:4]
    pdfs=[]
    for cu in cand:
        if cu.lower().endswith('.pdf'): pdfs.append(cu); continue
        b,fu,ct=get(cu,12)
        if b and 'html' in ct:
            for href,txt in re.findall(r'href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',b.decode('utf-8','ignore'),re.S|re.I):
                u=urllib.parse.urljoin(fu,href)
                if u.lower().endswith('.pdf') and re.search(r'(報告|report|校務|年報)',u+txt,re.I): pdfs.append(u)
    out['pdfs']=list(dict.fromkeys(pdfs))[:6]
    if not out['pdfs']: out['note']='no_pdf'
    return out
if __name__=='__main__':
    res=[]
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        for r in ex.map(probe, SCHOOLS.items()): res.append(r)
    json.dump({str(r['sid']):r for r in res},open('data/reports/shatin_probe.json','w'),ensure_ascii=False,indent=1)
    print('probed',len(res),'with pdf',sum(1 for r in res if r['pdfs']))
