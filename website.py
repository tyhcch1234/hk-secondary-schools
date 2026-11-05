import json, re, subprocess, concurrent.futures as cf, os
d=json.load(open('data/schools_raw.json'))
def web(sid):
    try:
        t=subprocess.run(['pdftotext','-enc','UTF-8','-f','1','-l','1',f'data/pdf/{sid}.pdf','-'],
                         capture_output=True,text=True,timeout=60).stdout
    except Exception: return sid,''
    urls=re.findall(r'(?:https?://)?(?:www\.)?[A-Za-z0-9\-\.]+\.(?:edu\.hk|com\.hk|org\.hk|hk|com|net|org)(?:/[^\s，、]*)?', t)
    best=''
    for u in urls:
        if 'chsc' in u: continue
        if not u.startswith('http'): u='http://'+u
        if 'edb.gov.hk' in u: continue
        best=u; break
    return sid,best.rstrip('.,)）')
res={}
with cf.ThreadPoolExecutor(max_workers=8) as ex:
    for sid,u in ex.map(web,[s['sch_id'] for s in d]): res[sid]=u
json.dump(res, open('data/websites.json','w'), ensure_ascii=False, indent=1)
print(sum(1 for v in res.values() if v), 'of', len(res))
print(list(res.items())[:8])
